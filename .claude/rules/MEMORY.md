# ccplugin 项目记忆索引

> Claude Code 插件市场项目的记忆管理中心。本文件前200行在每个会话启动时自动加载。

## 项目概述

**项目名称**：ccplugin (CCPlugin Market)
**项目类型**：Claude Code 插件市场 (Monorepo)
**技术栈**：Python 3.11+, uv, pytest, ruff
**核心组件**：

- `plugins/` — 插件实现集合（tools/languages/themes/office）
- `lib/` — 共享库（独立pyproject）
- `scripts/` — 根包CLI（clean/update/info/check/install）
- `.claude-plugin/marketplace.json` — 市场注册表

**关键文档**：

- `README.md` — 项目简介
- `AGENTS.md` — 结构速览、Agent Teams决策树
- `CLAUDE.md` — 仓库开发约定（复盘防回归规则、代码质量检查规范）
- `docs/plugin-development.md` — 插件开发指南

## Memory目录索引

`.claude/memory/` 目录存储项目长期记忆：

- `project-setup.md` — 项目Memory系统初始化记录（2026-03-27）
- `desktop-event-driven-architecture.md` — **@desktop 事件驱动架构规范**（2026-04-05）
  - **核心原则**：Rust 实现业务逻辑，事件驱动前端更新
  - **事件命名约定**：`<domain>-<entity>-<action>` 格式
  - **Rust 模式**：Command 立即返回 + 后台任务 + `emit()` 事件
  - **前端模式**：全局事件监听器 + 状态集中管理 + 无 `await` 调用
  - **迁移指南**：从 command-and-wait 迁移到事件驱动的步骤和示例
- `desktop-code-quality-2026-04-05.md` — **@desktop 代码质量审查记录**（2026-04-05）
  - **已修复问题**：Rust/前端代码复用（减少 110+ 行重复代码）、TOCTOU 反模式
  - **后续优化目标**：重复子进程调用、增量更新、冗余派生状态、UI 组件重复
  - **修复模式总结**：提取辅助函数、通用方法、通用执行器
  - **方法论**：三路并行 Agent 审查（代码复用/质量/效率）
- `cortex-plugin-2026-05-13.md` — **@cortex 整体重构基线**（2026-05-13）
  - **单一真相清单**：vault 结构 / 配置 / env var 政策 / slash 形式 / AUTO_MODE persistent / 插件路径硬编码 / MOC 已删
  - **实际计数**：8 agent · 21 skill · 20 command · 17 wrapper · 17 lint · 5 hook · 15 MCP
  - **目录布局**：所有 python/bash 集中 `scripts/`,install.sh 例外
  - **ingest 全局规则**：folder-first + 嵌套 git 独立 + L1-L6 深度 + 评分制度
  - **测试基线**：python 238 / bash 8 files / mcp 113 全绿

## Rules文件索引

`.claude/rules/` 目录存储项目特定规则（按需加载）：

- `MEMORY.md` (本文件) — 记忆系统索引
- _(可扩展：code-quality.md、plugin-development.md、frontend-rules.md等)_

## 核心约定

**代码提交规范**：

- 所有变更自动提交到暂存区（CLAUDE.md §1行）
- Desktop路由变更必须验证hash路由与首屏渲染
- Tailwind升级后必须验证utilities是否实际生成

**@desktop 架构规范**（2026-04-05）：

- **Rust 优先**：所有业务逻辑在 Rust 侧实现，TypeScript 仅负责 UI 渲染
- **事件驱动**：使用事件系统通知前端状态变化，禁止同步/异步等待结果
- **单向数据流**：Rust → Event → Frontend State → UI Render
- **无阻塞 UI**：命令立即返回，后台任务通过事件持续推送进度
- 详见：`.claude/memory/desktop-event-driven-architecture.md`

**质量检查规范**（CLAUDE.md §代码质量检查规范）：

- commands/skills/agents/agent.md优化后必须验证AI理解识别
- 使用 `claude --settings ~/.claude/settings.glm-4.7-flash.json` 验证

**复盘防回归规则**（CLAUDE.md §复盘防回归规则）：

1. Desktop信息架构：`插件市场`页面只展示marketplace列表；`插件`页面提供筛选
2. Desktop路由方案变更后，验证hash路由与首屏渲染
3. Desktop升级Tailwind构建链后，验证utilities实际生成

**GitNexus工具链**：

- 修改代码前必须运行 `gitnexus_impact` 分析影响范围
- 提交前必须运行 `gitnexus_detect_changes` 验证变更范围
- 高/严重风险警告必须报告用户
- 工具参考：`.claude/skills/gitnexus/`

## Agent Teams使用决策

**核心约束**：

- 优先避免使用Agent Teams
- 并发限制：≤2个
- 成员限制：≤2个

**决策树**（详见AGENTS.md §Agent Teams使用决策树）：

- 单一职责 → 单Agent
- 有依赖 → 串行调用
- 并行且独立 → Agent Teams (≤2成员)

## 常用命令

```bash
# 依赖管理
uv sync

# 代码质量
uv run ruff check .
uv run ruff format .

# 测试
uv run pytest lib/tests

# 版本同步
uv run scripts/update_version.py
```

## 相关技能 (Skills)

- `.claude/skills/plugin-skills/` — 插件开发规范和质量检查
- `.claude/skills/gitnexus/` — 代码智能工具（exploring/impact-analysis/debugging/refactoring/cli）

## 更新日志

**2026-05-13**：Cortex 插件整体重构 (10 commits, 一次性收尾)

- **路径迁移**：wiki/* + 数字前缀 + 记忆体系 → 中文目录 `知识库/{领域,来源,日记,...}` + `记忆/{L0-L4,...}`
- **AUTO_MODE persistent**：禁询问 ≠ 中止;AI 自决循环修复直至 lint clean
- **Slash 形式**：`/cortex:<name>` 冒号 (dash 形式 claude 无法解析)
- **目录集中**：所有 python/bash 移到 `scripts/`,install.sh 例外
- **MOC 完全删除**：canvas + dashboard 二件套替代
- **版本号清理**：删 v2 / v1 / legacy / migration 标记
- **env var 政策**：禁配置类,运行时只读 `~/.cortex/config.json`
- **插件路径硬编码**：`$HOME/.claude/plugins/marketplaces/...` (env var 解析 bug 规避)
- **文档分层**：用户文档 `docs/` + 开发者 `docs/_internal/`,计数对齐实际
- **ingest 全局规则**：folder-first + 嵌套 git 独立 + L1-L6 深度 + 强制 frontmatter + 评分
- 详见：`memory/cortex-plugin-2026-05-13.md`

**2026-04-08**：Task 插件重大更新

- **DAG 执行模型**：exec 基于 dependencies 动态调度，2个worker协程并发
- **Align 优化**：合并 prompt-optimizer 的 SMART-V 验收标准原则
- **实时状态更新**：任务状态变更立即写入 task.json
- **Plan 验证**：写入前验证 DAG 可用性
- 详见：`memory/task-dag-execution-model.md`、`memory/task-align-merge-prompt-optimizer-2026-04-08.md`

**2026-03-27**：Memory系统初始化

- 创建 `.claude/rules/` 和 `.claude/memory/` 目录
- 生成本索引文件（MEMORY.md）
- 移除自动记忆禁用配置（CLAUDE_CODE_DISABLE_AUTO_MEMORY）
- 确保符合Claude Code官方记忆规范
