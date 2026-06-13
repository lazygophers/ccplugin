# CCPlugin Onboarding Guide

> 自动生成自知识图谱 · 2026-05-26 · 1474 文件分析

---

## 1. 项目概览

| 字段 | 值 |
|------|-----|
| 名称 | **ccplugin** |
| 定位 | Claude Code 插件市场与工具链 |
| 语言 | Python, Markdown, JSON, YAML, TypeScript |
| 框架 | Click (CLI), Rich (终端渲染), PyYAML, uv (包管理) |
| 入口 | `scripts/main.py` → Click CLI |

CCPlugin Market 是 Claude Code 的插件生态，提供 6+ 沿插件（Memory、Git、Notify、Version、Task、Llms），同时内置任务编排系统（Trellis）和智能体配置框架。

---

## 2. 架构层级

```
┌─────────────────────────────────────────────┐
│  插件市场层 (layer:plugins)      749 files   │  ← 各插件独立自治
├─────────────────────────────────────────────┤
│  任务管理层 (layer:trellis)      537 files   │  ← Spec → 任务 → 工作流
├─────────────────────────────────────────────┤
│  智能体系统层 (layer:agent-system) 113 files │  ← Skills / Hooks / Agents
├─────────────────────────────────────────────┤
│  核心库层 (layer:core)            36 files   │  ← DB / Hooks / Logging / Utils
├─────────────────────────────────────────────┤
│  CLI 脚本层 (layer:scripts)       14 files   │  ← install / update / check
├─────────────────────────────────────────────┤
│  配置层 (layer:config)            13 files   │  ← pyproject.toml / .version
├─────────────────────────────────────────────┤
│  文档层 (layer:documentation)     12 files   │  ← README / AGENTS / docs/
└─────────────────────────────────────────────┘
```

### 各层职责

| 层 | 职责 | 关键文件 |
|----|------|----------|
| **插件市场层** | Claude Code 扩展能力集合 | `plugins/tools/notify/`, `plugins/tools/git/` |
| **任务管理层** | Trellis 任务编排、Spec 模板、会话上下文 | `.trellis/scripts/task.py`, `.trellis/workflow.md` |
| **智能体系统层** | Agent 配置、Skills 定义、Hooks 注入 | `.claude/scripts/hooks.py`, `.claude/hooks/inject-subagent-context.py` |
| **核心库层** | 共享基础设施（DB、日志、Hook 系统） | `lib/db/core.py`, `lib/logging/manager.py`, `lib/hooks/hook.py` |
| **CLI 脚本层** | 项目管理命令 | `scripts/install.py`, `scripts/update.py`, `scripts/check.py` |
| **配置层** | 构建与运行时配置 | `pyproject.toml`, `.version`, `coverage.json` |
| **文档层** | 项目文档集合 | `README.md`, `AGENTS.md`, `docs/plugin-development.md` |

---

## 3. 关键概念

### 插件架构

每个插件是独立 Python 包，标准结构：

```
plugins/<name>/
  plugin.json      ← 插件清单（名称、版本、commands、hooks）
  scripts/
    main.py        ← CLI 入口（Click 命令组）
    hooks.py       ← Hook 事件处理器
  pyproject.toml   ← 依赖声明
```

### Hook 系统

插件通过 `hooks.py` 注册 Claude Code 生命周期事件：

- `pre_tool_use` / `post_tool_use` — 工具执行前后
- `notification` — 系统通知
- `session_start` / `session_end` — 会话管理

核心实现：`lib/hooks/hook.py` + `lib/hooks/pre_tool_use.py`

### Trellis 任务系统

三阶段工作流：

```
Planning (prd.md + research/) → In Progress (tasks/*.md) → Done (archive/)
```

关键脚本：`.trellis/scripts/task.py` (任务生命周期)、`common/active_task.py` (当前任务状态)、`common/session_context.py` (上下文注入)

### 代码质量检查

所有 skills/agents/commands 优化后必须通过 AI 可理解性测试：

```bash
claude -p "<content>" --output-format stream-json | jq ...
```

---

## 4. 引导巡游

按以下顺序阅读项目，从外到内：

| 步骤 | 主题 | 核心文件 |
|------|------|----------|
| 1 | **项目概览** | `README.md`, `pyproject.toml` |
| 2 | **插件入口脚本** | `plugins/*/scripts/main.py` — 每个插件的 CLI 入口 |
| 3 | **核心库基础** | `lib/__init__.py`, `lib/logging/manager.py` |
| 4 | **Hooks 系统** | `lib/hooks/hook.py`, `lib/hooks/pre_tool_use.py` |
| 5 | **Trellis 任务编排** | `.trellis/scripts/task.py`, `.trellis/workflow.md` |
| 8 | **CLI 安装脚本** | `scripts/install.py` |
| 9 | **通知与版本插件** | `plugins/tools/notify/`, `plugins/tools/version/` |

---

## 5. 文件地图

### 核心库层 (36 files)

| 文件 | 复杂度 | 职责 |
|------|--------|------|
| `lib/logging/manager.py` | complex | 日志管理器，基于 Rich 的终端日志系统 |
| `lib/db/core.py` | complex | 数据库核心抽象层（DatabaseConfig, Adapter, Connection） |
| `lib/db/adapters/sqlite.py` | complex | SQLite 适配器，含连接池和向量搜索 |
| `lib/db/models.py` | complex | ORM 数据模型基类（FieldType, Field, Model） |
| `lib/hooks/hook.py` | moderate | Hook 生命周期管理 |
| `lib/hooks/pre_tool_use.py` | moderate | pre_tool_use 事件处理 |
| `lib/utils/gitignore.py` | moderate | .gitignore 规则解析 |

### CLI 脚本层 (14 files)

| 文件 | 复杂度 | 职责 |
|------|--------|------|
| `scripts/install.py` | complex | 插件安装/卸载/更新（最高 fan-out） |
| `scripts/update.py` | complex | 批量更新脚本 |
| `scripts/update_version.py` | complex | SemVer 版本管理 |
| `scripts/check.py` | complex | 插件质量检查 |
| `scripts/clean.py` | complex | 清理构建产物 |
| `scripts/info.py` | complex | 项目信息展示 |
| `scripts/md2html.py` | complex | Markdown → HTML（含 Mermaid 渲染） |

### 插件市场层 — 核心插件

| 插件 | 入口 | 职责 |
|------|------|------|
| **notify** | `plugins/tools/notify/scripts/` | 系统通知（多平台 + TTS） |
| **version** | `plugins/tools/version/scripts/mcp.py` | SemVer 版本管理 MCP 服务器 |
| **git** | `plugins/tools/git/scripts/` | Git 操作工具 |
| **llms** | `plugins/llms/scripts/` | LLMs.txt 生成 |

### 智能体系统层

| 文件 | 职责 |
|------|------|
| `.claude/scripts/hooks.py` | Hook 事件处理器（complex） |
| `.claude/hooks/inject-subagent-context.py` | Subagent 上下文注入 |
| `.claude/hooks/inject-workflow-state.py` | 工作流状态注入 |
| `.claude/hooks/session-start.py` | 会话启动 hook |
| `.claude/skills/trellis-brainstorm/SKILL.md` | 需求发现 Skill |
| `.claude/skills/trellis-update-spec/SKILL.md` | Spec 更新 Skill |

---

## 6. 复杂度热点

共 173 个文件标记为 `complex`，以下为最需注意的区域：

### Hook 系统（高内聚，改动需谨慎）

```
.claude/scripts/hooks.py
plugins/tools/notify/scripts/hooks.py
```
多插件共享 hook 签名，修改一处需检查所有实现。

### Trellis 脚本（任务状态机）

```
.trellis/scripts/task.py
.trellis/scripts/common/active_task.py
.trellis/scripts/common/config.py
.trellis/scripts/common/task_store.py
.trellis/scripts/common/session_context.py
```
任务生命周期管理的核心状态机，影响所有开发工作流。

### 核心库（所有层的依赖）

```
lib/db/core.py
lib/db/adapters/sqlite.py
lib/db/models.py
lib/logging/manager.py
```
改动这里会影响所有插件，务必跑完测试再提交。

---

## 7. 快速上手

```bash
# 安装项目依赖
uv sync

# 查看可用插件
python scripts/main.py ls

# 安装所有插件到 ~/.claude/plugins/
python scripts/install.py

# 运行测试
python -m pytest lib/tests/ plugins/*/tests/

# 检查插件质量
python scripts/check.py

# 更新版本号
python scripts/update_version.py patch
```

---

*Generated by Understand Anything — knowledge graph has 2215 nodes, 2295 edges*
