---
title: finish
category: task-lifecycle
keywords: [finish,candidates,anchors,recall,git-diff]
status: active
inclusion: auto
anchors: .skein/spec/product/spec-memory/spec-cli.md
---

## finish-candidates 候选反查

### finish-candidates 三路降级策略

在 task finish 阶段，反查需更新的 product 页面。当 git diff 涉及的代码路径无明确 anchors 对应时，按以下优先级降级：

1. **第一优先：anchors 反查**（高置信）
   - 扫描 product 页面 frontmatter 的 anchors 字段
   - 若 git diff 触及声明的代码路径，该页为强候选
   - 理由：anchors 是明确维护的关联

2. **第二优先：prd 关键词 recall**（弱候选）
   - 用 task prd.md 的关键词做 FTS5 BM25 全库搜索
   - 返回匹配度高的 product 页面
   - 人工审核后决策是否需更新

3. **第三优先：建议新建**（无候选）
   - 若前两路均无结果，提示用户可创建新 product 页面
   - 理由：task 可能引入新功能域

降级策略确保覆盖率同时不过度提示。
