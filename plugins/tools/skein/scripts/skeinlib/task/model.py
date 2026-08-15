"""task/subtask 数据结构 — 状态常量 / id 正则 / pydantic 模型 / 时间戳。

task 包的底层模型, 供 dag / views / store / commands 共享。
"""
from __future__ import annotations

import re
import time
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


# task 状态 (英文落盘, 中文只在展示层映射)
# 生命周期: pending(规划中) ⇄ research(查资料) → [confirm 用户确认门, 吸收原 start] → active
#          → [check] → check → [revert 可回退] → pending / [finishing 占 gate 槽] → finishing → [finish] → done
class TaskStatus(StrEnum):
	PENDING = "pending"
	RESEARCH = "research"
	ACTIVE = "active"
	CHECK = "check"
	FINISHING = "finishing"
	DONE = "done"


def normalize_task_status(s: str) -> TaskStatus:
	"""将 task.json 里的 status 值归一化为 TaskStatus enum。"""
	if isinstance(s, TaskStatus):
		return s
	try:
		return TaskStatus(s)
	except ValueError:
		return TaskStatus.PENDING


# 两套语义分离: STATUS_ACTIVE = 有人正在干活的态 (含调研/收尾, 运行态判断用);
# STATUS_INFLIGHT = 已建 worktree 需在 finish/del 时销毁的态 (调研中未建 worktree, 不在此列)
STATUS_ACTIVE = {TaskStatus.ACTIVE, TaskStatus.RESEARCH, TaskStatus.FINISHING}
STATUS_INFLIGHT = {TaskStatus.ACTIVE, TaskStatus.CHECK, TaskStatus.FINISHING}
# list --status 过滤别名 (英文简写 → 中文态); open=plan 阶段, unfinished=全部未完成 特判在 query.list_
_STATUS_ALIAS = {"pending": TaskStatus.PENDING, "research": TaskStatus.RESEARCH,
                 "active": TaskStatus.ACTIVE, "check": TaskStatus.CHECK,
                 "finishing": TaskStatus.FINISHING, "done": TaskStatus.DONE}
# 看板排序: 进行中 > 检查中 > 收尾中 > 调研中 > 待处理 > 已完成 (同状态内按 id 稳定)
STATUS_ORDER = {TaskStatus.ACTIVE: 0, TaskStatus.CHECK: 1, TaskStatus.FINISHING: 2,
                TaskStatus.RESEARCH: 3, TaskStatus.PENDING: 4, TaskStatus.DONE: 5}
# task status → 回复前缀阶段
PHASE_OF = {TaskStatus.PENDING: "plan", TaskStatus.RESEARCH: "research",
            TaskStatus.ACTIVE: "exec", TaskStatus.CHECK: "check",
            TaskStatus.FINISHING: "finishing"}


# subtask 状态 (英文落盘, 中文只在展示层映射)
class SubtaskStatus(StrEnum):
	PENDING = "pending"
	RUNNING = "running"
	DONE = "done"
	FAILED = "failed"


# subtask phase: exec(改码/写产出) | research(查资料), 缺省 exec
class SubtaskPhase(StrEnum):
	EXEC = "exec"
	RESEARCH = "research"


# 可读 task id: kebab-case slug, 兼作 git 分支名 + 目录名 (人工传入)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# 拒短字母+数字编号 (t01/t2/ab12): 不可读, 强制描述性 slug. subtask sid 不受此限.
CODE_ID_RE = re.compile(r"^[a-z]{1,4}\d+$")


# task 优先级: 四档枚举, 落盘存机读值 (urgent/high/normal/low)
class TaskPriority(StrEnum):
	URGENT = "urgent"
	HIGH = "high"
	NORMAL = "normal"
	LOW = "low"


PRIORITIES: tuple[TaskPriority, ...] = (TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW)
PRIORITY_DEFAULT = TaskPriority.NORMAL
# 排序权重 (数值越大越优先)
PRIORITY_RANK: dict[TaskPriority, int] = {TaskPriority.URGENT: 3, TaskPriority.HIGH: 2,
                                          TaskPriority.NORMAL: 1, TaskPriority.LOW: 0}

# 工时统一解析 — task/subtask estimate 三个入口共用, 免得「小时」这个隐式单位只写在报错里。
# 裸数字按小时; 收 `30m` / `1.5h` 后缀是因为 agent 天然写带单位的值 (实测占 CLI 失败的一大半)。
ESTIMATE_UNITS: dict[str, float] = {"m": 1 / 60, "h": 1.0}
ESTIMATE_HINT = "预计工时单位=小时 (0.5=30分钟); 也收 `30m` / `1.5h` 后缀"


def parse_hours(raw: object) -> float:
	"""工时 → 小时 float。非法抛 ValueError (调用方裹成 SkeinError/BadParameter)。"""
	s = str(raw).strip().lower()
	unit = ESTIMATE_UNITS.get(s[-1:])
	if unit is not None and s[:-1]:
		return round(float(s[:-1]) * unit, 4)
	return float(s)


class Timing(BaseModel):
	"""通用时间记录 — task/subtask 共用基座。"""
	created: int | None = Field(default=None, description="创建时间")
	started: int | None = Field(default=None, description="执行开始时间")
	finished: int | None = Field(default=None, description="执行结束时间")


class Boundary(BaseModel):
	"""任务边界 — 该做/不该做清单。"""
	should: list[str] = Field(default_factory=list, description="应该做的")
	should_not: list[str] = Field(default_factory=list, description="不应该做的")


class TaskSpec(BaseModel):
	"""任务核心四要素 — task/subtask 共用 (描述/边界/验收/工时)。"""
	desc: str = Field(..., description="任务描述", json_schema_extra={"requirements": ["required"]})
	boundary: Boundary = Field(..., description="边界", json_schema_extra={"requirements": ["required"]})
	estimate: float = Field(..., ge=0, description="预计工时", json_schema_extra={"requirements": ["required"]})
	acceptance: list[str] = Field(..., description="验收项", json_schema_extra={"requirements": ["required"]})


class SubtaskData(TaskSpec):
	"""subtask 落盘结构。"""
	tid: str = Field(..., description="所属 task id", json_schema_extra={"requirements": ["required"]})
	sid: str = Field(..., description="subtask 标识", json_schema_extra={"requirements": ["required"]})
	name: str = Field(..., description="subtask 名称", json_schema_extra={"requirements": ["required"]})
	status: SubtaskStatus = Field(default=SubtaskStatus.PENDING, description="subtask 状态")
	depends_on: list[str] = Field(default_factory=list, description="依赖的 subtask sid")
	timing: Timing = Field(default_factory=Timing, description="时间记录")


class WorktreeRef(BaseModel):
	"""task worktree 记录。"""
	repo: str = Field(description="git 仓库路径, 根仓为 .")
	wt: str = Field(description="worktree 相对路径")
	branch: str = Field(description="worktree 分支")
	merged: bool = Field(default=False, description="是否已合并回目标仓")


class TaskTiming(Timing):
	"""task 时间记录 — 在通用三时刻上补 task 专属节点。"""
	confirmed: int | None = Field(default=None, description="确认时间")
	checked: int | None = Field(default=None, description="检查开始时间")
	checked_end: int | None = Field(default=None, description="检查结束时间")
	updated: int | None = Field(default=None, description="更新时间")


class TimelineEvent(BaseModel):
	"""task 生命周期事件 (只追加, 不可改/删)。字段刻意精简 —— 随 task.json 每次 save 全量重写, 长 task 会累积上百条。"""
	kind: Literal["task", "subtask"] = Field(description="事件所属对象类型")
	status: str = Field(description="task 事件存 TaskStatus 值, subtask 事件存 SubtaskStatus 值")
	at: int = Field(description="Unix epoch 秒, 与其余落盘时间字段同制")
	sid: str | None = Field(default=None, description="仅 subtask 事件携带")
	note: str = Field(default="", description="失败原因 / 回滚说明")
	rollback: bool = Field(default=False, description="状态序号回退时 True")


class TaskData(TaskSpec):
	"""task.json 结构 — 元信息/执行结构平铺。"""
	id: str = Field(..., description="task id", json_schema_extra={"requirements": ["required"]})
	name: str = Field(..., description="task 名称", json_schema_extra={"requirements": ["required"]})
	status: TaskStatus = Field(default=TaskStatus.PENDING, description="task 状态")
	priority: TaskPriority = Field(default=PRIORITY_DEFAULT, description="优先级")
	deps: list[str] = Field(default_factory=list, description="前置 task id")
	subtasks: list[SubtaskData] = Field(default_factory=list, description="subtask 列表")
	research_tasks: list[SubtaskData] = Field(default_factory=list, description="research 任务清单")
	repos: list[str] = Field(default_factory=list, description="涉及仓库")
	worktree: str | None = Field(default=None, description="task worktree 展示汇总")
	worktrees: list[WorktreeRef] = Field(default_factory=list, description="worktree 记录")
	branch: str | None = Field(default=None, description="task 分支")
	timing: TaskTiming = Field(default_factory=TaskTiming, description="时间记录")
	timeline: list[TimelineEvent] = Field(default_factory=list,
	                                      description="生命周期事件日志 (老 task 缺此字段, 空列表容错)")


def now() -> int:
	return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳
