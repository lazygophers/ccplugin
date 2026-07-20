---
title: plugin 必有 .claude-plugin/plugin.json + README.md
layer: recall
category: plugin-arch
keywords: [plugin,packaging,metadata,marketplace]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
发布新 plugin。

## 陷阺-正解
**陷阺**：缺 .claude-plugin/plugin.json 或 README.md。
**正解**：每 plugin 必有 plugin.json（name/description/author/license 等）；SHOULD 有 README.md；集中 marketplace.json 注册。
