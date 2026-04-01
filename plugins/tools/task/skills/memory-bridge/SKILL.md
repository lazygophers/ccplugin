---
description: "记忆桥接 - 连接MindFlow与Memory插件的适配层，管理短期/情节/语义三层记忆，支持版本隔离和智能检索"
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

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

## Graceful Fallback

Memory 插件不可用时的处理策略：

1. **检测**：初始化阶段调用 `load_task_memories()` 失败时，判定 Memory 插件不可用
2. **提示用户安装**：输出 `[MindFlow·Reflection] Memory 插件未安装，记忆功能受限。安装方式：/install memory`，询问用户是否安装
3. **用户选择不安装**：降级为本地文件系统 `.claude/rules/`，记忆以 Markdown 文件存储（如 `.claude/rules/task-memories.md`）
4. **降级模式限制**：本地文件不支持语义检索和模式匹配，仅支持读写操作；`search_failure_patterns()` 和 `match_failure_to_patterns()` 返回空结果
5. **核心原则**：记忆操作失败不阻断 Loop 流程，降级后继续执行

## 记忆匹配规则

历史记忆匹配采用关键词匹配策略，按以下维度检索：

| 维度 | 匹配方式 | 权重 | 示例 |
|------|---------|------|------|
| 任务类型 | 精确匹配 | 40% | `feature`/`bugfix`/`refactor`/`exploration` |
| 技术栈 | 包含匹配 | 30% | `React`/`Go`/`Python` |
| 错误类型 | 精确匹配 | 30% | `execution_error`/`timeout`/`validation_failed` |

**匹配流程**：
1. 从情节记忆中按任务类型筛选候选
2. 在候选中按技术栈关键词过滤
3. （失败场景）按错误类型匹配历史失败模式
4. 返回匹配度最高的 3 条记录

**降级模式**：本地文件系统仅支持按文件名关键词查找，不支持多维度匹配。

## 记忆清理规则

**低价值判定标准**（同时满足以下条件）：
- 创建时间 >30 天
- 最近 30 天未被访问（未命中任何匹配查询）
- 属于失败任务的情节记忆（`result="failed"`）且无被后续任务引用

**清理策略**：
1. Finalizer 阶段自动扫描符合条件的记忆条目
2. 列出待清理项（URI + 创建时间 + 任务摘要）
3. 不自动删除，仅标记为 `deprecated`
4. 用户可通过 `/memory cleanup` 确认删除

**永不清理**：成功任务的情节记忆、语义记忆（知识/模式）、用户手动创建的记忆

## 注意事项

依赖Memory插件（推荐安装） | URI遵循memory-schema.md | 避免存储敏感信息

文档：[API详情](./api-details.md) | [数据模型](./memory-schema.md) | [检索策略](./retrieval-strategy.md)

<!-- /STATIC_CONTENT -->
