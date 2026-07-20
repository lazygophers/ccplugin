---
title: CLI 脚本首行 shebang + 模块 docstring
layer: core
category: script
keywords: [cli,script,shebang,docstring]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
新建 CLI 脚本。

## 陷阺-正解
**陷阺**：无 shebang，或缺 docstring。
**正解**：首行 `#!/usr/bin/env python3`，紧随模块级 docstring。

## 规则
8/8 脚本一致（check.py:1-2 等）。
