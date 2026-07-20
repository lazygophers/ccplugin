---
title: 独立验证防自评偏差
layer: core
category: test
keywords: [validation,自评,防偏,独立子agent]
source: sediment
authored-by: skein-spec
created: 1784473563
status: active
related: []
updated: 1784473563
---

---
title: 独立验证防自评偏差
layer: recall
category: test
keywords: [validation,自评,防偏,独立子agent]
source: sediment
authored-by: skein-specer
created: 1784473542
status: active
related: []
updated: 1784473542
---

## 铁律 / 契约

- MUST：评分/评估 spawn 独立子 agent 或独立 session，禁同 context 自评自改
- MUST：独立验证是唯一纠偏机制，自评分数一律 +1 偏乐观
- MUST：重要质量决策（破坏性变更/接线/触发词）必须人审，禁"我觉得更好"直落
- MUST：LLM-as-judge 准确率仅 46.4%，fine-grained 差异不可信

## 反例 (命中=违规)

| 禁 | 改为 |
|---|---|
| 同 context 自评自改 | Spawn 独立子 agent 跑评分，主 agent 只读结果 |
| 相信自评分数 fine-grained 差异 | 只看 gross 信号 (Δ>0)，细粒度差异需人审 |
| 评分后直接提交改后内容 | 重要决策用 AskUserQuestion 拍板 |
