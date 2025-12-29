---
name: task-create
description: 快速创建任务
---

# 创建任务

请提供以下信息创建新任务：

- **标题**（必填）: 任务的简短描述
- **描述**（可选）: 任务的详细说明
- **类型**（可选）: bug / feature / task / epic / chore（默认: task）
- **优先级**（可选）: 0-4（0=critical, 1=high, 2=medium, 3=low, 4=backlog，默认: 2）
- **负责人**（可选）: 负责人邮箱或用户名
- **标签**（可选）: 任务标签列表

## 示例

```
标题: 实现用户登录功能
描述: 开发用户登录页面和 API，支持邮箱密码登录
类型: feature
优先级: 1
负责人: developer@example.com
标签: auth, frontend, backend
```

## 提示

- 优先级 0 (critical) 适用于紧急生产问题
- 使用 epic 类型创建大型功能集合
- 标签可以用于 Sprint 规划（如 "sprint-23"）
