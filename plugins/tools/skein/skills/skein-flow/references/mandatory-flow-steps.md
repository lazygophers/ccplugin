# 强制流程 (不可跳步)

> 贯穿全程: 每个生命周期节点 (create/start/阶段推进/finish) 后跑 `skein.py board` 更新看板。

0. **前置** — 无 `.skein/` → 先 `python3 <plugin>/scripts/skein.py init`。判新旧 (新建 vs 并入 active task), 不准 → `AskUserQuestion`。
1. **plan** (main 同步) — 委托 `skein-planning`: 判新旧 + `skein.py create` 登记 + brainstorm 需求/方案 + grill 硬门 (必走)。产出 `.skein/task/<id>/{prd.md,implement.md}`[+design.md]。
2. **memory recall** (main) — 委托 `skein-memory` recall: 按任务描述召回相关 recall 规则注入 (core 规则已由 SessionStart 常驻)。
3. **激活 🔴 CHECKPOINT** (main) — 产物齐 → `AskUserQuestion` 交用户评审 → **用户批准前禁 start** → `skein.py start <id>` (建 worktree, status=in_progress) → 更新看板。用户驳回 → 退回 plan 修工件重审, 禁绕过。
4. **exec** (agent 编排) — main 作调度器, 动态 DAG 派 `skein-implementer` 各执行 1 subtask, 改动落 task worktree。见 `skein-orchestrate`。每个 agent 完成即回传。
   - 🔴 **异步等待 MUST 输出任务清单** — 派出异步任务后结束本回合前, 输出全景表 (4 列: id/状态/摘要/进度%)。
   - 🔴 **exec 阶段禁问用户顺序** — 顺序归 planning (调度图 + deps + 冲突 DAG)。ready 即派 / 完成即派 / 并发 2。PRD 缺调度图 → 退回 planning 补, 不在 exec 问。
5. **check** (委托 `skein-check`) — 派 `skein-checker` 验证 (lint / type-check / tests / 契约合规); 未过 → 派 `skein-implementer` 定点修复重检, 不跳 finish。
6. **finish** (main 同步) — check 通过 →
   - 🔴 **sediment 判定门** — 按 `skein-memory` 的 checklist 逐项 ✅/❌ 输出 trace, 判本 task learning → core/recall/drop。触发 → 走 sediment 提案 (审批后写盘) 再 finish; 全否 → 跳过 (仍输出全 ❌ trace)。
   - **清理** — `TaskList` 查残留 subagent / 后台任务, `TaskStop` 关闭。禁 `sleep` 轮询等后台跑完。
   - `skein.py finish <id>` — 自动 commit worktree → merge --no-ff 回主 → archive → 销 worktree。冲突 → 自动 abort + 报冲突文件, 停, 转手动解, 禁强解 / 禁当成功。
   - 更新看板 (status=completed)。
