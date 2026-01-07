# Task Manager Plugin

> 项目任务管理插件 - 使用 SQLite 存储任务，支持 Markdown 导出

## 功能特性

- ✅ **任务管理**：创建、更新、删除任务
- ✅ **状态跟踪**：pending、in_progress、completed、blocked、cancelled
- ✅ **任务类型**：feature、bug、refactor、test、docs、config
- ✅ **验收标准**：为每个任务定义验收标准
- ✅ **依赖关系**：支持前置依赖和父子任务
- ✅ **SQLite 存储**：轻量级，无需额外依赖
- ✅ **Markdown 导出**：便于版本控制和分享

## 数据存储

任务数据存储在项目目录的专用位置：

```
<项目根目录>/.lazygophers/ccplugin/task/
├── tasks.db          # SQLite 数据库
└── backup/           # 自动备份（可选）
```

## 任务元信息

每个任务包含：

- **id** - 任务ID（自动生成，6位随机字符串）
- **title** - 任务名称（必填）
- **description** - 任务描述
- **type** - 任务类型（feature/bug/refactor/test/docs/config）
- **status** - 任务状态
- **acceptance_criteria** - 验收标准
- **dependencies** - 前置依赖任务ID列表
- **parent_id** - 父任务ID（支持层级关系）

## 快速开始

### 1. 安装插件

```bash
/plugin install ./task
```

### 2. 创建第一个任务

```bash
/task add "项目初始化"
```

这会自动创建数据库：`.lazygophers/ccplugin/task/tasks.db`

### 3. 查看任务

```bash
/task list              # 所有任务
/task list pending      # 待处理
/task stats             # 统计信息
```

## 命令参考

### 任务操作

| 命令 | 说明 | 示例 |
|------|------|------|
| `/task add <title>` | 添加任务 | `/task add "实现登录"` |
| `/task add <title> --type <type>` | 指定类型 | `/task add "修复Bug" --type bug` |
| `/task add <title> --acceptance <标准>` | 设置验收标准 | `/task add "登录功能" --acceptance "用户可使用邮箱密码登录"` |
| `/task add <title> --depends <ids>` | 设置依赖 | `/task add "登录UI" --depends "task1,task2"` |
| `/task update <id> --status <status>` | 更新状态 | `/task update 1 --status completed` |
| `/task done <id>` | 完成任务 | `/task done 1` |
| `/task delete <id>` | 删除任务 | `/task delete 1` |
| `/task list [--type <type>]` | 列出任务 | `/task list --type feature` |
| `/task show <id>` | 查看详情 | `/task show 1` |

### 任务类型

| 类型 | 图标 | 说明 |
|------|------|------|
| `feature` | ✨ | 新功能开发 |
| `bug` | 🐛 | 缺陷修复 |
| `refactor` | ♻️ | 代码重构 |
| `test` | 🧪 | 测试相关 |
| `docs` | 📝 | 文档编写 |
| `config` | ⚙️ | 配置变更 |

### 状态值

- `pending` - 待处理 ⏳
- `in_progress` - 进行中 🔄
- `completed` - 已完成 ✅
- `blocked` - 已阻塞 🚫
- `cancelled` - 已取消 ❌

### 导出任务

| 命令 | 说明 | 示例 |
|------|------|------|
| `/task-export <file>` | 导出任务 | `/task-export tasks.md` |

## 使用场景

### 1. 项目初始化

```bash
/task add "项目初始化" --type feature
/task add "数据库设计" --type feature --depends "项目初始化"
/task add "API开发" --type feature --depends "数据库设计"
/task add "前端实现" --type feature --depends "API开发"
/task add "测试部署" --type test

/task-export "tasks-initial.md"
```

### 2. 日常开发

```bash
# 开始工作
/task list pending
/task update <id> --status in_progress

# 完成任务
/task done <id>
```

### 3. 缺陷修复

```bash
# 创建bug任务
/task add "修复登录超时" \
  --type bug \
  --description "生产环境登录接口在并发>100时超时超过30秒" \
  --acceptance "并发100时响应时间<2秒，成功率>99%"

# 修复完成后验证
/task done <id>
```

### 4. 版本发布

```bash
# 导出任务快照
/task-export "tasks-v1.0.md"

# 提交到 Git
git add tasks-v1.0.md
git commit -m "v1.0 任务归档"
```

## 工作流程

### 推荐流程

1. **项目启动**
   ```bash
   /task add "项目初始化" --type feature --acceptance "项目结构创建完成"
   /task-export "tasks-plan.md"
   ```

2. **每日工作**
   ```bash
   /task list pending
   /task update <id> --status in_progress
   # ... 工作完成 ...
   /task done <id>
   ```

3. **里程碑**
   ```bash
   /task-export "tasks-milestone-1.md"
   /task list completed
   ```

## 最佳实践

### 1. 任务粒度

✅ **好的任务**（1-3天完成）：
- "实现用户登录功能"
- "编写登录API单元测试"
- "修复登录页面样式"

❌ **不好的任务**：
- "完成用户模块"（太大）
- "写代码"（不明确）

### 2. 验收标准

每个任务都应该有清晰的验收标准：

```bash
/task add "实现用户注册" \
  --type feature \
  --acceptance "用户可以使用邮箱注册，收到验证邮件，完成邮箱验证激活账户"
```

好的验收标准应该：
- ✅ 具体、可验证
- ✅ 包含明确的完成条件
- ✅ 可以通过测试验证

❌ 不好的验收标准：
- "完成功能"（太模糊）
- "代码质量好"（无法验证）

### 3. 依赖关系

使用依赖关系管理任务顺序：

```bash
# 基础任务
/task add "设计数据库" --type feature

# 依赖任务
/task add "实现用户API" --type feature --depends "设计数据库"
/task add "实现前端页面" --type feature --depends "实现用户API"

# 测试任务
/task add "编写测试用例" --type test --depends "实现用户API,实现前端页面"
```

### 4. 定期导出

每日或每周导出任务：

```bash
/task-export "tasks-$(date +%Y-%m-%d).md"
```

## 数据库结构

### tasks 表

```sql
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT DEFAULT 'feature',
    status TEXT DEFAULT 'pending',
    acceptance_criteria TEXT,
    dependencies TEXT,
    parent_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

### notes 表

```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);
```

## 技术细节

### 存储位置

```
项目根目录/
└── .lazygophers/
    └── ccplugin/
        └── task/
            └── tasks.db
```

### 环境变量

- `CLAUDE_PLUGIN_ROOT`: 插件根目录
- 数据库相对路径：`.lazygophers/ccplugin/task/tasks.db`

### 依赖

- uv（Python 包管理器和执行器）
- typer（CLI 框架）
- rich（终端美化）

## 故障排除

### 数据库不存在

首次使用自动创建：
```bash
/task add "初始化"
```

### 权限问题

```bash
mkdir -p .lazygophers/ccplugin/task
chmod 755 .lazygophers/ccplugin/task
```

### uv 不可用

```bash
# 检查 uv
uv --version
```

## 开发指南

### 核心脚本

- `scripts/task.py` - 核心 Python 脚本
  - 数据库操作
  - CRUD 接口
  - 导出功能

### 扩展功能

1. **添加新命令**
   - 在 `commands/` 创建新的 `.md` 文件
   - 在 `task.py` 添加处理逻辑

2. **修改数据库结构**
   - 更新 `init_database()` 函数
   - 添加迁移逻辑

3. **自定义技能**
   - 编辑 `skills/task/SKILL.md`
   - 添加特定场景指导

## 参考资源

- [插件开发指南](../../docs/plugin-development.md)
- [API 参考](../../docs/api-reference.md)
- [最佳实践](../../docs/best-practices.md)

## 许可证

MIT License

## 作者

CCPlugin Team
