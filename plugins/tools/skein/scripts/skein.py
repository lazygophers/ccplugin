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
import datetime
import json
import re
import shutil
import subprocess
import sys
import time
from fnmatch import fnmatch
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
# subtask 状态
SS_PENDING = "待处理"
SS_RUNNING = "运行中"
SS_DONE = "已完成"
SS_FAILED = "失败"
# 可读 task id: kebab-case slug, 兼作 git 分支名 + 目录名 (人工传入)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳


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


def git(*args, cwd=None, check=True, capture=True):
    r = subprocess.run(
        ["git", *args], cwd=cwd, check=False,
        capture_output=capture, text=True,
    )
    if check and r.returncode != 0:
        sys.stderr.write((r.stderr or "") + "\n")
        raise SystemExit(f"git {' '.join(args)} 失败 (exit {r.returncode})")
    return r


def gitroot() -> Path:
    r = git("rev-parse", "--show-toplevel", check=False)
    if r.returncode != 0:
        raise SystemExit("不在 git 仓库内 — SKEIN 需要 git")
    return Path(r.stdout.strip())


def _overlap(a: str, b: str) -> bool:
    # 写文件 glob 是否重叠 → 冲突边。ponytail: fnmatch 双向近似, 误判偏保守 (宁串行)
    return a == b or fnmatch(a, b) or fnmatch(b, a)


class Skein:
    def __init__(self):
        self.root = gitroot()
        self.dir = self.root / ".skein"
        self.tasks = self.dir / "task"
        self.archive_dir = self.tasks / "archive"

    # ---- 存取 ----
    def config(self) -> dict:
        f = self.dir / "config.yaml"
        if not f.exists():
            raise SystemExit("未初始化 — 先跑 `skein.py init`")
        return _yaml_load(f.read_text())

    def _sync(self):
        # 顶层 task.json 唯一写入口: tasks 是未归档 task 的去规范化状态镜像 (per-task task.json 仍单一真值源),
        # 每次变更重算, 免各处同步。无 task 级 focus — 无未完成前置的 task 皆可并行 (DAG 就绪即跑)。
        tasks = [{"id": t["id"], "status": t["status"], "deps": t["deps"],
                  "worktree": t.get("worktree")} for t in self._all()]
        (self.dir / "task.json").write_text(
            json.dumps({"tasks": tasks}, ensure_ascii=False, indent=2))
        self._board(None)  # 变更即刷 task.md, 免看板漂移

    def _load(self, tid) -> dict:
        f = self.tasks / tid / "task.json"
        if not f.exists():
            raise SystemExit(f"task 不存在: {tid}")
        return json.loads(f.read_text())

    def _save(self, t: dict):
        t["updated"] = now()
        (self.tasks / t["id"] / "task.json").write_text(json.dumps(t, ensure_ascii=False, indent=2))

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
            cfg.write_text(_yaml_dump({
                "max_active": 2,
                "max_parallel": 2,
                "auto_commit": True,
                "worktree_root": ".worktrees",
            }))
        # .skein/.gitignore — 忽略自动渲染看板 (task.md 从 task.json 无损重建, 且 AI 禁读写)
        gi = self.dir / ".gitignore"
        if not gi.exists():
            gi.write_text("# skein.py 自动渲染, 从 task.json 无损重建, 不入库\ntask.md\n")
        # worktree 目录在 git 根 (worktree_root), .skein/.gitignore 管不到 → 补到根 .gitignore
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
        if tid in self._used_ids():
            raise SystemExit(f"id 已占用: {tid} — 换一个 (含已归档的也不可复用)")
        (self.tasks / tid).mkdir(parents=True)
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        t = {
            "id": tid, "name": a.name or tid, "desc": a.desc or "",
            "status": S_PENDING, "deps": deps, "contracts": [], "subtasks": [],
            "worktree": None, "branch": f"skein/{tid}",
            "created": now(), "updated": now(),
        }
        self._save(t)
        self._board_task(t)
        self._sync()  # 刷新顶层 tasks 索引 + 看板
        print(f"{tid}\t{self.tasks / tid}")

    def start(self, a):
        t = self._load(a.id)
        if t["status"] != S_PENDING:
            raise SystemExit(f"{a.id} 状态为 {t['status']}, 只能 start 待处理 task")
        cfg = self.config()
        active = self._active()
        if len(active) >= cfg["max_active"]:
            raise SystemExit(
                f"task 级并发上限 {cfg['max_active']} (当前 active: "
                f"{', '.join(x['id'] for x in active)}), 先 finish 一个再 start")
        undone = [d for d in t["deps"] if self._dep_unfinished(d)]
        if undone:
            raise SystemExit(f"前置未完成: {', '.join(undone)} — 先 finish 它们")
        rel = f"{cfg['worktree_root']}/skein-{a.id}"  # 相对 project root 存盘, 免机器绝对路径入库
        wt = self.root / rel
        git("worktree", "add", "-b", t["branch"], str(wt), "HEAD", cwd=self.root)
        t["status"] = S_ACTIVE
        t["worktree"] = rel
        self._save(t)
        self._sync()
        print(f"{a.id} started\nworktree: {rel}\nbranch: {t['branch']}")

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
        self._save(t)
        self._archive(tid)
        self._sync()  # 归档后重写顶层 tasks 索引 (去掉本 task)
        rest = self._active()
        print(f"{tid} finished + archived" + (f", 剩余 active: {', '.join(x['id'] for x in rest)}" if rest else ", 无剩余 active"))

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

    def session_context(self):
        # SessionStart hook: 有 active task 时用 memory.py 相同 JSON envelope 注入, 供 compaction 后恢复
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

    def board(self, a):
        self._board(a)
        print(f"看板已更新: {self.dir / 'task.md'}")

    def _board(self, _):
        rows = []
        for t in self._all():
            deps = ",".join(t["deps"]) or "-"
            wt = t.get("worktree") or "-"  # 已是相对路径
            rows.append(f"| {t['id']} | {t['name']} | {t['status']} | {deps} | {wt} |")
        body = "\n".join(rows) if rows else "| - | - | - | - | - |"
        md = (
            "# SKEIN 看板\n\n"
            "> 经 `skein.py board` 渲染, 禁直接编辑。无 task 级 focus — 就绪 task 皆可并行。\n\n"
            "| id | 名称 | 状态 | 前置 | worktree |\n"
            "|---|---|---|---|---|\n"
            f"{body}\n"
        )
        (self.dir / "task.md").write_text(md)

    # ---- subtask DAG 调度 (单 task 内, 存 per-task task.json 的 subtasks[]) ----
    def _ready(self, t: list) -> list:
        """就绪批: pending + 依赖全 done + 与 running/同批无写文件冲突, 截到空闲槽位。"""
        subs = t.get("subtasks", [])
        done = {s["sid"] for s in subs if s["status"] == SS_DONE}
        running = [s for s in subs if s["status"] == SS_RUNNING]
        slots = self.config().get("max_parallel", 2) - len(running)
        if slots <= 0:
            return []  # 并发满 → 阻塞
        claimed = [g for s in running for g in s.get("write", [])]  # running 占用写集
        picked = []
        for s in subs:
            if s["status"] != SS_PENDING:
                continue
            if not all(d in done for d in s.get("depends_on", [])):
                continue
            w = s.get("write", [])
            if any(_overlap(a, b) for a in w for b in claimed):
                continue  # 与已占用写集冲突 → 串行
            picked.append(s)
            claimed += w
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
                "depends_on": _split(a.deps), "write": _split(a.write),
                "reason": a.reason or "", "status": SS_PENDING,
            })
            self._save(t)
            self._board_task(t)
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
                w = ",".join(s.get("write", [])) or "-"
                print(f"{s['sid']}\t{s['status']}\t{s['name']}\t依赖:{deps}\t写:{w}")
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
                self._save(t)
                self._board_task(t)
                print("已认领 (running) — main 逐个 dispatch skein-implementer, 完成即 subtask done/fail:")
            else:
                print("就绪 (只读预览, 认领用 `subtask claim`):")
            for s in batch:
                print(f"{s['sid']}\t{s['name']}\t写: {','.join(s.get('write', [])) or '-'}\t{s.get('reason', '')}")
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
            busy = [g for x in run for g in x.get("write", [])]
            if any(_overlap(w, b) for w in s.get("write", []) for b in busy):
                raise SystemExit(f"{a.sid} 写集与 running 冲突 — 须串行, 等其 done")
            s["status"] = SS_RUNNING
        elif a.action == "done":
            s["status"] = SS_DONE
        elif a.action == "fail":
            s["status"] = SS_FAILED
            if a.reason:
                s["reason"] = a.reason
        self._save(t)
        self._board_task(t)
        print(f"{a.tid}/{a.sid} → {s['status']}")

    def _board_task(self, t):
        rows = []
        for s in t.get("subtasks", []):
            deps = ",".join(s.get("depends_on", [])) or "-"
            w = ",".join(s.get("write", [])) or "-"
            rows.append(f"| {s['sid']} | {s['name']} | {s['status']} | {deps} | {w} | {s.get('reason', '') or '-'} |")
        body = "\n".join(rows) if rows else "| - | - | - | - | - | - |"
        md = (
            f"# SKEIN 子任务看板 — {t['id']} {t['name']}\n\n"
            "> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。\n\n"
            "| sid | 名称 | 状态 | 依赖 | 写文件 | reason |\n"
            "|---|---|---|---|---|---|\n"
            f"{body}\n\n"
            f"并发上限: {self.config().get('max_parallel', 2)}\n"
        )
        (self.tasks / t["id"] / "task.md").write_text(md)


def _split(s):
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def main():
    p = argparse.ArgumentParser(
        prog="skein.py",
        description="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约/journal",
        epilog="生命周期: init → create → start → (exec/check) → finish → archive",
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sub.add_parser("init", help="初始化 .skein/ 工作区 (幂等)")
    c = sub.add_parser("create", help="登记新 task (id 必填, 可读 slug)")
    c.add_argument("id", help="可读 id (kebab-case slug, 如 order-create-api; 兼作分支/目录名)")
    c.add_argument("--name", help="task 标题 (省略则用 id)")
    c.add_argument("--desc", help="一句话描述")
    c.add_argument("--deps", help="前置 task id, 逗号分隔")
    s = sub.add_parser("start", help="激活 task: 建 worktree + in_progress (就绪即可并行, 无 focus)")
    s.add_argument("id", help="task id")
    f = sub.add_parser("finish", help="收束 task: commit→merge→archive→销 worktree")
    f.add_argument("id", help="task id")
    ar = sub.add_parser("archive", help="归档 task (不合并, 仅移入 archived)")
    ar.add_argument("id", help="task id")
    sub.add_parser("current", help="列全部 active task (无 focus, 就绪皆可并行)")
    sub.add_parser("ready", help="脚本算就绪 task 批 (pending+前置全done+有空闲槽, 只读预览)")
    sub.add_parser("list", help="列所有 task (含状态)")
    sub.add_parser("board", help="渲染 .skein/task.md 看板")
    sub.add_parser("session-context", help="[hook 用] 注入活跃 task 状态")
    co = sub.add_parser("contract", help="查/加 task 契约 (check 逐条验)")
    co.add_argument("id", help="task id")
    co.add_argument("--add", help="追加一条契约 (省略则列出)")
    j = sub.add_parser("journal", help="查/加 task journal")
    j.add_argument("--id", required=True, help="task id")
    j.add_argument("--add", help="追加一条 journal (省略则列出)")
    st = sub.add_parser(
        "subtask", help="单 task 内 subtask DAG 调度 (add/claim/ready/start/done/fail/list)",
        epilog="调度环: claim 认领就绪批 (整批标 running) → 逐个派 agent → 完成即 done/fail → 再 claim (并发 max_parallel)")
    st.add_argument("action", choices=["add", "claim", "ready", "start", "done", "fail", "list"],
                    help="add 登记 / claim 认领就绪批(整批标running) / ready 只读预览 / start 单个占槽 / done 完成 / fail 失败 / list 列态")
    st.add_argument("tid", help="所属 task id")
    st.add_argument("sid", nargs="?", help="subtask id (add/start/done/fail 必带)")
    st.add_argument("--name", help="[add] subtask 名称")
    st.add_argument("--deps", help="[add] 前置 subtask id, 逗号分隔 (依赖全 done 才就绪)")
    st.add_argument("--write", help="[add] 写文件 glob, 逗号分隔 (相交则串行, 冲突自算边)")
    st.add_argument("--reason", help="[add/fail] 备注 (add: 改它满足哪条契约/需求)")

    a = p.parse_args()
    if getattr(a, "cmd", None) == "subtask" and a.action in ("add", "start", "done", "fail") and not a.sid:
        p.error(f"subtask {a.action} 需要 sid")
    if a.cmd == "session-context":
        # hook 在任意仓库每 session 都跑: 非 skein 项目 (无 git / 无 config) 静默 exit 0
        try:
            sk = Skein()
            sk.config()
        except SystemExit:
            return
        sk.session_context()
        return
    sk = Skein()
    dispatch = {
        "init": sk.init, "create": sk.create, "start": sk.start,
        "finish": sk.finish, "archive": sk.archive, "current": sk.current,
        "ready": sk.ready,
        "list": sk.list_, "board": sk.board, "contract": sk.contract,
        "journal": sk.journal, "subtask": sk.subtask,
    }
    dispatch[a.cmd](a)


if __name__ == "__main__":
    main()
