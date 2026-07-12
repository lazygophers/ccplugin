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
  .skein/task/<id>/task.md        单 task 子任务看板 (渲染) — 脚本维护, AI 禁读写
  .skein/task/<id>/{prd,design,implement}.md  planning 工件 (skein-planning 写, AI 可读写)
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
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # 同目录 hooklib 可导入 (hook 环境非 Bash PATH)
from hooklib import budget_guard  # noqa: E402

SESSION_CTX_BUDGET_TOKENS = 400  # session-context 注入 token 硬预算 (active task ≤2, 正常远低于)

# task 状态 (中文落盘, 逻辑比较用常量)
S_PENDING = "待处理"
S_ACTIVE = "进行中"
S_CHECK = "检查中"
S_DONE = "已完成"
STATUS_ACTIVE = {S_ACTIVE, S_CHECK}
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
# 看板主题/配色 (值 = board/ 下 css 文件名; 独立 css, 非内联). 页内切换器 + config 默认二选一.
THEMES = [("morandi", "莫兰迪"), ("glassmorphism", "玻璃拟态"),
          ("liquid", "液态玻璃"), ("handdrawn", "手绘"),
          ("flat", "极简扁平"), ("sketch", "素描"), ("terminal", "终端"),
          ("bauhaus", "包豪斯"), ("comic", "漫画"), ("collage", "拼贴"),
          ("aero", "水光"), ("blueprint", "蓝图"), ("linear", "Linear"),
          ("gradient", "现代渐变"), ("neumorphism", "新拟物"),
          ("ghibli", "吉卜力"), ("holographic", "全息")]
PALETTES = [("stone", "石灰"), ("ocean", "海洋"), ("warm", "暖橙"),
            ("forest", "森林"), ("dusk", "暮紫"), ("mono", "单色")]


def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳


# 插件无法直接发货 settings.json 的 env 块 (plugin.json 无 env 字段)。
# 官方持久化 env 的机制: SessionStart hook 往 $CLAUDE_ENV_FILE 追加 export。
# 这样该 env 随 skein 插件的 SessionStart hook 一起发货, 不落用户项目 settings。
_BASH_CWD_EXPORT = "export CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1"


def _persist_bash_cwd_env():
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        return  # 非 SessionStart/Setup/CwdChanged/FileChanged 事件时不可用, 静默跳过
    try:
        p = Path(env_file)
        if p.exists() and _BASH_CWD_EXPORT in p.read_text():
            return  # 幂等: 同会话已写过不重复
        with p.open("a") as f:
            f.write(_BASH_CWD_EXPORT + "\n")
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
        yield
    finally:
        f.close()  # 关闭即释放 flock


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
    "worktree_root": ".worktrees",
    "retain_days": 7,  # 完成 task 保留天数; 0=finish 即归档, 负=永不自动
    "board_theme": "sketch",
    "board_palette": "stone",
    "board_mode": "light",
    "board_server": False,  # view: True→本地 http server 随机 port + 开浏览器; False→file:// 直开
    "web_serve": True,  # experimental.monitors: 每 session 起持久看板 http 服务; False→关闭 (monitor 仍启动但 serve 命令 no-op 退出)
}


def git(*args, cwd=None, check=True, capture=True):
    r = subprocess.run(
        ["git", *args], cwd=cwd, check=False,
        capture_output=capture, text=True,
    )
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
        self._board(None)  # 变更即刷 task.md, 免看板漂移
        self._board_html()  # + 生成 .skein/task.html 可视化页 (不自动打开; `skein.py view` 按需开)

    def _load(self, tid) -> dict:
        f = self.tasks / tid / "task.json"
        if not f.exists():
            raise SystemExit(f"task 不存在: {tid}")
        return json.loads(f.read_text())

    def _save(self, t: dict):
        t["updated"] = now()
        (self.tasks / t["id"] / "task.json").write_text(json.dumps(t, ensure_ascii=False, indent=2))
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
                out.append(json.loads(f.read_text()))
        # 状态优先排序 (进行中>检查中>待处理>已完成), 同状态内保持 id 序
        out.sort(key=lambda t: STATUS_ORDER.get(t["status"], 9))
        return out

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
            gi.write_text("# skein.py 自动渲染, 从 task.json 无损重建, 不入库\ntask.md\ntask.html\nboard/\n.lock\n")
        # worktree 目录在 git 根 (worktree_root), .skein/.gitignore 管不到 → 补到根 .gitignore
        # (仅 git 仓库需要; 非 git 无 worktree, 不制造多余 .gitignore)
        if self.git:
            wt = self.config()["worktree_root"].rstrip("/") + "/"
            root_gi = self.root / ".gitignore"
            existing = root_gi.read_text() if root_gi.exists() else ""
            if wt not in existing:
                sep = "\n" if existing and not existing.endswith("\n") else ""
                with root_gi.open("a") as f:
                    f.write(f"{sep}# skein worktree 隔离 (任务源码改动落此, 不入库)\n{wt}\n")
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
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        t = {
            "id": tid, "name": a.name or tid, "desc": a.desc or "",
            "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
            "worktree": None, "branch": f"skein/{tid}",
            "estimate": a.estimate,  # AI 执行预期耗时 (分钟, planning 填; None=未估)
            "created": now(),        # 创建时刻
            "started": None,         # exec 时刻 (start 时置)
            "finished": None,        # 完成时刻 (finish 时置; 保留期从此计)
            "updated": now(),
        }
        self._save(t)  # _save 已渲染子任务看板
        self._sync()  # 刷新顶层 tasks 索引 + 看板 + html
        print(f"{tid}\t{self.tasks / tid}")

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
        if self.git:
            rel = f"{cfg['worktree_root']}/skein-{a.id}"  # 相对 project root 存盘, 免机器绝对路径入库
            git("worktree", "add", "-b", t["branch"], str(self.root / rel), "HEAD", cwd=self.root)
            t["worktree"] = rel
        else:
            t["worktree"] = None  # 非 git: 原地执行, 无 worktree 隔离
        if not t.get("started"):
            t["started"] = now()  # exec 时刻 (首次 start; 重启不覆盖)
        self._save(t)
        self._sync()
        loc = (f"worktree: {t['worktree']}\nbranch: {t['branch']}"
               if self.git else "非 git 仓库: 原地执行 (无 worktree 隔离)")
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
        rel = t.get("worktree")
        wt = self.root / rel if rel else None  # 存盘相对, 文件/git 操作用绝对
        if wt and wt.exists():
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
            # 合并回主工作区
            m = git("merge", "--no-ff", t["branch"], "-m",
                    f"skein: merge {tid} {t['name']}", cwd=self.root, check=False)
            if m.returncode != 0:
                git("merge", "--abort", cwd=self.root, check=False)
                raise SystemExit(
                    f"合并冲突 {tid} — 已 abort。手动解冲突后重跑 finish:\n{m.stdout}{m.stderr}")
            git("worktree", "remove", str(wt), "--force", cwd=self.root, check=False)
            git("branch", "-D", t["branch"], cwd=self.root, check=False)
        elif rel:
            sys.stderr.write(
                f"{tid} worktree 记录存在但目录缺失 ({rel}) — "
                f"跳过合并, 分支 {t['branch']} 若有提交未并入\n")
        t["status"] = S_DONE
        t["worktree"] = None
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
            rel = t.get("worktree")
            wt = self.root / rel if rel else None
            if wt and wt.exists():
                git("worktree", "remove", str(wt), "--force", cwd=self.root, check=False)
                git("branch", "-D", t["branch"], cwd=self.root, check=False)
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

    def list_(self, a):
        for t in self._all():
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

    def journal(self, a):
        # append-only 过程记录: 存 task 目录内 journal.md, 随 _archive 一并归档 (无审批, 区别 contract/sediment)
        tid = a.id
        self._load(tid)  # 校验 task 存在
        f = self.tasks / tid / "journal.md"
        if a.add:
            with f.open("a") as fh:  # 追加, 不存在则建
                fh.write(f"- {now()} {a.add}\n")
            print(f"{tid} journal +1")
        elif not f.exists():
            print("无 journal")
        else:
            print(f.read_text(), end="")

    def doctor(self, a):
        # 纯脚本体检: 扫 task/subtask 不变量违规 (源码真值 = per-task task.json)。
        # 不做 AI 判断, 只查机械可验的结构性问题。有 ✗ 错误 → exit 1 (可 CI/hook 门禁)。
        tasks = self._all()
        used = self._used_ids()  # 含已归档, dep 指向归档 task 合法
        ids = {t["id"] for t in tasks}
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
            if t.get("status") in STATUS_ACTIVE:
                if not t.get("subtasks"):
                    errs.append(f"{tid}: active 但无 subtask — 无法派发")
                if not t.get("started"):
                    warns.append(f"{tid}: active 但 started 未置")
                rel = t.get("worktree")
                if self.git:
                    if not rel:
                        warns.append(f"{tid}: active (git 仓) 但 worktree 未置")
                    elif not (self.root / rel).exists():
                        errs.append(f"{tid}: worktree 路径不存在: {rel}")
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

        # 顶层索引 vs per-task 真值
        idxf = self.dir / "task.json"
        if idxf.exists():
            idx = {x["id"]: x for x in json.loads(idxf.read_text()).get("tasks", [])}
            for t in tasks:
                ix = idx.get(t["id"])
                if ix is None:
                    warns.append(f"{t['id']}: 未在顶层 task.json 索引中 (跑任意变更命令重建)")
                elif ix.get("status") != t["status"]:
                    warns.append(f"{t['id']}: 索引 status ({ix.get('status')}) != 真值 ({t['status']})")

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
        ctx = ("# SKEIN task 判定\n"
               "若本次请求是**任务** (跨 ≥2 文件 / 单文件多处 / 多步骤 / 需调研 / 产出文档), "
               "加载 **skein-flow** skill 走强制闭环 (plan→exec→check→finish), 禁 inline 直接做。\n"
               "豁免 (直接答/改): 纯查询 · 问答 · 单文件单处 ≤20 行且位置已知。边界模糊 → AskUserQuestion 问用户。")
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
                return
        except OSError:
            pass
        path.write_text(content)

    def _board(self, _):
        rows = []
        for t in self._all():
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

    # ---- subtask DAG 调度 (单 task 内, 存 per-task task.json 的 subtasks[]) ----
    def _ready(self, t: list) -> list:
        """就绪批: pending + 依赖全 done, 截到空闲槽位 (并行只看 depends_on DAG, 无写文件冲突自算)。"""
        subs = t.get("subtasks", [])
        done = {s["sid"] for s in subs if s["status"] == SS_DONE}
        running = [s for s in subs if s["status"] == SS_RUNNING]
        slots = self.config().get("max_parallel", 2) - len(running)
        if slots <= 0:
            return []  # 并发满 → 阻塞
        picked = []
        for s in subs:
            if s["status"] != SS_PENDING:
                continue
            if not all(d in done for d in s.get("depends_on", [])):
                continue
            picked.append(s)
            if len(picked) >= slots:
                break
        return picked

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
                "sid": a.sid, "name": a.name or a.sid,
                "depends_on": _split(a.deps),
                "验收": _split_semi(a.check),  # 验收标准 checklist (字符串数组)
                "验收done": [],  # 已通过验收标准序号(1-based); 完成百分比 = len/len(验收)
                "status": SS_PENDING,
                "estimate": a.estimate,  # AI 执行预期耗时 (分钟, None=未估)
                "agent": a.agent or "general-purpose",  # 执行 agent (无合适则通用)
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
                ag = s.get("agent", "general-purpose")
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
                print(f"{s['sid']}\t{s['name']}\tagent: {s.get('agent', 'general-purpose')}\tskills: {sk}"
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
            ag = s.get("agent", "general-purpose")
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
    def _board_html(self):
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

        def dag_html(nodes):
            # nodes: [(id, name, status, deps)] -> SVG 有向连接图: 箭头 dep->node, 并行节点同列; 离线无 JS/CDN
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
            COL, ROW, NW, NH = 170, 56, 140, 40
            pos = {i: (d * COL + 10, r * ROW + 10)
                   for d, ids_ in layers.items() for r, i in enumerate(ids_)}
            W = (max(layers) + 1) * COL + 10
            H = max(len(v) for v in layers.values()) * ROW + 10
            lines = []
            for i in ids:
                x2, y2 = pos[i]
                ey = y2 + NH / 2
                for p in dep[i]:
                    x1, y1 = pos[p]
                    sx, sy = x1 + NW, y1 + NH / 2
                    mx = (sx + x2) / 2
                    lines.append(
                        f'<path d="M{sx},{sy} C{mx},{sy} {mx},{ey} {x2 - 2},{ey}" fill="none" '
                        f'stroke="var(--muted)" stroke-width="1.5"/>'
                        f'<polygon points="{x2 - 8},{ey - 4} {x2},{ey} {x2 - 8},{ey + 4}" fill="var(--muted)"/>')
            boxes = []
            for i in ids:
                x, y = pos[i]
                _id, nm, stt, _ = smap[i]
                nm2 = (nm[:9] + "…") if len(nm) > 10 else nm
                boxes.append(
                    f'<g><rect x="{x}" y="{y}" width="{NW}" height="{NH}" rx="6" '
                    f'fill="var(--bg)" stroke="var(--brd)"/>'
                    f'<rect x="{x}" y="{y}" width="4" height="{NH}" rx="2" '
                    f'fill="var({node_var.get(stt, "--muted")})"/>'
                    f'<text x="{x + 12}" y="{y + 17}" font-size="12" fill="var(--fg)">{esc(_id)}</text>'
                    f'<text x="{x + 12}" y="{y + 31}" font-size="10" fill="var(--muted)">{esc(nm2)}</text></g>')
            return (f'<svg class="dag" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
                    f'xmlns="http://www.w3.org/2000/svg">{"".join(lines)}{"".join(boxes)}</svg>')

        tnow = now()
        tasks = self._all()
        name_of = {t["id"]: t.get("name", t["id"]) for t in tasks}  # 依赖显示名字, 存储仍用 id

        def elapsed_of(t):
            # ponytail: 实际耗时 = 最后活动(updated) - created; 活跃 task 粗值, 已完成即总耗时
            if t.get("status") == S_PENDING:  # 未启动 task 无耗时
                return 0
            return round((t.get("updated", tnow) - t.get("created", tnow)) / 60)

        # 任务进展总览: 各状态计数 + 综合/预估加权完成率 + 时长合计
        cnt = {}
        fracs = []       # 综合进度: DONE task 记满, 未完成 task 按其 subtask 完成比例
        est_total = 0    # 预期时长合计 (min)
        elapsed_total = 0  # 已耗合计 (min)
        wsum = wdone = 0.0  # 预估加权完成率: 权 = estimate (未估默认 60m 免消失)
        remain_est = 0.0    # 剩余预估时长 = Σ 未完成 task 的 estimate×(1-frac)
        for t in tasks:
            cnt[t["status"]] = cnt.get(t["status"], 0) + 1
            if t["status"] == S_DONE:
                frac = 1.0
            else:
                subs = t.get("subtasks", [])
                frac = sum(_sub_pct(s) for s in subs) / (len(subs) * 100) if subs else 0.0
            fracs.append(frac)
            est = t.get("estimate") or 0
            est_total += est
            elapsed_total += elapsed_of(t)
            w = est or 60
            wsum += w
            wdone += w * frac
            remain_est += est * (1 - frac)  # 未估 (est=0) 不计剩余
        overall = round(sum(fracs) / len(fracs) * 100) if fracs else 0
        weighted = round(wdone / wsum * 100) if wsum else overall
        chips = " ".join(f'{badge(k, st_cls)} {v}' for k, v in cnt.items()) or "-"
        task_nodes = [(t["id"], t.get("name", t["id"]), t["status"], t.get("deps", [])) for t in tasks]
        overview = (
            f'<section class="card"><h2>任务进展</h2>'
            f'<p class="meta">{len(tasks)} task · {chips}</p>'
            f'<p class="meta">预期合计 {fmt_dur(est_total or None)} · 已耗 {fmt_dur(elapsed_total or None)} · '
            f'剩余预估 {fmt_dur(round(remain_est) or None)}</p>'
            f'<p class="meta">综合完成率</p>{bar(overall)}'
            f'<p class="meta">预估加权完成率</p>{bar(weighted, cls="est")}'
            f'{dag_html(task_nodes)}</section>')

        cards = []
        for t in tasks:
            subs = t.get("subtasks", [])
            sname_of = {s["sid"]: s.get("name", s["sid"]) for s in subs}  # subtask 依赖也显示名字
            sdone = sum(1 for s in subs if s["status"] == SS_DONE)
            spct = round(sum(_sub_pct(s) for s in subs) / len(subs)) if subs else 0
            elapsed = elapsed_of(t)
            est = t.get("estimate")
            # 时间进度条: 已耗/预期%, 超时标红 (无估则不显)
            time_bar = (f'<p class="meta">时间 {fmt_dur(elapsed)}/{fmt_dur(est)}</p>'
                        + bar(round(elapsed / est * 100), cls="time" + (" over" if elapsed > est else ""))
                        ) if est else ""
            snodes = [(s["sid"], s.get("name", s["sid"]), s["status"], s.get("depends_on", [])) for s in subs]
            srows = "".join(
                f'<tr><td>{esc(s["sid"])}</td><td>{esc(s["name"])}</td>'
                f'<td>{badge(s["status"], ss_cls)}</td>'
                f'<td>{bar(_sub_pct(s), sub=True)}</td>'
                f'<td>{esc(fmt_dur(s.get("estimate")))}</td>'
                f'<td>{esc(s.get("agent", "general-purpose"))}</td>'
                f'<td>{esc(",".join(s.get("skills", [])) or "-")}</td>'
                f'<td>{esc(", ".join(sname_of.get(d, d) for d in s.get("depends_on", [])) or "-")}</td>'
                f'<td>{esc("; ".join(s.get("验收", [])) or "-")}</td></tr>' for s in subs)
            subtable = (
                '<table><thead><tr><th>sid</th><th>名称</th><th>状态</th><th>进度</th>'
                '<th>预期</th><th>agent</th><th>skills</th><th>依赖</th><th>验收标准</th></tr></thead>'
                f'<tbody>{srows}</tbody></table>' if subs
                else '<p class="empty">无 subtask</p>')
            cards.append(
                f'<section class="card"><h2>{esc(t["id"])} {badge(t["status"], st_cls)}</h2>'
                f'<p class="name">{esc(t.get("name", ""))}</p>'
                f'<p class="meta">前置: {esc(", ".join(name_of.get(d, d) for d in t.get("deps", [])) or "-")} · '
                f'worktree: {esc(t.get("worktree") or "-")} · '
                f'耗时 {fmt_dur(elapsed)} / 预期 {fmt_dur(est)}</p>'
                f'{time_bar}'
                f'<p class="meta">子任务 {sdone}/{len(subs)}</p>{bar(spct, sub=True)}'
                f'<details class="detail" open><summary>明细 · DAG + 子任务表</summary>'
                f'{dag_html(snodes)}'
                f'{subtable}</details></section>')
        body = overview + "\n" + ("\n".join(cards) if cards else '<p class="empty">无 task</p>')

        self._copy_board_assets()
        cfg = self.config()
        theme = cfg.get("board_theme", "sketch")
        palette = cfg.get("board_palette", "stone")
        mode = cfg.get("board_mode", "light")
        links = ('<link rel=stylesheet href="board/base.css">'
                 + "".join(f'<link rel=stylesheet href="board/themes/{k}.css">' for k, _ in THEMES)
                 + "".join(f'<link rel=stylesheet href="board/palettes/{k}.css">' for k, _ in PALETTES))

        def opts(items, cur):
            return "".join(f'<option value="{k}"{" selected" if k == cur else ""}>{esc(label)}</option>'
                           for k, label in items)
        switcher = (
            '<div class="switcher">'
            f'<label>主题<select id="sw-theme">{opts(THEMES, theme)}</select></label>'
            f'<label>配色<select id="sw-palette">{opts(PALETTES, palette)}</select></label>'
            f'<label>明暗<select id="sw-mode">{opts([("light", "浅色"), ("dark", "深色")], mode)}</select></label>'
            '</div>')
        html = (
            f'<!doctype html><html lang=zh-CN data-theme="{theme}" data-palette="{palette}" data-mode="{mode}">'
            '<head><meta charset=utf-8>'
            '<meta name=viewport content="width=device-width,initial-scale=1">'
            # 兜底刷新: file:// 下 HEAD 轮询 fetch 抛错无效 → 每 600s 硬刷新保证不 stale
            '<meta http-equiv=refresh content=600>'
            f'<title>SKEIN · {esc(self.proj)}</title>{links}</head><body>'
            f'{switcher}<h1>SKEIN 看板 · {esc(self.proj)}</h1>{body}'
            '<script src="board/switcher.js"></script>'
            # 自动刷新: serve (http) 下轮询自身 Last-Modified, 变了才 reload (空闲不闪);
            # file:// 下 fetch 抛错 → 静默 no-op (view 每次重开已是最新)
            '<script>(function(){var m;setInterval(function(){'
            'fetch(location.href,{method:"HEAD",cache:"no-store"}).then(function(r){'
            'var v=r.headers.get("Last-Modified");if(v){if(m&&v!==m)location.reload();m=v;}'
            '}).catch(function(){});},2000);})();</script></body></html>')
        self._write_if_changed(self.html_path, html)

    def _copy_board_assets(self):
        # 主题/配色 CSS 独立文件, 从插件 assets 拷到 .skein/board/ (相对路径供 html link)
        src = Path(__file__).resolve().parent.parent / "assets" / "board"
        if src.exists():
            shutil.copytree(src, self.dir / "board", dirs_exist_ok=True)

    def view(self, _):
        if not self.html_path.exists():
            self._board_html()
        if self.config().get("board_server"):
            self._run_server(open_browser=True)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.run([opener, str(self.html_path)], check=False)
            print(f"已打开可视化看板: {self.html_path}")

    def serve(self, _):
        # experimental.monitors 入口: 每 session 起持久看板 http 服务, 服务器 stdout 每行经 monitor 递给 Claude。
        # monitor 总启动本命令 (不读 config.yaml), 由本命令按 config 决定跑不跑: 未初始化 / web_serve=false → 静默 no-op 退出。
        f = self.dir / "config.yaml"
        if not f.exists():
            return  # 无 .skein 工作区 — monitor 在无 task 项目里空跑, 直接退出
        if not _yaml_load(f.read_text()).get("web_serve", CONFIG_DEFAULTS["web_serve"]):
            return  # 用户在 config.yaml 关闭
        if not self.html_path.exists():
            self._board_html()
        self._run_server(open_browser=False, quiet=True)  # monitor 每 session 跑, 不弹浏览器 + 静默 (只 error 到 stderr, 见下)

    def _run_server(self, open_browser=True, quiet=False):
        # 起本地 http 服务 (随机 port) 服务 .skein/。相对资源 (board/*.js/css) 靠 http root 正确解析。Ctrl-C 停。
        # quiet=True (monitor): 不打印 info (启动 URL / 停止行); 访问日志 (info/warn) 恒静默; error 走 log_error → stderr 保留。
        import http.server, socketserver, functools

        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_request(self, *a):
                pass  # 静默访问日志 (info/warn); 错误经默认 log_error → stderr

        handler = functools.partial(Handler, directory=str(self.dir))
        with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
            url = f"http://127.0.0.1:{httpd.server_address[1]}/task.html"
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
        # 已归档 (archive/) 不迁; 已存在的同名 skein task 不覆盖 (幂等)。subtask/contract/journal 语义搬运由 agent 补。
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
            # 状态一律置待处理 — 迁移不自动开 worktree; 原状态回报 agent 供 journal 留痕
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
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            subprocess.run([opener, str(self.html_path)], check=False, stdout=sys.stderr, stderr=sys.stderr)
        manifest = {
            "web_serve": web_enabled,
            "mode": "full" if a.full else "compat",
            "trellis_present": trellis.exists(),
            "spec_copied": spec_copied,
            "spec_needs_reorg": spec_copied,  # 拷自 trellis → agent 重组为 core/recall×类目 (在 .skein/spec 原地改, 安全)
            "trellis_tasks": tasks,  # 已物理迁入 .skein/task/; agent 只补语义 (subtask/contract/journal)
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


def main():
    p = argparse.ArgumentParser(
        prog="skein.py",
        description="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约/journal",
        epilog="生命周期: init → create → start → (exec/check) → finish → archive",
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sub.add_parser("init", help="初始化 .skein/ 工作区 (幂等)")
    su = sub.add_parser("setup", help="初始化 + trellis 迁移 (默认兼容: 拷 spec/task + 删接线, 留 .trellis 数据; --full 再整删 .trellis)")
    su.add_argument("--full", action="store_true", help="完全迁移+移除: 兼容操作 + 整删 .trellis/ (spec/task 已拷入 .skein)")
    su.add_argument("--no-web", action="store_true", help="关闭持久看板 web 服务 (写 config.yaml web_serve=false; 缺省启用并打开看板)")
    c = sub.add_parser("create", help="登记新 task (id 必填, 可读 slug)")
    c.add_argument("id", help="可读 id (kebab-case slug, 如 order-create-api; 兼作分支/目录名)")
    c.add_argument("--name", help="task 标题 (省略则用 id)")
    c.add_argument("--desc", help="一句话描述")
    c.add_argument("--deps", help="前置 task id, 逗号分隔")
    c.add_argument("--estimate", type=int, help="AI 执行预期耗时 (分钟, planning 填)")
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
    sub.add_parser("list", help="列所有 task (含状态)")
    sub.add_parser("doctor", help="纯脚本体检 task/subtask 不变量违规 (有错 exit 1, 可 CI/hook 门禁)")
    sub.add_parser("board", help="渲染 .skein/task.md 看板")
    sub.add_parser("view", help="生成并打开 .skein/task.html 可视化看板 (仅此命令主动打开)")
    sub.add_parser("serve", help="持久看板 http 服务 (experimental.monitors 入口; config web_serve=false 则 no-op 退出)")
    sub.add_parser("session-context", help="[hook 用] 注入活跃 task 状态")
    sub.add_parser("user-prompt", help="[hook 用] 注入 task 判定提醒 (是任务则走 skein-flow)")
    co = sub.add_parser("contract", help="查/加 task 契约 (check 逐条验)")
    co.add_argument("id", help="task id")
    co.add_argument("--add", help="追加一条契约 (省略则列出)")
    j = sub.add_parser("journal", help="查/加 task journal")
    j.add_argument("--id", required=True, help="task id")
    j.add_argument("--add", help="追加一条 journal (省略则列出)")
    st = sub.add_parser(
        "subtask", help="单 task 内 subtask DAG 调度 (add/claim/ready/start/done/fail/list)",
        epilog="调度环: claim 认领就绪批 (整批标 running) → 逐个派 agent → 完成即 done/fail → 再 claim (并发 max_parallel)")
    st.add_argument("action", choices=["add", "claim", "ready", "start", "check", "done", "fail", "list"],
                    help="add 登记 / claim 认领就绪批(整批标running) / ready 只读预览 / start 单个占槽 / check 勾验收(算百分比) / done 完成 / fail 失败 / list 列态")
    st.add_argument("tid", help="所属 task id")
    st.add_argument("sid", nargs="?", help="subtask id (add/start/done/fail 必带)")
    st.add_argument("--name", help="[add] subtask 名称")
    st.add_argument("--deps", help="[add] 前置 subtask id, 逗号分隔 (依赖全 done 才就绪; 并行只看此 DAG)")
    st.add_argument("--check", help="[add] 验收标准 checklist, 分号分隔 (每条一个可验断言)")
    st.add_argument("--note", help="[fail] 失败备注")
    st.add_argument("--passed", help="[check] 已通过验收标准序号(1-based), 逗号分隔; all=全过, none=清空")
    st.add_argument("--estimate", type=int, help="[add] AI 执行预期耗时 (分钟)")
    st.add_argument("--agent", help="[add] 关联执行 agent (省略默认 general-purpose)")
    st.add_argument("--skills", help="[add] 关联 skills, 逗号分隔 (0-n, 省略即无)")

    a = p.parse_args()
    if getattr(a, "cmd", None) == "subtask" and a.action in ("add", "start", "check", "done", "fail") and not a.sid:
        p.error(f"subtask {a.action} 需要 sid")
    if a.cmd == "session-context":
        # hook 在任意仓库每 session 都跑: 非 git 且无 .skein → 方法内静默返回; git 仓无 .skein → 注入 setup 建议
        # env 持久化与 git 无关, 必须先于 Skein() 跑 —— 微服务/前后端分离场景 cwd 无 git (子目录各自是仓)。
        _persist_bash_cwd_env()  # 随插件发货 CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=1 (plugin.json 无 env 字段, 只能经 CLAUDE_ENV_FILE)
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
        "ready": sk.ready,
        "list": sk.list_, "board": sk.board, "view": sk.view, "serve": sk.serve,
        "doctor": sk.doctor, "contract": sk.contract,
        "journal": sk.journal, "subtask": sk.subtask,
    }
    # 会写 task.json / task.md 的命令加工作区写锁 (防多 skein 进程并发 read-modify-write)。
    # 纯读命令 (current/ready/list/board/view) 免锁。subtask 含读 action 但整体加锁最省事。
    MUTATING = {"init", "setup", "create", "start", "finish", "archive", "clean",
                "contract", "journal", "subtask"}
    if a.cmd in MUTATING:
        with _workspace_lock(sk.dir / ".lock"):
            dispatch[a.cmd](a)
    else:
        dispatch[a.cmd](a)


if __name__ == "__main__":
    main()
