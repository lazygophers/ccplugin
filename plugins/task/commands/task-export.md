---
description: 导出项目任务为 Markdown 文件
argument-hint: <output-file>
allowed-tools: Bash(uv*,*/task.py)
model: haiku
---

# task-export

## 命令描述

将项目任务数据库中的所有任务导出为结构化的 Markdown 文件，便于版本控制和分享。

## 工作流描述

1. **读取任务数据**：从项目数据库读取所有任务信息
2. **按状态分类**：将任务分类为待处理、进行中、已完成等状态
3. **生成 Markdown**：将任务信息转换为 Markdown 格式，包含统计信息
4. **保存文件**：将生成的 Markdown 写入到指定输出文件

## 命令执行方式

### 使用方法

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task-export <output-file>
```

### 执行时机

- 需要版本控制任务进度
- 生成项目状态报告
- 导出任务供他人审查
- 定期备份项目任务数据

### 执行参数

| 参数 | 说明 | 类型 | 默认值 |
|------|------|------|--------|
| `output-file` | 输出文件路径（必填）| string | - |

**输出文件规则**：
- 如果是相对路径，相对于项目根目录
- 如果只提供文件名，导出到 `.claude/` 目录
- 支持任意路径：`docs/`、`.claude/`、`./` 等

### 命令说明

- 导出包含所有任务的完整信息
- 自动按状态分组展示
- 包含任务统计信息（总数、各状态数量）
- 支持自定义输出路径

## 相关Skills（可选）

本命令无依赖Skills。

## 依赖脚本

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task-export "$@"
```

## 示例

### 基本用法

```bash
# 导出到 .claude/ 目录（推荐）
uvx --from git+https://github.com/lazygophers/ccplugin task-export tasks.md
```

### 带参数的用法

```bash
# 导出到指定目录
uvx --from git+https://github.com/lazygophers/ccplugin task-export docs/project-tasks.md
uvx --from git+https://github.com/lazygophers/ccplugin task-export .claude/tasks-2025-01-06.md

# 导出到项目根目录
uvx --from git+https://github.com/lazygophers/ccplugin task-export ./tasks.md
```

## 检查清单

在执行导出前，确保满足以下条件：

- [ ] 项目任务数据库已存在
- [ ] 已确定输出文件路径和文件名
- [ ] 输出目录具有写入权限
- [ ] 无需要保留的已有导出文件（将被覆盖）

## 注意事项

- **文件覆盖**：如果输出文件已存在，将被覆盖，无法恢复
- **路径建议**：推荐导出到 `.claude/` 目录，便于 AI 访问和版本控制
- **文件名**：建议使用有意义的名称如 `tasks.md` 或 `project-status.md`
- **目录路径**：自动创建不存在的目录

## 其他信息

### 输出格式

导出的 Markdown 文件包含以下结构：

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

### 性能考虑

- 小型项目（<100任务）：快速完成
- 中型项目（100-1000任务）：通常需要 1-2 秒
- 大型项目（>1000任务）：可能需要更长时间

### 用途示例

- **进度报告**：定期导出生成项目状态报告
- **版本控制**：导出到 `.claude/` 并添加到 git，跟踪任务历史
- **分享协作**：导出供团队成员审查项目进度
- **备份**：定期导出作为任务数据备份
