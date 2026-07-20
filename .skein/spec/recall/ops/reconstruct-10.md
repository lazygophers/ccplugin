---
title: 文件移动用 shutil.move（跨平台）
layer: recall
category: ops
keywords: [filesystem,move,platform,agnostic]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
移动文件到 trash 或归档。

## 陷阱-正解
**陷阱**：用 os.rename，win/mac 行为不一。
**正解**：用 shutil.move；目标存在先清后移。

## 规则
skein.py:709-711 (trash), :724 (archive)。

## 关联
ops/platform-agnostic-filesystem
