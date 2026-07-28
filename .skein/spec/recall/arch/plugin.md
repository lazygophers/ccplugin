---
title: plugin
layer: recall
category: arch
keywords: [plugin,packaging,metadata,marketplace]
status: active
---

## plugin 必有 .claude-plugin/plugin.json + README.md

### 触发场景
发布新 plugin。

### 陷阱-正解
**陷阱**：缺 .claude-plugin/plugin.json 或 README.md。
**正解**：每 plugin 必有 plugin.json（name/description/author/license 等）；SHOULD 有 README.md；集中 marketplace.json 注册。
