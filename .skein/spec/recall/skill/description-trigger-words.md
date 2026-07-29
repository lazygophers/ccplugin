---
title: description-trigger-words
layer: recall
category: skill
keywords: [skill,description,触发词,中文,同义词,no-op,实测]
status: active
---

## 中文同义触发词实测结论：删无损

### 触发场景
改写 skill description 时，需决定是否保留中文同义触发词列表还是精简为单一主触发词。

### 陷阱-正解
**陷阱**：保留同义词列表为了「覆盖所有可能的说法」，实际上无法提升触发率。
**正解**：中文同义触发词实测已定（delete 版本 6/6 命中，baseline 版本也 6/6 命中），删除同义词列表是 no-op，对触发率无影响，按「逐句 no-op 测」规则整段删。

### 实测数据
git-commit (s1) 作实验组，测试基准版本 vs 删除同义词列表版本：

| 版本 | prompt 内容 | 调用次数 | 命中次数 | 结论 |
|---|---|---|---|---|
| baseline（含同义词列表） | 把改动交了 | 3 | 3 | ✅ |
| baseline（含同义词列表） | 暂存并提交 | 3 | 3 | ✅ |
| deleted（删同义词列表） | 把改动交了 | 3 | 3 | ✅ |
| deleted（删同义词列表） | 暂存并提交 | 3 | 3 | ✅ |

6/6 → 6/6，**触发率零下降**。

### 规则
- MUST：后续 12 个 skill 的 description 中文同义触发词列表一律照删，不重跑实验
- MUST：description 精简为**一 branch 一 trigger**，删掉「也可以说...」这类同义词列表
- MUST：触发词本身保留，只删列表部分

### 关联
本轮改写结果已入 skill-quality-checklist.md 的「中文同义触发词实测」章节，下游 skill 直接参照该记录，禁各自质疑或重测
