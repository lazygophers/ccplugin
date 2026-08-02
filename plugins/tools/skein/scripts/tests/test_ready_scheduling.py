"""待处理 task confirm 后直接进行中, subtask 随时可被调度认领。

## 改了什么 (四态机)
原五态机中「就绪」状态已移除: confirm 直接激活 (体检+并发+worktree+started)。
这意味着 confirm 后的 task 已在进行中, 其 subtask 立刻可被 claim / subtask start 认领。
不再需要「自动启动就绪 task」逻辑 — confirm 即启动。

## 这条测试真正在守什么
confirm 必须走**完整的激活副作用** — worktree、started 时间戳、task 级并发上限、deps 门。
少任何一样, confirm 出来的 task 就和原来的 start 不是同一种状态,
那类差异极难查 (线上表现是「有的 task 莫名没有 worktree」)。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import run_skein  # noqa: E402

PRD = """# {tid} — PRD

## 目标
- [ ] g

## 边界
- b

## 验收标准
- [ ] a

## 索引
- design.md
"""


def _active(ws: Path, tid: str, *, subs: int = 1, est: float = 4) -> str:
    """造一个已 confirm 直接激活 (进行中) 的 task。"""
    run_skein(ws, "create", tid, "--name", tid, "--desc", "d")
    for i in range(1, subs + 1):
        run_skein(ws, "subtask", "add", tid, f"s{i}", "--name", f"子{i}", "--desc", "d",
                  "--estimate", "1")
    (ws / ".skein/task" / tid / "prd.md").write_text(PRD.format(tid=tid))
    design = ws / ".skein/task" / tid / "design.md"
    design.write_text(design.read_text().replace("- [ ] TODO: 填测试接缝", "- [x] 复用既有单测"))
    run_skein(ws, "estimate", tid, "--set", str(est))
    run_skein(ws, "confirm", tid)          # conftest 自动补 --approved → 直接激活
    return tid


def _t(ws: Path, tid: str) -> dict[str, Any]:
    return dict(json.loads((ws / ".skein/task" / tid / "task.json").read_text()))


def test_confirmed_task_subtask_is_claimable(ws: Path) -> None:
    """confirm 直接激活的 task, 其 subtask 立刻可被 claim。"""
    tid = _active(ws, "alpha-task")
    assert _t(ws, tid)["status"] == "进行中", "前置条件: confirm 后应在进行中"
    out = run_skein(ws, "claim", "exec").stdout
    assert f"{tid}/s1" in out, f"进行中 task 的 subtask 未被认领:\n{out}"


def test_confirm_has_same_side_effects_as_old_start(ws: Path) -> None:
    """confirm 激活 = 原 start: 进行中 + worktree + started 时间戳, 一个不少。

    只标个「进行中」而不建 worktree 是最容易漏的一样 —— 后续 executor 会往主工作区里写。
    """
    tid = _active(ws, "beta-task")
    t = _t(ws, tid)
    assert t["status"] == "进行中", t["status"]
    assert t.get("worktree"), "confirm 没建 worktree"
    assert (ws / t["worktree"]).is_dir(), f"worktree 目录不存在: {t['worktree']}"
    assert t.get("started"), "confirm 没打 started 时间戳"


def test_subtask_start_works_on_confirmed_task(ws: Path) -> None:
    """confirm 后的 task, subtask start 直接可用。"""
    tid = _active(ws, "gamma-task")
    out = run_skein(ws, "subtask", "start", tid, "s1").stdout
    assert "运行中" in out or tid in out, out
    assert _t(ws, tid)["subtasks"][0]["status"] == "运行中"


def test_confirm_respects_task_concurrency_cap(ws: Path) -> None:
    """满槽时 confirm 第三个 → 拒 (confirm 走完整 _activate 含并发校验)。"""
    run_skein(ws, "config", "set", "max_active", "2")
    for name in ("one-task", "two-task"):
        _active(ws, name)
    # 第三个 confirm 应被并发上限拒
    run_skein(ws, "create", "three-task", "--name", "three-task", "--desc", "d")
    run_skein(ws, "subtask", "add", "three-task", "s1", "--name", "子1", "--desc", "d",
              "--estimate", "1")
    (ws / ".skein/task/three-task/prd.md").write_text(PRD.format(tid="three-task"))
    design = ws / ".skein/task/three-task/design.md"
    design.write_text(design.read_text().replace("- [ ] TODO: 填测试接缝", "- [x] 复用既有单测"))
    run_skein(ws, "estimate", "three-task", "--set", "4")
    r = run_skein(ws, "confirm", "three-task", "--approved", check=False)
    assert r.returncode != 0, f"满槽时 confirm 不该放行: {r.stdout}"
    assert _t(ws, "three-task")["status"] == "待处理", "满槽却把第三个 task 激活了"


def test_confirmed_task_with_unfinished_deps_is_not_scheduled(ws: Path) -> None:
    """前置未完成的 task → confirm 时 deps 门拒 (与原 start 的 deps 门同一判据)。"""
    first = _active(ws, "front-task")
    run_skein(ws, "create", "back-task", "--name", "back-task", "--desc", "d")
    run_skein(ws, "subtask", "add", "back-task", "s1", "--name", "子1", "--desc", "d",
              "--estimate", "1")
    (ws / ".skein/task/back-task/prd.md").write_text(PRD.format(tid="back-task"))
    design = ws / ".skein/task/back-task/design.md"
    design.write_text(design.read_text().replace("- [ ] TODO: 填测试接缝", "- [x] 复用既有单测"))
    run_skein(ws, "estimate", "back-task", "--set", "4")
    run_skein(ws, "deps", "back-task", "--set", first, check=False)
    # front 未 finish; back 依赖它 → confirm 应被 deps 门拒
    r = run_skein(ws, "confirm", "back-task", "--approved", check=False)
    assert r.returncode != 0, f"deps 未完成的 task confirm 不该放行: {r.stdout}{r.stderr}"
    assert "前置未完成" in r.stderr, f"未报 deps 门: {r.stderr}"


if __name__ == "__main__":
    import tempfile

    from conftest import make_ws
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "w"
            d.mkdir()
            fn(make_ws(d))
    print("待处理态调度自检过")
