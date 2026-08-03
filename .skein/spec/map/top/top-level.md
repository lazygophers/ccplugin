---
title: 顶层地图
category: top
keywords: [地图, map, 概览]
inclusion: auto
anchors: []
---

# 顶层地图

这是项目的顶层地图，被 always 注入，为 AI 提供项目结构的整体概览。

## 主要目录

- **plugins/**: 市场插件目录
- **skills/**: skill 开发模板
- **skeinlib/**: 核心库实现
- **scripts/**: 对外脚本接口

## 核心概念

本项目实现三层规则记忆库：
- **core**: 常驻注入的核心规则
- **recall**: 按需召回的规则
- **map**: 代码地图语义页