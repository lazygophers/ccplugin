"""领域词汇 — 状态常量 / id 正则 / prd 章节 / 时间戳。

**最底层, 只依赖 stdlib**, 谁都能 import 而不成环。这些常量原本散在 skein.py 顶部, 一拆包
dag / views / store / commands 全要用 —— 留在入口文件里就意味着实现层反向 import 入口, 必成环。
"""
from __future__ import annotations

import re
import time

# task 状态 (中文落盘, 逻辑比较用常量)
# 生命周期: 待处理(规划中) → [confirm 用户确认门] → 就绪(规划完成待启动) → [start] → 进行中 → [check] → 检查中 → [finish] → 已完成
S_PENDING = "待处理"
S_READY = "就绪"
S_ACTIVE = "进行中"
S_CHECK = "检查中"
S_DONE = "已完成"
# 两套语义分离: 占 max_active 槽的仅执行中 (检查中/就绪不占); 已 start 有 worktree/可 finish 的含检查中
STATUS_ACTIVE = {S_ACTIVE}             # 占并发槽 (_active 门 / current 显示)
STATUS_INFLIGHT = {S_ACTIVE, S_CHECK}  # 已 start 有 worktree, 可 finish / del 需销 worktree
# list --status 过滤别名 (英文简写 → 中文态); open/未完成 特判非 done
_STATUS_ALIAS = {"pending": S_PENDING, "ready": S_READY, "active": S_ACTIVE, "check": S_CHECK, "done": S_DONE}
# 看板排序: 进行中 > 检查中 > 就绪 > 待处理 > 已完成 (同状态内按 id 稳定)
STATUS_ORDER = {S_ACTIVE: 0, S_CHECK: 1, S_READY: 2, S_PENDING: 3, S_DONE: 4}
PHASE_OF = {S_PENDING: "plan", S_READY: "ready", S_ACTIVE: "exec", S_CHECK: "check"}  # task status → 回复前缀阶段
# subtask 状态
SS_PENDING = "待处理"
SS_RUNNING = "运行中"
SS_DONE = "已完成"
SS_FAILED = "失败"
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
def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳
