---
title: 文档中文 / 代码标识符英文
layer: recall
category: style
keywords: [style,language,convention,documentation]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
编写 docstring 或 frontmatter。

## 陷阳-正解
**陷阱**：混用中英（docstring 英文，description 中文混乱)。
**正解**：文档/描述/docstring 用中文，代码标识符/frontmatter key/commit 术语用英文。

## 规则
全仓一致（utils.py:9 中文 docstring + 英文标识符）。
