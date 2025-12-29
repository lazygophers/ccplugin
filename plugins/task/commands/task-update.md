---
name: task-update
description: 更新任务状态或属性
---

# 更新任务

更新现有任务的各种属性。

## 可更新字段

- **status**: open / in_progress / blocked / deferred / closed
- **title**: 任务标题
- **description**: 任务描述
- **priority**: 0-4
- **assignee**: 负责人
- **acceptance_criteria**: 验收标准
- **tags**: 标签列表

## 常见操作

### 开始处理任务
```
将任务 tk-xxx 的状态更新为 in_progress
```

### 标记为阻塞
```
将任务 tk-xxx 标记为 blocked，原因：等待API文档
```

### 分配任务
```
将任务 tk-xxx 分配给 developer@example.com
```

### 提高优先级
```
将任务 tk-xxx 的优先级提升到 0 (critical)
```

### 更新验收标准
```
为任务 tk-xxx 添加验收标准：
1. 用户可以登录
2. 登录失败显示错误
3. 登录成功跳转首页
```

### 修改标题
```
将任务 tk-xxx 的标题改为"实现用户登录和注册功能"
```

## 批量更新

```
同时更新任务 tk-xxx 的多个字段：
- status: in_progress
- priority: 1
- assignee: developer@example.com
```

## 快速状态切换

### 开始工作
```
开始处理任务 tk-xxx
```

### 完成任务
```
关闭任务 tk-xxx
```

### 重新打开
```
重新打开任务 tk-xxx
```

## 提示

- 更新状态时建议同时更新描述，记录变更原因
- blocked 状态应该说明阻塞原因
- 验收标准帮助明确任务完成标准
- 使用 `task_close` 而不是 `task_update(status="closed")` 来完成任务
