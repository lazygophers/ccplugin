---
description: 记忆桥接 - 连接 MindFlow 与 Memory 插件，三层记忆存储和智能检索
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:memory-bridge) - 记忆桥接

MindFlow Loop与Memory插件的适配层：版本隔离、三层记忆(短期/情节/语义)、智能检索、自动管理。

## 三层记忆

| 层 | URI模式 | 生命周期 | 内容 | 优先级 |
|----|---------|---------|------|--------|
| 短期(Working) | `task://sessions/{id}` | 当前会话 | 任务上下文/子任务状态/临时变量 | 0(最高) |
| 情节(Episodic) | `workflow://task-episodes/{type}/{id}` | 永久 | 计划/结果/用时/agents/skills | 成功3/失败4 |
| 语义(Semantic) | `project://knowledge/{domain}/{topic}` | 永久 | 架构模式/最佳实践/技术栈/ADR | 1-2(核心) |

## 核心API

| API | 时机 | 说明 |
|-----|------|------|
| `load_task_memories(user_task, session_id?)` | 初始化/规划 | 返回{working, episodic, semantic} |
| `save_task_episode(user_task, plan, result, ...)` | 完成/失败 | 保存情节，返回episode_id |
| `update_working_memory(session_id, phase, context)` | 阶段转换 | 更新短期记忆 |
| `search_failure_patterns(failure_reason, task_type?)` | Adjuster | 检索相似失败+恢复策略 |
| `extract_failure_patterns(session_id)` | Finalization | 提取失败模式{pattern_id,signature,occurrences,fixes} |
| `match_failure_to_patterns(failure)` | Adjuster | 匹配当前失败→历史模式(pattern,confidence) |
| `load_patterns_from_memory()` | 初始化 | 加载所有历史模式 |

## Loop集成

- **初始化**：`load_task_memories()` → 显示episodic/semantic
- **Planner**：注入episodic+semantic记忆到prompt
- **完成**：`save_task_episode(result="success")`
- **Adjuster**：`search_failure_patterns()` → 注入失败模式

## 注意事项

依赖Memory插件 | URI遵循memory-schema.md | 避免存储敏感信息 | 定期清理低价值记忆

文档：[API详情](./api-details.md) | [数据模型](./memory-schema.md) | [检索策略](./retrieval-strategy.md)
