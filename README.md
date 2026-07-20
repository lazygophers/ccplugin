# CCPlugin Market

> Claude Code 插件市场 - 提供高质量插件和开发模板

## 简介

CCPlugin Market 是一个为 Claude Code 提供插件的集中市场。我们提供了一系列经过验证的高质量插件，帮助开发者提高工作效率，覆盖项目管理、代码搜索、Git 操作、多语言开发等多个领域。

## 快速开始

### 一键安装（推荐）

使用 `uvx` 一键安装市场和插件：

```bash
# 安装市场和指定插件
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin <插件名>@ccplugin-market

# 示例：安装 skein 任务管理插件
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin skein@ccplugin-market

# 示例：安装多个插件
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin skein@ccplugin-market cortex@ccplugin-market deepresearch@ccplugin-market
```

### 传统方式安装

```bash
# 1. 添加市场
claude plugin marketplace add lazygophers/ccplugin

# 2. 安装插件
claude plugin install <插件名>@ccplugin-market
```

### 在 Claude Code 中安装

```bash
# 方式 1: 直接安装插件（自动添加市场）
/plugin install skein@ccplugin-market

# 方式 2: 先添加市场再安装
/plugin marketplace add lazygophers/ccplugin
/plugin install skein@ccplugin-market
```

## 可用插件

所有插件源码位于 `plugins/tools/<name>`，清单见 `.claude-plugin/marketplace.json`。

| 插件名称 | 描述 | 关键词 |
|---------|------|--------|
| `deepresearch` | 深度研究插件 - 基于图思维框架的多智能体深度研究系统，支持多领域深度调查、引用验证、知识合成和专业报告生成 | research, analysis, citation, multi-agent, graph-of-thoughts |
| `version` | 版本号管理插件 - 提供 SemVer 版本管理，支持自动版本更新和手动版本设置，通过 Claude Code Hooks 自动检测任务完成并更新构建版本号 | version, semver, release, automation, hooks |
| `notify` | 系统通知插件 - 通过系统通知向用户实时提示会话状态变更、权限请求等重要事件，跨平台支持 macOS、Linux、Windows | notification, system-notification, hook, macos, linux, windows |
| `trellisx` | Trellis 增强改造工具 - 跑一次 trellisx-apply 把 强推task / subtask拆分 / worktree隔离 / plan→exec→check→finish闭环 / task.md看板 注入 .trellis; 含 flow 强制task / orchestrate 编排 / workspace 看板 / spec 破坏式重构 | trellis, task-orchestration, worktree, subtask, spec |
| `cortex` | 知识库 + 记忆管理插件 - 双层 vault、5 级记忆 (遗忘曲线)、8 skill (schema/ingest/lint/extract/history-digest/context-digest/evolve/recall) | knowledge-base, memory, vault, forgetting-curve, recall |
| `novelist` | 小说写作全流程插件 - 从爆款题材/世界观/人物/大纲到章节编写、一致性检查、校对、去AIGC、重写、批量流水线的端到端工作流 | novel, writing, fiction, worldbuilding, continuity-check |
| `skein` | SKEIN 独立任务管理插件 (零 trellis 依赖) - 强制 task 闭环 (plan→exec→check→finish) + 动态 DAG 编排调度 + worktree 隔离 + 两层×类目规则记忆 + 9 skill + 3 agent | task-management, dag-scheduling, worktree, rules-memory, kanban |

## 安装示例

```bash
# 任务管理（SKEIN）
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin skein@ccplugin-market

# 知识库 + 记忆（cortex）
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin cortex@ccplugin-market

# 深度研究（deepresearch）
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin deepresearch@ccplugin-market

# 版本号管理（version）
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin version@ccplugin-market
```

## 环境要求

- **Python**: >= 3.11
- **uv**: Python 包管理器和执行器
- **Claude Code**: 最新版本

### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version
```

## 插件开发

### 创建新插件

```bash
# 手动创建插件目录结构
mkdir -p my-new-plugin/.claude-plugin
mkdir -p my-new-plugin/commands   # 命令
mkdir -p my-new-plugin/agents     # 代理
mkdir -p my-new-plugin/skills     # 技能

# 编写配置
vi my-new-plugin/.claude-plugin/plugin.json
```

> 详细步骤参见 [docs/plugin-development.md](docs/plugin-development.md)。

### 插件结构

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json         # 插件清单（必需）
├── commands/               # 自定义命令
│   └── my-command.md
├── agents/                 # 子代理
│   └── my-agent.md
├── skills/                 # 技能
│   └── my-skill/
│       └── SKILL.md
├── scripts/                # 脚本（可选）
│   └── script.py
├── README.md               # 插件文档
└── CHANGELOG.md            # 版本历史
```

### 提交插件

1. Fork 本仓库
2. 在 `plugins/` 目录下创建插件
3. 更新 `marketplace.json`
4. 提交 Pull Request

## 文档

### 开发文档

- [插件开发指南](docs/plugin-development.md) - 完整的插件开发教程

### 项目文档

- [CLAUDE.md](CLAUDE.md) - 项目开发规范和指导
- [CHANGELOG.md](CHANGELOG.md) - 版本变更历史

## 插件缓存清理

```bash
# 预览将要删除的内容
uvx --from git+https://github.com/lazygophers/ccplugin.git@master clean --dry-run

# 实际执行清理
uvx --from git+https://github.com/lazygophers/ccplugin.git@master clean
```

## 常见问题

### 如何安装插件？

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin skein@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install skein@ccplugin-market
```

### 如何更新插件？

```bash
# 重新安装即可更新
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin skein@ccplugin-market
```

### 如何开发新插件？

1. 创建目录结构：`mkdir -p my-new-plugin/.claude-plugin`（commands/agents/skills 按需）
2. 修改配置：编辑 `.claude-plugin/plugin.json`
3. 实现功能：添加命令、代理、技能
4. 测试插件：`/plugin install ./my-new-plugin`
5. 提交市场：更新 `marketplace.json` 并提交 PR

## 许可证

AGPL-3.0-or-later - 详见 [LICENSE](LICENSE)

## 贡献指南

我们欢迎社区贡献！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/my-new-feature`
3. 提交更改：`git commit -m "Add some feature"`
4. 推送分支：`git push origin feature/my-new-feature`
5. 提交 Pull Request
