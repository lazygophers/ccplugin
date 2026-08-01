"""就绪 task 的 subtask 可直接被调度, 首个被认领时自动启动该 task。

## 改了什么
从前 `claim` 只从**进行中** task 取候选, 就绪 task 必须先手工 `skein start` 才能派 subtask。
但「就绪」= 已过人审门 + 规划完成 + 只差开工, 再要一次 `start` 仪式没有任何新信息进来。
现在候选池 = 进行中 + 就绪(前置已清), 首个 subtask 被认领时就地把 task 启动。

## 这条测试真正在守什么
自动启动必须走**与手工 `skein start` 完全相同**的副作用 —— worktree、started 时间戳、
task 级并发上限、deps 门。少任何一样, 自动启动出来的 task 就和手工启动的不是同一种状态,
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


def _ready(ws: Path, tid: str, *, subs: int = 1, est: float = 4) -> str:
    """造一个已过人审门、停在「就绪」的 task。"""
    run_skein(ws, "create", tid, "--name", tid, "--desc", "d")
    for i in range(1, subs + 1):
        run_skein(ws, "subtask", "add", tid, f"s{i}", "--name", f"子{i}", "--desc", "d",
                  "--estimate", "1")
    (ws / ".skein/task" / tid / "prd.md").write_text(PRD.format(tid=tid))
    design = ws / ".skein/task" / tid / "design.md"
    design.write_text(design.read_text().replace("- [ ] TODO: 填测试接缝", "- [x] 复用既有单测"))
    run_skein(ws, "estimate", tid, "--set", str(est))
    run_skein(ws, "confirm", tid)          # conftest 自动补 --approved
    return tid


def _t(ws: Path, tid: str) -> dict[str, Any]:
    return dict(json.loads((ws / ".skein/task" / tid / "task.json").read_text()))


def test_ready_task_subtask_is_claimable_without_manual_start(ws: Path) -> None:
    """就绪 task 从未 `skein start`, 直接 claim 就能拿到它的 subtask。"""
    tid = _ready(ws, "alpha-task")
    assert _t(ws, tid)["status"] == "就绪", "前置条件: 应停在就绪"
    out = run_skein(ws, "claim", "exec").stdout
    assert f"{tid}/s1" in out, f"就绪 task 的 subtask 未被认领:\n{out}"
    assert "自动启动就绪 task" in out and tid in out, f"未报自动启动: {out}"


def test_auto_start_has_same_side_effects_as_manual_start(ws: Path) -> None:
    """自动启动 = 手工 start: 进行中 + worktree + started 时间戳, 一个不少。

    只标个「进行中」而不建 worktree 是最容易漏的一样 —— 后续 executor 会往主工作区里写。
    """
    tid = _ready(ws, "beta-task")
    run_skein(ws, "claim", "exec")
    t = _t(ws, tid)
    assert t["status"] == "进行中", t["status"]
    assert t.get("worktree"), "自动启动没建 worktree"
    assert (ws / t["worktree"]).is_dir(), f"worktree 目录不存在: {t['worktree']}"
    assert t.get("started"), "自动启动没打 started 时间戳"
    assert t["subtasks"][0]["status"] == "运行中"


def test_subtask_start_also_auto_starts(ws: Path) -> None:
    """单个 `subtask start` 路径同理 —— 两条入口行为一致, 免得只修了 claim 那条。"""
    tid = _ready(ws, "gamma-task")
    out = run_skein(ws, "subtask", "start", tid, "s1").stdout
    assert "自动启动就绪 task" in out, out
    t = _t(ws, tid)
    assert t["status"] == "进行中" and t.get("worktree")


def test_auto_start_does_not_bypass_task_concurrency_cap(ws: Path) -> None:
    """满槽时**不**自动启动 —— 自动化不得成为绕过并发上限的后门。"""
    run_skein(ws, "config", "set", "max_active", "2")
    for name in ("one-task", "two-task"):
        _ready(ws, name)
    run_skein(ws, "claim", "exec")                # 占满 2 个槽
    third = _ready(ws, "three-task")
    out = run_skein(ws, "claim", "exec").stdout
    assert "无全局就绪 subtask" in out, f"满槽仍认领了: {out}"
    assert _t(ws, third)["status"] == "就绪", "满槽却把第三个 task 启动了"


def test_ready_task_with_unfinished_deps_is_not_scheduled(ws: Path) -> None:
    """前置未完成的就绪 task 不进候选池 —— 与手工 start 的 deps 门同一判据。"""
    first = _ready(ws, "front-task")
    second = _ready(ws, "back-task")
    run_skein(ws, "deps", second, "--set", first, check=False)
    # front 未 finish; back 依赖它 → back 的 subtask 不该被认领
    out = run_skein(ws, "claim", "exec", "--dry-run").stdout
    assert f"{second}/s1" not in out, f"依赖未完成的 task 被排进了调度: {out}"


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
    print("就绪态调度自检过")
