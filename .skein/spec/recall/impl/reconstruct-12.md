---
title: StaticFiles mount 设 check_dir=False
layer: recall
category: impl
keywords: [mount,static,webserver,configuration]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
mount 目录未落地或构建失败。

## 陷阱-正解
**陷阱**：check_dir=True (默认)，目录不存在时 mount 炸。
**正解**：check_dir=False 允许目录缺失。

## 规则
skein.py:2342-2348 五处 mount 均设 check_dir=False。

## 关联
impl/graceful-mount-missing-assets
