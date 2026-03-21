---
description: 记忆桥接 - 连接 MindFlow 任务系统与 Memory 插件，提供三层记忆存储和智能检索
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:memory-bridge) - 记忆桥接

<overview>

记忆桥接（Memory Bridge）作为 MindFlow Loop 与 Memory 插件之间的适配层，提供统一的记忆管理接口，隔离 Memory 插件版本差异，支持任务规划过程中的知识积累和经验复用。

**核心价值**:
- **版本隔离**: 封装 Memory 插件 API 变化，保持 Loop 稳定性
- **三层记忆**: 支持短期记忆（当前会话）、情节记忆（成功/失败经验）、语义记忆（项目知识）
- **智能检索**: 基于任务相似度和失败模式匹配，推荐相关记忆
- **自动管理**: 在 Loop 生命周期中自动加载和保存记忆

**使用场景**:
- **规划阶段**: 加载相似任务的规划模式和架构决策
- **执行失败**: 检索失败模式和恢复策略
- **任务完成**: 保存成功经验和优化建议

**文档导航**:
- **API 详细实现** → [api-details.md](./api-details.md)
- **三层记忆数据模型** → [memory-schema.md](./memory-schema.md)
- **检索策略** → [retrieval-strategy.md](./retrieval-strategy.md)

</overview>

<memory-layers>

## 三层记忆架构

基于 [Agentic Context Engineering](https://arxiv.org/html/2602.20478v1) 中的记忆层次，Memory Bridge 实现三层记忆系统（详见 `memory-schema.md`）：

### 1. 短期记忆（Working Memory）

**URI 路径**: `task://sessions/{session_id}`
**生命周期**: 当前会话，任务完成后归档
**存储内容**: 当前任务上下文、正在执行的子任务状态、临时变量、用户交互记录
**更新时机**: 会话开始时创建、每个阶段转换时更新、会话结束时归档

### 2. 情节记忆（Episodic Memory）

**URI 路径**: `workflow://task-episodes/{task_type}/{episode_id}`
**生命周期**: 永久保存，定期归档低价值记录
**存储内容**: 任务类型和关键参数、执行计划和分解策略、成功/失败结果和原因、用时/迭代次数/停滞次数、使用的 Agent 和 Skills 组合
**更新时机**: 任务完成时保存成功情节、任务失败时保存失败情节和修复方案

### 3. 语义记忆（Semantic Memory）

**URI 路径**: `project://knowledge/{domain}/{topic}`
**生命周期**: 永久保存，手动维护
**存储内容**: 项目架构模式和约定、代码风格和最佳实践、技术栈版本和依赖关系、常见问题和解决方案、架构决策记录（ADR）
**更新时机**: 发现新的架构决策时、项目约定变更时、积累足够多的情节记忆后提炼

</memory-layers>

<api>

## 核心 API

完整实现参见 [api-details.md](./api-details.md)

### 1. load_task_memories()

**功能**: 在 Loop 初始化或规划阶段加载相关记忆

**调用时机**: Loop 初始化阶段、Planner 信息收集阶段

**返回**: `{ working_memory, episodic_memory, semantic_memory }`

### 2. save_task_episode()

**功能**: 任务完成或失败时保存情节记忆

**调用时机**: Loop 完成阶段（任务成功）、Adjuster 失败调整后（任务失败）

**返回**: episode_id（情节记忆 ID）

### 3. update_working_memory()

**功能**: 更新短期记忆（当前会话状态）

**调用时机**: 每个阶段转换时

**返回**: True（成功）/ False（失败）

### 4. search_failure_patterns()

**功能**: 检索失败模式和恢复策略（用于 Adjuster）

**调用时机**: Adjuster 分析失败原因时

**返回**: 相似失败情节列表和恢复策略

</api>

<integration>

## 与 Loop 的集成

详细示例参见 [api-details.md](./api-details.md#与-loop-的完整集成)

### 初始化阶段

```python
task_memories = load_task_memories(user_task, session_id=session_id)
```

### Planner 集成

```python
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

【情节记忆】相似任务参考：{format_episodic_memories(task_memories["episodic_memory"])}
【语义记忆】项目知识：{format_semantic_memories(task_memories["semantic_memory"])}
...
"""
)
```

### 完成阶段

```python
save_task_episode(user_task=user_task, task_type=task_type, plan=planner_result, result="success", ...)
```

### Adjuster 集成

```python
adjustment_result = Agent(
    agent="task:adjuster",
    prompt=f"""执行失败调整：

【失败模式】历史相似失败：{format_failure_patterns(search_failure_patterns(failure_reason, task_type))}
...
"""
)
```

</integration>

<notes>

## 注意事项

1. **依赖 Memory 插件**: Memory Bridge 需要 Memory 插件正确安装并初始化
2. **URI 命名规范**: 遵循 Memory 插件的 URI 命名空间约定（详见 `memory-schema.md`）
3. **优先级设置**:
   - 短期记忆：priority=0（最高，始终加载）
   - 情节记忆（成功）：priority=3（重要，按需加载）
   - 情节记忆（失败）：priority=4（重要，按需加载）
   - 语义记忆：priority=1-2（核心，自动加载）
4. **检索性能**: 大量情节记忆可能影响检索速度，建议定期归档旧记录
5. **隐私保护**: 避免在记忆中存储敏感信息（密码、密钥、个人数据）
6. **版本兼容**: Memory Bridge 封装了 Memory 插件 API，升级插件时需要测试兼容性
7. **记忆清理**: 定期清理低价值的情节记忆（失败且未修复、过时的知识）

</notes>
