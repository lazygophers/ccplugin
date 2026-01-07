---
description: 导出项目任务为 Markdown 文件
argument-hint: <output-file>
allowed-tools: Bash(uv*,*/task.py)
---

# task-export

导出项目任务为 Markdown 文件。

## 使用方法

/task-export <output-file>

## 参数

- `output-file`: 必需，输出文件路径
  - 如果是相对路径，相对于项目根目录
  - 如果只提供文件名，导出到 `.claude/` 目录

## 示例

导出到 `.claude/` 目录（推荐）：
```bash
/task-export tasks.md
```

导出到指定目录：
```bash
/task-export docs/project-tasks.md
/task-export .claude/tasks-2025-01-06.md
```

导出到项目根目录：
```bash
/task-export ./tasks.md
```

## MCP 技能调用

使用 MCP 技能导出任务：

```bash
# 导出任务到默认位置
/task:task-export "tasks.md"

# 导出到指定路径
/task:task-export "docs/project-tasks.md"
```

## 命令行执行

使用 uvx 执行脚本：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task-export "$@"
```

## 输出格式

导出的 Markdown 文件包含：

```markdown
# 任务列表

生成时间: 2025-01-06 20:00:00

## 待处理

### 🔴 实现用户登录功能 (#1)

任务描述...

## 进行中

### 🟠 修复API超时问题 (#2)

任务描述...

## 已完成

### ✅ 编写单元测试 (#3)

任务描述...

## 统计

- 总任务数: 10
- 待处理: 5
- 进行中: 3
- 已完成: 2
```

