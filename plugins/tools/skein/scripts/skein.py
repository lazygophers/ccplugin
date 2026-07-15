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
(current/list/board/subtask list/ready), 禁直接 Read/Edit/Write (guard-skein.py 硬阻)。
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
    def _board_html(self, persist=True):
        # persist=False (serve 每请求实时渲染): 只返回 html 字符串, 不落盘 task.html — serve 不写 task.md/task.html。
        st_cls = {S_PENDING: "s-pending", S_ACTIVE: "s-active",
                  S_CHECK: "s-check", S_DONE: "s-done"}
        ss_cls = {SS_PENDING: "ss-pending", SS_RUNNING: "ss-running",
                  SS_DONE: "ss-done", SS_FAILED: "ss-failed"}

        def esc(s):
            return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        def badge(text, clsmap):
            return f'<span class="badge {clsmap.get(text, "")}">{esc(text)}</span>'

        def fmt_dur(mins):
            if mins is None:
                return "-"
            return f"{mins}m" if mins < 60 else f"{mins // 60}h{mins % 60:02d}m"

        def bar(pct, sub=False, cls=""):
            # width + label 均封顶 100% (进度不可 >100%); 超时靠红色 over class + 原始耗时/预期文本传达
            p = min(pct, 100)
            kind = cls or "prog"  # 完成度条标 prog: CSS 按 --p 在主题 palette 内插值上色, 随主题/配色自适应
            c = "bar " + kind + (" sub" if sub else "")
            style = f"width:{p}%" + (f";--p:{p}" if kind == "prog" else "")
            return (f'<div class="{c}"><div class="fill" '
                    f'style="{style}"></div><span class="pct">{p}%</span></div>')

        # 状态 -> CSS 变量 (执行顺序图节点左边框着色); task/subtask 状态共用 (值同名)
        node_var = {S_PENDING: "--st-pending", S_ACTIVE: "--st-active", S_CHECK: "--st-check",
                    S_DONE: "--st-done", SS_RUNNING: "--st-active", SS_FAILED: "--st-failed"}
        # 状态 -> 节点 CSS 类 (整框按状态着色 + 进行中/运行中 呼吸动画, 见 base.css .dag g.n-*)
        node_cls = {S_PENDING: "n-pending", S_ACTIVE: "n-active", S_CHECK: "n-check",
                    S_DONE: "n-done", SS_RUNNING: "n-active", SS_FAILED: "n-failed"}

        def dag_html(nodes, tips=None, links=None, force_vertical=False):
            # nodes: [(id, name, status, deps, pct, desc)] -> SVG 有向连接图: 箭头 dep->node, 并行节点同列; 离线无 JS/CDN
            # pct/desc 可缺 (老三元组兼容): 节点框显 id + 完成% + 名字 + desc
            # tips: {id: html} -> 该节点悬浮浮层内容 (subtask DAG + 总进度条), switcher.js 绑定 hover 显隐
            # links: {id: href} -> 该节点包 <a> 点击跳转 (task 节点 -> 对应卡片锚点)
            # force_vertical: True -> 恒上往下布局 (窄左栏用, 不看宽度阈值)
            if len(nodes) < 2:
                return ""
            ids = {n[0] for n in nodes}
            dep = {n[0]: [d for d in n[3] if d in ids] for n in nodes}
            smap = {n[0]: n for n in nodes}
            order = {n[0]: k for k, n in enumerate(nodes)}  # 稳定排行
            # 分层: layer = 最长依赖深度 (列 = 执行波次, 并行节点落同列)
            layer = {}

            def depth(i, seen):
                if i in layer:
                    return layer[i]
                if i in seen:  # 环兜底
                    return 0
                d = 1 + max((depth(p, seen | {i}) for p in dep[i]), default=-1)
                layer[i] = d
                return d
            for i in ids:
                depth(i, set())
            layers = {}
            for i, d in layer.items():
                layers.setdefault(d, []).append(i)
            for d in layers:
                layers[d].sort(key=lambda i: order[i])
            # 节点框限宽: 不再靠加宽容纳长 name/desc (避免水平滚动), 而是限宽 + 文本多行换行, 框高随行数增长。
            # 估文本像素宽 (CJK 全宽 1em, 其余约 0.6em)。
            def txtw(s, fs):
                return sum(fs if ord(c) > 0x2E80 else fs * 0.6 for c in str(s))
            def wrap(s, fs, maxpx):  # 按估宽贪心断行 (CJK 无词界逐字断; 拉丁尽量在空格断)
                s = str(s or "")
                if not s:
                    return []
                out, cur = [], ""
                for ch in s:
                    if cur and txtw(cur + ch, fs) > maxpx:
                        cut = cur.rfind(" ")
                        if cut > 0 and ord(ch) < 0x2E80:  # 拉丁: 回退到最近空格断词
                            out.append(cur[:cut]); cur = cur[cut + 1:] + ch
                        else:
                            out.append(cur); cur = ch
                    else:
                        cur += ch
                if cur:
                    out.append(cur)
                return out
            PAD, CAP = 14, 272                       # 内边距 + 框宽上限 (超出即换行不加宽)
            need = 208.0                             # 最小框宽保底
            for n in nodes:                          # id 行不换行 → 参与定宽; name/desc 换行不撑宽
                pct = n[4] if len(n) > 4 else None
                idrow = txtw(n[0], 13) + (txtw(f"{pct}%", 11) + 14 if pct is not None else 0)
                need = max(need, idrow + PAD * 2)
            NW = min(int(need + 0.999), CAP)
            inner = NW - PAD * 2 - 4                 # 文本可用宽 (减左色条)
            wrapped = {}                             # id -> (name 行列表, desc 行列表)
            for n in nodes:
                dsc = n[5] if len(n) > 5 and n[5] else ""
                wrapped[n[0]] = (wrap(n[1], 12, inner) or [""], wrap(dsc, 10, inner))
            nm_max = max(len(v[0]) for v in wrapped.values())
            ds_max = max(len(v[1]) for v in wrapped.values())
            # 统一框高 = id 行 + name 行块 + (desc 行块) + 上下留白 (各节点顶对齐, 短内容留白底)
            NH = 30 + nm_max * 16 + (6 + ds_max * 14 if ds_max else 0) + 10
            COL, ROW = NW + 34, NH + 20
            nlayer = max(layers) + 1
            span = max(len(v) for v in layers.values())
            # 交叉削减 (Sugiyama 重心法): 迭代按相邻层邻居的平均序位重排各层, 减连线交叉、让子节点自然对到父节点下方,
            # 避免节点全堆左侧、连线乱交叉。上行看子、下行看父, 往返数轮收敛。
            kids = {i: [] for i in ids}
            for i in ids:
                for p in dep[i]:
                    kids[p].append(i)
            col_of = {i: k for d in layers for k, i in enumerate(layers[d])}
            def _bary(i, nb):
                ns = nb[i]
                return sum(col_of[n] for n in ns) / len(ns) if ns else col_of[i]
            for _ in range(4):
                for d in sorted(layers)[1:]:            # 下行: 按父重心排
                    layers[d].sort(key=lambda i: _bary(i, dep))
                    for k, i in enumerate(layers[d]):
                        col_of[i] = k
                for d in sorted(layers, reverse=True)[:-1]:  # 上行: 按子重心排
                    layers[d].sort(key=lambda i: _bary(i, kids))
                    for k, i in enumerate(layers[d]):
                        col_of[i] = k
            # 朝向: 默认 layer→列 (左右向); 但左右向宽 > 1180 (超典型正文宽必横向滚动) 转纵向 (layer→行, 上往下),
            # 纵向列数 = 单层并行节点数, 通常更少, 更可能一屏放下、只需纵向滚动。
            vertical = force_vertical or nlayer * COL + 10 > 1180
            if vertical:
                # 同层并行节点横排, 一行最多 PER=4 个 (超出折行免过宽被缩糊); 每视觉行水平居中 → 金字塔铺开非左堆
                PER = 4
                maxcols = min(span, PER)
                pos, roff = {}, 0  # roff = 已累计占用行数
                for d in sorted(layers):
                    ids_ = layers[d]
                    nrow = (len(ids_) + PER - 1) // PER
                    for sub in range(nrow):
                        chunk = ids_[sub * PER:(sub + 1) * PER]
                        off = (maxcols - len(chunk)) * COL // 2  # 居中该视觉行
                        for col, i in enumerate(chunk):
                            pos[i] = (off + col * COL + 10, (roff + sub) * ROW + 10)
                    roff += nrow
                W = maxcols * COL + 10
                H = roff * ROW + 10
            else:
                # 每列 (执行波次) 垂直居中 → 对称铺开非顶堆
                pos = {}
                for d, ids_ in layers.items():
                    off = (span - len(ids_)) * ROW // 2
                    for r, i in enumerate(ids_):
                        pos[i] = (d * COL + 10, off + r * ROW + 10)
                W = nlayer * COL + 10
                H = span * ROW + 10
            lines = []
            for i in ids:
                x2, y2 = pos[i]
                for p in dep[i]:
                    x1, y1 = pos[p]
                    if vertical:
                        # dep 在上、node 在下: 父下缘中点 → 子上缘中点, 箭头朝下
                        sx, sy = x1 + NW / 2, y1 + NH
                        ex, ey = x2 + NW / 2, y2
                        my = (sy + ey) / 2
                        lines.append(
                            f'<path d="M{sx},{sy} C{sx},{my} {ex},{my} {ex},{ey - 2}" fill="none" '
                            f'stroke="var(--muted)" stroke-width="1.5"/>'
                            f'<polygon points="{ex - 4},{ey - 8} {ex},{ey} {ex + 4},{ey - 8}" fill="var(--muted)"/>')
                    else:
                        # dep 在左、node 在右: 父右缘中点 → 子左缘中点, 箭头朝右
                        ey = y2 + NH / 2
                        sx, sy = x1 + NW, y1 + NH / 2
                        mx = (sx + x2) / 2
                        lines.append(
                            f'<path d="M{sx},{sy} C{mx},{sy} {mx},{ey} {x2 - 2},{ey}" fill="none" '
                            f'stroke="var(--muted)" stroke-width="1.5"/>'
                            f'<polygon points="{x2 - 8},{ey - 4} {x2},{ey} {x2 - 8},{ey + 4}" fill="var(--muted)"/>')
            boxes = []
            for i in ids:
                x, y = pos[i]
                node = smap[i]
                _id, stt = node[0], node[2]
                pct = node[4] if len(node) > 4 else None
                nm_lines, ds_lines = wrapped[_id]
                pct_txt = (f'<text x="{x + NW - 12}" y="{y + 22}" font-size="11" text-anchor="end" '
                           f'fill="var(--head)">{pct}%</text>') if pct is not None else ""
                # name 多行: 首行 y+44, 步进 16; desc 接在 name 行块 (nm_max) 之后, 步进 14
                nm_txt = "".join(
                    f'<text x="{x + 14}" y="{y + 44 + k * 16}" font-size="12" '
                    f'fill="var(--fg)">{esc(ln)}</text>' for k, ln in enumerate(nm_lines))
                ds_top = 44 + nm_max * 16
                desc_txt = "".join(
                    f'<text x="{x + 14}" y="{y + ds_top + k * 14}" font-size="10" '
                    f'fill="var(--muted)">{esc(ln)}</text>' for k, ln in enumerate(ds_lines))
                has_tip = tips and i in tips
                has_link = links and i in links
                # data-search: id+名+desc 小写拼串, switcher.js 搜索按子串命中此节点 (命中高亮/未命中变灰)
                blob = esc(" ".join(str(x or "") for x in (_id, node[1], node[5] if len(node) > 5 else "")).lower())
                g_attr = (f' data-tip="{esc(i)}"' if has_tip else "") + f' data-search="{blob}"'
                g_cls = (node_cls.get(stt, "") + (" has-tip" if has_tip else "")
                         + (" has-link" if has_link else "")).strip()
                g = (
                    f'<g class="{g_cls}"{g_attr}><rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="6" '
                    f'fill="var(--bg)" stroke="var(--brd)"/>'
                    f'<rect x="{x}" y="{y}" width="4" height="{NH}" rx="2" '
                    f'fill="var({node_var.get(stt, "--muted")})"/>'
                    f'<text x="{x + 14}" y="{y + 22}" font-size="13" fill="var(--fg)">{esc(_id)}</text>'
                    f'{pct_txt}{nm_txt}{desc_txt}</g>')
                if has_link:
                    g = f'<a href="{esc(links[i])}">{g}</a>'
                boxes.append(g)
            svg = (f'<svg class="dag" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
                   f'xmlns="http://www.w3.org/2000/svg">{"".join(lines)}{"".join(boxes)}</svg>')
            # 恒包 dag-wrap: 容器 overflow:auto, 过长 DAG 滚动而非缩糊 (svg 保持固有 W×H)
            tip_html = "".join(f'<div class="dag-tip" data-for="{esc(i)}">{tips[i]}</div>'
                               for i in ids if i in tips) if tips else ""
            return f'<div class="dag-wrap">{svg}{tip_html}</div>'

        tnow = now()
        # 排序: 状态分组 (进行中→检查中→待处理→已完成), 组内按执行时间(started)倒序 (新执行在前; 未启动 started=None 视 0)
        _srank = {S_ACTIVE: 0, S_CHECK: 1, S_PENDING: 2, S_DONE: 3}
        tasks = sorted(self._render_tasks(), key=lambda t: (_srank.get(t["status"], 9), -(t.get("started") or 0)))
        DBG.rule("渲染看板 HTML")
        total_sub = sum(len(t.get("subtasks", [])) for t in tasks)
        dest = self.html_path if persist else "(内存, serve 实时渲染, 不落盘)"
        DBG.log(f"渲染 {len(tasks)} 个 task / 合计 {total_sub} 个 subtask → {dest}", style="cyan")
        name_of = {t["id"]: t.get("name", t["id"]) for t in tasks}  # 依赖显示名字, 存储仍用 id

        def elapsed_of(t):
            # 实际耗时: DONE = finished-started (真实执行时长); active = tnow-started (至今); pending = 0
            st = t.get("status")
            if st == S_PENDING:  # 未启动 task 无耗时
                return 0
            start = t.get("started") or t.get("created")
            if not start:
                return 0
            end = t.get("finished") if (st == S_DONE and t.get("finished")) else tnow
            return round((end - start) / 60)

        def task_pct(t):
            # task 完成百分比: DONE=100, 否则 = subtask 平均完成比 (无 subtask 记 0)
            if t["status"] == S_DONE:
                return 100
            subs = t.get("subtasks", [])
            return round(sum(_sub_pct(s) for s in subs) / len(subs)) if subs else 0

        # 任务进展总览: 各状态计数 + 时长合计 (整体进度改由 combined 单位均值算, 见下)
        cnt = {}
        est_total = 0    # 预期时长合计 (min)
        elapsed_total = 0  # 已耗合计 (min)
        remain_est = 0.0    # 剩余预估时长 = Σ 未完成 task 的 estimate×(1-frac)
        for t in tasks:
            cnt[t["status"]] = cnt.get(t["status"], 0) + 1
            if t["status"] == S_DONE:
                frac = 1.0
            else:
                subs = t.get("subtasks", [])
                frac = sum(_sub_pct(s) for s in subs) / (len(subs) * 100) if subs else 0.0
            est = t.get("estimate") or 0
            est_total += est
            elapsed_total += elapsed_of(t)
            remain_est += est * (1 - frac)  # 未估 (est=0) 不计剩余
        task_nodes = [(t["id"], t.get("name", t["id"]), t["status"], t.get("deps", []),
                       task_pct(t), t.get("desc", "")) for t in tasks]
        # 概览 task 节点悬浮浮层: 该 task 的总进度条 + subtask DAG (单 subtask 无图则列表兜底)
        # links: 点击 task 节点跳到对应卡片锚点 (#task-<id>)
        tips = {}
        links = {t["id"]: f'#task-{t["id"]}' for t in tasks}
        for t in tasks:
            subs = t.get("subtasks", [])
            snodes = [(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", []),
                       _sub_pct(s), s.get("desc", "")) for s in subs]
            sub_dag = dag_html(snodes)
            if not sub_dag:
                sub_dag = ('<p class="empty">无 subtask</p>' if not subs else
                           '<p class="meta">' + " · ".join(
                               f'{esc(s.get("name", s["sid"]))} {_sub_pct(s)}%' for s in subs) + '</p>')
            tips[t["id"]] = (f'<p class="meta">{esc(t.get("name", t["id"]))} · 总进度</p>'
                             f'{bar(task_pct(t), sub=True)}{sub_dag}')
        # task+subtask 维度 DAG: task 不作单独节点 — 只画 subtask, subtask 间连 sub-deps;
        # 跨 task 前置 = 连到前置 task 的叶子 subtask (该 task 内无人再依赖的 subtask); 无 subtask 的 task 仍作节点兜底。
        has_sub = any(t.get("subtasks") for t in tasks)
        leaves = {}  # tid -> 该 task 的出口节点 id 列表 (供后继 task 的入口 subtask 挂靠)
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
                combined.append((t["id"], t.get("name", t["id"]), t["status"], prereq,
                                 task_pct(t), t.get("desc", "")))
                continue
            intra = {s["sid"] for s in subs}
            for s in subs:
                sid = f'{t["id"]}/{s["sid"]}'
                sdeps = [f'{t["id"]}/{d}' for d in s.get("depends_on", []) if d in intra]
                if not sdeps:  # 入口 subtask: 继承父 task 的前置 (连到前置 task 出口)
                    sdeps = list(prereq)
                combined.append((sid, s.get("name", s["sid"]), s["status"], sdeps,
                                 _sub_pct(s), s.get("desc", "")))
        # 整体进度 = task+subtask 维度综合 (每 subtask / 每无 subtask 的 task 各记 1 单位, 取完成 % 均值)
        combined_pct = round(sum(n[4] for n in combined) / len(combined)) if combined else 0
        # 三状态统计卡 (已完成 / 进行中 / 待处理 数量)
        def statcard(label, key):
            return (f'<div class="stat"><span class="stat-n">{cnt.get(key, 0)}</span>'
                    f'<span class="stat-l">{esc(label)}</span></div>')
        stats = (f'<div class="stats">{statcard("已完成", S_DONE)}'
                 f'{statcard("进行中", S_ACTIVE)}{statcard("待处理", S_PENDING)}</div>')
        # DAG 维度切换 (task 默认 / task+subtask); switcher.js 绑定按钮显隐对应视图
        switch = (f'<div class="dag-switch" role="group">'
                  f'<button type="button" data-dag="task" class="on">task 维度</button>'
                  f'<button type="button" data-dag="full"{"" if has_sub else " disabled"}>'
                  f'task+subtask 维度</button></div>')
        task_view = f'<div class="dag-view" data-dag="task">{dag_html(task_nodes, tips, links, force_vertical=True)}</div>'
        full_view = (f'<div class="dag-view" data-dag="full" hidden>{dag_html(combined, force_vertical=True)}</div>'
                     if has_sub else "")
        # 状态筛选 (从图钉移入任务进展): switcher.js 按 #sw-filter 值显隐右栏 task 卡
        filter_opts = [("all", "全部"), (S_ACTIVE, S_ACTIVE), (S_CHECK, S_CHECK),
                       (S_PENDING, S_PENDING), (S_DONE, S_DONE)]
        filter_ctrl = ('<label class="filter">状态筛选 <select id="sw-filter">'
                       + "".join(f'<option value="{esc(k)}">{esc(lb)}</option>' for k, lb in filter_opts)
                       + '</select></label>')
        overview = (
            f'<section class="card"><h2>任务进展</h2>'
            f'{switch}{filter_ctrl}{stats}'
            f'<p class="meta">{len(tasks)} task · 预期合计 {fmt_dur(est_total or None)} · '
            f'已耗 {fmt_dur(elapsed_total or None)} · 剩余预估 {fmt_dur(round(remain_est) or None)}</p>'
            f'<p class="meta">整体进度 (task+subtask 综合)</p>{bar(combined_pct)}'
            f'{task_view}{full_view}</section>')

        def prd_block(tid):
            # 解析 prd.md 的「目标」「验收标准」两节: checklist (- [ ]/- [x]) 显进度徽标 + 勾选; 纯文本/段落行也直显 (无 checkbox 亦不丢)。跳过未填 TODO 占位。
            prd = self.tasks / tid / "prd.md"
            if not prd.exists():
                return ""
            secs, cur = {}, None
            for ln in prd.read_text(encoding="utf-8", errors="replace").splitlines():
                h = re.match(r"^#{1,6}\s+(.+?)\s*$", ln)
                if h:
                    cur = h.group(1).strip() if h.group(1).strip() in ("目标", "验收标准") else None
                    continue
                if not cur:
                    continue
                m = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.+?)\s*$", ln)
                if m:  # checklist 项
                    txt = m.group(2).strip()
                    if not txt.lstrip().startswith("TODO"):
                        secs.setdefault(cur, []).append(("check", m.group(1).lower() == "x", txt))
                    continue
                # 非 checklist: 纯文本 / 无框列表项 (- foo), 收敛为 prose 直显 (跳空行 / TODO 占位)
                txt = re.sub(r"^\s*[-*]\s+", "", ln).strip()
                if txt and not txt.lstrip().startswith("TODO"):
                    secs.setdefault(cur, []).append(("prose", False, txt))
            parts = []
            for name in ("目标", "验收标准"):
                items = secs.get(name)
                if not items:
                    continue
                checks = [d for k, d, _ in items if k == "check"]
                badge = (f'<span class="prd-p">{sum(checks)}/{len(checks)}</span>'
                         if checks else "")
                lis = "".join(
                    (f'<li class="{"done" if d else ""}">{esc(t)}</li>' if k == "check"
                     else f'<li class="prose">{esc(t)}</li>')
                    for k, d, t in items)
                parts.append(f'<div class="prd-sec"><div class="prd-h">{esc(name)}{badge}</div>'
                             f'<ul class="prd-list">{lis}</ul></div>')
            return f'<div class="prd">{"".join(parts)}</div>' if parts else ""

        cards = []
        for t in tasks:
            subs = t.get("subtasks", [])
            sname_of = {s["sid"]: s.get("name", s["sid"]) for s in subs}  # subtask 依赖也显示名字
            sdone = sum(1 for s in subs if s["status"] == SS_DONE)
            spct = task_pct(t)  # DONE→100, 否则各 subtask 均值 (避免"都完成却非 100%")
            elapsed = elapsed_of(t)
            est = t.get("estimate")
            snodes = [(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", []),
                       _sub_pct(s), s.get("desc", "")) for s in subs]
            srows = "".join(
                f'<tr><td>{esc(s["sid"])}</td><td>{esc(s["name"])}</td>'
                f'<td>{badge(s["status"], ss_cls)}</td>'
                f'<td>{bar(_sub_pct(s), sub=True)}</td>'
                f'<td>{esc(fmt_dur(s.get("estimate")))}</td>'
                f'<td>{esc(s.get("agent", "skein-executor"))}</td>'
                f'<td>{esc(",".join(s.get("skills", [])) or "-")}</td>'
                f'<td>{esc(", ".join(sname_of.get(d, d) for d in s.get("depends_on", [])) or "-")}</td>'
                f'<td>{esc("; ".join(s.get("验收", [])) or "-")}</td></tr>' for s in subs)
            subtable = (
                '<table><thead><tr><th>sid</th><th>名称</th><th>状态</th><th>进度</th>'
                '<th>预期</th><th>agent</th><th>skills</th><th>依赖</th><th>验收标准</th></tr></thead>'
                f'<tbody>{srows}</tbody></table>' if subs
                else '<p class="empty">无 subtask</p>')
            # data-search: task id+名+desc + 各 subtask sid+名+desc 小写拼串, 搜索命中则右栏保留该卡 + 高亮关键词
            sblob = esc(" ".join(str(x or "") for x in (
                t["id"], t.get("name", ""), t.get("desc", ""),
                *(v for s in subs for v in (s["sid"], s.get("name", ""), s.get("desc", ""))))).lower())
            # 规划文档按钮: 仅当 .skein/task/<id>/<f>.md 存在才出; serve (http) 静态托管 .skein/ → doc.js fetch 渲染
            tdir = self.tasks / t["id"]
            dl = "".join(
                f'<button type="button" class="doc-link" data-doc="task/{esc(t["id"])}/{fn}" '
                f'data-title="{esc(lab)} · {esc(t["id"])}">{esc(lab)}</button>'
                for fn, lab in (("prd.md", "PRD"), ("design.md", "设计"), ("findings.md", "调研"))
                if (tdir / fn).exists())
            doc_row = f'<p class="doc-links">{dl}</p>' if dl else ""
            cards.append(
                f'<section class="card" id="task-{esc(t["id"])}" data-status="{esc(t["status"])}" data-search="{sblob}">'
                f'<h2>{esc(t["id"])} {badge(t["status"], st_cls)}</h2>'
                f'<p class="name">{esc(t.get("name", ""))}</p>'
                f'{doc_row}'
                f'{prd_block(t["id"])}'
                f'<p class="meta">前置: {esc(", ".join(name_of.get(d, d) for d in t.get("deps", [])) or "-")} · '
                f'worktree: {esc(t.get("worktree") or "-")} · '
                f'耗时 {fmt_dur(elapsed)} / 预期 {fmt_dur(est)}</p>'
                f'<p class="meta">子任务 {sdone}/{len(subs)}</p>{bar(spct, sub=True)}'
                f'<details class="detail" open><summary>明细 · DAG + 子任务表</summary>'
                f'{dag_html(snodes, force_vertical=True)}'  # 右栏详情恒上往下 (窄栏纵向铺开, CSS 再放开高度/固定宽)
                f'{subtable}</details></section>')
        # 两栏布局: 左=总计 (综合指标 + task DAG 上往下), 右=task 卡片列表 (窄屏 CSS 回落单列)
        right = "\n".join(cards) if cards else '<p class="empty">无 task</p>'
        body = (f'<div class="layout">'
                f'<aside class="col-side">{overview}</aside>'
                f'<main class="col-main">{right}</main></div>')

        # 链接恒用相对 board/: file:// 视图 (persist) 解析到 .skein/board/ (需拷贝); serve(http) 由 do_GET 路由 /board/* → 插件 assets, 不拷。
        if persist:
            self._copy_board_assets()
        base = "board"
        cfg = self.config()
        theme = cfg.get("board_theme", "skein")
        links = (f'<link rel=stylesheet href="{base}/base.css">'
                 + "".join(f'<link rel=stylesheet href="{base}/themes/{k}.css">' for k, _ in THEMES))

        def opts(items, cur):
            return "".join(f'<option value="{k}"{" selected" if k == cur else ""}>{esc(label)}</option>'
                           for k, label in items)
        # 浮动按钮 (FloatButton 式): fixed 右下角圆钮, 点击展开控件面板 (switcher.js 绑定开合)
        # 状态筛选已移入任务进展卡; 面板留主题 + 刷新页面 + 回到顶部
        switcher = (
            '<div class="fab-wrap">'
            '<div class="switcher">'
            f'<label>主题<select id="sw-theme">{opts(THEMES, theme)}</select></label>'
            '<button type="button" class="sw-btn" id="sw-refresh">⟳ 刷新页面</button>'
            '<button type="button" class="sw-btn" id="sw-top">↑ 回到顶部</button>'
            '</div>'
            '<button type="button" class="fab" id="sw-fab" aria-label="看板设置" aria-expanded="false">⚙</button>'
            '</div>')
        html = (
            f'<!doctype html><html lang=zh-CN data-theme="{theme}">'
            '<head><meta charset=utf-8>'
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            # 兜底刷新: file:// 下 HEAD 轮询 fetch 抛错无效 → 每 1800s (半小时) 硬刷新保证不 stale
            '<meta http-equiv=refresh content=1800>'
            f'<title>SKEIN · {esc(self.proj)}</title>{links}</head><body>'
            f'<header class="topbar"><h1>SKEIN 看板 · {esc(self.proj)}</h1>'
            '<input type="search" id="sw-search" class="search" placeholder="搜索 id / 名称 / 描述…" '
            'autocomplete="off" aria-label="搜索 task">'
            f'</header>{body}{switcher}'
            # 规划文档查看浮层 (doc.js 绑定 .doc-link 点击 → fetch md → 渲染)
            '<div class="doc-modal" id="doc-modal" hidden>'
            '<div class="doc-backdrop"></div>'
            '<div class="doc-panel" role="dialog" aria-modal="true">'
            '<header class="doc-head"><span class="doc-title"></span>'
            '<button type="button" class="doc-copy" aria-label="复制 md 原文">⧉ 复制</button>'
            '<button type="button" class="doc-close" aria-label="关闭">✕</button></header>'
            '<article class="doc-body markdown"></article></div></div>'
            f'<script src="{base}/switcher.js"></script>'
            f'<script src="{base}/skein-fx.js"></script>'  # 缕光主题 canvas 水面动效 (自门控)
            f'<script src="{base}/vendor/marked.min.js"></script>'  # 离线 markdown 渲染器 (vendored)
            f'<script src="{base}/doc.js"></script>'  # 规划文档 (prd/design/findings) 浮层查看
            # 自动刷新: serve (http) 下轮询 /__skein__/rev (全部 task.json 最大 mtime), 变了才 reload (空闲不闪);
            # file:// 下端点不存在 fetch 抛错 → 静默 no-op (view 每次重开已是最新)
            '<script>(function(){var m;setInterval(function(){'
            'fetch("/__skein__/rev",{cache:"no-store"}).then(function(r){return r.text();}).then(function(v){'
            'if(v){if(m&&v!==m)location.reload();m=v;}'
            '}).catch(function(){});},2000);})();</script></body></html>')
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
    _REV_PATH = "/__skein__/rev"  # 版本探测端点: 全部 task.json 最大 mtime, 前端轮询变则 reload

    def _task_json_rev(self) -> str:
        # 顶层 task.json + 各 task/<id>/task.json 的最大 mtime_ns → 任一变更即变, 驱动前端自动重载。
        files = [self.dir / "task.json"] + list(self.tasks.glob("*/task.json"))
        return str(max((f.stat().st_mtime_ns for f in files if f.exists()), default=0))

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
        # 起本地 http 服务 (随机 port, bind :0) 服务 .skein/。相对资源 (board/*.js/css) 靠 http root 正确解析。Ctrl-C 停。
        # quiet=True (monitor): 不打印 info (启动 URL / 停止行); 访问日志 (info/warn) 恒静默; error 走 log_error → stderr 保留。
        import http.server, socketserver, functools, json, atexit, signal

        lock = self._lock_file()
        proj_id = str(self.dir.resolve())
        # 已有同项目服务在跑 → 复用, 不再起第二个 (多 session monitor 去重)。lock 失效/属别的项目 → 落下方 bind :0 拿新随机 port 覆盖。
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
                    import webbrowser
                    webbrowser.open(url)
                return

        id_path, id_body = self._LOCK_ID_PATH, proj_id.encode()
        rev_path, board = self._REV_PATH, self  # board: 每请求实时从 task.json 渲染, 不吃静态 task.html
        assets_dir = (Path(__file__).resolve().parent.parent / "assets" / "board").resolve()  # /board/* 直出插件资产, 不拷 .skein/

        class Handler(http.server.SimpleHTTPRequestHandler):
            def _send(self, body, ctype):
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                p = self.path.split("?", 1)[0]
                if p == id_path:  # 身份探测端点
                    self._send(id_body, "text/plain")
                    return
                if p == rev_path:  # 版本探测端点: 前端轮询
                    self._send(board._task_json_rev().encode(), "text/plain")
                    return
                if p in ("/", "/task.html"):  # 看板页: 每请求实时从 task.json 渲染, 不落盘 task.html
                    self._send(board._board_html(persist=False).encode("utf-8"), "text/html; charset=utf-8")
                    return
                if p.startswith("/board/"):  # 静态资产直出插件 assets/board/, 不经 .skein/board/ (serve 不拷)
                    import mimetypes
                    fp = (assets_dir / p[len("/board/"):]).resolve()
                    if not str(fp).startswith(str(assets_dir) + "/") or not fp.is_file():
                        self.send_error(404)
                        return
                    self._send(fp.read_bytes(), mimetypes.guess_type(str(fp))[0] or "application/octet-stream")
                    return
                return super().do_GET()

            def do_POST(self):  # 看板 UI 改配置 → 落回 config.yaml (仅 board_theme, 值须在 THEMES 内)
                if self.path.split("?", 1)[0] != "/__skein__/config":
                    self.send_error(404)
                    return
                try:
                    body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                    self._log_extra = f" body={json.dumps(body, ensure_ascii=False)}"
                    v = body.get("board_theme")
                    if v not in {k for k, _ in THEMES}:
                        raise ValueError("bad theme")
                    board._set_config("board_theme", v)
                    self._send(b'{"ok":true}', "application/json")
                except Exception:
                    self.send_error(400)

            _log_extra = ""  # 请求附加信息 (POST body 等); 处理器按需设, _log 打印后清

            def _log(self, code):
                # 2026-07-15 21:12:57.123 GET /task.html -> 200   (POST 追加 body=...)
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                sys.stderr.write(f"{ts} {self.command} {self.path}{self._log_extra} -> {code}\n")
                self._log_extra = ""  # 清, 免 keep-alive 连接下条请求串味

            def log_request(self, code="-", size="-"):
                self._log(code.value if hasattr(code, "value") else code)

            def log_error(self, *a):
                pass  # 错误码已并入 log_request 单行, 免 "code 404, message ..." 重复噪声

        handler = functools.partial(Handler, directory=str(self.dir))
        with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
            port = httpd.server_address[1]
            lock.write_text(json.dumps({"port": port, "project": proj_id}))

            def _cleanup():  # 退出前删 lock (仅删本进程写的, 防误删他实例)
                try:
                    if lock.exists() and json.loads(lock.read_text()).get("port") == port:
                        lock.unlink()
                except Exception:
                    pass

            atexit.register(_cleanup)
            # monitor 关服务发 SIGTERM (默认直接终止, 不走 atexit/finally) → 转成 KeyboardInterrupt 走清理
            try:
                signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
            except (ValueError, OSError):
                pass  # 非主线程无法注册, 忽略
            url = f"http://127.0.0.1:{port}/task.html"
            if not quiet:
                print(f"SKEIN 看板服务已启动: {url}  (Ctrl-C 停止)", flush=True)  # flush: 交互模式即时回显 URL
            if open_browser:
                import webbrowser
                webbrowser.open(url)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                if not quiet:
                    print("\n看板服务已停止")
            finally:
                _cleanup()

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
