# 修 spec 6 条断链 — PRD (主入口)

## 目标
- [ ] skein-spec maintain 报的 6 条断链清零 — 链接指向的 ## 锚点标题已不存在, 跳转失效
- [ ] 用户裁定: 逐条查目标文件真实标题修正锚点, 不走「去掉锚点只留文件链」的机械降级
## 边界
- 范围内 3 个 spec 文件的 wiki 链接: .skein/spec/recall/impl/claim.md, .skein/spec/recall/impl/writing-style.md, .skein/spec/recall/test/strategy.md
- 6 条断链: claim.md 2 条 (指向 claim 自身锚点), writing-style.md 2 条 (指向 writing-style 自身 + verification), strategy.md 2 条 (同 writing-style 那两条)
- 范围外: 不改任何 spec 的正文规则内容, 只动链接锚点 (或在目标文件补回被删的小节标题, 二选一按实情定)
- 约束: 写盘经 skein-spec CLI, 禁 Write/Edit 手改 spec 文件
- 约束: 与 max-parallel-cleanup 的 s2 共享 recall/impl/claim.md, 必须等其完成 (task 级 deps 已挂)
## 验收标准
- [ ] skein-spec maintain (不带 --apply) 输出的 broken-link 数为 0, 输出原文回传
- [ ] 每条修复给出: 原链接文本 → 新链接文本 + 目标文件里实际存在的标题原文 (file:line 引用)
- [ ] 若某条锚点的目标小节确实被删且无对应内容 → 不硬凑, 标 needs_main 报回, 禁编造锚点
- [ ] spec 正文规则内容零改动 (git diff 只应出现链接行)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list spec-broken-links`)
