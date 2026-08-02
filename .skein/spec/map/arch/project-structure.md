---
title: 项目架构总览
category: arch
keywords: [架构, structure, design]
inclusion: auto
anchors:
  - plugins/tools/skein/scripts/skeinlib/
  - plugins/tools/skein/scripts/hooks.py
---

# 项目架构总览

本项目是 Claude Code 插件 + skills 集合，由市场插件和 skill 开发模板组成。

## 核心组件

- **skeinlib/**: 核心库，包含 spec 引擎、状态机等
- **scripts/**: 对外脚本接口
- **plugins/**: 市场插件目录

## 架构原则

- 分层清晰：入口、CLI、业务逻辑分离
- 单一真值源：配置、状态、索引各有一个权威来源
- 零依赖：纯 stdlib 实现，无外部依赖