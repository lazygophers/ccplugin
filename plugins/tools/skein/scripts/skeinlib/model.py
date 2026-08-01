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
S_READY = "就绪"  # 已从状态机枚举/别名/排序/阶段表中剔除, 常量留存过渡 —— 仍有旧消费点未迁移 (归 s3)
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
def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 所有落盘时间字段统一时间戳
