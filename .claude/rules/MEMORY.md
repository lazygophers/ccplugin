# ccplugin 项目记忆索引

> Claude Code 插件市场项目的记忆管理中心。本文件前 200 行在每个会话启动时自动加载。

## 项目概述

**ccplugin** = Claude Code 插件市场 (Monorepo, Python 3.11 + uv + pytest + ruff)。

核心组件:
- `plugins/` — 插件实现 (tools / languages / themes / llms / template / memory)
- `lib/` — 共享库
- `scripts/` — 根包 CLI (clean / update / info / check / install)
- `.claude-plugin/marketplace.json` — 市场注册表

关键文档:
- `README.md` — 项目简介
- `AGENTS.md` — 结构 + Agent Teams 决策树
- `CLAUDE.md` — 仓库开发约定
- `docs/plugin-development.md` — 插件开发指南

## Memory 索引

`.claude/memory/` 项目长期记忆:

- `cortex-plugin-2026-05-13.md` — **@cortex 当前真相** (vault 4 子目录 / 6 agent / 19 skill (含 cortex-dataview 2026-05-23) / 19 slash / 27 wrapper / 15 py CLI / 40 templates / quickadd 6 choice preset / 30 lint / 4 cron / MCP 写 + 搜索回退链 / 评分字段 4+2 / 记忆 L0-L4 / digest stage 5 双向桥)
- `project-setup.md` — Memory 系统初始化记录
- `task-execution-log.md` — Task 插件 DAG 执行模型

## 核心约定

**代码提交**: 所有变更自动暂存 (CLAUDE.md §1)。**`.version` 文件强制随每次代码 commit 一同提交** (skill/CLI/wrapper/yaml 等任何用户可见变更), bump 末段 patch 号 (0.0.X.Y → 0.0.X.Y+1)。

**@cortex 写契约 (硬)**: AI 交互式 vault 写必走 `mcp__obsidian__*`。MCP 未注册 → `AskUserQuestion` 单次授权 (本会话有效不写盘)。未授权前 AI 硬拒 vault 写。例外: Stop/cron/python CLI。详见 `cortex-plugin-2026-05-13.md`。

**@cortex 搜索回退 (hook 每轮注入)**: 需查资料时**依次降级** (前一步无果才下一步) — `mcp__obsidian__*_search` → `mcp__qmd__search` → `bash ~/.cortex/scripts/search.sh --query "<词>"` → 本地 Read/Grep → WebSearch。

**@cortex 评分字段强制 (lint rule 21)**: 知识库 .md 必含 score/confidence/source_credibility/maturity 4 字段, 记忆 .md 必含 importance/confidence 2 字段, 全 0.0-10.0 浮点 (maturity enum)。AI 落档 ingest_remote/save 自动写, digest 双路调 (使用 ↑ importance / 反馈 ↑↓ confidence), refresh 重评 maturity。

**质量检查**: commands/skills/agents/agent.md 优化后必跑:
```bash
claude --settings ~/.claude/settings.glm-4.7-flash.json -p "<待测>" --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

**GitNexus**:
- 改代码前必跑 `gitnexus_impact` 分析影响
- 提交前必跑 `gitnexus_detect_changes` 验证范围
- HIGH/CRITICAL 风险必报告用户

## Agent Teams 决策

- 优先单 Agent
- 并发 ≤2, 成员 ≤2
- 单一职责 → 单 Agent; 有依赖 → 串行; 并行独立 → Team

详细决策树见 `AGENTS.md §Agent Teams 决策树`。

## 常用命令

```bash
uv sync                          # 依赖
uv run ruff check . && uv run ruff format .
uv run pytest lib/tests
uv run scripts/update_version.py # 版本同步
```

## 相关 Skills

- `.claude/skills/plugin-skills/` — 插件开发规范 + 质量检查
- `.claude/skills/gitnexus/` — 代码智能 (exploring / impact / debug / refactor / cli)
