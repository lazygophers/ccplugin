# trellisx workflow 执行规范优化

## Goal

让 trellisx 注入项目后, **当且仅当有 task 且进入执行阶段 (Phase 2 Execute)** 时, 实质工作必须用 Claude Code Workflow tool 编排, 且生成的每个 workflow 自带 4 条规范。无 task 的普通对话/简单问答豁免; Planning 阶段也不进 workflow。

## Background

落点盘点 (sub-agent a743e9af) 结论: 4 条规范 + 边界当前覆盖度 ①50% ②60% ③55% ④85% 边界70%。最大缺口 = Workflow 骨架无 retry、phase 无类型标注; 边界判定 flow 与 orchestrate 措辞冲突。

## Requirements

### R1 — phases 细致 + 标类型 (规范①)
- Workflow `meta.phases` 必须逐 phase 标明阶段类型 (research / design / implement / verify / finalize), 用户一眼看出每 phase 干什么、属什么类型。
- 骨架 (trellisx-flow) 必须示范带 `title` + `detail` + 类型语义的 meta.phases, 不是笼统一个 `exec`。

### R2 — 允许并行 (规范②)
- 无依赖的 phases / fan-out agent 必须用 `parallel()` 并发, 不留无谓串行。
- 有前后序依赖的, 用分阶段 `parallel()` 调用 (分层并行) 表达, 骨架须示范"并行组 + 依赖分层"两种形态。

### R3 — 失败自动重试 (规范③)
- 单 step/agent 失败 → 自动重试 (默认 ≤2 次), **不让整个 workflow 直接判失败**; 重试仍败才降级上报 (返回 null + 下游 `.filter(Boolean)` 跳过, 或转 manual Blocked)。
- 骨架必须含 `agent_with_retry` 式 try/catch/retry 包装示例。
- 重试分工明确: workflow 脚本内自动重试 (瞬时错误) vs main 重派 (逻辑失败, 对齐 apply 修复循环 ≤3)。

### R4 — 收尾无残留 (规范④)
- workflow 收尾 phase 强制: `task.py finish` (经 hook 触发 commit→merge→remove worktree→archive) + finish 前 AI 层自查无悬挂 Workflow/agent (TaskList 查 / TaskStop 关)。
- 文档必须清晰区分: **git 层** (finish.py 销 worktree/merge, 确定性脚本) vs **AI 层** (TaskStop 关 Workflow/Task, 脚本做不到)。
- worktree 未销 / Workflow 未关 = 未闭环, 禁宣告 Done。

### R5 — 作用域边界 (统一)
- 「无 task 豁免」量化判定表 (消除 flow vs orchestrate 冲突): 纯查询/单文件≤20行已知位置改 → 豁免; 跨 ≥2 文件 / 需调研产出 / 多步骤 → 必建 task; 边界模糊 → MUST AskUserQuestion。
- Planning 不进 workflow: brainstorm 主线 main 同步前台 (subagent 不能 AskUserQuestion); 纯信息调研可派 trellis-research, 设计决策由 main 汇总裁定。

## Constraints

- **零新增 reference 文件** — 规范内嵌进现有 canonical 落点 (flow 骨架 + workflow-injection 注入点), 高杠杆且落进项目规则, 避免文件膨胀。
- 不改核心功能/流程语义, 只补规范与骨架。
- 跨文件「建 task 判定表」「4 条规范措辞」「retry 分工」为**共享决策**, 由 design.md 定 canonical 文本, 所有 writer 逐字引用, 保持一致。
- 各 writer 文件集**互斥**, 可并行。

## Acceptance Criteria

- [ ] AC1: trellisx-flow 骨架同时体现 4 条规范 (meta.phases 带类型 / parallel 分层 / agent_with_retry / finalize phase 含 finish+commit+remove worktree+TaskStop)。
- [ ] AC2: workflow-injection.md 注入点编码 4 条规范 + no_task 量化判定表 + finish_force step ⓪ TaskStop 细节。
- [ ] AC3: 边界判定 flow / orchestrate / workflow-injection 三处措辞一致, 无冲突 (grep 验证)。
- [ ] AC4: ④收尾 git 层 vs AI 层界限在 flow / workflow-injection / finishcmd / finish.py 四处表述一致。
- [ ] AC5: 改后各文件体积 ≤ 原 1.5x; 无 AI 腔; 核心功能不变。
- [ ] AC6: 端到端验证 — tmp 目录 init+apply, 确认注入产物含 4 条规范 (按 trellisx 测试规程)。
