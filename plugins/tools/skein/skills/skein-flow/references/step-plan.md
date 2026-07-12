# plan — 规划与激活 (main 同步)

规划阶段由 main 同步前台承载, 委托 `skein-planning` skill, 全程不派 subagent (brainstorm/grill 逐问用户, subagent 不能与用户对话)。

**前置**: 无 `.skein/` → 先 `skein.py init` (幂等)。判新旧: 全新任务新建, 对现有 active task 的补充/延续则并入; 判不准 → `AskUserQuestion`, 禁替用户决定。

**规划**: planning 内完成 `skein.py create` 登记 + brainstorm 澄清需求方案 + grill 硬门对抗校对 (必走)。产出落 `.skein/task/<id>/`, 至少含 `prd.md` 与 `implement.md`, 需要设计再加 `design.md`。随后委托 `skein-memory` recall 相关规则注入 (core 已由 SessionStart 常驻, 此步只补 recall 层)。

**激活 CHECKPOINT**: 产物齐 → `AskUserQuestion` 交用户评审, **用户批准前禁 start**。批准后 `skein.py start <id>` 建 worktree、置 status=in_progress、刷看板。用户驳回则退回修工件重审, 禁绕过。start 前须已 `subtask add` ≥1 (planning 拆分产物); 无 subtask 时 `start` 直接报错 — 拆分未落 subtask = planning 未完, 退回补。
