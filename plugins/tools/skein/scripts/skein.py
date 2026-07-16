#!/usr/bin/env python3
"""SKEIN — 独立任务管理引擎 (零 trellis 依赖, 纯 stdlib)。

单文件子命令引擎: 生命周期 (create/start/finish/archive) + worktree 隔离 + task.md 看板。
skein.py 自身就是引擎, 无外部 hook 层 — start/finish 直接干活。

工作区布局 (git 根下):
  .skein/.gitignore               init 生成: 忽略 task.md (从 task.json 无损重建); 另补 worktree_root 到根 .gitignore
  .skein/config.yaml              设置 (max_active / max_parallel / auto_commit / worktree_root)
  .skein/task.json                {tasks:[{id,status,deps,worktree}]}  顶层状态汇总 — 脚本维护, AI 禁读写
  .skein/task.md                  顶层看板 (task.json 渲染, git 忽略) — 脚本维护, AI 禁读写
  .skein/task/<id>/task.json      单 task 记录 + subtask DAG — 脚本维护, AI 禁读写
  .skein/task/<id>/task.md        单 task 子任务看板 + 调度 DAG (渲染) — 脚本维护, AI 禁读写
  .skein/task/<id>/prd.md         主入口: 需求 + 索引区 (create 落脚手架, skein-plan 填, AI 可读写)
  .skein/task/<id>/design.md      详细设计 (架构/取舍/选型; 不含调度图, 调度归 task.json)
  .skein/task/<id>/findings.md    深度调研收敛结论 (research/ 存过程, 此文件收敛; skein-plan/main 汇总写)
  .skein/task/<id>/research/       researcher 过程笔记 (多篇, 最终收敛进 findings.md)
  .skein/task/archive/<年>/<月-日>/<id>/  归档 (按完成日期分层)

四个 task.json/task.md (顶层 + per-task) 全由本脚本维护, AI 只经命令 stdout 取态
(current/list/board/subtask list/ready), 禁直接 Read/Edit/Write (skein-hooks guard 硬阻)。
"""
import argparse
import contextlib
import datetime
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # 同目录 hooklib 可导入 (hook 环境非 Bash PATH)
from hooklib import budget_guard, Debug, debug_enabled  # noqa: E402

SESSION_CTX_BUDGET_TOKENS = 400  # session-context 注入 token 硬预算 (active task ≤2, 正常远低于)

# --debug 叙事器 (默认关): main() 按 --debug/SKEIN_DEBUG 重建。git/写盘/锁等模块级函数经此叙事,
# 全走 stderr — stdout 保持机器纯净 (被 AI/hook 消费)。
DBG = Debug(False)

# task 状态 (中文落盘, 逻辑比较用常量)
S_PENDING = "待处理"
S_ACTIVE = "进行中"
S_CHECK = "检查中"
S_DONE = "已完成"
STATUS_ACTIVE = {S_ACTIVE, S_CHECK}
# list --status 过滤别名 (英文简写 → 中文态); open/未完成 特判非 done
_STATUS_ALIAS = {"pending": S_PENDING, "active": S_ACTIVE, "check": S_CHECK, "done": S_DONE}
# 看板排序: 进行中 > 检查中 > 待处理 > 已完成 (同状态内按 id 稳定)
STATUS_ORDER = {S_ACTIVE: 0, S_CHECK: 1, S_PENDING: 2, S_DONE: 3}
# subtask 状态
SS_PENDING = "待处理"
SS_RUNNING = "运行中"
SS_DONE = "已完成"
SS_FAILED = "失败"
# 可读 task id: kebab-case slug, 兼作 git 分支名 + 目录名 (人工传入)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# 拒短字母+数字编号 (t01/t2/ab12): 不可读, 强制描述性 slug. subtask sid 不受此限.
CODE_ID_RE = re.compile(r"^[a-z]{1,4}\d+$")
# 看板主题 = 装饰预设 (值 = board/themes/ 下 css 文件名). 每个预设 = 5 原语 (卡片质感/边框/圆角/字型/底纹)
# 固定搭配 + 一处签名点缀, 结构全从 palette token 派生 → 自动随配色/明暗变, 每预设不塌成同一套灰.
THEMES = [("skein", "skein"),
          ("minimal", "极简"), ("terminal", "终端"), ("glass", "磨砂"),
          ("blueprint", "蓝图"), ("sketch", "手绘"), ("neumorphism", "浮起"),
          ("holographic", "虹彩"), ("magazine", "杂志"),
          ("sketchdark", "夜绘")]


def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳


# 插件无法直接发货 settings.json 的 env 块 (plugin.json 无 env 字段)。
# 官方持久化 env 的机制: SessionStart hook 往 $CLAUDE_ENV_FILE 追加 export。
# 这样这些 env 随 skein 插件的 SessionStart hook 一起发货, 不落用户项目 settings。
_ENV_EXPORTS = (
    "export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1",
    # skein 调度只用单 subagent (skein subtask + 单 Agent 调用), 禁 agent-teams 防误升级到 team。
    # CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0 = 显式关闭 (官方 docs/en/agent-teams: 默认即关, 此为冗余保障)。
    "export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0",
)


def _persist_bash_cwd_env():
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return  # 非 SessionStart/Setup/CwdChanged/FileChanged 事件时不可用, 静默跳过
    try:
        p = Path(env_file)
        existing = p.read_text() if p.exists() else ""
        missing = [e for e in _ENV_EXPORTS if e not in existing]  # 幂等: 逐条查, 已写的不重复
        if missing:
            with p.open("a") as f:
                f.write("\n".join(missing) + "\n")
    except OSError:
        pass  # env 持久化尽力而为, 失败不阻断 session-context 主流程


@contextlib.contextmanager
def _workspace_lock(lock_path: Path, timeout=10.0, poll=0.05):
    # 工作区级排他写锁 (fcntl.flock): 防多 skein 进程并发 read-modify-write 破坏 task.json。
    # 阻塞等待锁释放, 超 timeout 秒仍拿不到 → SystemExit (非死等)。CLI 短命, 全局锁足够。
    # ponytail: global lock, per-task locks if throughput matters.
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_path, "w")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise SystemExit(
                        f"获取 .skein 写锁超时 ({timeout}s) — 另一 skein 进程持锁未释放: {lock_path}")
                time.sleep(poll)
        DBG.log(f"🔒 已获工作区写锁 {lock_path}", style="dim")
        yield
    finally:
        f.close()  # 关闭即释放 flock
        DBG.log("🔓 释放工作区写锁", style="dim")


# ponytail: config 只有 4 个扁平标量键 → 手写 mini YAML 读写, 免 PyYAML 依赖。
# ceiling: 只认 `key: value` + `#` 注释, 不支持嵌套/列表/多行。够 config 用即止。
def _yaml_load(text: str) -> dict:
    out = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip().strip("'\"")
        if v in ("true", "false"):
            v = v == "true"
        elif v.lstrip("-").isdigit():
            v = int(v)
        out[k.strip()] = v
    return out


def _yaml_dump(d: dict) -> str:
    def fmt(v):
        return "true" if v is True else "false" if v is False else str(v)
    return "".join(f"{k}: {fmt(v)}\n" for k, v in d.items())


# config.yaml 全部键的默认值 — init 写入 + config() 缺键自动回填的唯一真值源。
CONFIG_DEFAULTS = {
    "max_active": 2,
    "max_parallel": 2,
    "auto_commit": True,
    "use_worktree": True,  # False→禁用 worktree 隔离 (原地执行, 同非 git); start 不建、doctor 不查 worktree
    "worktree_root": ".worktrees",
    "retain_days": 7,  # 完成 task 保留天数; 0=finish 即归档, 负=永不自动
    "board_theme": "skein",  # 唯一看板外观选项; 配色/明暗已烘焙进各主题预设 (skein=默认旗舰主题)
    "web_serve": True,  # 看板 http 服务总开关: True→monitor 每 session 起持久服务 + view 起 http 服务; False→monitor no-op + view 仅打印路径 (不主动开)
    "board_open": True,  # 仅 view 命令生效 (monitor serve 从不开浏览器): True→view 起服务后自动开浏览器; False→只打印 URL 不开
}


def git(*args, cwd=None, check=True, capture=True):
    DBG.log(f"$ git {' '.join(args)}" + (f"   (cwd={cwd})" if cwd else ""), style="dim")
    r = subprocess.run(
        ["git", *args], cwd=cwd, check=False,
        capture_output=capture, text=True,
    )
    if r.returncode != 0:
        DBG.log(f"  ↳ git exit={r.returncode}", style="yellow")
    if check and r.returncode != 0:
        sys.stderr.write((r.stderr or "") + "\n")
        raise SystemExit(f"git {' '.join(args)} 失败 (exit {r.returncode})")
    return r


class Skein:
    def __init__(self):
        # git 非强制: 在 git 仓库内则用其根 + 启用 worktree 隔离; 否则用 cwd 原地执行
        # (微服务/前后端分离: cwd 无 git, 子目录各自独立仓库 — 正是最需要不挡 git 的场景)。
        r = git("rev-parse", "--show-toplevel", check=False)
        self.git = r.returncode == 0
        self.root = Path(r.stdout.strip()) if self.git else Path.cwd()
        self.dir = self.root / ".skein"
        self.tasks = self.dir / "task"
        self.archive_dir = self.tasks / "archive"
        # 看板 title/标题带项目名, 用户一眼知是哪个项目
        self.proj = self.root.name
        self.html_path = self.dir / "task.html"

    # ---- 存取 ----
    def config(self) -> dict:
        f = self.dir / "config.yaml"
        if not f.exists():
            raise SystemExit("未初始化 — 先跑 `skein.py init`")
        cfg = _yaml_load(f.read_text())
        # 缺键自动回填默认值 (旧 config.yaml 补新增键), 有变更才回写省磁盘
        missing = {k: v for k, v in CONFIG_DEFAULTS.items() if k not in cfg}
        if missing:
            cfg = {**CONFIG_DEFAULTS, **cfg}  # 保留用户值, 仅补缺键
            f.write_text(_yaml_dump(cfg))
        # 用户在插件启用时确认的 userConfig 优先于 config.yaml (经 CLAUDE_PLUGIN_OPTION_* 传入)
        for k in ("max_active", "max_parallel"):
            v = os.environ.get(f"CLAUDE_PLUGIN_OPTION_{k.upper()}")
            if v and v.strip().isdigit():
                cfg[k] = int(v)
        return cfg

    def _set_config(self, key, value) -> bool:
        # 看板 UI 改配置 (如主题) 落回 config.yaml。仅白名单键, 有变更才写。返回是否写入。
        f = self.dir / "config.yaml"
        if not f.exists() or key not in CONFIG_DEFAULTS:
            return False
        cfg = _yaml_load(f.read_text())
        if cfg.get(key) == value:
            return False
        cfg[key] = value
        f.write_text(_yaml_dump({**CONFIG_DEFAULTS, **cfg}))
        return True

    def _autoclean(self, days=None) -> list:
        # 惰性归档: 已完成且超保留期的 task 移入 archive (保留期内留看板)。days 省略用 config retain_days。
        # 负数 = 永不自动清理。0 = finish 即归档 (旧行为)。每次 _sync 触发, 无需守护进程。
        d = days if days is not None else self.config().get("retain_days", 7)
        if d is None or int(d) < 0:
            return []
        cutoff = now() - int(d) * 86400
        archived = []
        for t in self._all():
            if t["status"] == S_DONE and t.get("finished", t.get("done_at", 0)) <= cutoff:
                self._archive(t["id"])
                archived.append(t["id"])
        return archived

    def _sync(self):
        # 顶层 task.json 唯一写入口: tasks 是未归档 task 的去规范化状态镜像 (per-task task.json 仍单一真值源),
        # 每次变更重算, 免各处同步。无 task 级 focus — 无未完成前置的 task 皆可并行 (DAG 就绪即跑)。
        self._autoclean()  # 惰性归档超保留期的完成 task, 再重算索引
        tasks = [{"id": t["id"], "status": t["status"], "deps": t["deps"],
                  "worktree": t.get("worktree")} for t in self._all()]
        self._write_if_changed(self.dir / "task.json",
            json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
        self._board(None)  # 变更即刷 task.md + task.html (_board 内已调 _board_html; 皆 diff 后写)

    def _load(self, tid) -> dict:
        f = self.tasks / tid / "task.json"
        if not f.exists():
            raise SystemExit(f"task 不存在: {tid}")
        return json.loads(f.read_text())

    def _save(self, t: dict):
        t["updated"] = now()
        # 先算 diff 再写: 内容未变则跳过 (增量, 不全量覆盖 → 免无谓 IO/mtime 抖动)
        self._write_if_changed(self.tasks / t["id"] / "task.json",
                               json.dumps(t, ensure_ascii=False, indent=2))
        self._board_task(t)  # task.json 唯一写入口 → 同步渲染子任务看板, 免各调用点漏刷 (task.json 变更即同步 task.md)
        self._board_html()  # subtask 变更 (add/done/fail) 也刷全局 html, 免看板漂移 (subtasks 不进顶层 index, 故不走 _sync)

    def _all(self) -> list:
        if not self.tasks.exists():
            return []
        out = []
        for d in sorted(self.tasks.iterdir()):
            if d.name == "archive":
                continue
            f = d / "task.json"
            if f.exists():
                t = json.loads(f.read_text())
                out.append(t)
                DBG.log(f"读 {f}  → id={t.get('id')} status={t.get('status')} "
                        f"subtasks={len(t.get('subtasks', []))} deps={t.get('deps') or '-'} "
                        f"contracts={len(t.get('contracts', []))}", style="dim")
        # 状态优先排序 (进行中>检查中>待处理>已完成), 同状态内保持 id 序
        out.sort(key=lambda t: STATUS_ORDER.get(t["status"], 9))
        return out

    def _render_tasks(self) -> list:
        # 看板专用读取: 顶层 task.json 索引 + 各 task/<id>/task.json 明细 并集为数据源。
        # per-task 目录是真值源 (有 subtask/desc/name, 明细胜出); 顶层镜像补齐目录被删/迁移丢失、
        # 仅存于索引的 task (只 id/status/deps/worktree), 免看板静默空白。
        # 只服务 _board / _board_html 只读渲染; 调度/mutation 仍走严格 _all() (幽灵骨架不可派发/归档)。
        # ponytail: 顶层索引本就无 name 字段, 看板对幽灵骨架直接用 id 显示 (task 一向以 id 标识, 非降级);
        #           要恢复 subtask/desc 等完整明细需从有 per-task 目录的分支 checkout。
        DBG.rule("看板数据源合并 (顶层索引 ∪ per-task 明细)")
        tasks = self._all()
        DBG.log(f"per-task 明细: {len(tasks)} 个 (真值源, 明细胜出)", style="cyan")
        have = {t["id"] for t in tasks}
        mirror = self.dir / "task.json"
        mirrored = 0
        if mirror.exists():
            try:
                rows = json.loads(mirror.read_text()).get("tasks", [])
            except (json.JSONDecodeError, OSError):
                rows = []
            DBG.log(f"读顶层镜像 {mirror}  → {len(rows)} 条索引", style="dim")
            for r in rows:
                if r["id"] in have:  # per-task 明细已覆盖 → 保留明细, 跳过镜像骨架
                    continue
                tasks.append({"id": r["id"], "name": r.get("name", r["id"]), "status": r["status"],
                              "deps": r.get("deps", []), "worktree": r.get("worktree")})
                mirrored += 1
                DBG.log(f"  + 镜像补齐幽灵骨架 {r['id']} (per-task 目录缺失, 仅顶层索引可用)", style="yellow")
        else:
            DBG.log(f"顶层镜像 {mirror} 不存在, 仅用 per-task 明细", style="dim")
        tasks.sort(key=lambda t: STATUS_ORDER.get(t["status"], 9))
        by_status = {}
        sub_total = 0
        sub_by_status = {}
        with_sub = 0
        for t in tasks:
            by_status[t["status"]] = by_status.get(t["status"], 0) + 1
            subs = t.get("subtasks", [])
            if subs:
                with_sub += 1
            sub_total += len(subs)
            for s in subs:
                ss = s.get("status", "?")
                sub_by_status[ss] = sub_by_status.get(ss, 0) + 1
        DBG.log(f"subtask 统计: 合计 {sub_total} 个, 分布于 {with_sub} 个 task "
                f"(其余 {len(tasks) - with_sub} 个无 subtask/幽灵骨架)", style="cyan")
        DBG.kv({"合计 task": len(tasks), "明细": len(tasks) - mirrored, "镜像补齐": mirrored,
                **{f"状态·{k}": v for k, v in by_status.items()},
                "合计 subtask": sub_total, "含 subtask 的 task": with_sub,
                **{f"subtask·{k}": v for k, v in sub_by_status.items()}}, title="看板数据源汇总")
        return tasks

    def _archived_path(self, tid):
        # 归档嵌套: archive/<年>/<月-日>/<id>
        hits = list(self.archive_dir.glob(f"*/*/{tid}")) if self.archive_dir.exists() else []
        return hits[0] if hits else None

    def _active(self) -> list:
        return [t for t in self._all() if t["status"] in STATUS_ACTIVE]

    def _used_ids(self) -> set:
        used = {p.name for p in self.tasks.iterdir() if p.name != "archive"} if self.tasks.exists() else set()
        used |= {p.name for p in self.archive_dir.glob("*/*/*")} if self.archive_dir.exists() else set()
        return used

    def _scaffold(self, tid: str, name: str):
        """落 planning 三工件脚手架 (prd 主入口 / design 详细设计 / findings 调研收敛).
        模板极简 (只给骨架标题, 正文 planning 填), 避免占 token; 已存在则不覆盖。
        调度 DAG / 子任务不在此 — 归 task.json (脚本维护)。"""
        d = self.tasks / tid
        files = {
            "prd.md": (
                f"# {name} — PRD (主入口)\n\n"
                "## 目标\n要解决什么 / 用户价值 / 成功长什么样:\n- [ ] TODO: 填目标\n\n"
                "## 边界\n范围内 / 范围外 (非目标) / 已知约束:\n- [ ] TODO: 填边界\n\n"
                "## 验收标准\n可执行、可核对的完成断言 (逐条):\n- [ ] TODO: 填验收标准\n\n"
                "## 索引\n- [ ] TODO: 补全链接\n- 详细设计: [design.md](design.md)\n"
                "- 调研收敛: [findings.md](findings.md)\n"
                "- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list " + tid + "`)\n"),
            "design.md": (
                f"# {name} — 详细设计\n\n"
                "架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):\n"),
            "findings.md": (
                f"# {name} — 调研收敛\n\n"
                "深度调研的收敛结论 + 依据/引用 (过程笔记存 research/):\n"),
        }
        for fn, body in files.items():
            p = d / fn
            if not p.exists():
                p.write_text(body)

    # ---- 命令 ----
    def init(self, _):
        self.dir.mkdir(exist_ok=True)
        self.tasks.mkdir(exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.dir / "config.yaml"
        if not cfg.exists():
            cfg.write_text(_yaml_dump(dict(CONFIG_DEFAULTS)))
        # .skein/.gitignore — 忽略自动渲染看板 (task.md 从 task.json 无损重建, 且 AI 禁读写)
        gi = self.dir / ".gitignore"
        if not gi.exists():
            gi.write_text("# skein.py 自动渲染, 从 task.json 无损重建, 不入库\ntask.md\ntask.html\nboard/\n*.lock\n")
        # worktree 目录在 git 根 (worktree_root), .skein/.gitignore 管不到 → 补到根 .gitignore
        # (仅 git 仓库需要; 非 git 无 worktree, 不制造多余 .gitignore)。子仓的忽略由 _mkwt 各自补。
        if self.git:
            self._ignore_wt(self.root)
        if not (self.dir / "task.json").exists():
            self._sync()
        self._board(None)
        print(f"已初始化 SKEIN 工作区: {self.dir}")

    def create(self, a):
        tid = a.id.strip()
        # 可读 id: 人工传入, 必须是 slug (kebab-case, 兼作 git 分支名 + 目录名)
        if not SLUG_RE.match(tid):
            raise SystemExit(
                f"非法 id: {tid!r} — 须为 kebab-case slug "
                "(小写字母/数字/连字符, 字母数字开头, 如 order-create-api)")
        if CODE_ID_RE.match(tid):
            raise SystemExit(
                f"id 须可读: {tid!r} 是字母+数字编号 — 用描述性 slug "
                "(如 order-create-api / user-auth), 勿用 t01 这类代号")
        if tid in self._used_ids():
            raise SystemExit(f"id 已占用: {tid} — 换一个 (含已归档的也不可复用)")
        (self.tasks / tid).mkdir(parents=True)
        self._scaffold(tid, a.name)  # 落 prd/design/findings 脚手架 (planning 填)
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        repos = self._parse_repos(getattr(a, "repos", None))
        t = {
            "id": tid, "name": a.name, "desc": a.desc,
            "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
            "repos": repos,          # planning 声明的目标子 git (rel 路径; 空=单根/原地模式)
            "worktree": None, "worktrees": [], "branch": f"skein/{tid}",
            "estimate": a.estimate,  # AI 执行预期耗时 (分钟, planning 填; None=未估)
            "created": now(),        # 创建时刻
            "started": None,         # exec 时刻 (start 时置)
            "finished": None,        # 完成时刻 (finish 时置; 保留期从此计)
            "updated": now(),
        }
        self._save(t)  # _save 已渲染子任务看板
        self._sync()  # 刷新顶层 tasks 索引 + 看板 + html
        print(f"{tid}\t{self.tasks / tid}")

    @staticmethod
    def _parse_repos(raw) -> list:
        # "a, b/c" → ["a","b/c"]; 归一去空/去首尾斜杠 ('.' 保留=根仓)
        return [p.strip().strip("/") or "." for p in (raw or "").split(",") if p.strip()]

    def _wts(self, t) -> list:
        # task 的 worktree 生命周期真值; 兼容旧结构 (仅 scalar worktree/branch)
        ws = t.get("worktrees")
        if ws:
            return ws
        rel = t.get("worktree")
        if rel:
            return [{"repo": ".", "wt": rel, "branch": t.get("branch"), "merged": False}]
        return []

    def _ignore_wt(self, repo_dir: Path):
        # 把 worktree_root 写进该 git 仓 .gitignore (缺则补), 免 worktree 目录污染该仓 status。
        # 子仓是独立 git/submodule, root .gitignore 管不到, 故各子仓自补。
        wt = self.config()["worktree_root"].rstrip("/") + "/"
        gi = repo_dir / ".gitignore"
        existing = gi.read_text() if gi.exists() else ""
        if wt in existing:
            return
        sep = "\n" if existing and not existing.endswith("\n") else ""
        with gi.open("a") as f:
            f.write(f"{sep}# skein worktree 隔离 (任务源码改动落此, 不入库)\n{wt}\n")

    def _mkwt(self, t, repo, cfg) -> dict:
        # 在指定子 git (repo='.'=根仓) 建 worktree+branch; 校验确是 git 工作树 (含 submodule)
        sub = self.root if repo == "." else self.root / repo
        if not sub.exists():
            raise SystemExit(f"repos 声明的路径不存在: {repo}")
        rc = git("rev-parse", "--is-inside-work-tree", cwd=sub, check=False)
        if rc.returncode != 0 or rc.stdout.strip() != "true":
            raise SystemExit(f"{repo} 不是 git 仓库 (repos 只能声明 git 仓/submodule)")
        wt_root = cfg["worktree_root"].strip("/")
        # worktree 落在**该子 git 内部** (<repo>/<worktree_root>/skein-<id>), 相对 root 存盘免绝对路径入库。
        # 每子仓各自 .worktrees 目录, 天然无碰撞 (旧版全塞 root, 现落各仓内)。
        base = wt_root if repo == "." else f"{repo}/{wt_root}"
        wt_rel = f"{base}/skein-{t['id']}"
        git("worktree", "add", "-b", t["branch"], str(self.root / wt_rel), "HEAD", cwd=sub)
        if repo != ".":
            self._ignore_wt(sub)  # 子仓自忽略; 根仓已由 init 补
        return {"repo": repo, "wt": wt_rel, "branch": t["branch"], "merged": False}

    def repos(self, a):
        # 查/声明 task 的目标子 git (planning 声明: 每个各开 worktree)。仅 pending 可改 (start 后 worktree 已定)
        t = self._load(a.id)
        if a.set is None:
            print("\n".join(t.get("repos") or []) or "(未声明子 git — 单根/原地模式)")
            return
        if t["status"] != S_PENDING:
            raise SystemExit(f"{a.id} 状态 {t['status']}, repos 只能在 start 前 (pending) 声明")
        t["repos"] = self._parse_repos(a.set)
        self._save(t)
        self._sync()
        print(f"{a.id} repos = {', '.join(t['repos']) or '(空)'}")

    def start(self, a):
        t = self._load(a.id)
        if t["status"] != S_PENDING:
            raise SystemExit(f"{a.id} 状态为 {t['status']}, 只能 start 待处理 task")
        if not t.get("subtasks"):
            raise SystemExit(f"{a.id} 无 subtask — start 前先 `subtask add {a.id} <sid> ...` 至少登记 1 个 (planning 拆分产物)")
        cfg = self.config()
        active = self._active()
        if len(active) >= cfg["max_active"]:
            raise SystemExit(
                f"task 级并发上限 {cfg['max_active']} (当前 active: "
                f"{', '.join(x['id'] for x in active)}), 先 finish 一个再 start")
        undone = [d for d in t["deps"] if self._dep_unfinished(d)]
        if undone:
            raise SystemExit(f"前置未完成: {', '.join(undone)} — 先 finish 它们")
        t["status"] = S_ACTIVE
        repos = t.get("repos") or []
        wt_cfg = cfg.get("use_worktree", True)
        wt_on = self.git and wt_cfg  # 单根 worktree: 需根仓是 git; 配置禁用→原地执行
        # --repos 的 git 性由 _mkwt 逐子仓校验 (worktree 落各子仓内), 与父目录是否 git 无关 —
        # 故只在 config 显式禁用时挡, 不吃 self.git (支持非 git 父 + 多 git 子的微服务布局)。
        if repos and not wt_cfg:
            raise SystemExit(
                f"{a.id} 声明了 --repos 但 config use_worktree=false — 多子 git 隔离需启用 worktree")
        if repos:
            # 多子 git: planning 声明的每个子 git 各开 worktree+branch (并列 repo / submodule 同理)
            t["worktrees"] = [self._mkwt(t, r, cfg) for r in repos]
            t["worktree"] = ", ".join(w["wt"] for w in t["worktrees"])  # 显示汇总
        elif wt_on:
            rel = f"{cfg['worktree_root']}/skein-{a.id}"  # 相对 project root 存盘, 免机器绝对路径入库
            git("worktree", "add", "-b", t["branch"], str(self.root / rel), "HEAD", cwd=self.root)
            t["worktree"] = rel
            t["worktrees"] = [{"repo": ".", "wt": rel, "branch": t["branch"], "merged": False}]
        else:
            t["worktree"] = None  # 非 git / config 禁用, 无 repos: 原地执行, 无 worktree 隔离
            t["worktrees"] = []
        if not t.get("started"):
            t["started"] = now()  # exec 时刻 (首次 start; 重启不覆盖)
        self._save(t)
        self._sync()
        if t["worktrees"]:
            loc = "\n".join(f"worktree: {w['wt']} (子 git: {w['repo']}, branch: {w['branch']})"
                            for w in t["worktrees"])
        else:
            reason = "config use_worktree=false" if self.git else "非 git 仓库"
            loc = f"{reason}: 原地执行 (无 worktree 隔离)"
        print(f"{a.id} started\n{loc}")

    def _dep_unfinished(self, dep) -> bool:
        # 归档即视为完成
        if self._archived_path(dep):
            return False
        f = self.tasks / dep / "task.json"
        if not f.exists():
            return False  # 未知 dep 不阻塞
        return json.loads(f.read_text())["status"] != S_DONE

    def finish(self, a):
        tid = a.id
        t = self._load(tid)
        if t["status"] not in STATUS_ACTIVE:
            raise SystemExit(f"{tid} 状态 {t['status']}, 非 active 无法 finish")
        cfg = self.config()
        wts = self._wts(t)
        conflicts = []  # [(repo, 冲突输出)] — 部分子 git 冲突时保留已合并进度, task 留 active 供幂等重跑
        for w in wts:
            if w.get("merged"):
                continue  # 幂等: 前次已合并的子 git 跳过 (部分冲突重跑场景)
            sub = self.root if w["repo"] == "." else self.root / w["repo"]  # merge 落各子 git
            wt = self.root / w["wt"]
            if not wt.exists():
                sys.stderr.write(
                    f"{tid} worktree 缺失 ({w['wt']}) — 跳过, 分支 {w['branch']} 若有提交未并入\n")
                w["merged"] = True  # 缺失即无从合并, 标记免卡住
                continue
            if cfg.get("auto_commit"):
                git("add", "-A", cwd=wt)
                r = git("commit", "-m", f"skein({tid}): {t['name']}", cwd=wt, check=False)
                if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
                    sys.stderr.write(r.stdout + r.stderr)
            else:
                # auto_commit 关: 用户须自行提交; 有未提交改动则拒绝 (下面 --force 会强删丢失)
                st = git("status", "--porcelain", cwd=wt, check=False)
                if st.stdout.strip():
                    raise SystemExit(
                        f"{tid} worktree 有未提交改动且 auto_commit=false — "
                        f"先手动提交再 finish (禁强删丢失):\n{wt}")
            # 合并回该子 git 的主工作区
            m = git("merge", "--no-ff", w["branch"], "-m",
                    f"skein: merge {tid} {t['name']}", cwd=sub, check=False)
            if m.returncode != 0:
                git("merge", "--abort", cwd=sub, check=False)
                conflicts.append((w["repo"], m.stdout + m.stderr))
                continue
            git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
            git("branch", "-D", w["branch"], cwd=sub, check=False)
            w["merged"] = True
        if conflicts:
            # 保存已合并进度 (worktrees 各 merged 标记), task 仍 active — 解冲突后重跑 finish 只补未合并子 git
            t["worktrees"] = wts
            self._save(t)
            self._sync()
            detail = "\n".join(f"  子 git {r}: 冲突已 abort" for r, _ in conflicts)
            raise SystemExit(
                f"{tid} 部分子 git 合并冲突, 已合并的保留、task 仍 active。"
                f"解冲突后重跑 finish (幂等跳过已合并):\n{detail}")
        t["status"] = S_DONE
        t["worktree"] = None
        t["worktrees"] = []
        t["finished"] = now()  # 完成时刻 — 保留期从此计, 超 retain_days 由 _autoclean 归档
        self._save(t)
        self._sync()  # 重写顶层索引 (完成 task 仍留看板; retain_days=0 时 _autoclean 即归档)
        archived = not (self.tasks / tid).exists()  # retain_days<=0 → 已被 _autoclean 归档
        cfg = self.config()
        rest = self._active()
        tail = (f", 剩余 active: {', '.join(x['id'] for x in rest)}" if rest else ", 无剩余 active")
        keep = "已归档" if archived else f"保留 {cfg.get('retain_days', 7)} 天后自动归档"
        print(f"{tid} finished ({keep})" + tail)

    def archive(self, a):
        # 归档 = 丢弃 (不 merge): 先销 worktree/branch, 免残留悬挂
        f = self.tasks / a.id / "task.json"
        if f.exists():
            t = json.loads(f.read_text())
            for w in self._wts(t):
                sub = self.root if w["repo"] == "." else self.root / w["repo"]
                wt = self.root / w["wt"]
                if wt.exists():
                    git("worktree", "remove", str(wt), "--force", cwd=sub, check=False)
                git("branch", "-D", w["branch"], cwd=sub, check=False)
        self._archive(a.id)
        self._sync()  # 重写顶层 tasks 索引 (去掉已归档 task)
        print(f"{a.id} archived")

    def _archive(self, tid):
        src = self.tasks / tid
        if not src.exists():
            return
        d = datetime.datetime.now()
        dst = self.archive_dir / d.strftime("%Y") / d.strftime("%m-%d") / tid
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            shutil.rmtree(dst)
        shutil.move(str(src), str(dst))

    def clean(self, a):
        # 用户主动清理 (skein-clean skill 唯一入口): 归档完成超 --days 天的 task。
        # ponytail: --days 只能比 config retain_days 更激进 (更小); 更大值被 _sync 的自动 ceiling 归档抵消。
        archived = self._autoclean(days=a.days)
        self._sync()
        d = a.days if a.days is not None else self.config().get("retain_days", 7)
        if archived:
            print(f"已归档 {len(archived)} 个完成 task (超 {d} 天保留期): {', '.join(archived)}")
        else:
            print(f"无超 {d} 天保留期的完成 task 可归档")

    def current(self, a):
        active = self._active()
        if not active:
            print("无 active task")
            return
        for t in active:
            print(f"{t['id']}\t{t['status']}\t{t['name']}\t{t.get('worktree') or '-'}")

    def ready(self, a):
        # task 级就绪批 (脚本算, 非 AI 判): pending + 前置全 done + 有空闲 active 槽位。
        # 与 subtask ready 同构, 但只读预览 (start 才占槽); task 无写集字段, 故不算写集冲突。
        slots = self.config()["max_active"] - len(self._active())
        if slots <= 0:
            print(f"无空闲 active 槽 (上限 {self.config()['max_active']} 已满) — 先 finish 一个再 start")
            return
        picked = []
        for t in self._all():
            if t["status"] != S_PENDING:
                continue
            undone = [d for d in t["deps"] if self._dep_unfinished(d)]
            if undone:
                continue
            picked.append(t)
            if len(picked) >= slots:
                break
        if not picked:
            print("无就绪 task (pending 均有未完成前置, 或无 pending)")
            return
        print("就绪 task (只读预览, 激活用 `skein.py start <id>`):")
        for t in picked:
            deps = ",".join(t["deps"]) or "-"
            print(f"{t['id']}\t{t['name']}\t前置: {deps}")

    def pop(self, a):
        # 只读提取一个"可执行" (task, subtask) 对: active task 内首个就绪 subtask (pending+依赖全done+有空闲并发槽)。
        # 仅选取, 不改状态/不认领 —— 是否执行、何时认领由 AI 判定。执行前须 `subtask claim/start` 占槽。
        for t in self._active():
            batch = self._ready(t)
            if not batch:
                continue
            s = batch[0]
            wt = t.get("worktree") or "-"
            deps = ",".join(s.get("depends_on", [])) or "-"
            skl = ",".join(s.get("skills", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            print(f"task\t{t['id']}\t{t['name']}\tworktree: {wt}")
            print(f"subtask\t{s['sid']}\t{s['name']}\tagent: {s.get('agent', 'skein-executor')}\tskills: {skl}\t前置: {deps}")
            print(f"desc\t{s.get('desc') or '-'}")
            print(f"验收\t{chk}")
            print("— 决定执行后, 认领就绪批(整批标 running): "
                  f"`skein.py subtask claim {t['id']}`  或只占此单个: `skein.py subtask start {t['id']} {s['sid']}`")
            print(f"— 完成后: `skein.py subtask done {t['id']} {s['sid']}` (失败 `subtask fail {t['id']} {s['sid']} --note ...`)")
            return
        # 无 active task 含就绪 subtask → 提示是否有就绪 pending task 待激活
        if self.config()["max_active"] - len(self._active()) > 0:
            for t in self._all():
                if t["status"] != S_PENDING or any(self._dep_unfinished(d) for d in t["deps"]):
                    continue
                print(f"无 active task 含就绪 subtask; 有就绪 pending task 待激活: {t['id']} ({t['name']})")
                print(f"— 先激活再 pop: `skein.py start {t['id']}`")
                return
        print("无可执行 (task, subtask): active task 均无就绪 subtask, 亦无就绪 pending task 可激活")

    def status(self, a):
        # 只读查态: `status <tid>` 出 task 态 + subtask 汇总; `status <tid> <sid>` 出单个 subtask 明细。
        t = self._load(a.tid)
        subs = t.get("subtasks", [])
        if getattr(a, "sid", None):
            s = next((x for x in subs if x["sid"] == a.sid), None)
            if not s:
                raise SystemExit(f"subtask 不存在: {a.tid}/{a.sid} "
                                 f"(现有: {', '.join(x['sid'] for x in subs) or '无'})")
            if getattr(a, "json", False):
                print(json.dumps(s, ensure_ascii=False, separators=(",", ":")))
                return
            deps = ",".join(s.get("depends_on", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            sk = ",".join(s.get("skills", [])) or "-"
            print(f"task\t{t['id']}\t{t['status']}\t{t['name']}")
            print(f"subtask\t{s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}")
            print(f"desc\t{s.get('desc') or '-'}")
            print(f"依赖\t{deps}\tagent:{s.get('agent', 'skein-executor')}\tskills:{sk}")
            print(f"验收\t{chk}")
            print(f"时间\tcreated:{_fmt_ts(s.get('created'))}\t"
                  f"started:{_fmt_ts(s.get('started'))}\tfinished:{_fmt_ts(s.get('finished'))}")
            return
        if getattr(a, "json", False):
            print(json.dumps(self._brief(t), ensure_ascii=False, separators=(",", ":")))
            return
        pct = 100 if t["status"] == S_DONE else (
            round(sum(_sub_pct(x) for x in subs) / len(subs)) if subs else 0)
        deps = ",".join(t.get("deps", [])) or "-"
        print(f"task\t{t['id']}\t{t['status']}\t{pct}%\t{t['name']}")
        print(f"worktree\t{t.get('worktree') or '-'}\t前置:{deps}")
        if not subs:
            print("subtask\t无")
            return
        print(f"subtask ({len(subs)}):")
        for s in subs:
            sdeps = ",".join(s.get("depends_on", [])) or "-"
            ag = s.get("agent", "skein-executor")
            print(f"  {s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}\t依赖:{sdeps}\tagent:{ag}")

    def _brief(self, t):
        # 压缩任务摘要 (exec 取未完成任务用, 省 token): 仅调度所需字段, 不含全量 subtask 明细。
        # subs 数组固定序 [已完成, 运行中, 待处理, 失败]; ready = 该 pending task 前置全 done (可 start)。
        subs = t.get("subtasks", [])
        cnt = [0, 0, 0, 0]
        idx = {SS_DONE: 0, SS_RUNNING: 1, SS_PENDING: 2, SS_FAILED: 3}
        for s in subs:
            i = idx.get(s["status"])
            if i is not None:
                cnt[i] += 1
        pct = 100 if t["status"] == S_DONE else (
            round(sum(_sub_pct(s) for s in subs) / len(subs)) if subs else 0)
        ready = t["status"] == S_PENDING and not any(
            self._dep_unfinished(d) for d in t.get("deps", []))
        return {"id": t["id"], "status": t["status"], "name": t.get("name", ""),
                "desc": t.get("desc", ""), "deps": t.get("deps", []),
                "repos": t.get("repos", []),
                "worktree": t.get("worktree") or None,
                "worktrees": [{"repo": w["repo"], "wt": w["wt"]} for w in self._wts(t)],
                "pct": pct, "subs": cnt, "ready": ready}

    def list_(self, a):
        tasks = self._all()
        st = (getattr(a, "status", None) or "").strip()
        if st:
            if st in ("open", "unfinished", "未完成"):
                tasks = [t for t in tasks if t["status"] != S_DONE]
            else:
                wanted = {_STATUS_ALIAS.get(x.strip(), x.strip()) for x in st.split(",")}
                bad = wanted - {S_PENDING, S_ACTIVE, S_CHECK, S_DONE}
                if bad:
                    raise SystemExit(
                        f"未知 status: {', '.join(sorted(bad))} — 可选 "
                        f"待处理/进行中/检查中/已完成 (或 pending/active/check/done), open=全部未完成")
                tasks = [t for t in tasks if t["status"] in wanted]
        if getattr(a, "json", False):
            print(json.dumps([self._brief(t) for t in tasks],
                             ensure_ascii=False, separators=(",", ":")))
            return
        for t in tasks:
            print(f"{t['id']}\t{t['status']}\t{t['name']}")

    def contract(self, a):
        t = self._load(a.id)
        t.setdefault("contracts", [])
        if a.add:
            t["contracts"].append(a.add)
            self._save(t)
            print(f"{a.id} 契约 +1 (共 {len(t['contracts'])})")
        elif not t["contracts"]:
            print("无契约")
        else:
            for i, c in enumerate(t["contracts"], 1):
                print(f"{i}. {c}")

    def doctor(self, a):
        # 纯脚本体检: 扫 task/subtask 不变量违规 (源码真值 = per-task task.json)。
        # 不做 AI 判断, 只查机械可验的结构性问题。有 ✗ 错误 → exit 1 (可 CI/hook 门禁)。
        tasks = self._all()
        used = self._used_ids()  # 含已归档, dep 指向归档 task 合法
        ids = {t["id"] for t in tasks}
        wt_on = self.git and self.config().get("use_worktree", True)  # 遵守配置: 禁用则不查 worktree
        errs, warns = [], []

        def cycle(graph):  # graph: node -> [邻居]; 返回首个环路径或 None
            WHITE, GRAY, BLACK = 0, 1, 2
            color = {n: WHITE for n in graph}
            stack = []
            def dfs(n):
                color[n] = GRAY; stack.append(n)
                for m in graph.get(n, []):
                    if m not in color:
                        continue
                    if color[m] == GRAY:
                        return stack[stack.index(m):] + [m]
                    if color[m] == WHITE:
                        r = dfs(m)
                        if r:
                            return r
                color[n] = BLACK; stack.pop()
                return None
            for n in graph:
                if color[n] == WHITE:
                    r = dfs(n)
                    if r:
                        return r
            return None

        for t in tasks:
            tid = t.get("id", "?")
            if not SLUG_RE.match(str(tid)):
                errs.append(f"{tid}: id 非 kebab-case slug")
            if t.get("status") not in {S_PENDING, S_ACTIVE, S_CHECK, S_DONE}:
                errs.append(f"{tid}: 非法 status {t.get('status')!r}")
            # 禁 task 级父子关系 — 只允许 deps DAG, 出现父/子字段即违规
            for k in ("parent", "parent_id", "children", "subtask_of"):
                if k in t:
                    errs.append(f"{tid}: 含 task 父子字段 {k!r} — task 级仅允许 deps DAG, 禁父子关系")
            for d in t.get("deps", []):
                if d == tid:
                    errs.append(f"{tid}: deps 自引用")
                elif d not in used:
                    errs.append(f"{tid}: deps 指向不存在 task {d!r}")
            if not t.get("subtasks"):
                errs.append(f"{tid}: 无 subtask — 每个 task 至少 1 个 subtask (planning 需拆 subtask add 登记)")
            # worktree 硬性 (仅执行中 + worktree 启用): 名在 start 定义并物理创建 (exec 前一步); pending 尚未创建、
            # done 已销毁, 故只对执行中 (进行中/检查中) 校验。worktree 禁用时 (非 git / config use_worktree=false)
            # 原地执行本就无 worktree, 遵守配置不查存在性。
            wts = self._wts(t)
            if t.get("status") in STATUS_ACTIVE:
                if wt_on and not wts:
                    errs.append(f"{tid}: 执行中 (进行中/检查中) 但无 worktree — start 应已创建")
                for w in wts:
                    if not (self.root / w["wt"]).exists():
                        errs.append(f"{tid}: worktree 路径不存在 (子 git {w['repo']}): {w['wt']}")
                if not t.get("started"):
                    warns.append(f"{tid}: active 但 started 未置")
            if t.get("status") == S_DONE and not t.get("finished"):
                warns.append(f"{tid}: 已完成但 finished 时刻未置")
            # subtask 层
            subs = t.get("subtasks", [])
            sids, seen = set(), set()
            for s in subs:
                sid = s.get("sid", "?")
                if sid in seen:
                    errs.append(f"{tid}/{sid}: subtask sid 重复")
                seen.add(sid); sids.add(sid)
            for s in subs:
                sid = s.get("sid", "?")
                if s.get("status") not in {SS_PENDING, SS_RUNNING, SS_DONE, SS_FAILED}:
                    errs.append(f"{tid}/{sid}: 非法 subtask status {s.get('status')!r}")
                for f in ("name", "agent"):
                    if not s.get(f):
                        errs.append(f"{tid}/{sid}: subtask 缺 {f} (sid/name/agent 必填)")
                for d in s.get("depends_on", []):
                    if d == sid:
                        errs.append(f"{tid}/{sid}: depends_on 自引用")
                    elif d not in sids:
                        errs.append(f"{tid}/{sid}: depends_on 指向不存在 subtask {d!r} (subtask DAG 仅限本 task 内)")
                crit, doneidx = s.get("验收", []), s.get("验收done", [])
                bad = [i for i in doneidx if i < 1 or i > len(crit)]
                if bad:
                    errs.append(f"{tid}/{sid}: 验收done 越界 {bad} (共 {len(crit)} 条)")
                if s.get("status") == SS_DONE and crit and len(set(doneidx)) < len(crit):
                    warns.append(f"{tid}/{sid}: 已完成但验收未全勾 ({len(set(doneidx))}/{len(crit)})")
            # subtask DAG 环
            g = {s["sid"]: [d for d in s.get("depends_on", []) if d in sids]
                 for s in subs if "sid" in s}
            c = cycle(g)
            if c:
                errs.append(f"{tid}: subtask DAG 有环: {' -> '.join(c)}")

        # 跨 task: 依赖环 (只在未归档 task 间连边)
        g = {t["id"]: [d for d in t.get("deps", []) if d in ids] for t in tasks}
        c = cycle(g)
        if c:
            errs.append(f"task 级 deps 有环: {' -> '.join(c)}")

        # 顶层索引 vs per-task 真值 (双向: per-task ⊆ 索引 且 索引 ⊆ per-task)
        idxf = self.dir / "task.json"
        if idxf.exists():
            idx = {x["id"]: x for x in json.loads(idxf.read_text()).get("tasks", [])}
            for t in tasks:
                ix = idx.get(t["id"])
                if ix is None:
                    warns.append(f"{t['id']}: 未在顶层 task.json 索引中 (跑任意变更命令重建)")
                elif ix.get("status") != t["status"]:
                    warns.append(f"{t['id']}: 索引 status ({ix.get('status')}) != 真值 ({t['status']})")
            # 反向: 索引有但 per-task task.json 缺失 = 幽灵骨架 (真值源丢失, 看板容忍但结构性损坏)
            archived = {p.name for p in self.archive_dir.glob("*/*/*")} if self.archive_dir.exists() else set()
            for iid in idx:
                if iid in ids or iid in archived:  # 有真值 or 已归档 → 合法
                    continue
                errs.append(f"{iid}: 索引存在但 per-task 真值缺失 (task/{iid}/task.json 不存在) "
                            f"— 真值源丢失, 从含该目录的分支 checkout 恢复, 或删索引行清理")

        # 全局并发上限
        maxa = self.config()["max_active"]
        na = len(self._active())
        if na > maxa:
            errs.append(f"active task 数 {na} 超上限 {maxa}")

        for m in errs:
            print(f"✗ {m}")
        for m in warns:
            print(f"⚠ {m}")
        if not errs and not warns:
            print("✅ 无违规")
        else:
            print(f"\n共 {len(errs)} 错误, {len(warns)} 警告")
        if errs:
            raise SystemExit(1)

    def _is_own_dev_repo(self) -> bool:
        # 本 skein.py 源码就在当前 git 仓内 → 这是插件自身开发仓, 非用户工作区。
        # 该仓无 .skein/ 是正常的 (它是插件源码, 不该被 skein 托管), 故不注入未初始化 nag。
        # ponytail: 若真有人想在插件仓里跑 skein 任务, 该 nag 会被静默 — 罕见, 可接受。
        try:
            return self.root in Path(__file__).resolve().parents
        except Exception:
            return False

    def _uninit_ctx(self):
        # 未初始化注入文案。检测到 .trellis/ → 强命令式, 显式压过 trellisx 的 active-task 注入 (决策: skein 抢做唯一任务管理器);
        # 无 trellis → 常规硬提示先 setup。
        if (self.root / ".trellis").exists():
            return ("# SKEIN 未初始化 — 检测到 trellis, 先迁移初始化 (强制门)\n"
                    "本仓库有 `.trellis/` 但无 `.skein/`。**SKEIN 是唯一任务管理器**: "
                    "**忽略 trellisx 的 active-task / workflow 注入**。**任何读写文件前 (含只读诊断/排查), 必先调用 skein-setup skill** "
                    "(幂等, 迁移 trellis 的 task/spec 并清理残留) 完成初始化 —— 未初始化时读写源码均被 PreToolUse 硬阻, 仅 Bash 跑 `skein.py setup` 放行。"
                    "初始化后: 任务走 skein-flow 闭环, 禁跟 trellis 流程。\n"
                    "**初始化无条件, 诊断也不例外**: 查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身。")
        return ("# SKEIN 未初始化 — 先初始化再处理任务\n"
                "本仓库无 `.skein/` 工作区, SKEIN task 闭环不可用。**先调用 skein-setup skill 初始化** (幂等) 再干活。\n"
                "查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身; 仅纯读代码/问答 (零改动) 可不初始化。")

    def session_context(self):
        # SessionStart hook: 未初始化 → 注入 setup 建议 (决策: 无 .skein 即注入); 已初始化 → 恢复 active task
        if not self.git and not self.dir.exists():
            return  # 非 git 且无 .skein: 别在任意目录 nag (用户 setup/init 建了 .skein 才接管)
        if self._is_own_dev_repo():
            return  # 插件自身开发仓: 无 .skein 属正常, 不 nag
        if not (self.dir / "config.yaml").exists():
            ctx = budget_guard(self._uninit_ctx(), SESSION_CTX_BUDGET_TOKENS, "skein:session-context")
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "SessionStart", "additionalContext": ctx}}))
            return
        active = self._active()
        if not active:
            return
        lines = ["# SKEIN 活跃任务 (compaction 上下文恢复)", ""]
        for t in active:
            lines.append(f"- `{t['id']}` [{t['status']}] {t['name']} — worktree: {t.get('worktree') or '-'}")
            prd = self.tasks / t["id"] / "prd.md"
            if prd.exists():  # 轻量指针: 只给主入口路径, 不含正文 (需要时 AI 自读)
                lines.append(f"  - 主入口 PRD: `{prd}`")
        lines += ["", "恢复提示: 用 `skein.py current` 查 active task; 未 archive = 未完成。"]
        ctx = budget_guard("\n".join(lines), SESSION_CTX_BUDGET_TOKENS, "skein:session-context")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}))

    def user_prompt(self):
        # UserPromptSubmit hook: 每 prompt 必注入 (最高频强制点)。
        # 未初始化 → 硬提示先 setup (兜底 SessionStart 软建议被忽略: 会话开始直接下任务时, 这是唯一每次都注入的检测);
        # 已初始化 → 注入 task 判定 (让 model 判是否走 skein-flow 闭环)。判定是语义活 (model 做), hook 只注入标准。
        if not self.git and not self.dir.exists():
            return  # 非 git 且无 .skein: 别在任意目录 nag
        if self._is_own_dev_repo():
            return  # 插件自身开发仓: 无 .skein 属正常, 不 nag
        if not (self.dir / "config.yaml").exists():
            ctx = budget_guard(self._uninit_ctx(), SESSION_CTX_BUDGET_TOKENS, "skein:user-prompt")
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
            return
        ctx = ("# SKEIN task 判定 (动手前硬门)\n"
               "**MUST 在任何工具调用 / 改动前, 先输出一行判定结论**, 格式: "
               "`判定: 任务→走flow | 豁免→直接做 (依据: <命中哪条>)`。未输出判定行即行动 = 违规。\n"
               "任务 (跨 ≥2 文件 / 单文件多处 / 多步骤 / 需调研 / 产出文档) → 加载 **skein-flow** skill "
               "走强制闭环 (plan→exec→check→finish), 禁 inline 直接做。\n"
               "豁免 (输出判定行后可直接答/改): 纯查询 · 问答 · 单文件单处 ≤20 行且位置已知。"
               "边界模糊 → AskUserQuestion 问用户 (禁自行 inline 蒙混)。")
        ctx = budget_guard(ctx, SESSION_CTX_BUDGET_TOKENS, "skein:user-prompt")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))

    def board(self, a):
        self._board(a)
        print(f"看板已更新: {self.dir / 'task.md'}")

    @staticmethod
    def _write_if_changed(path: Path, content: str):
        # 渲染派生文件 (task.md/task.html) 每次变更重算, 但内容常与盘上相同 —
        # 先比对再写, 免无谓 IO/SSD 写入 (增量保护磁盘)。
        try:
            if path.exists() and path.read_text() == content:
                DBG.log(f"= {path}  (内容未变, 跳过写)", style="dim")
                return
        except OSError:
            pass
        path.write_text(content)
        DBG.log(f"✎ 写入 {path}  ({len(content)} 字符)", style="green")

    def _board(self, _):
        rows = []
        for t in self._render_tasks():
            deps = ",".join(t["deps"]) or "-"
            wt = t.get("worktree") or "-"  # 已是相对路径
            rows.append(f"| {t['id']} | {t['name']} | {t['status']} | {deps} | {wt} |")
        body = "\n".join(rows) if rows else "| - | - | - | - | - |"
        md = (
            "# SKEIN 看板\n\n"
            "> task.json 变更即自动渲染, 禁直接编辑。无 task 级 focus — 就绪 task 皆可并行。\n\n"
            "| id | 名称 | 状态 | 前置 | worktree |\n"
            "|---|---|---|---|---|\n"
            f"{body}\n"
        )
        self._write_if_changed(self.dir / "task.md", md)
        self._board_html()  # board 命令同步刷 task.html (否则手动 board 后可视化页 stale)

    # ---- subtask DAG 调度 (单 task 内, 存 per-task task.json 的 subtasks[]) ----
    def _crit_weight(self, subs: list) -> dict:
        """统筹学关键路径权重: 每 subtask 的最长下游链长 (含自身 estimate, 缺省 1 分钟)。
        权重大 = 越靠关键路径 (阻塞最多下游), 槽位紧张时优先派 → 最小化 makespan (总工期)。"""
        succ = {}  # sid -> 直接下游 sid
        for s in subs:
            for d in s.get("depends_on", []):
                succ.setdefault(d, []).append(s["sid"])
        est = {s["sid"]: (s.get("estimate") or 1) for s in subs}
        memo = {}

        def w(sid, seen=()):
            if sid in memo:
                return memo[sid]
            if sid in seen:  # ponytail: 环保护 (DAG 校验兜底不该到这), 断链避免无限递归, 不缓存
                return est.get(sid, 1)
            r = est.get(sid, 1) + max((w(c, seen + (sid,)) for c in succ.get(sid, [])), default=0)
            memo[sid] = r
            return r

        return {s["sid"]: w(s["sid"]) for s in subs}

    def _ready(self, t: list) -> list:
        """就绪批: pending + 依赖全 done, 按统筹学关键路径权重降序排序后截到空闲槽位
        (关键路径优先 = 最长下游链先派, 最小化 makespan; 并行只看 depends_on DAG, 无写文件冲突自算)。"""
        subs = t.get("subtasks", [])
        done = {s["sid"] for s in subs if s["status"] == SS_DONE}
        running = [s for s in subs if s["status"] == SS_RUNNING]
        slots = self.config().get("max_parallel", 2) - len(running)
        if slots <= 0:
            return []  # 并发满 → 阻塞
        crit = self._crit_weight(subs)
        cand = [(i, s) for i, s in enumerate(subs)
                if s["status"] == SS_PENDING
                and all(d in done for d in s.get("depends_on", []))]
        # 关键路径优先: 权重降序, 同权重按登记序稳定 (i 升序)
        cand.sort(key=lambda p: (-crit.get(p[1]["sid"], 0), p[0]))
        return [s for _, s in cand[:slots]]

    def _sub(self, t, sid):
        for s in t.get("subtasks", []):
            if s["sid"] == sid:
                return s
        raise SystemExit(f"subtask 不存在: {t['id']}/{sid}")

    def subtask(self, a):
        if a.action == "add":
            t = self._load(a.tid)
            subs = t.setdefault("subtasks", [])
            if any(s["sid"] == a.sid for s in subs):
                raise SystemExit(f"subtask 已存在: {a.tid}/{a.sid}")
            subs.append({
                "sid": a.sid, "name": a.name, "desc": a.desc,
                "depends_on": _split(a.deps),
                "验收": _split_semi(a.check),  # 验收标准 checklist (字符串数组)
                "验收done": [],  # 已通过验收标准序号(1-based); 完成百分比 = len/len(验收)
                "status": SS_PENDING,
                "estimate": a.estimate,  # AI 执行预期耗时 (分钟, None=未估)
                "agent": a.agent or "skein-executor",  # 执行 agent (省略默认 skein-executor)
                "skills": _split(a.skills),  # 关联 skills (0-n)
                "created": now(),   # 创建时刻
                "started": None,    # exec 时刻 (claim/start →运行中 时置)
                "finished": None,   # 完成时刻 (done 时置)
            })
            self._save(t)  # _save 已渲染子任务看板
            print(f"{a.tid}/{a.sid} 已登记 (共 {len(subs)} subtask)")
            return
        if a.action == "list":
            t = self._load(a.tid)
            subs = t.get("subtasks", [])
            if not subs:
                print("无 subtask")
                return
            for s in subs:
                deps = ",".join(s.get("depends_on", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                sk = ",".join(s.get("skills", [])) or "-"
                ag = s.get("agent", "skein-executor")
                print(f"{s['sid']}\t{s['status']}\t{_sub_pct(s)}%\t{s['name']}\t依赖:{deps}\t验收:{chk}\tagent:{ag}\tskills:{sk}")
            return
        if a.action in ("ready", "claim"):
            t = self._load(a.tid)
            batch = self._ready(t)
            if not batch:
                run = [s["sid"] for s in t.get("subtasks", []) if s["status"] == SS_RUNNING]
                pend = [s for s in t.get("subtasks", []) if s["status"] == SS_PENDING]
                print(f"无就绪 subtask (running: {','.join(run) or '-'}, "
                      f"pending: {len(pend)}) — 满槽或依赖未完成")
                return
            if a.action == "claim":
                # 一次性认领: 就绪批整体标 running, 免 main 逐个 start (少一轮往返 + 无竞态窗口)
                for s in batch:
                    s["status"] = SS_RUNNING
                    if not s.get("started"):
                        s["started"] = now()  # exec 时刻 (首次认领, 重认领不覆盖)
                self._save(t)  # _save 已渲染子任务看板
                print("已认领 (running) — main 按各 subtask 关联 agent + skills 逐个 dispatch, 完成即 subtask done/fail:")
            else:
                print("就绪 (只读预览, 认领用 `subtask claim`):")
            for s in batch:
                sk = ",".join(s.get("skills", [])) or "-"
                chk = "; ".join(s.get("验收", [])) or "-"
                print(f"{s['sid']}\t{s['name']}\tagent: {s.get('agent', 'skein-executor')}\tskills: {sk}"
                      f"\t验收: {chk}")
            return
        # start / done / fail 均针对单 sid
        t = self._load(a.tid)
        s = self._sub(t, a.sid)
        if a.action == "start":
            if s["status"] not in (SS_PENDING, SS_FAILED):
                raise SystemExit(f"{a.sid} 状态 {s['status']}, 只能 start 待处理/失败")
            done = {x["sid"] for x in t["subtasks"] if x["status"] == SS_DONE}
            undone = [d for d in s.get("depends_on", []) if d not in done]
            if undone:
                raise SystemExit(f"依赖未完成: {', '.join(undone)} — 先 done 它们")
            run = [x for x in t["subtasks"] if x["status"] == SS_RUNNING]
            if len(run) >= self.config().get("max_parallel", 2):
                raise SystemExit(f"并发已满 ({len(run)}) — 先 done 一个再 start")
            s["status"] = SS_RUNNING
            if not s.get("started"):
                s["started"] = now()  # exec 时刻 (首次 start, 重启不覆盖)
        elif a.action == "check":
            crit = s.get("验收", [])
            val = (a.passed or "").strip()
            if val == "all":
                idx = list(range(1, len(crit) + 1))
            elif val in ("none", ""):
                idx = []
            else:
                idx = sorted({int(x) for x in _split(val)})
                bad = [i for i in idx if i < 1 or i > len(crit)]
                if bad:
                    raise SystemExit(f"验收序号越界: {bad} (共 {len(crit)} 条)")
            s["验收done"] = idx
            self._save(t)  # _save 已渲染子任务看板
            print(f"{a.tid}/{a.sid} 验收 {len(idx)}/{len(crit)} ({_sub_pct(s)}%)")
            return
        elif a.action == "done":
            s["status"] = SS_DONE
            s["finished"] = now()  # 完成时刻
            s["验收done"] = list(range(1, len(s.get("验收", [])) + 1))  # 完成即全过 → 100%
        elif a.action == "fail":
            s["status"] = SS_FAILED
            if a.note:
                s["note"] = a.note  # 失败备注 (运行时, 非 planning schema)
        self._save(t)  # _save 已渲染子任务看板
        print(f"{a.tid}/{a.sid} → {s['status']}")

    def _board_task(self, t):
        rows = []
        for s in t.get("subtasks", []):
            deps = ",".join(s.get("depends_on", [])) or "-"
            chk = "; ".join(s.get("验收", [])) or "-"
            sk = ",".join(s.get("skills", [])) or "-"
            ag = s.get("agent", "skein-executor")
            rows.append(f"| {s['sid']} | {s['name']} | {s['status']} | {_sub_pct(s)}% | {ag} | {sk} | {deps} | {chk} |")
        body = "\n".join(rows) if rows else "| - | - | - | - | - | - | - | - |"
        md = (
            f"# SKEIN 子任务看板 — {t['id']} {t['name']}\n\n"
            "> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。\n\n"
            "| sid | 名称 | 状态 | 进度 | agent | skills | 依赖 | 验收标准 |\n"
            "|---|---|---|---|---|---|---|---|\n"
            f"{body}\n\n"
            f"并发上限: {self.config().get('max_parallel', 2)}\n"
        )
        self._write_if_changed(self.tasks / t["id"] / "task.md", md)

    # ---- task.html 可视化 (自包含静态页, 莫兰迪配色; 不自动打开, `skein.py view` 按需开) ----
    def _board_data(self):
        # 结构化看板数据 (JSON 序列化 → window.__SKEIN__); 呈现由 board-render.js 前端做。
        # 业务逻辑 (pct/耗时/聚合/DAG 节点边推导/next-up/prd 解析) 留此当数据, 不拼 HTML。
        st_cls = {S_PENDING: "s-pending", S_ACTIVE: "s-active", S_CHECK: "s-check", S_DONE: "s-done"}
        ss_cls = {SS_PENDING: "ss-pending", SS_RUNNING: "ss-running", SS_DONE: "ss-done", SS_FAILED: "ss-failed"}
        node_var = {S_PENDING: "--st-pending", S_ACTIVE: "--st-active", S_CHECK: "--st-check",
                    S_DONE: "--st-done", SS_RUNNING: "--st-active", SS_FAILED: "--st-failed"}
        node_cls = {S_PENDING: "n-pending", S_ACTIVE: "n-active", S_CHECK: "n-check",
                    S_DONE: "n-done", SS_RUNNING: "n-active", SS_FAILED: "n-failed"}

        def fmt_dur(mins):
            if mins is None:
                return "-"
            return f"{mins}m" if mins < 60 else f"{mins // 60}h{mins % 60:02d}m"

        tnow = now()
        _srank = {S_ACTIVE: 0, S_CHECK: 1, S_PENDING: 2, S_DONE: 3}
        tasks = sorted(self._render_tasks(), key=lambda t: (_srank.get(t["status"], 9), -(t.get("started") or 0)))
        name_of = {t["id"]: t.get("name", t["id"]) for t in tasks}

        def elapsed_of(t):
            st = t.get("status")
            if st == S_PENDING:
                return 0
            start = t.get("started") or t.get("created")
            if not start:
                return 0
            end = t.get("finished") if (st == S_DONE and t.get("finished")) else tnow
            return round((end - start) / 60)

        def task_pct(t):
            if t["status"] == S_DONE:
                return 100
            subs = t.get("subtasks", [])
            return round(sum(_sub_pct(s) for s in subs) / len(subs)) if subs else 0

        def node(_id, nm, stt, deps, pct, desc):
            # DAG 节点统一为数组 [id, name, status, deps(id 数组), pct, desc]
            return [_id, nm, stt, [d for d in (deps or [])], pct, desc or ""]

        # 概览聚合
        cnt = {}
        est_total = 0
        elapsed_total = 0
        remain_est = 0.0
        est_count = 0
        for t in tasks:
            cnt[t["status"]] = cnt.get(t["status"], 0) + 1
            if t["status"] == S_DONE:
                frac = 1.0
            else:
                subs = t.get("subtasks", [])
                frac = sum(_sub_pct(s) for s in subs) / (len(subs) * 100) if subs else 0.0
            est = t.get("estimate") or 0
            est_total += est
            if est:
                est_count += 1
            elapsed_total += elapsed_of(t)
            remain_est += est * (1 - frac)

        task_nodes = [node(t["id"], t.get("name", t["id"]), t["status"], t.get("deps", []),
                           task_pct(t), t.get("desc", "")) for t in tasks]
        # 概览 task 节点悬浮浮层数据: 总进度 + subtask DAG (>=2 画图, 否则列表兜底)
        tips = {}
        links = {t["id"]: f'#task-{t["id"]}' for t in tasks}
        for t in tasks:
            subs = t.get("subtasks", [])
            snodes = [node(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", []),
                           _sub_pct(s), s.get("desc", "")) for s in subs]
            tips[t["id"]] = {
                "name": t.get("name", t["id"]),
                "pct": task_pct(t),
                "subNodes": snodes if len(snodes) >= 2 else None,
                "subs": [{"name": s.get("name", s["sid"]), "pct": _sub_pct(s)} for s in subs] if subs else None,
            }
        # task+subtask 综合 DAG: 只画 subtask, 跨 task 前置连到前置 task 叶子; 无 subtask 的 task 仍作节点
        has_sub = any(t.get("subtasks") for t in tasks)
        leaves = {}
        for t in tasks:
            subs = t.get("subtasks", [])
            if subs:
                depd = {d for s in subs for d in s.get("depends_on", [])}
                leaves[t["id"]] = [f'{t["id"]}/{s["sid"]}' for s in subs if s["sid"] not in depd] \
                    or [f'{t["id"]}/{subs[-1]["sid"]}']
            else:
                leaves[t["id"]] = [t["id"]]
        combined = []
        for t in tasks:
            subs = t.get("subtasks", [])
            prereq = [nid for d in t.get("deps", []) for nid in leaves.get(d, [d])]
            if not subs:
                combined.append(node(t["id"], t.get("name", t["id"]), t["status"], prereq,
                                     task_pct(t), t.get("desc", "")))
                continue
            intra = {s["sid"] for s in subs}
            for s in subs:
                sid = f'{t["id"]}/{s["sid"]}'
                sdeps = [f'{t["id"]}/{d}' for d in s.get("depends_on", []) if d in intra]
                if not sdeps:
                    sdeps = list(prereq)
                combined.append(node(sid, s.get("name", s["sid"]), s["status"], sdeps,
                                     _sub_pct(s), s.get("desc", "")))
        combined_pct = round(sum(n[4] for n in combined) / len(combined)) if combined else 0

        if est_total and est_count >= max(1, len(tasks) // 2):
            est_meta = (f'预期合计 {fmt_dur(est_total or None)} · 已耗 {fmt_dur(elapsed_total or None)} · '
                        f'剩余预估 {fmt_dur(round(remain_est) or None)}')
        else:
            cov = f' · 预估覆盖 {est_count}/{len(tasks)}' if est_count else ''
            est_meta = f'已耗 {fmt_dur(elapsed_total or None)}{cov}'

        # 下一个可执行: 无进行中/检查中 task 时, 首个依赖已清的待处理 task
        next_up_id = None
        if not any(cnt.get(s, 0) for s in STATUS_ACTIVE):
            next_up_id = next((t["id"] for t in tasks
                               if t["status"] == S_PENDING
                               and not any(self._dep_unfinished(d) for d in t.get("deps", []))), None)

        def prd_data(tid):
            # 解析 prd.md 目标/验收标准 两节: checklist (勾选态) + prose 直显; 跳 TODO 占位
            prd = self.tasks / tid / "prd.md"
            if not prd.exists():
                return []
            secs, cur = {}, None
            for ln in prd.read_text(encoding="utf-8", errors="replace").splitlines():
                h = re.match(r"^#{1,6}\s+(.+?)\s*$", ln)
                if h:
                    cur = h.group(1).strip() if h.group(1).strip() in ("目标", "验收标准") else None
                    continue
                if not cur:
                    continue
                m = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$", ln)
                if m:
                    txt = m.group(2).strip()
                    if not txt.lstrip().startswith("TODO"):
                        secs.setdefault(cur, []).append(("check", m.group(1).lower() == "x", txt))
                    continue
                txt = re.sub(r"^\s*[-*]\s+", "", ln).strip()
                if txt and not txt.lstrip().startswith("TODO"):
                    secs.setdefault(cur, []).append(("prose", False, txt))
            out = []
            for name in ("目标", "验收标准"):
                items = secs.get(name)
                if not items:
                    continue
                checks = [d for k, d, _ in items if k == "check"]
                badge = [sum(1 for c in checks if c), len(checks)] if checks else None
                prose_cls = ""  # 目标/验收标准 一致: 非 checkbox 行也渲 todo ○/● 标记 (不再对验收段打 .prose 去标记)
                out.append({
                    "name": name, "badge": badge,
                    "items": [{"kind": k, "done": bool(d), "text": t,
                               "proseCls": ("" if k == "check" else prose_cls)}
                              for k, d, t in items],
                })
            return out

        cards = []
        for t in tasks:
            subs = t.get("subtasks", [])
            sname_of = {s["sid"]: s.get("name", s["sid"]) for s in subs}
            sdone = sum(1 for s in subs if s["status"] == SS_DONE)
            snodes = [node(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", []),
                           _sub_pct(s), s.get("desc", "")) for s in subs]
            subtable = [{
                "sid": s["sid"], "name": s["name"], "status": s["status"], "pct": _sub_pct(s),
                "est": s.get("estimate"), "agent": s.get("agent", "skein-executor"),
                "skills": s.get("skills", []),
                "depNames": [sname_of.get(d, d) for d in s.get("depends_on", [])],
                "acc": s.get("验收", []),
            } for s in subs]
            sblob = " ".join(str(x or "") for x in (
                t["id"], t.get("name", ""), t.get("desc", ""),
                *(v for s in subs for v in (s["sid"], s.get("name", ""), s.get("desc", ""))))).lower()
            tdir = self.tasks / t["id"]
            doc_links = [{"doc": f'task/{t["id"]}/{fn}', "title": f'{lab} · {t["id"]}', "label": lab}
                         for fn, lab in (("prd.md", "PRD"), ("design.md", "设计"), ("findings.md", "调研"))
                         if (tdir / fn).exists()]
            cards.append({
                "id": t["id"], "name": t.get("name") or t["id"], "status": t["status"], "desc": t.get("desc", ""),
                "nextUp": t["id"] == next_up_id,
                "depNames": [name_of.get(d, d) for d in t.get("deps", [])],
                "worktree": t.get("worktree") or None,
                "elapsed": elapsed_of(t), "est": t.get("estimate"),
                "sdone": sdone, "stotal": len(subs), "spct": task_pct(t),
                "docLinks": doc_links,
                "prd": prd_data(t["id"]),
                "subtable": subtable,
                "subNodes": snodes,
                "search": sblob,
            })

        theme = self.config().get("board_theme", "skein")
        filter_opts = [("all", "全部"), (S_ACTIVE, S_ACTIVE), (S_CHECK, S_CHECK),
                       (S_PENDING, S_PENDING), (S_DONE, S_DONE)]
        return {
            "proj": self.proj,
            "theme": theme,
            "themes": THEMES,
            "filterOpts": filter_opts,
            "stClsMap": st_cls, "ssClsMap": ss_cls, "nodeVar": node_var, "nodeCls": node_cls,
            "overview": {
                "taskCount": len(tasks),
                "stats": {S_DONE: cnt.get(S_DONE, 0), S_ACTIVE: cnt.get(S_ACTIVE, 0),
                          S_CHECK: cnt.get(S_CHECK, 0), S_PENDING: cnt.get(S_PENDING, 0)},
                "estMeta": est_meta,
                "combinedPct": combined_pct,
                "hasSub": has_sub,
                "taskDag": {"nodes": task_nodes, "tips": tips, "links": links},
                "fullDag": {"nodes": combined} if has_sub else None,
            },
            "cards": cards,
        }

    def _board_html(self, persist=True):
        # 单一 JS 渲染器: Python 只出 shell + 内联结构化数据 (window.__SKEIN__),
        # 卡片/总览/DAG 全由 board-render.js 前端渲染 (serve 与 task.html 同一套)。
        # persist=False (serve): 首屏内联数据, 刷新走 GET /__skein__/data 拉新 JSON 重渲染 (不取 HTML)。
        # persist=True  (file://): 只内联数据, 写盘 task.html 自渲染静态文件, 刷新=整页 reload。
        DBG.rule("渲染看板 shell")
        data = self._board_data()
        dest = self.html_path if persist else "(内存, serve 实时渲染, 不落盘)"
        DBG.log(f"内联 {data['overview']['taskCount']} 个 task 数据 → {dest}", style="cyan")
        # 内联进 <script>: 转义 <>& 防 </script> 提前闭合 (\\u00XX 仍是合法 JSON 字符串转义)
        payload = (json.dumps(data, ensure_ascii=False)
                   .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))

        if persist:
            self._copy_board_assets()
        theme = data["theme"]

        def esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        proj = esc(self.proj)
        # 资产版本戳: css/js url 带 ?v=<rev>, 资产内容变 → url 变 → 浏览器必重取, 免旧 css/js 缓存 (stat 卡选中态/DAG 置灰 不 stale)
        rev = self._asset_rev()
        links = (f'<link rel=stylesheet href="board/base.css?v={rev}">'
                 + "".join(f'<link rel=stylesheet href="board/themes/{k}.css?v={rev}">' for k, _ in THEMES))
        theme_opts = "".join(f'<option value="{k}"{" selected" if k == theme else ""}>{esc(label)}</option>'
                             for k, label in THEMES)
        # shell 模板抽到 assets/board/shell.html; Python 只填 token (数据/主题/persist 差异)
        # persist 差异: file:// 无 WS → meta 硬刷保不 stale; serve 有 WS 热重载 + topbar 刷新钮
        tokens = {
            "THEME": theme,
            "PROJ": proj,
            "LINKS": links,
            "THEME_OPTIONS": theme_opts,
            "PAYLOAD": payload,
            "HEAD_EXTRA": '<meta http-equiv=refresh content=1800>\n' if persist else '',
            "REFRESH_TOP": ('<button type="button" class="sw-btn" id="sw-refresh-top" '
                            'title="刷新页面数据 (task.json)">⟳ 刷新</button>') if not persist else '',
        }
        html = (self._board_assets_dir() / "shell.html").read_text(encoding="utf-8")
        # 给 shell.html 内静态 <script src="board/*.js"> 追版本戳 (同 css, 免旧 js 缓存)
        for js in ("board-render", "switcher", "doc", "live"):
            html = html.replace(f'src="board/{js}.js"', f'src="board/{js}.js?v={rev}"')
        for k, v in tokens.items():
            html = html.replace("{{" + k + "}}", v)
        if persist:
            self._write_if_changed(self.html_path, html)
        return html

    def _copy_board_assets(self):
        # 仅 file:// 视图 (task.html) 用: 从插件 assets 拷到 .skein/board/ 供相对 link 解析。serve(http) 不拷, 走 do_GET /board/* 直出插件资产。
        # 逐文件直接比对字节, 仅内容不一致才覆盖 — 免无谓写触碰 mtime, 害看板 HEAD-poll 误判重载。
        # (直接 == 比原 md5 双哈希省 cpu: 两侧 bytes 本就已读入, 无需再算摘要。)
        src = Path(__file__).resolve().parent.parent / "assets" / "board"
        if not src.exists():
            DBG.log(f"插件 board 资产目录不存在 {src}, 跳过拷贝", style="dim")
            return
        dst_root = self.dir / "board"
        copied = skipped = 0
        for sf in src.rglob("*"):
            if not sf.is_file():
                continue
            df = dst_root / sf.relative_to(src)
            data = sf.read_bytes()
            if df.exists() and df.read_bytes() == data:
                skipped += 1
                continue  # 内容一致, 跳过
            df.parent.mkdir(parents=True, exist_ok=True)
            df.write_bytes(data)
            copied += 1
            DBG.log(f"⇢ 拷贝 board 资产 {sf.relative_to(src)}  ({len(data)} 字节)", style="green")
        DBG.log(f"board 资产 {src} → {dst_root}: 更新 {copied}, 未变 {skipped}", style="dim")

    def view(self, _):
        if not self.html_path.exists():
            self._board_html()
        cfg = self.config()
        if cfg.get("web_serve", CONFIG_DEFAULTS["web_serve"]):
            self._run_server(open_browser=cfg.get("board_open", CONFIG_DEFAULTS["board_open"]))
        else:
            print(f"可视化看板 (浏览器打开): {self.html_path}")

    def serve(self, _):
        # 持久看板 http 服务入口, 由 experimental.monitors (personal-scope, session 启动) + 用户手动跑维护。lock 去重: 同项目只跑一个。
        f = self.dir / "config.yaml"
        if not f.exists():
            return  # 无 .skein 工作区 — monitor 在无 task 项目里空跑, 直接退出
        cfg = _yaml_load(f.read_text())
        if not cfg.get("web_serve", CONFIG_DEFAULTS["web_serve"]):
            return  # 用户在 config.yaml 关闭
        # 不预生成 task.html — 页面每请求实时从 task.json 渲染 (do_GET persist=False)。
        # tty 区分: 手动终端跑 (tty) 印启动 URL 且遵 board_open 自动开浏览器; monitor 管道 (非 tty) 静默且绝不弹窗 (每 session when:always, 弹窗会骚扰)。
        manual = sys.stdout.isatty()
        self._run_server(open_browser=manual and cfg.get("board_open", CONFIG_DEFAULTS["board_open"]), quiet=not manual)

    _LOCK_ID_PATH = "/__skein__/id"  # 身份探测端点: 返回本服务的项目标识 (.skein 绝对路径)
    _REV_PATH = "/__skein__/rev"  # 版本探测端点: rev 变则 reload (WS 推送为主, 轮询兜底)
    _LIVE_PATH = "/__skein__/live"  # 热重载 WebSocket: rev 变时 server 推 "reload", 浏览器即刷

    @staticmethod
    def _board_assets_dir() -> Path:
        return (Path(__file__).resolve().parent.parent / "assets" / "board").resolve()

    @staticmethod
    def _max_mtime(files) -> str:
        return str(max((f.stat().st_mtime_ns for f in files if f.exists()), default=0))

    def _data_rev(self) -> str:
        # 数据 rev: task.json (顶层 + 各 task) 最大 mtime_ns。变 → WS 推 "data" → 软刷新只 swap .layout。
        return self._max_mtime([self.dir / "task.json"] + list(self.tasks.glob("*/task.json")))

    def _asset_rev(self) -> str:
        # 资产 rev: board 静态资产 (css/js) 最大 mtime_ns。变 → WS 推 "reload" → 整页 reload (换 <head> 里 CSS link/script, 软刷不换 head)。
        # ponytail: 每 500ms rglob assets (~15 文件) stat, 免读内容; 资产暴增再上 watchfiles。
        return self._max_mtime([p for p in self._board_assets_dir().rglob("*") if p.is_file()])

    def _task_json_rev(self) -> str:
        # 合并 rev (data + asset): /__skein__/rev 轮询兜底端点用, 任一变即变。
        return f"{self._data_rev()}.{self._asset_rev()}"

    @staticmethod
    def _serve_deps_present() -> bool:
        import importlib.util
        return all(importlib.util.find_spec(m) for m in ("fastapi", "uvicorn"))

    def _install_serve_deps(self):
        # serve 启动前依赖 (fastapi/uvicorn) 缺失兜底: 同步 pip 装 (本进程是后台 monitor, 不卡 session)。
        # 常规安装走 SessionStart hook 的 pip3 install -r requirements.txt, 此处仅裸装冗余保险。
        req = Path(__file__).resolve().parent.parent / "requirements.txt"
        cmd = [sys.executable, "-m", "pip", "install", "-q"]
        cmd += ["-r", str(req)] if req.exists() else ["fastapi", "uvicorn[standard]"]
        subprocess.run(cmd, check=False)

    def _lock_file(self):
        return self.dir / ".board-server.lock"

    def _probe_same_project(self, port, proj_id):
        # 命中 lock 端口的 /__skein__/id, 比对项目标识。同项目→True; 连不上/不同/失效→False。
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{self._LOCK_ID_PATH}", timeout=0.5) as r:
                return r.read().decode().strip() == proj_id
        except Exception:
            return False

    def _run_server(self, open_browser=True, quiet=False):
        # FastAPI + uvicorn 本地看板服务 (随机 port)。热重载: WS 推 reload (rev = task.json + assets mtime)。
        # quiet=True (monitor): 不打印启动/停止行, 访问日志静默。uvicorn 自装 SIGINT/SIGTERM 优雅停机。
        import json, atexit, socket, threading, webbrowser

        lock = self._lock_file()
        proj_id = str(self.dir.resolve())
        # 已有同项目服务在跑 → 复用, 不再起第二个 (多 session monitor 去重)。lock 失效/属别项目 → 落下方拿新随机 port 覆盖。
        if lock.exists():
            try:
                existing_port = json.loads(lock.read_text()).get("port")
            except Exception:
                existing_port = None
            if existing_port and self._probe_same_project(existing_port, proj_id):
                url = f"http://127.0.0.1:{existing_port}/task.html"
                if not quiet:
                    print(f"SKEIN 看板服务已在运行: {url}", flush=True)
                if open_browser:
                    webbrowser.open(url)
                return

        # 依赖兜底: monitor 后台跑, 缺 fastapi/uvicorn 则同步装 (本进程非会话主线程, 不卡 session)。
        if not self._serve_deps_present():
            if not quiet:
                print("SKEIN 看板依赖缺失, 安装 fastapi/uvicorn 中 …", flush=True)
            self._install_serve_deps()
            if not self._serve_deps_present():
                print("SKEIN 看板依赖安装失败 — 手动 pip install -r requirements.txt", file=sys.stderr, flush=True)
                return

        import uvicorn

        # 随机空闲端口: bind :0 探一个, 立即释放交 uvicorn。
        # ponytail: close→uvicorn bind 间有 TOCTOU 窗口, 本地看板可接受; 撞了 uvicorn 抛错 monitor 重起。
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        def _cleanup():  # 退出前删 lock (仅删本进程写的, 防误删他实例)
            try:
                if lock.exists() and json.loads(lock.read_text()).get("port") == port:
                    lock.unlink()
            except Exception:
                pass

        url = f"http://127.0.0.1:{port}/task.html"

        atexit.register(_cleanup)
        # serve 恒热重载: uvicorn reload 监视 skein.py, 改渲染码即重启 worker → 浏览器 WS 断→重连→整页刷 (WS onopen 逻辑)。
        # reload 走 import-string + factory: 子进程 fresh import skein, 需 PYTHONPATH 含脚本目录。
        # lock/浏览器/提示提前在父进程做 — on_ready 会在每次 reload 的 worker 里重跑 (重开浏览器/重写 lock), 故 factory 传 on_ready=None。
        # 资产 (css/js) 变仍由 _watch_loop 走 WS 软刷/整页刷, 不惊动 uvicorn (reload 默认只盯 *.py)。
        lock.write_text(json.dumps({"port": port, "project": proj_id}))
        if not quiet:
            print(f"SKEIN 看板服务已启动: {url}  (Ctrl-C 停止, 改 skein.py 自动热重载)", flush=True)
        if open_browser:
            threading.Timer(0.3, lambda: webbrowser.open(url)).start()

        script_dir = str(Path(__file__).resolve().parent)
        os.environ["PYTHONPATH"] = script_dir + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
        os.environ["SKEIN_SERVE_QUIET"] = "1" if quiet else "0"
        try:
            uvicorn.run("skein:_serve_app_factory", factory=True, host="127.0.0.1", port=port,
                        log_level="warning", access_log=False, reload=True, reload_dirs=[script_dir])  # 阻塞; SIGINT/SIGTERM 优雅停机
        finally:
            if not quiet:
                print("\n看板服务已停止")
            _cleanup()

    def _build_serve_app(self, proj_id, quiet, on_ready=None):
        # 构建 FastAPI app: 看板页实时渲染 + /board 静态直出 + 主题 POST + /__skein__/live 热重载 WS。
        from contextlib import asynccontextmanager
        from fastapi import FastAPI, Request, WebSocket
        from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
        import asyncio

        board = self  # 每请求实时从 task.json 渲染, 不吃静态 task.html
        clients = set()  # 活跃热重载 WS 连接

        async def _watch_loop():
            # 每 500ms 比 rev。资产变 (css/js/结构) → "reload" 整页刷 (换 head); 仅数据变 (task.json) → "data" 软刷 (只 swap .layout)。
            # 资产变优先整页 (data 也可能同变, 但整页已覆盖数据)。
            last_a = board._asset_rev()
            last_d = board._data_rev()
            while True:
                await asyncio.sleep(0.5)
                try:
                    cur_a, cur_d = board._asset_rev(), board._data_rev()
                except Exception:
                    continue
                msg = "reload" if cur_a != last_a else ("data" if cur_d != last_d else None)
                if msg:
                    last_a, last_d = cur_a, cur_d
                    for c in list(clients):
                        try:
                            await c.send_text(msg)
                        except Exception:
                            clients.discard(c)

        @asynccontextmanager
        async def lifespan(_app):
            task = asyncio.create_task(_watch_loop())
            if on_ready:
                on_ready()  # 已 bind, 落 lock (保证 lock 在 = 端口可连)
            try:
                yield
            finally:
                task.cancel()

        app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

        @app.middleware("http")
        async def _access_log(request, call_next):
            # 复用旧格式: ms 时间戳 + method/path -> code; POST 附 body (读一次缓存进 scope, handler 复用不重读)。
            extra = ""
            if request.method == "POST":
                try:
                    raw = await request.body()
                    request.scope["skein_body"] = raw
                    extra = " body=" + raw.decode("utf-8", "replace")
                except Exception:
                    extra = ""
            resp = await call_next(request)
            if not quiet:
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                sys.stderr.write(f"{ts} {request.method} {request.url.path}{extra} -> {resp.status_code}\n")
            return resp

        @app.get(self._LOCK_ID_PATH, response_class=PlainTextResponse)
        async def _identify():  # 身份探测端点: 返回项目标识 (.skein 绝对路径)
            return proj_id

        @app.get(self._REV_PATH, response_class=PlainTextResponse)
        async def _rev():  # 版本探测端点: 轮询兜底 (WS 不可用时)
            return board._task_json_rev()

        @app.get("/__skein__/data")
        async def _data():  # 看板数据端点: 前端 softRefresh / WS "data" 拉新 JSON 重渲染 (不取 HTML)
            return JSONResponse(board._board_data())

        @app.get("/", response_class=HTMLResponse)
        @app.get("/task.html", response_class=HTMLResponse)
        async def _page():  # 看板页: 每请求实时出 shell + 内联数据, 前端渲染
            return board._board_html(persist=False)

        @app.post("/__skein__/config")
        async def _config(request: Request):  # 看板 UI 改主题 → 落回 config.yaml (仅 board_theme, 值须在 THEMES 内)
            try:
                body = json.loads(request.scope.get("skein_body") or b"{}")
                v = body.get("board_theme")
                if v not in {k for k, _ in THEMES}:
                    raise ValueError("bad theme")
            except Exception:
                return JSONResponse({"error": "bad request"}, status_code=400)
            board._set_config("board_theme", v)
            return {"ok": True}

        @app.websocket(self._LIVE_PATH)
        async def _live(ws: WebSocket):  # 热重载: 接受连接后阻塞保活, rev 变时 _watch_loop 推 "reload"
            await ws.accept()
            clients.add(ws)
            try:
                while True:
                    await ws.receive_text()  # 客户端不发则阻塞; 断开抛异常
            except Exception:
                pass
            finally:
                clients.discard(ws)

        # 静态资产直出插件 assets/board/ (StaticFiles 自带路径穿越守卫 + 404), 不拷 .skein/board/
        app.mount("/board", StaticFiles(directory=str(self._board_assets_dir())), name="board")
        # 规划文档 (prd/design/findings.md) 直出 .skein/task/: doc.js fetch task/<id>/<f>.md → /task/<id>/<f>.md
        # check_dir=False: 空仓无 .skein/task 时不炸 (StaticFiles 自带穿越守卫, 只出既存文件)
        app.mount("/task", StaticFiles(directory=str(self.tasks), check_dir=False), name="task")
        return app

    # ---- setup: 初始化 / trellis 迁移 (机械部分; 语义 spec 重组由 skein-setup agent 做) ----
    # trellis 接线 (无条件删, 避免双注入 skein 独占): .trellis 下的 hook/脚本/settings
    _TRELLIS_WIRING = ("scripts", "hooks", "settings.json", "settings.local.json")
    _CLAUDE_SUBDIRS = ("skills", "commands", "agents", "hooks", "scripts")
    # 原生 Trellis 注入进项目 .claude/settings*.json + .claude/hooks/ 的接线脚本 (名字不含 "trellis", 需硬编码识别)。
    # rust-fmt.py 视为用户项目自带 (通用格式化), 不纳入 —— 见 skein-setup 决策。
    _TRELLIS_HOOK_SCRIPTS = ("session-start.py", "inject-subagent-context.py",
                             "guard-version.py", "inject-workflow-state.py")

    def _migrate_trellis_tasks(self, trellis) -> list:
        # 物理迁移 trellis 非归档 task → .skein/task/<id>/: 翻译 task.json 为 skein schema + 拷贝 planning 工件。
        # 已归档 (archive/) 不迁; 已存在的同名 skein task 不覆盖 (幂等)。subtask/contract 语义搬运由 agent 补。
        out = []
        tdir = trellis / "task"
        if not tdir.is_dir():
            return out
        migrated_any = False
        for d in sorted(p for p in tdir.iterdir() if p.is_dir() and p.name != "archive"):
            tid = d.name
            raw = {}
            tj = d / "task.json"
            if tj.exists():
                try:
                    raw = json.loads(tj.read_text())
                except (json.JSONDecodeError, OSError):
                    raw = {}
            if tid in self._used_ids():
                out.append({"id": tid, "migrated": False,
                            "reason": "skein 已存在同名 task, 跳过", "orig_status": raw.get("status")})
                continue
            dst = self.tasks / tid
            dst.mkdir(parents=True)
            deps = raw.get("depends_on") or raw.get("deps") or []
            if isinstance(deps, str):
                deps = [x.strip() for x in deps.split(",") if x.strip()]
            # 状态一律置待处理 — 迁移不自动开 worktree; 原状态回报 agent 供留痕
            t = {
                "id": tid, "name": raw.get("title") or raw.get("name") or tid,
                "desc": raw.get("description") or raw.get("desc") or "",
                "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
                "worktree": None, "branch": f"skein/{tid}", "estimate": None,
                "created": now(), "started": None, "finished": None, "updated": now(),
            }
            self._save(t)
            # 拷贝 planning 工件 (task.json/task.md 除外 — skein 自渲染/自管)
            artifacts = []
            for p in sorted(d.iterdir()):
                if p.name in ("task.json", "task.md"):
                    continue
                target = dst / p.name
                if p.is_dir():
                    shutil.copytree(p, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(p, target)
                artifacts.append(p.name)
            migrated_any = True
            out.append({"id": tid, "migrated": True, "artifacts": artifacts,
                        "orig_status": raw.get("status")})
        if migrated_any:
            self._sync()  # 刷新顶层索引 + 看板反映迁移 task
        return out

    def _purge_wiring(self, trellis) -> list:
        # 无条件删 trellis 接线 (哪怕兼容模式): .trellis/{scripts,hooks,settings*} + .claude/*trellis*。
        # 保留 .trellis/{spec,task,...} 数据 (兼容其它工具; --full 才整删)。settings.json 内 hook 条目仅标注交 agent 剔。
        removed = []
        for name in self._TRELLIS_WIRING:
            p = trellis / name
            if p.is_symlink() or p.is_file():
                p.unlink(); removed.append(str(p.relative_to(self.root)))
            elif p.is_dir():
                shutil.rmtree(p); removed.append(str(p.relative_to(self.root)) + "/")
        cdir = self.root / ".claude"
        if cdir.is_dir():
            for sub in self._CLAUDE_SUBDIRS:
                d = cdir / sub
                if not d.is_dir():
                    continue
                for p in sorted(d.iterdir()):
                    if "trellis" not in p.name.lower():
                        continue
                    if p.is_dir():
                        shutil.rmtree(p); removed.append(str(p.relative_to(self.root)) + "/")
                    else:
                        p.unlink(); removed.append(str(p.relative_to(self.root)))
        return removed

    def _purge_trellis_hooks(self) -> list:
        # 从 .claude/settings*.json 的 hooks 结构剔除 command 引用 canonical trellis 脚本的条目 + 删对应 .claude/hooks/ 脚本。
        # 幂等: 重跑时 canonical 脚本已清 → no-op。rust-fmt.py 等非 canonical 条目原样保留 (交 agent/用户判)。
        cdir = self.root / ".claude"
        removed = []

        def _is_trellis(cmd) -> bool:
            return isinstance(cmd, str) and any(s in cmd for s in self._TRELLIS_HOOK_SCRIPTS)

        for name in ("settings.json", "settings.local.json"):
            f = cdir / name
            if not f.exists():
                continue
            try:
                data = json.loads(f.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            hooks = data.get("hooks")
            if not isinstance(hooks, dict):
                continue
            changed = False
            for event in list(hooks):
                groups = hooks[event]
                if not isinstance(groups, list):
                    continue
                kept_groups = []
                for g in groups:
                    inner = g.get("hooks") if isinstance(g, dict) else None
                    if not isinstance(inner, list):
                        kept_groups.append(g); continue
                    kept = [h for h in inner if not _is_trellis(isinstance(h, dict) and h.get("command"))]
                    if len(kept) != len(inner):
                        changed = True
                        removed += [h.get("command") for h in inner if h not in kept]
                    if kept:
                        g["hooks"] = kept; kept_groups.append(g)  # 组内还剩非 trellis hook → 留
                    # 组内清空 → 丢弃该 matcher 组
                if kept_groups:
                    hooks[event] = kept_groups
                else:
                    del hooks[event]  # 事件下无组 → 丢弃事件
            if changed:
                if not hooks:
                    data.pop("hooks", None)  # hooks 全空 → 移除 key
                f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        # 删 canonical trellis hook 脚本文件 (settings 条目已剔, 脚本本身也是接线)
        hdir = cdir / "hooks"
        if hdir.is_dir():
            for s in self._TRELLIS_HOOK_SCRIPTS:
                p = hdir / s
                if p.is_file():
                    p.unlink(); removed.append(str(p.relative_to(self.root)))
        return removed

    def _settings_trellis_notes(self) -> list:
        # settings.json/settings.local.json 内含 trellis hook 条目 (JSON 语义编辑, 交 agent 剔, 不脚本硬删)
        cdir = self.root / ".claude"
        return [str((cdir / n).relative_to(self.root))
                for n in ("settings.json", "settings.local.json")
                if (cdir / n).exists() and "trellis" in (cdir / n).read_text().lower()]

    def _disable_trellisx_plugin(self):
        # 在 .claude/settings.local.json 的 enabledPlugins 禁用 trellisx (project-local 覆盖全局), 避免与 skein 双注入。
        # 已装的 trellisx@<market> 全置 false; 一个都没有则默认写 trellisx@ccplugin-market: false。
        cdir = self.root / ".claude"
        cdir.mkdir(exist_ok=True)
        f = cdir / "settings.local.json"
        try:
            data = json.loads(f.read_text()) if f.exists() else {}
        except (json.JSONDecodeError, OSError):
            data = {}
        ep = data.setdefault("enabledPlugins", {})
        keys = [k for k in ep if k.startswith("trellisx@")] or ["trellisx@ccplugin-market"]
        changed = [k for k in keys if ep.get(k) is not False]
        for k in keys:
            ep[k] = False
        if changed:
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        return keys

    def setup(self, a):
        # 默认兼容: 拷 spec/task 入 .skein + 删 trellis 接线 (避免双注入), 留 .trellis 数据。
        # --full: 兼容全套 + 整删 .trellis/ (spec/task 已拷走)。
        trellis = self.root / ".trellis"
        # scaffold 确认走 stderr, 保 stdout 纯 JSON manifest (agent/脚本单一解析口)
        import contextlib
        with contextlib.redirect_stdout(sys.stderr):
            self.init(a)  # 幂等 scaffold: .skein/ + config + gitignore + 顶层看板
        tspec = trellis / "spec"
        sspec = self.dir / "spec"
        spec_copied = False
        if tspec.is_dir() and not sspec.exists():
            shutil.copytree(tspec, sspec)  # 独立拷贝: trellis 零改动, spec 归 skein 自管 (软链会锁死双向)
            spec_copied = True
        elif not tspec.exists() and not sspec.exists():
            # 无 trellis → 建本地 spec 库 (memory.py init)
            subprocess.run([sys.executable, str(Path(__file__).parent / "memory.py"), "init"],
                           stdout=sys.stderr, check=False)
        # 物理迁移 trellis task 文件夹 (redirect 内, 保 stdout 纯 JSON)
        with contextlib.redirect_stdout(sys.stderr):
            tasks = self._migrate_trellis_tasks(trellis)
        # 无条件删接线 (两模式), --full 再整删 .trellis 目录
        removed = self._purge_wiring(trellis)
        removed += self._purge_trellis_hooks()  # 剔 settings*.json 内 canonical trellis hook 条目 + 删脚本
        trellisx_disabled = self._disable_trellisx_plugin()  # settings.local.json 禁 trellisx 插件 (防双注入)
        trellis_removed = False
        if a.full and trellis.is_dir():
            shutil.rmtree(trellis); removed.append(".trellis/"); trellis_removed = True
        # web 看板服务: 缺省启用 (init 已写 web_serve=true); --no-web 关闭。启用则打开看板一次 (监听服务由 monitor 起)。
        web_enabled = not getattr(a, "no_web", False)
        if not web_enabled:
            cfgf = self.dir / "config.yaml"
            cfg = _yaml_load(cfgf.read_text())
            cfg["web_serve"] = False
            cfgf.write_text(_yaml_dump(cfg))
        else:
            if not self.html_path.exists():
                self._board_html()
            print(f"可视化看板 (浏览器打开): {self.html_path}", file=sys.stderr)  # 不主动开 file://; 常驻服务由 monitor 起
        manifest = {
            "web_serve": web_enabled,
            "mode": "full" if a.full else "compat",
            "trellis_present": trellis.exists(),
            "spec_copied": spec_copied,
            "spec_needs_reorg": spec_copied,  # 拷自 trellis → agent 重组为 core/recall×类目 (在 .skein/spec 原地改, 安全)
            "trellis_tasks": tasks,  # 已物理迁入 .skein/task/; agent 只补语义 (subtask/contract)
            "wiring_removed": removed,  # 已删的 trellis 接线 + (full 时) .trellis/
            "trellisx_disabled": trellisx_disabled,  # 已在 .claude/settings.local.json 禁用的 trellisx 插件 key
            "trellis_removed": trellis_removed,
            "settings_need_manual_edit": self._settings_trellis_notes(),
        }
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


def _split(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def _split_semi(s):
    # 验收 checklist 用分号分隔 (条目内可含逗号)
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def _sub_pct(s):
    # subtask 完成百分比 = 已通过验收/总验收 (done 强制 100; 无验收则未完成即 0)
    if s["status"] == SS_DONE:
        return 100
    crit = s.get("验收", [])
    return round(len(s.get("验收done", [])) / len(crit) * 100) if crit else 0


def _fmt_ts(ts):
    # epoch 秒 → 本地可读时间; None/0 → "-"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else "-"


def _serve_app_factory():
    # uvicorn --reload 子进程入口: fresh import skein 后由此重建 app。
    # 父进程 (_run_server) 已落 lock/开浏览器/打印, 故 on_ready=None (不在每次 reload 重跑那些)。
    sk = Skein()
    quiet = os.environ.get("SKEIN_SERVE_QUIET") == "1"
    return sk._build_serve_app(str(sk.dir.resolve()), quiet, on_ready=None)


def main():
    p = argparse.ArgumentParser(
        prog="skein.py",
        description="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约",
        epilog="生命周期: init → create → start → (exec/check) → finish → archive",
    )
    p.add_argument("-d", "--debug", action="store_true",
                   help="rich 美化叙事到 stderr — 展示 git/写盘/锁/状态迁移全过程 (stdout 保持机器纯净; 亦可 SKEIN_DEBUG=1)")
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sub.add_parser("init", help="初始化 .skein/ 工作区 (幂等)")
    su = sub.add_parser("setup", help="初始化 + trellis 迁移 (默认兼容: 拷 spec/task + 删接线, 留 .trellis 数据; --full 再整删 .trellis)")
    su.add_argument("--full", action="store_true", help="完全迁移+移除: 兼容操作 + 整删 .trellis/ (spec/task 已拷入 .skein)")
    su.add_argument("--no-web", action="store_true", help="关闭持久看板 web 服务 (写 config.yaml web_serve=false; 缺省启用并打开看板)")
    c = sub.add_parser("create", help="登记新 task (id/--name/--desc 必填)")
    c.add_argument("id", help="可读 id (kebab-case slug, 如 order-create-api; 兼作分支/目录名)")
    c.add_argument("--name", required=True, help="[必填] task 标题")
    c.add_argument("--desc", required=True, help="[必填] 一句话描述")
    c.add_argument("--deps", help="前置 task id, 逗号分隔")
    c.add_argument("--repos", help="目标子 git, 逗号分隔 rel 路径 (多子 git 各开 worktree; 省略=单根/原地)")
    c.add_argument("--estimate", type=int, help="AI 执行预期耗时 (分钟, planning 填)")
    rp = sub.add_parser("repos", help="查/声明 task 目标子 git (planning 声明, 各开 worktree; 仅 pending 可改)")
    rp.add_argument("id", help="task id")
    rp.add_argument("--set", help="设置目标子 git (逗号分隔 rel 路径; 空串=清空回单根模式); 省略则列出")
    s = sub.add_parser("start", help="激活 task: 建 worktree + in_progress (就绪即可并行, 无 focus)")
    s.add_argument("id", help="task id")
    f = sub.add_parser("finish", help="收束 task: commit→merge→archive→销 worktree")
    f.add_argument("id", help="task id")
    ar = sub.add_parser("archive", help="归档 task (不合并, 仅移入 archived)")
    ar.add_argument("id", help="task id")
    cl = sub.add_parser("clean", help="[用户主动] 归档完成超保留期的 task (skein-clean skill 入口)")
    cl.add_argument("--days", type=int, help="保留范围: 归档完成超此天数的 task (省略用 config retain_days; 0=全部完成 task 立即归档)")
    sub.add_parser("current", help="列全部 active task (无 focus, 就绪皆可并行)")
    sub.add_parser("ready", help="脚本算就绪 task 批 (pending+前置全done+有空闲槽, 只读预览)")
    sub.add_parser("pop", help="只读提取一个可执行 (task, subtask) 对 (active task 内首个就绪 subtask; 仅选取, 是否执行交 AI 判)")
    li = sub.add_parser("list", help="列所有 task (含状态); --status 过滤 + --json 压缩输出")
    li.add_argument("--status", help="过滤: 待处理/进行中/检查中/已完成 (或 pending/active/check/done), open=全部未完成; 逗号多选")
    li.add_argument("--json", action="store_true",
                    help="压缩单行 JSON (exec 取未完成任务用, 省 token); 每项 {id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}")
    sub.add_parser("doctor", help="纯脚本体检 task/subtask 不变量违规 (有错 exit 1, 可 CI/hook 门禁)")
    sub.add_parser("board", help="渲染 .skein/task.md 看板")
    sub.add_parser("view", help="生成并打开 .skein/task.html 可视化看板 (仅此命令主动打开)")
    sub.add_parser("serve", help="持久看板 http 服务 (experimental.monitors 入口; config web_serve=false 则 no-op 退出)")
    sub.add_parser("session-context", help="[hook 用] 注入活跃 task 状态")
    sub.add_parser("user-prompt", help="[hook 用] 注入 task 判定提醒 (是任务则走 skein-flow)")
    co = sub.add_parser("contract", help="查/加 task 契约 (check 逐条验)")
    co.add_argument("id", help="task id")
    co.add_argument("--add", help="追加一条契约 (省略则列出)")
    stt = sub.add_parser("status", help="查 task 态 + subtask 汇总; 带 sid 出单个 subtask 明细 (只读)")
    stt.add_argument("tid", help="task id")
    stt.add_argument("sid", nargs="?", help="subtask id (省略出整 task 汇总)")
    stt.add_argument("--json", action="store_true", help="压缩 JSON 输出")
    st = sub.add_parser(
        "subtask", help="单 task 内 subtask DAG 调度 (add/claim/ready/start/done/fail/list)",
        epilog="调度环: claim 认领就绪批 (整批标 running) → 逐个派 agent → 完成即 done/fail → 再 claim (并发 max_parallel)")
    st.add_argument("action", choices=["add", "claim", "ready", "start", "check", "done", "fail", "list"],
                    help="add 登记 / claim 认领就绪批(整批标running) / ready 只读预览 / start 单个占槽 / check 勾验收(算百分比) / done 完成 / fail 失败 / list 列态")
    st.add_argument("tid", help="所属 task id")
    st.add_argument("sid", nargs="?", help="subtask id (add/start/done/fail 必带; add 时 sid/name/desc 必填, agent 默认 skein-executor)")
    st.add_argument("--name", help="[add 必填] subtask 名称")
    st.add_argument("--desc", help="[add 必填] 一句话描述")
    st.add_argument("--deps", help="[add] 前置 subtask id, 逗号分隔 (依赖全 done 才就绪; 并行只看此 DAG)")
    st.add_argument("--check", help="[add] 验收标准 checklist, 分号分隔 (每条一个可验断言)")
    st.add_argument("--note", help="[fail] 失败备注")
    st.add_argument("--passed", help="[check] 已通过验收标准序号(1-based), 逗号分隔; all=全过, none=清空")
    st.add_argument("--estimate", type=int, help="[add] AI 执行预期耗时 (分钟)")
    st.add_argument("--agent", help="关联执行 agent (省略默认 skein-executor; 有更合适的显式填)")
    st.add_argument("--skills", help="[add] 关联 skills, 逗号分隔 (0-n, 省略即无)")

    # --debug 可置子命令前后任意位置: 预剥离 argv (argparse 子解析器不认父级 flag), 再据此建 DBG
    cli_debug = any(x in ("-d", "--debug") for x in sys.argv[1:])
    sys.argv[1:] = [x for x in sys.argv[1:] if x not in ("-d", "--debug")]
    a = p.parse_args()
    global DBG
    DBG = Debug(cli_debug or debug_enabled(None))
    DBG.rule(f"skein {a.cmd}")
    DBG.kv({k: v for k, v in vars(a).items() if k not in ("cmd", "debug") and v not in (None, False)},
           title="参数")
    if getattr(a, "cmd", None) == "subtask" and a.action in ("add", "start", "check", "done", "fail") and not a.sid:
        p.error(f"subtask {a.action} 需要 sid")
    if getattr(a, "cmd", None) == "subtask" and a.action == "add":
        missing = [f for f, v in (("--name", a.name), ("--desc", a.desc)) if not v]
        if missing:
            p.error(f"subtask add 必填: {', '.join(missing)} (sid/name/desc 缺一不可; agent 省略默认 skein-executor)")
    if a.cmd == "session-context":
        # hook 在任意仓库每 session 都跑: 非 git 且无 .skein → 方法内静默返回; git 仓无 .skein → 注入 setup 建议
        # env 持久化与 git 无关, 必须先于 Skein() 跑 —— 微服务/前后端分离场景 cwd 无 git (子目录各自是仓)。
        _persist_bash_cwd_env()  # 随插件发货 _ENV_EXPORTS (cwd 保持 + 禁 agent-teams; plugin.json 无 env 字段, 只能经 CLAUDE_ENV_FILE)
        Skein().session_context()
        return
    if a.cmd == "user-prompt":
        # 每 prompt 都跑: 非 git 且无 .skein → 方法内静默返回; 提醒不依赖 .skein 初始化状态
        Skein().user_prompt()
        return
    sk = Skein()
    dispatch = {
        "init": sk.init, "setup": sk.setup, "create": sk.create, "start": sk.start,
        "finish": sk.finish, "archive": sk.archive, "clean": sk.clean, "current": sk.current,
        "ready": sk.ready, "pop": sk.pop,
        "list": sk.list_, "board": sk.board, "view": sk.view, "serve": sk.serve,
        "doctor": sk.doctor, "contract": sk.contract, "repos": sk.repos,
        "status": sk.status, "subtask": sk.subtask,
    }
    # 会写 task.json / task.md 的命令加工作区写锁 (防多 skein 进程并发 read-modify-write)。
    # 纯读命令 (current/ready/list/board/view) 免锁。subtask 含读 action 但整体加锁最省事。
    MUTATING = {"init", "setup", "create", "start", "finish", "archive", "clean",
                "contract", "repos", "subtask"}
    if a.cmd in MUTATING:
        with _workspace_lock(sk.dir / ".lock"):
            dispatch[a.cmd](a)
    else:
        dispatch[a.cmd](a)
    DBG.log(f"✓ {a.cmd} 完成", style="bold green")


if __name__ == "__main__":
    main()
