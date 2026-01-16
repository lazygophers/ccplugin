---
name: task-best-practices
description: 任务管理最佳实践和工作流程指南 - 包括任务粒度、工作流程、依赖管理和导出策略
---

# 任务管理最佳实践和工作流程指南

## 工作流程

### 1. 项目开始时

创建初始任务列表：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "项目初始化" --type feature --acceptance "项目结构创建完成，数据库初始化成功"
uvx --from git+https://github.com/lazygophers/ccplugin task add "设计数据库架构" --type feature --depends "项目初始化" --acceptance "完成表设计、索引设计、关系设计"
uvx --from git+https://github.com/lazygophers/ccplugin task add "实现API接口" --type feature --depends "设计数据库架构" --acceptance "核心CRUD接口可用，通过单元测试"
uvx --from git+https://github.com/lazygophers/ccplugin task add "编写单元测试" --type test --depends "实现API接口"
uvx --from git+https://github.com/lazygophers/ccplugin task add "准备部署" --type config --depends "编写单元测试" --acceptance "Docker配置完成，部署脚本可用"
```

### 2. 每日工作

开始工作时：

```bash
# 查看待处理任务
uvx --from git+https://github.com/lazygophers/ccplugin task list pending

# 开始任务
uvx --from git+https://github.com/lazygophers/ccplugin task update <id> --status in_progress
```

完成工作时：

```bash
# 完成任务
uvx --from git+https://github.com/lazygophers/ccplugin task done <id>
```

### 3. 添加新需求

当用户提出新需求时：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "新需求描述" \
  --type feature \
  --description "详细说明" \
  --acceptance "明确的验收标准"
```

### 4. 处理 Bug

当发现 Bug 时：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "Bug描述" \
  --type bug \
  --description "复现步骤、影响范围" \
  --acceptance "修复后验证通过，回归测试无问题"
```

### 5. 任务跟踪

定期查看任务状态：

```bash
# 查看统计
uvx --from git+https://github.com/lazygophers/ccplugin task stats

# 按类型查看
uvx --from git+https://github.com/lazygophers/ccplugin task list --type bug

# 查看进行中的任务
uvx --from git+https://github.com/lazygophers/ccplugin task list in_progress
```

## 最佳实践

### 1. 任务粒度

✅ **好的任务**（1-3 天完成）：

- "实现用户登录功能"
- "添加用户注册表单验证"
- "编写登录 API 单元测试"

❌ **不好的任务**：

- "完成用户模块"（太宽泛）
- "写代码"（不明确）
- "修复 bug"（缺少上下文）

### 2. 任务描述

提供清晰的上下文：

```bash
uvx --from git+https://github.com/lazygophers/ccplugin task add "修复API超时问题" \
  --type bug \
  --description "生产环境/api/users接口在并发>100时超时，需要优化查询性能" \
  --acceptance "并发100时响应时间<2秒，成功率>99%"
```

### 3. 验收标准

每个任务都应该有清晰的验收标准：

✅ **好的验收标准**：

- 具体、可验证
- 包含明确的完成条件
- 可以通过测试验证

示例：

```bash
--acceptance "用户可以使用邮箱、手机号注册并完成验证"
--acceptance "并发100时响应时间<2秒，成功率>99%"
--acceptance "单元测试覆盖率>80%，所有测试通过"
```

❌ **不好的验收标准**：

- "完成功能"（太模糊）
- "代码质量好"（无法验证）

### 4. 任务类型选择

根据任务性质选择合适的类型：

- **feature** - 新功能开发、功能增强
- **bug** - 缺陷修复、错误修复
- **refactor** - 代码重构、性能优化（不改功能）
- **test** - 测试相关（单元测试、集成测试）
- **docs** - 文档编写、API 文档
- **config** - 配置变更、环境设置

### 5. 依赖关系

使用依赖关系管理任务顺序：

```bash
# 基础任务
uvx --from git+https://github.com/lazygophers/ccplugin task add "设计数据库" --type feature

# 依赖任务
uvx --from git+https://github.com/lazygophers/ccplugin task add "实现用户API" --type feature --depends "设计数据库"
uvx --from git+https://github.com/lazygophers/ccplugin task add "实现前端页面" --type feature --depends "实现用户API"

# 测试任务
uvx --from git+https://github.com/lazygophers/ccplugin task add "编写测试用例" --type test --depends "实现用户API,实现前端页面"
```

注意：

- 依赖任务必须是已存在的任务 ID
- 多个依赖用逗号分隔
- 依赖表示前置任务必须完成后才能开始当前任务

### 6. 定期导出

每日或每周导出任务到 Git：

```bash
/task-export "tasks-$(date +%Y-%m-%d).md"
git add "tasks-$(date +%Y-%m-%d).md"
git commit -m "任务更新 - $(date +%Y-%m-%d)"
```

### 7. 导出归档

重要里程碑导出任务：

```bash
/task-export "tasks-milestone-1.md"
git add "tasks-milestone-1.md"
git commit -m "里程碑1任务归档"
```

## 参考资源

- [插件 README](${CLAUDE_PLUGIN_ROOT}/README.md)
- [命令文档](${CLAUDE_PLUGIN_ROOT}/commands/task.md)
