"""领域词汇 — 状态常量 / id 正则 / prd 章节 / 时间戳。

**最底层, 只依赖 stdlib**, 谁都能 import 而不成环。这些常量原本散在 skein.py 顶部, 一拆包
dag / views / store / commands 全要用 —— 留在入口文件里就意味着实现层反向 import 入口, 必成环。
"""
from __future__ import annotations

import re
import time

# task 状态 (中文落盘, 逻辑比较用常量)
# 生命周期: 待处理(规划中) ⇄ 调研中(查资料) → [confirm 用户确认门, 吸收原 start] → 进行中
#          → [check] → 检查中 → [finishing 占 gate 槽] → 收尾中 → [finish] → 已完成
S_PENDING = "待处理"
S_RESEARCH = "调研中"
S_ACTIVE = "进行中"
S_CHECK = "检查中"
S_FINISHING = "收尾中"
S_DONE = "已完成"
# 两套语义分离: STATUS_ACTIVE = 有人正在干活的态 (含调研/收尾, current 显示用);
# STATUS_INFLIGHT = 已建 worktree 需在 finish/del 时销毁的态 (调研中未建 worktree, 不在此列)
STATUS_ACTIVE = {S_ACTIVE, S_RESEARCH, S_FINISHING}
STATUS_INFLIGHT = {S_ACTIVE, S_CHECK, S_FINISHING}
# list --status 过滤别名 (英文简写 → 中文态); open/未完成 特判非 done
_STATUS_ALIAS = {"pending": S_PENDING, "research": S_RESEARCH, "active": S_ACTIVE,
                  "check": S_CHECK, "finishing": S_FINISHING, "done": S_DONE}
# 看板排序: 进行中 > 检查中 > 收尾中 > 调研中 > 待处理 > 已完成 (同状态内按 id 稳定)
STATUS_ORDER = {S_ACTIVE: 0, S_CHECK: 1, S_FINISHING: 2, S_RESEARCH: 3, S_PENDING: 4, S_DONE: 5}
# task status → 回复前缀阶段
PHASE_OF = {S_PENDING: "plan", S_RESEARCH: "research", S_ACTIVE: "exec",
            S_CHECK: "check", S_FINISHING: "finishing"}
# subtask 状态
SS_PENDING = "待处理"
SS_RUNNING = "运行中"
SS_DONE = "已完成"
SS_FAILED = "失败"
# subtask phase: exec(改码/写产出) | research(查资料), 缺省 exec (老数据免迁移, 见 PRD)
SS_PHASE_EXEC = "exec"
SS_PHASE_RESEARCH = "research"
# 可读 task id: kebab-case slug, 兼作 git 分支名 + 目录名 (人工传入)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# 拒短字母+数字编号 (t01/t2/ab12): 不可读, 强制描述性 slug. subtask sid 不受此限.
CODE_ID_RE = re.compile(r"^[a-z]{1,4}\d+$")
# prd 章节 CLI: --type 中英 alias → 标准中文章节名 (内部统一存中文, 对齐 fmt/_validate_prd 的章节判定)
PRD_TYPE_ALIAS: dict[str, str] = {
    "目标": "目标", "goal": "目标",
    "边界": "边界", "scope": "边界",
    "验收标准": "验收标准", "acceptance": "验收标准", "accept": "验收标准",
}
# 可经 prd 命令操作的章节 (索引章节脚本维护, 禁用户改 → 不在此列)
PRD_SECTIONS: tuple[str, ...] = ("目标", "边界", "验收标准")
# 写入时补 `- [ ]` checkbox 的章节 (验收条目都该可勾); 边界只补 `- ` list marker 不补 checkbox
PRD_TODO_SECTIONS: set[str] = {"目标", "验收标准"}
# prd 标准六段 (对齐 `/to-spec`: 目标/边界 承接 Problem+Solution, User Stories/Testing Decisions 新增, 索引脚本维护)
PRD_SECTIONS_V6: list[str] = ["目标", "边界", "User Stories", "验收标准", "Testing Decisions", "索引"]
# 旧四段 (存量 task 兼容态) — 校验只 warning 不阻断, 新建 task 一律走 V6
PRD_SECTIONS_V4: list[str] = ["目标", "边界", "验收标准", "索引"]
# task 优先级: 四档枚举, 落盘存机读值 (urgent/high/normal/low) — 文案会改, 落盘值不该跟着变
# (中文档位/展示层映射归调用方)。存量 0-10 数字迁移映射见 skeinlib.priority.priority_from_legacy。
P_URGENT = "urgent"
P_HIGH = "high"
P_NORMAL = "normal"
P_LOW = "low"
PRIORITIES: tuple[str, ...] = (P_URGENT, P_HIGH, P_NORMAL, P_LOW)
PRIORITY_DEFAULT = P_NORMAL  # 未指定落「中」
# 排序权重 (数值越大越优先); 老代码的 `-(priority or 5)` 数字降序换成这张表, 相对顺序不变
PRIORITY_RANK: dict[str, int] = {P_URGENT: 3, P_HIGH: 2, P_NORMAL: 1, P_LOW: 0}
# ── task.json 中文 key 常量 ──
# 所有落盘 key 用中文, 代码通过常量引用免散落字符串。
# 迁移层 (store._migrate) 在 load 时自动把旧英文 key 搬到中文。
K_NAME = "名称"
K_DESC = "描述"
K_STATUS = "状态"
K_DEPS = "前置"
K_CONTRACTS = "契约"
K_SUBTASKS = "子任务"
K_PRIORITY = "优先级"
K_ESTIMATE = "预计工时"
K_REPOS = "仓库"
K_WORKTREE = "工作树"
K_WORKTREES = "工作树列表"
K_BRANCH = "分支"
K_PARENT = "父任务"
K_KIND = "类型"
K_CREATED = "创建时间"
K_CONFIRMED = "确认时间"
K_CONFIRMED_BY = "确认人"
K_EXEC_START = "执行开始"
K_CHECK_START = "检查开始"
K_CHECK_END = "检查结束"
K_FINISHED = "完成时间"
K_UPDATED = "更新时间"

# subtask 级中文 key (部分与 task 共用: 名称/描述/状态/预计工时)
K_SID = "标识"
K_DEPENDS_ON = "依赖"
K_ACCEPT_DONE = "验收完成"
K_SKILLS = "技能"
K_NOTE = "备注"
K_EXEC_END = "执行结束"  # subtask 的执行结束 (= done/fail 时刻)

# task 级 旧英文 → 中文 映射 (迁移用)
TASK_KEY_MAP: dict[str, str] = {
    "name": K_NAME, "desc": K_DESC, "status": K_STATUS, "deps": K_DEPS,
    "contracts": K_CONTRACTS, "subtasks": K_SUBTASKS, "priority": K_PRIORITY,
    "estimate": K_ESTIMATE, "repos": K_REPOS, "worktree": K_WORKTREE,
    "worktrees": K_WORKTREES, "branch": K_BRANCH, "parent": K_PARENT,
    "kind": K_KIND, "created": K_CREATED, "confirmed": K_CONFIRMED,
    "confirmed_by": K_CONFIRMED_BY, "started": K_EXEC_START,
    "checked": K_CHECK_START, "finished": K_FINISHED, "updated": K_UPDATED,
}
# subtask 级 旧英文 → 中文 映射
SUB_KEY_MAP: dict[str, str] = {
    "sid": K_SID, "name": K_NAME, "desc": K_DESC, "estimate": K_ESTIMATE,
    "depends_on": K_DEPENDS_ON, "status": K_STATUS, "skills": K_SKILLS,
    "created": K_CREATED, "started": K_EXEC_START, "finished": K_EXEC_END,
    "note": K_NOTE, "验收done": K_ACCEPT_DONE,
}


def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳
