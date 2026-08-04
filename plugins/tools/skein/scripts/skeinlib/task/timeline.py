"""task.json timeline 写入 — 唯一入口, 纯函数, 只追加不改写。

不接入任何调用点 (由后续 subtask 在 6 处 task 迁移 + 3 处 subtask 迁移显式调用)。
`t` 是 `TaskStore.load` 读出的原始 dict (非 pydantic 模型), 与 store 的落盘层保持同一形状。
"""
from __future__ import annotations

import time as _time
from typing import Any, Literal, Optional

from skeinlib.task.model import SubtaskStatus, TaskStatus, now

# 生命周期前进序号 —— 与展示用的 STATUS_ORDER (看板排序权重) 是两套语义, 不可复用:
# STATUS_ORDER 是"最紧急排最前"的展示权重 (active=0 最高优先级), 不满足 "序号单调递增=前进" 的比较语义。
_TASK_SEQ: dict[str, int] = {
    TaskStatus.PENDING: 0,
    TaskStatus.RESEARCH: 1,
    TaskStatus.ACTIVE: 2,
    TaskStatus.CHECK: 3,
    TaskStatus.FINISHING: 4,
    TaskStatus.DONE: 5,
}
# subtask 隐含顺序: running 是唯一的"进行中"态, done/failed 同为终态 (打平即可, 唯一的
# 回退路径是 failed → running 定点重派, 判定只需 running < 终态)。
_SUBTASK_SEQ: dict[str, int] = {
    SubtaskStatus.RUNNING: 0,
    SubtaskStatus.DONE: 1,
    SubtaskStatus.FAILED: 1,
}


def append(t: dict[str, Any], kind: Literal["task", "subtask"], status: str, *,
           sid: str | None = None, note: str = "") -> None:
    """给 task dict 的 timeline 追加一条事件 (原地修改)。

    rollback 判定: 找同 kind (subtask 事件再同 sid) 的上一条事件, 新状态序号 <= 旧状态序号即回滚。
    序号表未知的状态 (理论上不会出现) 视为 0, 不判回滚。
    """
    timeline: list[dict[str, Any]] = t.setdefault("timeline", [])
    seq = _TASK_SEQ if kind == "task" else _SUBTASK_SEQ

    prev = None
    for ev in reversed(timeline):
        if ev.get("kind") != kind:
            continue
        if kind == "subtask" and ev.get("sid") != sid:
            continue
        prev = ev
        break

    rollback = False
    if prev is not None:
        rollback = seq.get(status, 0) <= seq.get(prev.get("status", ""), 0)

    timeline.append({
        "kind": kind,
        "status": status,
        "at": now(),
        "sid": sid,
        "note": note,
        "rollback": rollback,
    })


def fmt_ts(ts: Optional[int]) -> str:
    """epoch 秒 → 本地可读时间; None/0 → '-'。
    从 views._fmt_ts 下沉到中立层, 供 scheduling 和 views 共用 (ADR 0003 G6)。"""
    return _time.strftime("%Y-%m-%d %H:%M", _time.localtime(ts)) if ts else "-"
