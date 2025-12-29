---
name: task-list
description: 列出任务（支持过滤）
---

# 列出任务

显示任务列表，支持多种过滤条件。

## 可用过滤器

- **status**: open / in_progress / blocked / deferred / closed
- **task_type**: bug / feature / task / epic / chore
- **priority**: 0-4
- **assignee**: 负责人邮箱或用户名
- **limit**: 返回的最大任务数（默认 20）
- **brief**: true/false（默认 true，简化模式）

## 快速命令

### 查看所有任务
```
显示所有任务（简化模式）
```

### 查看进行中的任务
```
列出所有状态为 in_progress 的任务
```

### 查看我的任务
```
列出负责人为 developer@example.com 的任务
```

### 查看高优先级任务
```
列出优先级为 0 (critical) 和 1 (high) 的任务
```

### 查看详细信息
```
列出所有任务，使用详细模式（brief=false）
```

## 组合过滤器

```
列出我负责的、进行中的、高优先级任务
- assignee: developer@example.com
- status: in_progress
- priority: 1
```
