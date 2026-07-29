# main 调度状态先行铁律 (state-before-action) — PRD (主入口)

## 目标
- [ ] skein-flow SKILL.md 顶部加「状态先行铁律」段: 三环节硬门 (task 未 start 禁 exec / subtask 未 claim 禁派 / 全 done 未 skein check 禁验证宣告), 用 STOP/🛑 标记, 禁留 AI 自降级口子
- [ ] skein-exec SKILL.md exec 段重述 subtask 状态先行硬门 (claim 占槽是派的硬前置, pending 禁派)
- [ ] skein-check SKILL.md 重述 check 状态先行硬门 (必须 skein check 进检查中态才跑验证, 禁 main 未 check 自跑 lint/test 当结果)
- [ ] 文档表述禁泛化 (避免 AI 自降级绕过, 如「简单的可直接验证」类口子)
- [ ] 成功: main 读 skills 后三环节都守状态先行, 不绕过
## 边界
- [ ] skills/skein-flow/SKILL.md: 顶部加铁律段
- [ ] skills/skein-exec/SKILL.md: exec 段重述
- [ ] skills/skein-check/SKILL.md: check 段重述
- [ ] 不改 CLI (skein.py 状态机已正确)
- [ ] 不改 webapp
## 验收标准
- [x] skein-flow SKILL.md 含「状态先行铁律」顶部段, 三环节硬门齐全 (task/subtask/check)
- [x] skein-exec SKILL.md exec 段含 subtask 状态先行重述 (claim 占槽硬前置)
- [x] skein-check SKILL.md 含 check 状态先行重述 (skein check 进检查中才验证)
- [x] 三文档表述禁泛化口子 (无「简单的可直接」类自降级措辞)
- [x] python3 skein.py doctor 通过
- [x] 三文档状态先行表述一致 (task/subtask/check 三层同构语义)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list state-before-action`)
