---
title: quality-method-reference
layer: recall
category: skill
keywords: [skill,writing-great-skills,Matt Pocock,方法论,单一真值源,predictability,checklist,质量,validation,optimization]
status: active
---

## writing-great-skills 方法论单一真值源

### 触发场景
后续改写或诊断 skill 时，需要参照方法论判定合理性（如 negation 转正向、progressive disclosure 分层、leading word 前置）。

### 陷阱-正解
**陷阱**：各 skill 各自重推方法论，导致理解漂移、标准不一。
**正解**：整个项目的 writing-great-skills 方法论落单一真值源文件 `skills/skill-dev/skill-dev/references/skill-quality-checklist.md`，后续改 skill 一律先读它，禁各自重推。

### 规则
- MUST：本文件含 5 个改写动作与 6 个 failure modes，后续诊断对照使用
- MUST：后续改写 skill 参照本文件的「改写动作清单」逐条过（description 剪枝 / frontmatter 清标 / 步骤补完成判据 / negation 转正向 / 逐句 no-op 测）
- MUST：改写后验证走「质量门验证法」(stdin 命令 + 三跑一致)，不各自重跑实验

### 关联
- 本轮 git 试点四份实测记录已并入该文件，下游 9 份 skill 直接复用不重测
- 与文件内「中文同义触发词实测」章节关联（测试已定，其余 12 份照删）

### 适用范围
所有 skill 改写与诊断工作流必备参考

## 三份 checklist 职责边界

### 触发场景
skill 开发流程中，需要确认文档职责边界，防止重复或误用。

### 三份 checklist 职责边界

| 文件 | 层级 | 职责 | 何时用 |
|---|---|---|---|
| `skill-quality-checklist.md` | 元方法论 | 编写期 & 诊断期：5 动作 + 6 failure modes + 质量门验证法 + 实测记录 | 改写前参照；改写中对照；改写后验证 |
| `validation-checklist.md` | 发布前门 | 发布前逐项勾选：13 项硬门 + 反例表对照 | skill 发布前最后卡口 |
| `optimization-log.md` | 历史记录 | 每轮改写的实测记录 + 决策痕迹 | 追溯改写历史；后续论证时引用 |

### 规则
- MUST：改写 skill 时对照 skill-quality-checklist.md，不混用三份文件职责
- MUST：发布前跑 validation-checklist.md，确保无遗漏
- MUST：本轮改写记录已入 quality-checklist.md 的「实测记录」章节，禁单独追加 optimization-log 副本

### 关联
三份文件位置都在 `skills/skill-dev/skill-dev/references/` 下，整个 skill-dev 文件夹改写时需同步更新这三份
