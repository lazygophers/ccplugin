---
title: 正向表述优先原则
layer: recall
category: impl
keywords: [positive,表述,文档编写,AI]
source: sediment
authored-by: skein-spec
created: 1784473563
status: active
related: []
updated: 1784473563
---

---
title: 正向表述优先原则
layer: recall
category: impl
keywords: [positive,表述,文档编写,AI]
source: sediment
authored-by: skein-specer
created: 1784473542
status: active
related: []
updated: 1784473542
---

## 铁律 / 契约

- MUST：AI 文档默认正向表述"该做什么"，禁负向"别做什么"列表
- MUST：仅无法正向化的硬护栏保留反例，且必须配正例对照
- MUST：反例段命名含"被拒模式 + 原因 + 正例"三要素
- MUST：禁裸"不要做 Y"黑名单，每条禁令必配正例

## 反例 (命中=违规)

| 禁 | 改为 |
|---|---|
| "组件目录禁进 `.claude-plugin/`" | "组件在插件根；`.claude-plugin/` 仅放 `plugin.json`" |
| "禁 hook `exit 1`" | "guard 用 `exit 2` 阻断；副作用 hook 失败 `exit 0` 兜底" |
| 列表式"禁 A、禁 B、禁 C" | 表格式"禁 A | 正例 A；禁 B | 正例 B；禁 C | 正例 C" |
| 独立"不要做什么"章节 | 融入正向流程，仅必要硬护栏处配对照表 |
