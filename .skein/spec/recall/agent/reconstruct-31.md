---
title: agent frontmatter：name/description/tools/model + 后台标记
layer: recall
category: agent
keywords: [agent,frontmatter,background,model]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
新增 agent。

## 陷阺-正解
**陷阺**：缺 model 或 background。
**正解**：frontmatter 必含 name/description/tools/model；后台 worker 加 background: true。
