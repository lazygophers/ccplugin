# Task Plugin Configuration

配置 Task Plugin 的行为和默认值。

## 配置文件位置

创建配置文件 `.claude/config/task-config.json`：

```bash
cp .claude/config/task-config.example.json .claude/config/task-config.json
```

## 配置项说明

### workspace - 工作空间配置

```json
{
  "workspace": {
    "default_root": ".",
    "auto_init": true,
    "database_path": ".task_data"
  }
}
```

- **default_root**: 默认工作空间根目录（默认当前目录）
- **auto_init**: 启动时自动初始化工作空间（默认 true）
- **database_path**: 自定义数据库路径（默认 `.task_data`）

### tasks - 任务管理设置

```json
{
  "tasks": {
    "default_priority": 2,
    "default_type": "task",
    "auto_assign": false,
    "default_assignee": null
  }
}
```

- **default_priority**: 新任务的默认优先级
  - 0 = critical
  - 1 = high
  - 2 = medium（默认）
  - 3 = low
  - 4 = backlog
- **default_type**: 默认任务类型（task / bug / feature / epic / chore）
- **auto_assign**: 自动分配任务给当前用户（默认 false）
- **default_assignee**: 默认负责人邮箱/用户名（如果 auto_assign 为 true）

### display - 显示和格式设置

```json
{
  "display": {
    "brief_mode": true,
    "default_limit": 20,
    "show_closed": false,
    "date_format": "%Y-%m-%d %H:%M:%S"
  }
}
```

- **brief_mode**: 默认使用简化模式列出任务（默认 true）
- **default_limit**: 列表中默认返回的任务数（默认 20）
- **show_closed**: 默认列表是否包含已完成任务（默认 false）
- **date_format**: 日期格式字符串（Python datetime 格式）

### dependencies - 依赖管理设置

```json
{
  "dependencies": {
    "default_dep_type": "blocks",
    "warn_circular": true,
    "auto_close_blocking": false
  }
}
```

- **default_dep_type**: 默认依赖类型
  - `blocks`: 硬阻塞
  - `related`: 软关联
  - `parent-child`: 层级关系
  - `discovered-from`: 发现关系
- **warn_circular**: 创建潜在循环依赖时发出警告（默认 true）
- **auto_close_blocking**: 关闭依赖任务时自动关闭阻塞任务（默认 false）

### notifications - 通知设置

```json
{
  "notifications": {
    "enabled": false,
    "on_task_created": true,
    "on_task_assigned": true,
    "on_dependency_blocked": true
  }
}
```

- **enabled**: 启用通知功能（默认 false，未来版本实现）
- **on_task_created**: 任务创建时通知
- **on_task_assigned**: 任务分配给你时通知
- **on_dependency_blocked**: 你的任务被依赖阻塞时通知

### integration - 插件集成

```json
{
  "integration": {
    "context_plugin": false,
    "knowledge_plugin": false,
    "memory_plugin": false
  }
}
```

- **context_plugin**: 启用与 Context Plugin 的集成
- **knowledge_plugin**: 启用与 Knowledge Plugin 的集成
- **memory_plugin**: 启用与 Memory Plugin 的集成

### advanced - 高级设置

```json
{
  "advanced": {
    "enable_caching": true,
    "cache_ttl": 300,
    "batch_size": 100,
    "log_level": "INFO"
  }
}
```

- **enable_caching**: 启用任务缓存以提高性能（默认 true）
- **cache_ttl**: 缓存生存时间（秒）（默认 300）
- **batch_size**: 批量操作的批次大小（默认 100）
- **log_level**: 日志级别（DEBUG / INFO / WARNING / ERROR / CRITICAL）

## 使用示例

### 示例 1：团队协作配置

```json
{
  "tasks": {
    "default_priority": 2,
    "auto_assign": false,
    "default_assignee": null
  },
  "display": {
    "brief_mode": false,
    "default_limit": 50,
    "show_closed": false
  },
  "dependencies": {
    "warn_circular": true,
    "auto_close_blocking": false
  },
  "notifications": {
    "enabled": true,
    "on_task_assigned": true,
    "on_dependency_blocked": true
  }
}
```

### 示例 2：个人开发配置

```json
{
  "tasks": {
    "default_priority": 2,
    "auto_assign": true,
    "default_assignee": "developer@example.com"
  },
  "display": {
    "brief_mode": true,
    "default_limit": 10,
    "show_closed": false
  },
  "dependencies": {
    "warn_circular": false,
    "auto_close_blocking": true
  },
  "advanced": {
    "log_level": "DEBUG"
  }
}
```

### 示例 3：高性能配置

```json
{
  "advanced": {
    "enable_caching": true,
    "cache_ttl": 600,
    "batch_size": 500,
    "log_level": "WARNING"
  },
  "display": {
    "brief_mode": true,
    "default_limit": 100
  }
}
```

## 配置验证

配置文件使用 JSON Schema 验证。确保你的配置符合 `task-config.schema.json` 定义的格式。

你可以使用在线工具验证配置：
1. 访问 https://www.jsonschemavalidator.net/
2. 粘贴 `task-config.schema.json` 到左侧
3. 粘贴你的配置到右侧
4. 查看验证结果

## 环境变量覆盖

某些配置可以通过环境变量覆盖：

```bash
# 工作空间根目录
export TASK_WORKSPACE_ROOT=/path/to/project

# 日志级别
export LOG_LEVEL=DEBUG

# 数据库路径
export TASK_DB_PATH=/custom/path/.task_data

# 默认优先级
export TASK_DEFAULT_PRIORITY=1
```

环境变量优先级高于配置文件。

## 最佳实践

1. **版本控制**: 将 `task-config.example.json` 加入版本控制，但不要提交 `task-config.json`（包含个人设置）

2. **团队配置**: 为团队创建统一的 `task-config.team.json`，团队成员可以复制并修改

3. **配置分层**:
   - 全局配置：`~/.claude/config/task-config.json`
   - 项目配置：`.claude/config/task-config.json`（优先级更高）

4. **定期审查**: 定期审查配置是否仍然适合当前团队工作流程

5. **文档化变更**: 如果修改了关键配置，在项目 README 中记录

## 故障排查

### 配置未生效

1. 检查配置文件路径是否正确
2. 验证 JSON 格式是否正确（使用 JSON 验证工具）
3. 检查环境变量是否覆盖了配置
4. 重启 Claude Code 使配置生效

### 配置冲突

如果全局配置和项目配置冲突，项目配置优先级更高。

### 性能问题

如果遇到性能问题，尝试：
1. 启用缓存：`"enable_caching": true`
2. 增加缓存时间：`"cache_ttl": 600`
3. 减少默认列表大小：`"default_limit": 10`
4. 降低日志级别：`"log_level": "WARNING"`

## 相关文档

- [JSON Schema 规范](https://json-schema.org/)
- [Task Plugin 基本使用](../../examples/basic_usage.md)
- [插件配置](../.claude-plugin/plugin.json)
