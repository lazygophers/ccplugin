---
description: 任务管理命令 - 用于创建、跟踪和管理项目任务
argument-hint: <sub-command> [args...]
allowed-tools: Bash(uv*,*/task.py)
---

# task

项目任务管理命令。使用 SQLite 数据库存储任务，数据位于项目根目录的 `.lazygophers/ccplugin/task/` 目录。

⚠️ **必须使用 uv 执行 Python 脚本**

## 子命令

### 创建任务
```bash
/task add "任务标题"
```

### 更新任务状态
```bash
/task update <id> status <status>
```

可用状态: `pending`, `in_progress`, `completed`, `blocked`, `cancelled`

### 更新任务优先级
```bash
/task update <id> priority <priority>
```

可用优先级: `critical`, `high`, `medium`, `low`

### 列出任务
```bash
/task list                    # 列出所有任务
/task list pending           # 列出待处理任务
/task list in_progress       # 列出进行中任务
```

### 查看任务详情
```bash
/task show <id>
```

### 删除任务
```bash
/task delete <id>
```

### 导出任务

使用 `/task-export <file>` 命令导出任务为 Markdown 文件：

```bash
/task-export tasks.md              # 导出到 .claude/tasks.md
/task-export .claude/project.md     # 导出到 .claude/ 目录
/task-export docs/tasks.md         # 导出到 docs/ 目录
```

推荐导出到 `.claude/` 目录，便于 AI 访问和版本控制。

### 显示统计
```bash
/task stats
```

## 执行

所有任务操作通过 `task.py` 脚本执行（使用 uv）：

```bash
cd ${CLAUDE_PLUGIN_ROOT}
uv run scripts/task.py "$@"
```

## 数据存储

任务数据库位于: `.lazygophers/ccplugin/task/tasks.db`

## 注意事项

1. **必须使用此插件**维护项目任务，不要使用其他任务管理方式
2. **必须使用 uv 执行 Python 脚本**，不要直接执行 python3
3. 任务数据存储在项目目录的 `.lazygophers/ccplugin/task/` 下
4. 数据库使用 SQLite，无需额外依赖
5. 支持 Markdown 导出，便于版本控制和分享
