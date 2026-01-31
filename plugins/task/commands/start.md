---
name: start
description: 开始执行任务 - 将任务从 todo.md 移动到 in-progress.md
---

# 开始执行任务

当准备开始执行任务时，将其从待完成状态移动到进行中状态。

## 工作流程

### 第 1 步：选择任务

从 `@.claude/task/todo.md` 中选择要开始的任务。

### 第 2 步：移动任务

1. 复制任务内容（从 todo.md）
2. 删除原任务
3. 粘贴到 `@.claude/task/in-progress.md`

### 第 3 步：添加进度字段

```markdown
- **进展**: 0% 已完成 (或初始进度)
- **完成的验收标准**:
  - [ ] 标准 1
  - [ ] 标准 2
- **下一步**: 接下来的工作步骤
```

## 开始任务示例

### 从 todo.md

```markdown
### [P1] TASK-001 实现用户认证 API

- **类别**: feature
- **描述**: 在后端实现基于 JWT 的用户认证系统
- **验收标准**:
  - [ ] 实现用户注册 API
  - [ ] 实现用户登录 API
  - [ ] 实现令牌刷新 API
  - [ ] 编写单元测试
```

### 到 in-progress.md

```markdown
### [P1] TASK-001 实现用户认证 API

- **类别**: feature
- **描述**: 在后端实现基于 JWT 的用户认证系统
- **进展**: 10% 已完成（完成了项目设置和数据库配置）
- **完成的验收标准**:
  - [ ] 实现用户注册 API
  - [ ] 实现用户登录 API
  - [ ] 实现令牌刷新 API
  - [ ] 编写单元测试
- **下一步**:
  1. 实现用户注册 API 端点
  2. 添加 JWT 令牌生成逻辑
  3. 编写登录功能测试
```

## 建议

- 同时进行的任务不超过 3 个
- 选择高优先级或有依赖的任务优先开始
- 定期更新进度（参考：@/task:task-skills/update）

## 相关资源

- **任务规范**：[@/task:task-skills/reference.md](../../skills/task-skills/reference.md) - 详细的组织规范
- **快速开始**：[@/task:task-skills/SKILL.md](../../skills/task-skills/SKILL.md) - 任务系统概念
- **任务示例**：[@/task:task-skills/examples/in-progress.md](../../skills/task-skills/examples/in-progress.md) - 实际示例
