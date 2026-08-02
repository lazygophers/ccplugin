# skein 流程严格执行 — PRD

## 目标
- [ ] 修复: 创建 task 后 AI 不按 skein 四阶段流程执行 (跳过 confirm/claim/check)
- [ ] 修复: subtask 不自动派 exec agent, main 过度手动处理

## 边界
- [ ] 范围内: skein-flow skill 文本强化 +skein-executor/skein-checker agent 强化
- [ ] 范围内: 检查是否有引擎层面可以让流程更自动化 (如 claim 后自动提示派 agent)
- [ ] 范围外: 不改状态机本身
- [ ] 范围外: 不改 agent 定义文件本身的格式 (那是 agent-json-api task)

## User Stories
1. As a AI, I want flow skill 明确告诉我创建后必须 confirm → claim → 派 agent, so that 我不会跳步
2. As a AI, I want claim exec 返回 subtask 后, flow skill 明确说「立即派 skein-executor」, so that 我不在 main 里手动做 subtask 的活
3. As a 用户, I want AI 严格走四阶段, so that 产出有质量保证

## 验收标准
- [ ] flow skill 的 exec 章节明确: claim 到 subtask → 立即 Agent(skein-executor), 禁 main 手写代码
- [ ] flow skill 的 plan 章节明确: create 后必须填 PRD + subtask + estimate + confirm, 不可跳过
- [ ] flow skill 的 check 章节明确: 全 subtask done → 立即 claim check, 不可停在 exec
- [ ] 质量门: flow skill 文件过 claude -p (端点可用时)
- [ ] 全量 pytest ≥ 425

## Testing Decisions
- [ ] 结构性验证: grep flow skill 确认「禁跳过」「禁 main 手写」等硬约束措辞在位

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json
