# CCPlugin Onboarding Guide

> 手工编写 · 2026-07-20 同步真实结构（marketplace = 7 插件 + 根 skills/ 开发模板）

---

## 1. 项目概览

CCPlugin 是 Claude Code 的 **插件市场 + skill 开发模板** 集合。仓库提供两类内容：

| 类别 | 位置 | 用途 |
|------|------|------|
| **市场插件** | `plugins/tools/<name>/` | 通过 `claude plugin install <name>@ccplugin-market` 安装的成品插件 |
| **skill 开发模板** | `skills/<category>/<skill>/` | 本仓库自用 / 示例的 skill 方法论，**不是市场插件**，不可经 marketplace 安装 |

市场清单 `.claude-plugin/marketplace.json` 共登记 **7 个插件**（见下表），统一许可证 `AGPL-3.0-or-later`。

### 项目元数据

| 字段 | 值 |
|------|-----|
| 名称 | `ccplugin`（pyproject）/ 市场名 `ccplugin-market` |
| 语言 | Python 3.11+、Markdown |
| 依赖管理 | `uv` + `pyproject.toml`（`lib` 为本地子包，见 `[tool.uv.sources]`） |
| CLI 入口 | `pyproject.toml [project.scripts]` 暴露 `install / update / info / check / clean / md2html` |
| 测试 | `pytest`（`lib/tests/`） |

> 注：仓库根**没有** `scripts/main.py`，CLI 经 `pyproject.toml` 注册的 console script 入口运行（见第 7 节）。

---

## 2. 仓库结构

```
ccplugin/
├── .claude-plugin/
│   └── marketplace.json          # 市场清单（7 插件登记）
├── plugins/
│   └── tools/                    # 7 个市场插件（见第 3 节）
├── skills/                       # skill 开发模板（非市场插件，见第 4 节）
├── lib/                          # 共享 Python 库（db / hooks / utils）
├── scripts/                      # 项目级 CLI（install/update/check/clean/info/md2html...）
├── docs/                         # 开发文档
├── AGENTS.md -> CLAUDE.md        # 软链接，指向 CLAUDE.md
├── CLAUDE.md                     # 项目规范
├── README.md
├── pyproject.toml
└── uv.lock
```

### `lib/` 共享库

| 模块 | 职责 |
|------|------|
| `lib/db/` | 数据库抽象（`core.py` / `models.py` / `schema.py` / `adapters/`） |
| `lib/hooks/` | Hook 生命周期（`hook.py` / `pre_tool_use.py`） |
| `lib/utils/` | 通用工具（`env.py` / `file.py` / `format.py` / `gitignore.py` / `help.py` / `version.py` 等） |
| `lib/tests/` | `lib` 的 pytest 用例 |

---

## 3. 市场插件（plugins/tools/，共 7 个）

`marketplace.json` 登记的 7 个插件，均位于 `plugins/tools/<name>/`：

| 插件 | 目录 | 简介 |
|------|------|------|
| `cortex` | `plugins/tools/cortex/` | 知识库 + 记忆管理（双层 vault、5 级记忆、8 skill） |
| `deepresearch` | `plugins/tools/deepresearch/` | 多智能体深度研究系统（DGoT / Agentic RAG） |
| `notify` | `plugins/tools/notify/` | 系统通知（跨平台 + TTS） |
| `novelist` | `plugins/tools/novelist/` | 小说写作全流程插件 |
| `skein` | `plugins/tools/skein/` | 独立任务管理插件（自带 `.skein/`，双层 DAG 调度） |
| `trellisx` | `plugins/tools/trellisx/` | Trellis 增强改造工具（注入 `.trellis/`） |
| `version` | `plugins/tools/version/` | SemVer 版本管理 |

> 说明：README.md 的「可用插件」表里列了 `git / python / golang / memory / env / llms / template` 等名称 —— 那些不在本仓库 `plugins/tools/` 下，也无 `marketplace.json` 登记，属于市场可路由的其他来源，**不是本仓库源码**。本 onboarding 只覆盖仓库内真实存在的 7 个。

### 插件标准结构

每个插件是独立的 Claude Code 插件包：

```
plugins/tools/<name>/
├── .claude-plugin/
│   └── plugin.json          # 插件清单（name / description / commands / hooks / skills / agents）
├── commands/                # 自定义命令（.md）
├── agents/                  # 子代理（.md）
├── skills/                  # 技能（SKILL.md + references/templates）
├── hooks/                   # Hook 脚本（部分插件）
├── scripts/                 # CLI / Hook 执行脚本（main.py / hooks.py 等）
└── README.md
```

注：不同插件按需启用上述子目录（如 `version/scripts/` 含 `mcp.py`、`notify/scripts/` 含 `notify.py`），并非每个插件都有全部子目录。

### Hook 系统

插件通过 `plugin.json` 的 `hooks:` 字段注册 Claude Code 生命周期事件（`SessionStart` / `Setup` / `PreToolUse` 等），事件命令通常是 `uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks`。共享 hook 基础设施位于 `lib/hooks/hook.py` + `lib/hooks/pre_tool_use.py`。

---

## 4. skill 开发模板（根 skills/）

根 `skills/` 目录是**本仓库自用的 skill 方法论合集**，**不在 marketplace 中**，不能通过 `claude plugin install` 安装。它们是开发 skill / 插件时的参考模板：

| 分类 | 子 skill |
|------|----------|
| `skills/skill-dev/` | `skill-dev`（单 skill 创建/优化方法论）、`plugin-dev`（整插件开发） |
| `skills/git/` | `git-commit` / `git-merge` / `git-rebase` / `git-pr` |
| `skills/code-quality/` | `architecture-design` / `clean-code` / `perf-optimization` |
| `skills/project/` | `oss-license` / `promo-posts` |

> 注意区分：插件内部的 skill 位于 `plugins/tools/<name>/skills/`（随插件分发），根 `skills/` 是开发模板。

---

## 5. scripts/ — 项目级 CLI

`scripts/` 是市场 / 项目管理脚本，通过 `pyproject.toml [project.scripts]` 暴露为命令：

| 脚本 | 命令 | 职责 |
|------|------|------|
| `install.py` | `install` | 从市场安装 / 更新指定插件 |
| `update.py` | `update` | 批量更新已启用插件 |
| `info.py` | `info` | 展示已注册市场与插件信息 |
| `check.py` | `check` | 单插件结构 / 配置 / hook 校验 |
| `clean.py` | `clean` | 清理 `~/.claude/plugins/cache/` 旧版本 |
| `md2html.py` | `md2html` | Markdown → HTML（含 Mermaid） |
| `statusline.py` / `subagent_statusline.py` | — | 终端状态栏渲染（非 console script） |
| `update_version.py` | — | 项目 SemVer 版本号维护 |
| `utils.py` | — | 共享工具函数 |

`scripts/CLAUDE.md` 是该目录的 agent 工作约定，与插件内的 skill 规范无关。

---

## 6. 引导读图（从外到内）

| 步骤 | 主题 | 核心文件 |
|------|------|----------|
| 1 | 项目概览 | `README.md`、`pyproject.toml`、`.claude-plugin/marketplace.json` |
| 2 | 市场清单 | `.claude-plugin/marketplace.json`（7 插件登记） |
| 3 | 任意插件清单 | `plugins/tools/<name>/.claude-plugin/plugin.json` |
| 4 | 插件 CLI 入口 | `plugins/tools/<name>/scripts/main.py`（如 notify / version） |
| 5 | 共享库 | `lib/__init__.py`、`lib/db/core.py`、`lib/hooks/hook.py` |
| 6 | 项目级 CLI | `scripts/install.py`、`scripts/check.py` |
| 7 | skill 开发模板 | `skills/skill-dev/`、`skills/git/` |
| 8 | 开发规范 | `docs/plugin-development.md`、`CLAUDE.md`（=`AGENTS.md`） |

---

## 7. 快速上手

```bash
# 1. 安装项目依赖（含本地 lib 子包）
uv sync

# 2. 经 uvx 一键安装市场 + 插件（用户视角，README 推荐）
uvx --from git+https://github.com/lazygophers/ccplugin.git@master \
    install lazygophers/ccplugin <插件名>@ccplugin-market

# 3. 列出已注册市场与插件（项目级 CLI，需先 uv sync）
uv run info

# 4. 更新已启用插件
uv run update

# 5. 校验单插件（cd 到插件目录 或用 -d 指定）
uv run check -d plugins/tools/notify

# 6. 清理插件缓存旧版本（先预览再执行）
uv run clean --dry-run
uv run clean

# 7. 更新项目版本号
uv run scripts/update_version.py patch

# 8. 跑 lib 测试
uv run pytest lib/tests/
```

---

## 8. 失真备忘（本次重写移除的旧引用）

旧版 onboarding（2026-05-26 自动生成自知识图谱）含大量失真，本次重写已移除以下引用 —— 它们在仓库中**均不存在**：

- 不存在的插件：`Memory` / `Git` / `Task` / `Llms`（README「可用插件」表里的这些名也非本仓库源码，见第 3 节注）
- 不存在的目录 / 文件：`.trellis/`、`.claude/scripts/`、`.claude/hooks/`、`.claude/skills/`、`scripts/main.py`
- 失真的文件计数与「层 / 复杂度热点」结构（基于过时知识图谱节点数，不可信）
