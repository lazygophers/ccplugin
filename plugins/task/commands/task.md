---
description: 任务管理命令 - 用于创建、跟踪和管理项目任务
argument-hint: <sub-command> [args...]
allowed-tools: Bash(uv*,*/task.py)
---

# task

项目任务管理命令。使用 SQLite 数据库存储任务，数据位于项目根目录的 `.lazygophers/ccplugin/task/` 目录。

## 任务元信息

每个任务包含以下元信息：

- **id** - 任务ID（自动生成，6位随机字符串）
- **title** - 任务名称（必填）
- **description** - 任务描述
- **type** - 任务类型（feature/bug/refactor/test/docs/config）
- **status** - 任务状态（pending/in_progress/completed/blocked/cancelled）
- **acceptance_criteria** - 验收标准
- **dependencies** - 前置依赖任务ID列表（逗号分隔）
- **parent_id** - 父任务ID（支持层级关系）

## 子命令

### 创建任务

```bash
/task add "任务标题"
```

完整参数：

```bash
/task add "任务标题" \
  --description "任务描述" \
  --type feature \
  --status pending \
  --acceptance "验收标准" \
  --depends "task_id1,task_id2" \
  --parent "parent_task_id"
```

**任务类型 (type)**：
- `feature` - 新功能 ✨
- `bug` - 缺陷修复 🐛
- `refactor` - 代码重构 ♻️
- `test` - 测试 🧪
- `docs` - 文档 📝
- `config` - 配置 ⚙️

**任务状态 (status)**：
- `pending` - 待处理 ⏳
- `in_progress` - 进行中 🔄
- `completed` - 已完成 ✅
- `blocked` - 已阻塞 🚫
- `cancelled` - 已取消 ❌

### 更新任务

```bash
/task update <id> --status <status>
```

可用参数：

```bash
/task update <id> --title "新标题"
/task update <id> --description "新描述"
/task update <id> --type bug
/task update <id> --status in_progress
/task update <id> --acceptance "验收标准"
/task update <id> --depends "task_id1,task_id2"
/task update <id> --parent "parent_task_id"
```

### 快速完成

```bash
/task done <id>
```

### 列出任务

```bash
/task list                    # 列出所有任务
/task list pending           # 列出待处理任务
/task list --type bug        # 列出所有bug类型任务
/task list --status completed --type feature  # 组合筛选
```

### 查看任务详情

```bash
/task show <id>
```

显示任务的完整信息，包括验收标准和依赖关系。

### 删除任务

```bash
/task delete <id>
```

### 子任务操作

```bash
# 创建子任务
/task add "子任务标题" --parent "parent_task_id"

# 列出子任务
/task children <parent_task_id>
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

## MCP 工具调用

使用 MCP 工具管理任务：

```bash
# 创建任务
/task-add "任务标题" --description "任务描述" --type feature

# 更新任务
/task-update "task_id" --status in_progress

# 删除任务
/task-delete "task_id"

# 列出任务
/task-list --status pending --limit 10

# 获取任务详情
/task-get "task_id"
```

## 命令行执行

使用 uvx 执行脚本：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task "$@"
```

## 数据存储

任务数据库位于: `.lazygophers/ccplugin/task/tasks.db`
