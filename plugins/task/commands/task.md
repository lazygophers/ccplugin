---
description: 任务管理命令 - 用于创建、跟踪和管理项目任务
argument-hint: <sub-command> [args...]
allowed-tools: Bash(uv*,*/task.py)
model: sonnet
---

# task

## 命令描述

综合任务管理命令，使用 SQLite 数据库存储任务。支持创建、更新、查看、删除等多种操作，支持任务分类、依赖关系和层级结构。

## 工作流描述

1. **任务管理**：创建、更新、删除任务
2. **状态追踪**：管理任务状态（待处理、进行中、已完成等）
3. **依赖管理**：定义任务间的依赖关系
4. **查询统计**：列出、筛选、统计任务信息

## 命令执行方式

### 使用方法

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task <sub-command> [args...]
```

### 执行时机

- 需要创建新的开发任务或 bug 修复
- 跟踪任务进度和状态
- 查看项目中的待办项
- 导出任务进行报告和分享

### 执行参数

#### 子命令列表

| 子命令 | 说明 | 用法 |
|--------|------|------|
| `add` | 创建新任务 | `uvx ... task add "任务标题" [选项]` |
| `update` | 更新任务 | `uvx ... task update <id> [选项]` |
| `done` | 快速完成任务 | `uvx ... task done <id>` |
| `delete` | 删除任务 | `uvx ... task delete <id>` |
| `list` | 列出任务 | `uvx ... task list [筛选条件]` |
| `show` | 查看任务详情 | `uvx ... task show <id>` |
| `children` | 列出子任务 | `uvx ... task children <parent_task_id>` |
| `stats` | 显示任务统计 | `uvx ... task stats` |

### 命令说明

- 数据库位置：`.lazygophers/ccplugin/task/tasks.db`
- 每个任务有唯一ID（6位随机字符串）
- 支持任务类型、状态、验收标准、依赖关系等属性
- 支持任务层级（父子任务关系）

## 相关Skills（可选）

本命令无依赖Skills，但可参考：
- `@${CLAUDE_PLUGIN_ROOT}/skills/task-strategy/SKILL.md` - 任务管理最佳实践

## 依赖脚本

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task "$@"
```

## 示例

### 基本用法 - 创建任务

```bash
# 最简单的创建方式
uvx --from git+https://github.com/lazygophers/ccplugin task add "实现用户登录功能"

# 完整的创建参数
uvx --from git+https://github.com/lazygophers/ccplugin task add "实现用户登录功能" \
  --description "需要实现基于JWT的用户认证系统" \
  --type feature \
  --status pending \
  --acceptance "用户可以通过用户名密码登录，登录成功返回JWT token" \
  --depends "task_id1,task_id2" \
  --parent "parent_task_id"
```

### 更新和状态管理

```bash
# 标记任务为进行中
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --status in_progress

# 修改任务标题
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --title "新的任务标题"

# 快速完成任务
uvx --from git+https://github.com/lazygophers/ccplugin task done <id>

# 更新验收标准
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --acceptance "新的验收标准"
```

### 查询和列表

```bash
# 列出所有任务
uvx --from git+https://github.com/lazygophers/ccplugin task list

# 列出待处理任务
uvx --from git+https://github.com/lazygophers/ccplugin task list pending

# 按类型筛选
uvx --from git+https://github.com/lazygophers/ccplugin task list --type bug

# 组合筛选
uvx --from git+https://github.com/lazygophers/ccplugin task list --status completed --type feature

# 查看任务详情
uvx --from git+https://github.com/lazygophers/ccplugin task show <id>

# 列出子任务
uvx --from git+https://github.com/lazygophers/ccplugin task children <parent_task_id>

# 显示统计
uvx --from git+https://github.com/lazygophers/ccplugin task stats
```

### 删除任务

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task delete <id>
```

## 任务类型和状态

### 任务类型 (type)

| 类型 | 说明 | 用途 |
|------|------|------|
| `feature` | 新功能 | 实现新的功能特性 |
| `bug` | 缺陷修复 | 修复已知的 bug |
| `refactor` | 代码重构 | 改进代码结构或性能 |
| `test` | 测试 | 编写或改进测试 |
| `docs` | 文档 | 编写或更新文档 |
| `config` | 配置 | 配置相关任务 |

### 任务状态 (status)

| 状态 | 说明 | 含义 |
|------|------|------|
| `pending` | 待处理 | 尚未开始 |
| `in_progress` | 进行中 | 正在进行 |
| `completed` | 已完成 | 完成并验证 |
| `blocked` | 已阻塞 | 被其他问题阻塞 |
| `cancelled` | 已取消 | 不再需要 |

## 检查清单

在使用任务管理前，确保满足以下条件：

- [ ] 了解项目的任务分类方式（type）
- [ ] 明确任务的优先级和依赖关系
- [ ] 确定任务的验收标准
- [ ] （可选）计划任务的层级结构（parent-child）

## 注意事项

- **任务ID**：自动生成的6位随机字符串，创建后不可修改
- **依赖关系**：多个依赖用逗号分隔（如：`task_id1,task_id2`）
- **父子任务**：可创建任务层级，便于复杂项目的任务组织
- **验收标准**：定义清晰的验收标准有助于任务完成的判定
- **类型规范**：选择合适的任务类型便于统计和追踪

## 其他信息

### 任务属性说明

每个任务包含以下属性：

| 属性 | 说明 | 可更新 |
|------|------|--------|
| `id` | 任务ID（自动生成） | ✗ |
| `title` | 任务名称 | ✓ |
| `description` | 任务描述 | ✓ |
| `type` | 任务类型 | ✓ |
| `status` | 任务状态 | ✓ |
| `acceptance_criteria` | 验收标准 | ✓ |
| `dependencies` | 前置依赖任务ID列表 | ✓ |
| `parent_id` | 父任务ID | ✓ |

### 导出功能

使用 `task-export` 命令导出任务为 Markdown 文件：

```bash
# 导出到 .claude/ 目录
uvx --from git+https://github.com/lazygophers/ccplugin task-export tasks.md

# 导出到自定义位置
uvx --from git+https://github.com/lazygophers/ccplugin task-export docs/project-tasks.md
```

### 性能考虑

- 小型项目（<100 任务）：快速响应
- 中型项目（100-1000 任务）：正常速度
- 大型项目（>1000 任务）：考虑按状态或类型分组查询

### 最佳实践

1. **清晰的标题**：任务标题应该清晰明确（不超过100字符）
2. **详细的描述**：复杂任务需要详细描述和验收标准
3. **合理的分类**：使用合适的任务类型便于统计
4. **定期更新**：及时更新任务状态反映进度
5. **依赖管理**：明确定义任务依赖关系避免阻塞
