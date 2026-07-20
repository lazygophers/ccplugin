---
title: Rejected Framings 三件套
layer: recall
category: test
keywords: [rejected,framings,三件套,反例,正例]
source: sediment
authored-by: skein-spec
created: 1784473564
status: active
related: []
updated: 1784473564
---

# Rejected Framings 三件套

## 触发场景

编写 rubric 或任何需要反例对照的评估文档—— 需要明确"什么不行 + 为什么 + 怎样才行"三要素。

## 陷阱 / 正解

❌ 单列"反例"或"黑名单"章节，罗列"不要做 X/Y/Z"  
根因：AI 不知道为什么被拒、正确做法是什么，容易误判或遗漏  
✅ 每条反例三要素齐全：被拒模式 + 原因 + 正例

## 反例

❌ "不要做 X"（无原因无正例）  
✅ "组件塞进 `.claude-plugin/` 目录 | 被拒原因：插件加载时只认 `plugin.json`，组件在此目录静默不加载 | 正例：组件在插件根；`.claude-plugin/` 仅放 `plugin.json`"

## 案例

- skill-dev 9 维 rubric dim9 (反例与黑名单): 完成准则明确要求「"Rejected framings」段命名被拒模式 + 原因 + 正例」
- plugin-dev optimize-rubric: 硬护栏表格式每条禁令都配原因和正例

## 适用

- rubric 编写（评分标准）
- 质量检查文档
- 任何需要"反例 + 正解"的场景
- 教学型文档（需解释为什么）

## 关联

[[sediment-51]] (core, 正向表述优先原则)
[[sediment-52]] (core, 独立验证防自评偏差)
