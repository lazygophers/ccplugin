---
title: refactor-semantics
layer: recall
category: skill
keywords: [skill,disable-model-invocation,refactor,semantics,对外行为]
status: active
---

## 改写 skill 时 disable-model-invocation 保守策略

### 触发场景
改写现有 skill 时，需决定是否改动 frontmatter 的 `disable-model-invocation` 字段。

### 陷阱-正解
**陷阱**：改写时顺手删掉 `disable-model-invocation: true`，以为简化了。
**正解**：对外语义不变的前提下（触发场景/硬规/失败兜底实际效果改前后一致），原有的 `disable-model-invocation` 标记一律保留不删。

### 规则
- MUST：若原 skill 不带 `disable-model-invocation` 字段，改写后也不加
- MUST：若原 skill 带 `disable-model-invocation: true`，改写后保留不删
- MUST：改写时**只改表达与结构，不改对外行为语义**；改触发方式 = 改语义，违反 PRD 约束

### 判据
这一条在 git-skills-optimize task 中是硬约束：git 四份 skill 原全是 model-invoked（无该字段），改写后仍保持 model-invoked，用剪 description 方式降低常驻 context 成本而不改触发方式。

### 关联
与 skill-quality-checklist.md 中「保持语义不变的前提」同源（该文件是 writing-great-skills 方法论的单一真值源）
