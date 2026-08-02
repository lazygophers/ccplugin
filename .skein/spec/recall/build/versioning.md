---
title: versioning
layer: recall
category: build
keywords: [version,build,automation,plugin]
status: active
---

## .version 四段式版本 + 自动 bump

### 触发场景
版本管理与 bump。

### 陷阱-正解
**陷阱**：仅 pyproject 三段版本。
**正解**：.version 文件 major.minor.patch.build 四段，由 version plugin hooks 自动 bump；pyproject 三段与之对应。

### 规则
.version:1 = 0.0.195.45；pyproject:3 = 0.0.195。
