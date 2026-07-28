"""_task_pct / _sub_pct 单元测试 — task 进度算法回归。

直接 import skein.py 模块级纯函数 (顶层仅 stdlib + hooklib, 无重依赖, 安全 import)。

新公式 (阶段区间 + 完成度线性插值, skein.py:2468-2495):
  _sub_pct  = done→100；否则按 status 取区间 (pending=0-5 / running=失败=10-90)，
              有验收按 done/total 线性插值 (floor)，无验收取区间中点。
  _task_pct = done→100；否则按 status 取区间 (pending=0-5 / ready=5-10 /
              active=10-85 / check=85-98)，有 subtask 按 subtask 均值线性插值
              (floor)，无 subtask 取区间中点。
全程 floor (int()) 取整，禁 round() — 防 banker's rounding 与前端 JS Math.floor 分歧。

覆盖场景:
  1. subs 全 done 的 active task → 85 (被 active 上限 85 封顶, 非旧语义 100)
  2. subs 多数 done (13/14) 的 check task → floor 插值 97
  3. subs 按验收部分通过 (pending, 3/4 验收) → _sub_pct=3, task 插值 12
  4. 无 subs 各状态取区间中点: pending=2 / ready=7 / active=47 / check=91 / done=100
  5. 空 subtasks list 与无 subs 字段等价 → 同样走区间中点分支
  6. SS_FAILED 与 SS_RUNNING 同区间 (10-90): 有验收插值 / 无验收中点
  7. floor 取整边界: 插值结果带 .5+ 小数时向下取整, 非四舍五入
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

S_PENDING, S_READY, S_ACTIVE, S_CHECK, S_DONE = (
    sk.S_PENDING, sk.S_READY, sk.S_ACTIVE, sk.S_CHECK, sk.S_DONE,
)
SS_PENDING, SS_RUNNING, SS_FAILED, SS_DONE = (
    sk.SS_PENDING, sk.SS_RUNNING, sk.SS_FAILED, sk.SS_DONE,
)
_task_pct, _sub_pct = sk._task_pct, sk._sub_pct


def _sub(status: str = SS_PENDING, crit: int = 0, done: int = 0) -> dict[str, Any]:
    # 造 subtask dict (对齐 skein.py:1518 subtask schema 的关键字段)
    return {
        "sid": "s1", "name": "n", "desc": "d",
        "status": status,
        "验收": [f"c{i}" for i in range(crit)],
        "验收done": list(range(done)),
    }


def _task(status: str, subs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"id": "feat-x", "status": status, "subtasks": subs or []}


# 1. subs 全 done 但 task 仍 active → 被 active 区间上限 85 封顶 (非 100)
def test_subs_all_done_active_task_capped_at_85() -> None:
    t = _task(S_ACTIVE, [_sub(SS_DONE), _sub(SS_DONE), _sub(SS_DONE)])
    assert _task_pct(t) == 85


# 2. subs 多数 done (13/14 done, 1 个 pending) 的 check task → floor 插值
def test_subs_mostly_done_check_task_floor_interp() -> None:
    subs = [_sub(SS_DONE)] * 13 + [_sub(SS_PENDING)]
    # sub_avg = (13*100 + 2) / 14 = 93.0；check 区间 (85,98) 插值 = 85+13*93/100 = 97.09 → floor 97
    assert _task_pct(_task(S_CHECK, subs)) == 97


# 3. subs 按验收部分通过 (pending, 4 验收通过 3) → _sub_pct 区间插值 (非直接百分比)
def test_subs_acceptance_partial_pass_interp() -> None:
    subs = [_sub(SS_PENDING, crit=4, done=3), _sub(SS_PENDING, crit=4, done=3)]
    # pending 区间 (0,5)，3/4 插值 = 0+5*3/4 = 3.75 → floor 3 (非 75)
    assert _sub_pct(subs[0]) == 3
    # task_avg = 3.0；active 区间 (10,85) 插值 = 10+75*3/100 = 12.25 → floor 12
    assert _task_pct(_task(S_ACTIVE, subs)) == 12


# 4. 无 subs 各状态取区间中点 (非区间下限)
def test_no_subs_status_takes_range_midpoint() -> None:
    assert _task_pct(_task(S_PENDING)) == 2   # (0+5)//2
    assert _task_pct(_task(S_READY)) == 7     # (5+10)//2
    assert _task_pct(_task(S_ACTIVE)) == 47   # (10+85)//2
    assert _task_pct(_task(S_CHECK)) == 91    # (85+98)//2
    assert _task_pct(_task(S_DONE)) == 100


# 5. 空 subtasks list (而非缺字段) 与无 subs 字段等价 → 同走区间中点分支
def test_empty_subtasks_list_falls_through_to_midpoint() -> None:
    assert _task_pct(_task(S_ACTIVE, subs=[])) == 47
    assert _task_pct(_task(S_CHECK, subs=[])) == 91


# 6. SS_FAILED 与 SS_RUNNING 同区间 (10,90)：有验收插值 / 无验收中点
def test_failed_subtask_shares_running_range() -> None:
    # 失败 + 验收 2/3 → 10+80*2/3 = 63.33 → floor 63
    assert _sub_pct(_sub(SS_FAILED, crit=3, done=2)) == 63
    assert _sub_pct(_sub(SS_RUNNING, crit=3, done=2)) == 63
    # 失败 + 无验收 → 区间中点 (10+90)//2 = 50
    assert _sub_pct(_sub(SS_FAILED)) == 50
    assert _sub_pct(_sub(SS_RUNNING)) == 50


# 7. floor 取整边界：插值结果带 .5+ 小数时向下取整，非四舍五入
def test_interp_floors_not_rounds_on_half_up_fraction() -> None:
    # running 区间 (10,90)，4/7 插值 = 10+80*4/7 = 55.714... → floor 55 (round 会给 56)
    assert _sub_pct(_sub(SS_RUNNING, crit=7, done=4)) == 55
    # task 层：done(100) + pending 中点(2) 均值 51.0；check 区间 (85,98) 插值 = 85+13*0.51 = 91.63 → floor 91 (round 会给 92)
    subs = [_sub(SS_DONE), _sub(SS_PENDING)]
    assert _task_pct(_task(S_CHECK, subs)) == 91
