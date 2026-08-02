# check 完整验证标准 — PRD

## 目标
- [ ] check 阶段必须是完整验证: bug 修复要验证可用 (CI/CD/部署/请求), 不只是跑 pytest
- [ ] plan 阶段就必须确认: 用什么方式验证、如何验证、什么标准算通过
- [ ] 能本地验证的尽量本地验证

## 边界
- [ ] 范围内: skein-checker agent + flow for-check + for-plan 章节
- [ ] 范围内: PRD 模板加「验证方式」字段 (plan 阶段填)
- [ ] 范围外: 不改 check 状态机
- [ ] 约束: CI/CD 验证需要外部环境, 可能无法在 agent 内完成 — 此时 plan 阶段就要标注

## User Stories
1. As a 用户, I want bug 修复经过真实验证, so that 我不会拿到「测试通过但 bug 还在」的结果
2. As a AI, I want plan 阶段就知道怎么验证, so that check 阶段有明确验收手段
3. As a 用户, I want 部署类改动验证请求成功, so that 我确认线上可用

## 验收标准
- [ ] PRD 模板「验收标准」章节加「验证方式」子项 (本地命令/CI/部署验证/请求验证)
- [ ] flow for-plan 加: plan 阶段必须确认验证方式和标准
- [ ] flow for-check 加: check 必须按 plan 定的验证方式执行, 不可跳过
- [ ] skein-checker agent 加: 按验收标准的验证方式逐条验证
- [ ] 全量 pytest ≥ 425

## Testing Decisions
- [ ] 结构性 grep: for-plan/for-check 含「验证方式」措辞

## 索引
- 详细设计: [design.md](design.md)
- 任务/子任务/调度: task.json
