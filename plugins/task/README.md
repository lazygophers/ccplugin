# Task Management Plugin

> 项目任务管理插件 - 基于文件系统的轻量级任务追踪系统

## 概述

**任务管理系统** 不依赖数据库或脚本，而是使用 `.claude/task/` 目录下的 Markdown 文件来管理所有项目任务。通过自动化 hooks 在会话的关键时刻（SessionStart、UserPromptSubmit、Stop）提示用户管理任务。

## 🎯 核心特性

- ✅ **文件系统存储** - 任务存放在 `.claude/task/` 下的 Markdown 文件
- ✅ **无脚本依赖** - 完全不依赖 Python 脚本或数据库，只使用文本文件
- ✅ **自动化提示** - 通过 hooks 在会话关键时刻主动提示用户
- ✅ **四阶段管理** - TODO → IN-PROGRESS → DONE → ARCHIVE
- ✅ **优先级和分类** - 支持 P0/P1/P2/P3 优先级和多种任务分类
- ✅ **灵活的归档** - 按项目/模块组织历史任务
- ✅ **Git 友好** - 所有任务都在版本控制中，支持代码审查

## 📁 任务存储结构

```
.claude/task/
├── todo.md              # 待完成任务
├── in-progress.md       # 进行中任务
├── done.md              # 已完成任务（最近）
└── archive/             # 历史任务存档
    ├── ccplugin/
    │   ├── features.md
    │   ├── plugins.md
    │   └── infrastructure.md
    └── README.md
```

## 🚀 快速开始

### 1. 理解任务三态

| 状态 | 文件 | 描述 |
|------|------|------|
| **TODO** | `todo.md` | 待完成任务队列 |
| **IN-PROGRESS** | `in-progress.md` | 当前进行中的任务 |
| **DONE** | `done.md` | 本会话完成的任务 |
| **ARCHIVE** | `archive/` | 历史任务存档 |

### 2. 创建新任务

在 `.claude/task/todo.md` 中添加：

```markdown
### [P{N}] {任务标题}

- **类别**: {功能/文档/重构/bug}
- **描述**: {详细说明}
```

### 3. 开始任务

当准备开始任务时：
1. 从 `todo.md` 中剪切该任务
2. 粘贴到 `in-progress.md`
3. 添加 `**开始时间**` 和 `**进展**` 字段

### 4. 完成任务

任务完成时：
1. 从 `in-progress.md` 中剪切该任务
2. 粘贴到 `done.md`
3. 添加 `**完成时间**` 和 `**关键交付物**` 字段

### 5. 归档任务

定期将 `done.md` 中的任务移动到 `archive/` 中对应的项目/模块文件。

## 📚 完整文档

所有详细说明都在 **@${CLAUDE_PLUGIN_ROOT}/skills/task/** 中：

- **[SKILL.md](skills/task/SKILL.md)** - 核心概念、快速开始、关键要点（推荐首先阅读）
- **[reference.md](skills/task/reference.md)** - 完整规范、字段说明、最佳实践、定期维护
- **[examples.md](skills/task/examples.md)** - 实际使用示例、各种场景、工作流程

## 🔔 自动化 Hooks

系统通过三个 hooks 自动化任务管理流程：

### SessionStart Hook
🔷 **时机**：会话开始时
- 初始化 `.claude/task` 目录（如果不存在）
- 提示用户任务管理系统已就绪

### UserPromptSubmit Hook
🔷 **时机**：用户提交提示词时
- 检查是否有进行中的任务
- 主动提示用户遵守 skills 规范
- 建议及时更新任务进展

### Stop Hook
🔷 **时机**：会话停止时
- 检查是否有未完成的任务
- 提示用户在下一个会话中继续完成
- 建议是否需要归档已完成的任务

## 💡 最佳实践

### 任务优先级

- **P0** - 紧急，需要立即处理（当天）
- **P1** - 高优先级，尽快处理（本周）
- **P2** - 普通优先级，按计划处理（本月）
- **P3** - 低优先级，有时间再处理

### 任务分类

- **feature** - 新功能开发、功能增强
- **bug** - 缺陷修复、问题解决
- **refactor** - 代码重构、性能优化
- **docs** - 文档编写、API 文档
- **test** - 测试相关工作
- **config** - 配置和环境设置

### 任务粒度

推荐 **1-3 天能完成** 的任务大小。如果超过 3 天，考虑拆分：

```markdown
❌ 太大："完成用户模块"（一周工作量）

✅ 合适：
  - "实现用户认证 API"（2 天）
  - "编写认证测试"（1 天）
  - "编写 API 文档"（1 天）
```

### 定期维护

- **每日** - 检查 `in-progress.md` 并更新进展
- **每周** - 回顾完成的任务和下周计划
- **定期** - 当 `done.md` 超过 5 个任务时考虑归档

## 🔗 与 TodoWrite 的关系

本任务管理系统与 Claude Code 的 TodoWrite 工具是**互补关系**：

- **TodoWrite** - 会话内的临时任务跟踪
- **Task 系统** - 项目长期任务管理和历史记录

推荐做法：
1. 会话内快速规划可用 TodoWrite
2. 重要任务信息同时记录在 `.claude/task/`
3. 会话结束时将重要信息整理到 `done.md` 或归档

## 📋 常见场景

### 场景 1：新项目启动

1. 打开 `.claude/task/todo.md`
2. 添加项目所有的初始任务
3. 按优先级排序
4. 每天选择优先级最高的任务开始工作

### 场景 2：修复紧急 Bug

1. 在 `todo.md` 中添加 `[P0] Bug 名称`
2. 立即开始，移动到 `in-progress.md`
3. 完成后移动到 `done.md`

### 场景 3：跨会话工作

1. 上个会话的进行中任务保留在 `in-progress.md`
2. 下个会话打开该文件继续工作
3. 更新进展，完成后移动到 `done.md`

### 场景 4：任务归档

1. 当 `done.md` 超过 5 个任务时
2. 在 `archive/` 中创建或打开相应项目/模块文件
3. 移动相关的已完成任务
4. 保持 `done.md` 简洁

## ❓ 常见问题

**Q: 如何处理跨会话的任务？**
A: 不要删除 `in-progress.md` 中的任务。下个会话继续完成，更新进展，完成后移动到 `done.md`。

**Q: 任务太大怎么办？**
A: 如果任务预估超过 3 天，拆分成多个小任务，分别在 `todo.md` 中创建。

**Q: 如何处理被取消的任务？**
A: 在任务前标记 `[取消]`，保留记录但不继续执行。

**Q: 如何与团队分享进度？**
A: 定期从 `done.md` 导出总结分享，或通过 git commit 记录任务完成情况。

## 📖 相关资源

- **Skills 文档** - [@${CLAUDE_PLUGIN_ROOT}/skills/task/](skills/task/)
- **项目架构** - [CLAUDE.md](../../CLAUDE.md)
- **插件市场** - [.claude-plugin/marketplace.json](../../.claude-plugin/marketplace.json)

---

**任务管理系统设计理念**：
- 简洁 - 没有复杂的脚本，只用 Markdown
- 实用 - 满足日常任务管理需求
- 可见 - 所有任务在 Git 中可见和可审查
- 灵活 - 支持多种工作流程和团队规模

详见 [SKILL.md](skills/task/SKILL.md) 快速开始！
