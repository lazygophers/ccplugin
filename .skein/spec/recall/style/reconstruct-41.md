---
title: status 色相语义固定（跨主题不变）
layer: recall
category: style
keywords: [style,status,color,semantic]
source: reconstruct
authored-by: skein-spec
created: 1784346092
status: active
related: []
updated: 1784346092
---

## 触发场景
状态染色（待/进行/完成等)。

## 陷阳-正解
**陷阺**：状态色跨主题变。
**正解**：状态色相 (--h-pending/active/done 等) 全局固定，仅 surface 染色与明度换肤。

## 规则
pending=蓝245 / active=橙70 / check=青200 / done=绿150 / failed=红25。
