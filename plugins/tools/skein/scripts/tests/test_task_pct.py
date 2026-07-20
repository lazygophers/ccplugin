"""_task_pct / _sub_pct 单元测试 — task 进度算法回归 (st2 验收)。

直接 import skein.py 模块级纯函数 (顶层仅 stdlib + hooklib, 无重依赖, 安全 import)。
覆盖 (5 场景):
  1. subs 全 done 的 active task → 100 (核心 bug 修复: 不再被状态机拉回 10)
  2. subs 部分完成 (13/14 done) → round 平均 ≈ 92
  3. subs 按验收部分通过 (有验收, 部分通过) → _sub_pct 均值
  4. 无 subs 各状态: pending=5 / active=10 / check=85 / done=100
  5. 空 subtasks list 的 active task → 10 (走无 subs 分支)
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

_SKEIN = Path(__file__).resolve().parent.parent / "skein.py"
_spec = importlib.util.spec_from_file_location("skein_pct", _SKEIN)
assert _spec is not None and _spec.loader is not None
sk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sk)

S_PENDING, S_ACTIVE, S_CHECK, S_DONE = sk.S_PENDING, sk.S_ACTIVE, sk.S_CHECK, sk.S_DONE
SS_DONE = sk.SS_DONE
_task_pct, _sub_pct = sk._task_pct, sk._sub_pct


def _sub(status: str = sk.SS_PENDING, crit: int = 0, done: int = 0) -> dict[str, Any]:
    # 造 subtask dict (对齐 skein.py:1518 subtask schema 的关键字段)
    return {
        "sid": "s1", "name": "n", "desc": "d",
        "status": status,
        "验收": [f"c{i}" for i in range(crit)],
        "验收done": list(range(done)),
    }


def _task(status: str, subs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"id": "feat-x", "status": status, "subtasks": subs or []}


# 1. 核心 bug 场景: subs 全 done 但 task 仍 active → 100 (旧逻辑给 10)
def test_subs_all_done_active_task_is_100() -> None:
    t = _task(S_ACTIVE, [_sub(SS_DONE), _sub(SS_DONE), _sub(SS_DONE)])
    assert _task_pct(t) == 100


# 2. subs 部分完成 (13/14 done, 1 个 pending) → round 平均
def test_subs_mostly_done_rounds_average() -> None:
    subs = [_sub(SS_DONE)] * 13 + [_sub(sk.SS_PENDING)]
    # 13*100 + 0 = 1300; // 14 = 92
    assert _task_pct(_task(S_CHECK, subs)) == 92


# 3. subs 按验收部分通过 (2 subs 各 4 验收, 通过 3/4 → 75 each → 均 75)
def test_subs_acceptance_partial_pass_average() -> None:
    subs = [_sub(sk.SS_PENDING, crit=4, done=3), _sub(sk.SS_PENDING, crit=4, done=3)]
    # 每个 _sub_pct = round(3/4*100) = 75; 均值 75
    assert _sub_pct(subs[0]) == 75
    assert _task_pct(_task(S_ACTIVE, subs)) == 75


# 4. 无 subs 状态机: pending=5 / active=10 / check=85 / done=100
def test_no_subs_status_machine() -> None:
    assert _task_pct(_task(S_PENDING)) == 5
    assert _task_pct(_task(S_ACTIVE)) == 10
    assert _task_pct(_task(S_CHECK)) == 85
    assert _task_pct(_task(S_DONE)) == 100


# 5. 空 subtasks list (而非缺字段) 的 active task → 走无 subs 分支 = 10
def test_empty_subtasks_list_falls_through_to_status() -> None:
    assert _task_pct(_task(S_ACTIVE, subs=[])) == 10
    assert _task_pct(_task(S_CHECK, subs=[])) == 85
