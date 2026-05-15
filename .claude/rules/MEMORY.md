# ccplugin 项目记忆索引

> Claude Code 插件市场项目的记忆管理中心。本文件前 200 行在每个会话启动时自动加载。

## 项目概述

**ccplugin** = Claude Code 插件市场 (Monorepo, Python 3.11 + uv + pytest + ruff)。

核心组件:
- `plugins/` — 插件实现 (tools / languages / themes / office)
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

- `cortex-plugin-2026-05-13.md` — **@cortex 当前真相** (vault 4 子目录 / 7 agent / 21 skill / 24 wrapper / 21 lint / 9 cron / MCP 写 + 搜索硬契约 / 评分字段强制 4+2 / 记忆 L0-L4)
- `desktop-event-driven-architecture.md` — **@desktop 事件驱动架构** (Rust 业务 + 事件驱动前端 + 单向数据流)
- `desktop-code-quality-2026-04-05.md` — **@desktop 代码质量** (代码复用 / TOCTOU 反模式 / 三路并行 Agent 审查)
- `desktop-testing.md` — **@desktop 测试约定**
- `project-setup.md` — Memory 系统初始化记录
- `task-execution-log.md` — Task 插件 DAG 执行模型

## 核心约定

**代码提交**: 所有变更自动暂存 (CLAUDE.md §1)。

**@desktop 架构**: Rust 业务 + 事件驱动前端, TS 仅 UI 渲染。Rust → Event → Frontend State → UI Render。详见 `.claude/memory/desktop-event-driven-architecture.md`。

**@cortex 写契约 (硬)**: AI 交互式 vault 写必走 `mcp__obsidian__*`。MCP 未注册 → `AskUserQuestion` 单次授权 (本会话有效不写盘)。未授权前 AI 硬拒 vault 写。例外: Stop/cron/python CLI。详见 `cortex-plugin-2026-05-13.md`。

**@cortex 搜索契约 (硬, hook 每轮注入)**: 非通用问答前第一个工具调用必须搜索 — L1 `mcp__obsidian__obsidian_simple_search` (优先 obsidian, **非 qmd**) → L2 `mcp__obsidian__obsidian_complex_search` → L3 `bash ~/.cortex/scripts/search.sh` (MCP 不可达) → L4 ripgrep。

**@cortex 评分字段强制 (lint rule 21)**: 知识库 .md 必含 score/confidence/source_credibility/maturity 4 字段, 记忆 .md 必含 importance/confidence 2 字段, 全 0.0-10.0 浮点 (maturity enum)。AI 落档 ingest_remote/save 自动写, digest 双路调 (使用 ↑ importance / 反馈 ↑↓ confidence), refresh 重评 maturity。

**质量检查**: commands/skills/agents/agent.md 优化后必跑:
```bash
claude --settings ~/.claude/settings.glm-4.7-flash.json -p "<待测>" --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

**复盘防回归** (CLAUDE.md §复盘防回归规则):
1. Desktop 信息架构: 插件市场页只展示 marketplace; 插件页提供筛选
2. Desktop 路由变更后验证 hash 路由 + 首屏渲染
3. Desktop Tailwind 升级后验证 utilities 实际生成

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
