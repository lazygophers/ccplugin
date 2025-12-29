# Task Plugin Commands

快速访问常用任务管理功能的命令。

## 可用命令

### 任务创建与管理

- **task-create**: 快速创建新任务
  - 支持设置标题、描述、类型、优先级、负责人和标签
  - 适用于快速记录新想法或需求

- **task-update**: 更新任务属性
  - 更新状态、标题、优先级、负责人等
  - 支持批量更新多个字段

### 任务查询

- **task-list**: 列出任务（支持过滤）
  - 按状态、类型、优先级、负责人过滤
  - 支持简化模式和详细模式

- **task-ready**: 显示就绪任务
  - 自动过滤无阻塞依赖的待处理任务
  - 适用于每日站会和Sprint规划

- **task-stats**: 显示任务统计
  - 按状态、类型、优先级分组统计
  - 适用于项目进度报告和健康度检查

## 使用方法

在 Claude Code 中，使用 `/` 命令来调用这些快捷命令：

```
/task-create
/task-list
/task-ready
/task-stats
/task-update
```

## 命令格式

所有命令遵循统一的 Markdown frontmatter 格式：

```markdown
---
name: command-name
description: 命令描述
---

# 命令标题

命令内容和使用说明...
```

## 自定义命令

你可以创建自己的命令文件：

1. 在 `.claude/commands/` 目录创建 `.md` 文件
2. 添加 frontmatter 元数据（name 和 description）
3. 编写命令内容和使用指南
4. 命令会自动加载到 Claude Code

### 示例：自定义 Sprint 规划命令

创建 `.claude/commands/sprint-plan.md`:

```markdown
---
name: sprint-plan
description: Sprint 规划助手
---

# Sprint 规划

帮助规划即将开始的 Sprint。

## 步骤

1. 创建 Sprint Epic
2. 从 backlog 选择用户故事
3. 拆分为技术任务
4. 设置依赖关系
5. 分配任务

...
```

## 最佳实践

1. **频繁使用就绪任务命令**: 每日站会前运行 `/task-ready` 了解可工作的任务
2. **定期查看统计**: 使用 `/task-stats` 监控项目健康度
3. **快速创建**: 使用 `/task-create` 快速记录新想法，稍后补充细节
4. **过滤查询**: 使用 `/task-list` 的过滤功能聚焦特定任务集

## 相关文档

- [基本使用示例](../../examples/basic_usage.md)
- [MCP 工具参考](../../docs/MCP工具参考.md)
- [插件配置](../.claude-plugin/plugin.json)
