---
name: task-stats
description: 显示任务统计信息
---

# 任务统计

显示任务的完整统计信息，包括：

## 统计维度

### 按状态
- 总任务数
- 待处理（open）
- 进行中（in_progress）
- 已阻塞（blocked）
- 已延期（deferred）
- 已完成（closed）

### 按类型
- Bug 数量
- Feature 数量
- Task 数量
- Epic 数量
- Chore 数量

### 按优先级
- Critical (0)
- High (1)
- Medium (2)
- Low (3)
- Backlog (4)

## 使用场景

### Sprint 回顾
```
显示 Sprint 23 的统计信息
```

### 项目进度报告
```
生成本周的任务统计报告
```

### 团队健康度检查
```
检查是否有太多阻塞任务或积压任务
```

## 快速命令

```
显示任务统计
```

```
查看项目整体进度
```

## 提示

- 大量 blocked 任务可能表示依赖管理问题
- 高比例的 backlog 任务可能需要优先级重评估
- closed 任务比例反映团队的交付速度
