#!/usr/bin/env python3
"""SKEIN — 独立任务管理引擎 (零 trellis 依赖, 纯 stdlib)。

单文件子命令引擎: 生命周期 (create/start/finish/archive) + worktree 隔离 + task.md 看板。
skein.py 自身就是引擎, 无外部 hook 层 — start/finish 直接干活。

工作区布局 (git 根下):
  .skein/config.json              设置 (max_active / auto_commit / worktree_root)
  .skein/state.json               {focus: <id>}
  .skein/task/<id>/task.json      单 task 记录 (活跃)
  .skein/task/<id>/*.md           planning 工件 (prd/design/implement, 由 skein-planning 写)
  .skein/task/archive/<年>/<月-日>/<id>/  归档 (按完成日期分层)
  .skein/task.md                  看板 (经本脚本 board, 禁直接编辑)
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

STATUS_ACTIVE = {"in_progress", "check"}


def now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


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


class Skein:
    def __init__(self):
        self.root = gitroot()
        self.dir = self.root / ".skein"
        self.tasks = self.dir / "task"
        self.archive_dir = self.tasks / "archive"

    # ---- 存取 ----
    def config(self) -> dict:
        f = self.dir / "config.json"
        if not f.exists():
            raise SystemExit("未初始化 — 先跑 `skein.py init`")
        return json.loads(f.read_text())

    def _state(self) -> dict:
        f = self.dir / "state.json"
        return json.loads(f.read_text()) if f.exists() else {"focus": None}

    def _set_focus(self, tid):
        (self.dir / "state.json").write_text(json.dumps({"focus": tid}, ensure_ascii=False, indent=2))
        self._board(None)  # state.json 唯一写入口 → 变更即刷 task.md, 免看板漂移

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

    def _next_id(self) -> str:
        n = 1
        existing = {p.name for p in self.tasks.iterdir() if p.name != "archive"} if self.tasks.exists() else set()
        existing |= {p.name for p in self.archive_dir.glob("*/*/*")} if self.archive_dir.exists() else set()
        while f"t{n:02d}" in existing:
            n += 1
        return f"t{n:02d}"

    # ---- 命令 ----
    def init(self, _):
        self.dir.mkdir(exist_ok=True)
        self.tasks.mkdir(exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        cfg = self.dir / "config.json"
        if not cfg.exists():
            cfg.write_text(json.dumps({
                "max_active": 2,
                "auto_commit": True,
                "worktree_root": ".worktrees",
            }, ensure_ascii=False, indent=2))
        if not (self.dir / "state.json").exists():
            self._set_focus(None)
        self._board(None)
        print(f"已初始化 SKEIN 工作区: {self.dir}")

    def create(self, a):
        tid = self._next_id()
        (self.tasks / tid).mkdir(parents=True)
        deps = [d.strip() for d in (a.deps or "").split(",") if d.strip()]
        t = {
            "id": tid, "name": a.name, "desc": a.desc or "",
            "status": "pending", "deps": deps, "contracts": [],
            "worktree": None, "branch": f"skein/{tid}",
            "created": now(), "updated": now(),
        }
        self._save(t)
        self._board(None)
        print(f"{tid}\t{self.tasks / tid}")

    def start(self, a):
        t = self._load(a.id)
        if t["status"] != "pending":
            raise SystemExit(f"{a.id} 状态为 {t['status']}, 只能 start pending task")
        cfg = self.config()
        active = self._active()
        if len(active) >= cfg["max_active"]:
            raise SystemExit(
                f"task 级并发上限 {cfg['max_active']} (当前 active: "
                f"{', '.join(x['id'] for x in active)}), 先 finish 一个再 start")
        undone = [d for d in t["deps"] if self._dep_unfinished(d)]
        if undone:
            raise SystemExit(f"前置未完成: {', '.join(undone)} — 先 finish 它们")
        wt = self.root / cfg["worktree_root"] / f"skein-{a.id}"
        git("worktree", "add", "-b", t["branch"], str(wt), "HEAD", cwd=self.root)
        t["status"] = "in_progress"
        t["worktree"] = str(wt)
        self._save(t)
        self._set_focus(a.id)
        self._board(None)
        print(f"{a.id} started\nworktree: {wt}\nbranch: {t['branch']}")

    def _dep_unfinished(self, dep) -> bool:
        # 归档即视为完成
        if self._archived_path(dep):
            return False
        f = self.tasks / dep / "task.json"
        if not f.exists():
            return False  # 未知 dep 不阻塞
        return json.loads(f.read_text())["status"] != "completed"

    def finish(self, a):
        tid = a.id or self._state().get("focus")
        if not tid:
            raise SystemExit("无 focus task — 指定 <id>")
        t = self._load(tid)
        if t["status"] not in STATUS_ACTIVE:
            raise SystemExit(f"{tid} 状态 {t['status']}, 非 active 无法 finish")
        cfg = self.config()
        wt = t.get("worktree")
        if wt and Path(wt).exists():
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
        elif wt:
            sys.stderr.write(
                f"{tid} worktree 记录存在但目录缺失 ({wt}) — "
                f"跳过合并, 分支 {t['branch']} 若有提交未并入\n")
        t["status"] = "completed"
        t["worktree"] = None
        self._save(t)
        self._archive(tid)
        # 仅当被 finish 的正是当前 focus (或 focus 已失效) 才切, 免抢占无关 active task
        rest = self._active()
        focus = self._state().get("focus")
        if focus in (None, tid) or focus not in {x["id"] for x in rest}:
            focus = rest[0]["id"] if rest else None
            self._set_focus(focus)
        self._board(None)
        print(f"{tid} finished + archived" + (f", focus→{focus}" if focus else ", 无剩余 active"))

    def archive(self, a):
        # 归档 = 丢弃 (不 merge): 先销 worktree/branch + 让出 focus, 免残留悬挂
        f = self.tasks / a.id / "task.json"
        if f.exists():
            t = json.loads(f.read_text())
            wt = t.get("worktree")
            if wt and Path(wt).exists():
                git("worktree", "remove", str(wt), "--force", cwd=self.root, check=False)
                git("branch", "-D", t["branch"], cwd=self.root, check=False)
            if self._state().get("focus") == a.id:
                rest = [x for x in self._active() if x["id"] != a.id]
                self._set_focus(rest[0]["id"] if rest else None)
        self._archive(a.id)
        self._board(None)
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
        focus = self._state().get("focus")
        if not active:
            print("无 active task")
            return
        if a.all:
            for t in active:
                tag = "<- current" if t["id"] == focus else "<- active"
                print(f"{t['id']}\t{t['status']}\t{t['name']}\t{tag}")
        else:
            t = self._load(focus) if focus else active[0]
            print(f"{t['id']}\t{t['status']}\t{t['name']}\t{t.get('worktree') or '-'}")

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
        tid = a.id or self._state().get("focus")
        if not tid:
            raise SystemExit("无 focus task — 指定 --id <id>")
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
        focus = self._state().get("focus")
        lines = ["# SKEIN 活跃任务 (compaction 上下文恢复)", "", f"focus: {focus or '-'}", ""]
        for t in active:
            lines.append(f"- `{t['id']}` [{t['status']}] {t['name']} — worktree: {t.get('worktree') or '-'}")
        lines += ["", "恢复提示: 用 `skein.py current` 查 focus; 未 archive = 未完成。"]
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": "\n".join(lines)}}))

    def board(self, a):
        self._board(a)
        print(f"看板已更新: {self.dir / 'task.md'}")

    def _board(self, _):
        rows = []
        focus = self._state().get("focus")
        for t in self._all():
            mark = " " if t["id"] == focus else ""
            deps = ",".join(t["deps"]) or "-"
            wt = t.get("worktree") or "-"
            if wt != "-":
                wt = os.path.relpath(wt, self.root)
            rows.append(f"| {t['id']}{mark} | {t['name']} | {t['status']} | {deps} | {wt} |")
        body = "\n".join(rows) if rows else "| - | - | - | - | - |"
        md = (
            "# SKEIN 看板\n\n"
            "> 经 `skein.py board` 渲染, 禁直接编辑。= focus。\n\n"
            "| id | 名称 | 状态 | 前置 | worktree |\n"
            "|---|---|---|---|---|\n"
            f"{body}\n\n"
            f"focus: {focus or '-'}　更新: {now()}\n"
        )
        (self.dir / "task.md").write_text(md)


def main():
    p = argparse.ArgumentParser(
        prog="skein.py",
        description="SKEIN 任务管理引擎 — task 生命周期 + 看板 + 契约/journal",
        epilog="生命周期: init → create → start → (exec/check) → finish → archive",
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    sub.add_parser("init", help="初始化 .skein/ 工作区 (幂等)")
    c = sub.add_parser("create", help="登记新 task, 返回 id")
    c.add_argument("name", help="task 名称")
    c.add_argument("--desc", help="一句话描述")
    c.add_argument("--deps", help="前置 task id, 逗号分隔")
    s = sub.add_parser("start", help="激活 task: 建 worktree + 设 focus + in_progress")
    s.add_argument("id", help="task id")
    f = sub.add_parser("finish", help="收束 task: commit→merge→archive→销 worktree")
    f.add_argument("id", nargs="?", help="task id (省略则用当前 focus)")
    ar = sub.add_parser("archive", help="归档 task (不合并, 仅移入 archived)")
    ar.add_argument("id", help="task id")
    cu = sub.add_parser("current", help="显示 focus task")
    cu.add_argument("--all", action="store_true", help="改列全部 active task")
    sub.add_parser("list", help="列所有 task (含状态)")
    sub.add_parser("board", help="渲染 .skein/task.md 看板")
    sub.add_parser("session-context", help="[hook 用] 注入活跃 task 状态")
    co = sub.add_parser("contract", help="查/加 task 契约 (check 逐条验)")
    co.add_argument("id", help="task id")
    co.add_argument("--add", help="追加一条契约 (省略则列出)")
    j = sub.add_parser("journal", help="查/加 task journal")
    j.add_argument("--id", help="task id (省略则用当前 focus)")
    j.add_argument("--add", help="追加一条 journal (省略则列出)")

    a = p.parse_args()
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
        "list": sk.list_, "board": sk.board, "contract": sk.contract,
        "journal": sk.journal,
    }
    dispatch[a.cmd](a)


if __name__ == "__main__":
    main()
