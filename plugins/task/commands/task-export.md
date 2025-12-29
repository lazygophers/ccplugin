---
description: 导出任务到文档
---

导出任务到 Markdown 文档，参数：$ARGUMENTS

**策略**：
1. 使用 `task_list` 或 `task_stats` 获取任务数据
2. 格式化为 Markdown 表格或列表
3. 保存到项目文档目录（建议：`docs/tasks.md` 或 `TASKS.md`）

**可选过滤**：status, priority, assignee, task_type
**输出格式**：
- **表格模式**：ID | 标题 | 状态 | 优先级 | 负责人
- **详细模式**：包含描述和依赖关系
- **统计模式**：基于 `task_stats` 生成摘要

**示例输出**：

```markdown
# 项目任务清单

生成时间：2025-12-29

## 任务统计
- 总任务数：15
- 待处理：5
- 进行中：3
- 已完成：7

## 待处理任务 (优先级排序)

| ID | 标题 | 优先级 | 负责人 | 标签 |
|----|------|--------|--------|------|
| tk-abc123 | 实现用户登录 | P1 | Alice | backend, auth |
| tk-def456 | 设计首页UI | P2 | Bob | frontend, design |

## 进行中任务

...
```
