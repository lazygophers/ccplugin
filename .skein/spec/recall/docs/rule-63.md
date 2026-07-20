---
title: 文档同步真值源选择
layer: recall
category: docs
keywords: [文档,真值源,marketplace,pyproject,同步,README,陷阱]
source: -
authored-by: skein-spec
created: 1784521896
status: active
related: []
updated: 1784521896
---

# 文档同步真值源选择

## 触发场景
编写或修改 ONBOARDING.md / README.md / 任何列出插件或 CLI 命令的文档时

## 陷阱-正解
陷阱：直接以 README 的「可用插件」表作为 plugins/tools/ 清单引用  
正解：以 .claude-plugin/marketplace.json (插件清单) + pyproject.toml [project.scripts] (CLI 命令) 为真值源

## 说明
README 的插件列表常包含市场路由的其他来源（非本仓库源码），不能直接当 plugins/tools/ 清单引用。文档同步任务必须基于真值源（marketplace.json 和 pyproject.toml）而非 README。

## 反例
- ONBOARDING 自动生成版本引用了 memory/git/task/llms 等不存在插件
- 引用了不存在的 scripts/main.py

## 改为
- 所有文档的插件列表从 marketplace.json 读取或生成
- CLI 命令列表从 pyproject.toml [project.scripts] 提取

## 适用
- 文档同步任务
- 编写用户指南
- 自动生成索引或 TOC

## 关联
- [core]: 对外插件清单单真源

## 案例
docs-sync-2026-07-20: ONBOARDING 自动生成版本引用了 memory/git/task/llms 等不存在插件 + 不存在的 scripts/main.py
