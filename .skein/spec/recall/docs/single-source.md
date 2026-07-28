---
title: single-source
layer: recall
category: docs
keywords: [插件,清单,单真源,marketplace,同步,漂移,文档,真值源,pyproject,README,陷阱]
status: active
---

## 对外插件清单单真源

### 对外插件清单单真源

### 铁律
- 所有对外可见的「可用插件清单」(README.md / docs/ONBOARDING.md / CLAUDE.md 等) **必须** 以 .claude-plugin/marketplace.json 为单真源
- 新增或移除插件时，三处清单必须同步，禁止清单与 marketplace.json 漂移

### 反例
- README 列出 22 个插件而 marketplace.json 只有 7 个
- 文档声称存在某个插件但 plugins/tools/ 下实际无源码

### 改为
- 所有文档的插件列表基于 marketplace.json 生成或引用
- 插件变更流程：marketplace.json → 文档自动同步

### 关联
- [arch]: SPA catch-all fallback 声明在所有 mount 之后
- [ops]: 插件许可统一 AGPL-3.0-or-later

### 触发场景
任何修改 plugins/tools/ 或 marketplace.json 的变更

### 案例
docs-sync-2026-07-20: 因 README 列 22 插件而 marketplace.json 只 7 个，漂移 15 个虚假条目导致 ONBOARDING 自动生成版本引用不存在插件

## 文档同步真值源选择

### 文档同步真值源选择

### 触发场景
编写或修改 ONBOARDING.md / README.md / 任何列出插件或 CLI 命令的文档时

### 陷阱-正解
陷阱：直接以 README 的「可用插件」表作为 plugins/tools/ 清单引用  
正解：以 .claude-plugin/marketplace.json (插件清单) + pyproject.toml [project.scripts] (CLI 命令) 为真值源

### 说明
README 的插件列表常包含市场路由的其他来源（非本仓库源码），不能直接当 plugins/tools/ 清单引用。文档同步任务必须基于真值源（marketplace.json 和 pyproject.toml）而非 README。

### 反例
- ONBOARDING 自动生成版本引用了 memory/git/task/llms 等不存在插件
- 引用了不存在的 scripts/main.py

### 改为
- 所有文档的插件列表从 marketplace.json 读取或生成
- CLI 命令列表从 pyproject.toml [project.scripts] 提取

### 适用
- 文档同步任务
- 编写用户指南
- 自动生成索引或 TOC

### 关联
- [core]: 对外插件清单单真源

### 案例
docs-sync-2026-07-20: ONBOARDING 自动生成版本引用了 memory/git/task/llms 等不存在插件 + 不存在的 scripts/main.py
