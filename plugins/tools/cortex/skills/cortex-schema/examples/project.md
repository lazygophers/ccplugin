> 样例 — type=project, 完整可直接落盘到 项目/github.com/lazygophers/ccplugin/README.md

---
type: project
source: https://github.com/lazygophers/ccplugin
summary: Claude Code 插件集 — cortex 知识库 / lint / extract 工具链
mindmap: ./mindmap.canvas
created: 2026-06-09
updated: 2026-06-09
tags: [claude-code, plugin, cortex, knowledge-base]
aliases: [ccplugin, lazygophers-ccplugin]
---

# ccplugin

Claude Code 官方插件市场扩展, 提供 cortex 知识库管理工具集 (lint / extract / schema 三 skill).

## 模块

- `plugins/tools/cortex/` — 核心插件, 含 3 skills
- `scripts/_lint/` — Python lint 实现
- `tests/` — e2e + 单元测试

## 关键决策

- 知识库统一契约见 [[cortex-schema]] (合并自 schema-knowledge + schema-memory)
- 5 级记忆模型见 [[memory-levels]]
- 三模块路径规则见 [[knowledge-modules]]

## 进度

当前 sprint 关注点: 详见 [[current-sprint-context]].
