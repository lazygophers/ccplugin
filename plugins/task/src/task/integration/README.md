# Task Plugin 集成模块

提供与其他 Claude Code 插件的集成功能。

## 概述

集成模块允许 Task Plugin 与 Context、Memory、Knowledge 等插件协同工作，实现：

- **上下文保存**: 保存任务讨论和决策到会话上下文
- **记忆管理**: 将任务知识存储到知识图谱
- **知识库**: 添加任务文档到向量数据库

## 模块结构

```
src/task/integration/
├── __init__.py         # 公共接口
├── context.py          # Context Plugin 集成
├── memory.py           # Memory Plugin 集成
├── knowledge.py        # Knowledge Plugin 集成
└── README.md           # 本文件
```

## 快速开始

### Context Plugin 集成

```python
from task.integration.context import get_context_integration

# 保存任务讨论
ctx = get_context_integration()
await ctx.save_task_context(
    task_id="tk-001",
    content="讨论了实现方案",
    role="assistant"
)

# 检索历史
contexts = await ctx.retrieve_task_context("tk-001")
```

### Memory Plugin 集成

```python
from task.integration.memory import get_memory_integration

# 存储技术决策
mem = get_memory_integration()
await mem.store_task_decision(
    task_id="tk-001",
    decision="使用 JWT 身份验证",
    tags=["authentication"]
)

# 搜索记忆
memories = await mem.search_task_memories("tk-001")
```

### Knowledge Plugin 集成

```python
from task.integration.knowledge import get_knowledge_integration

# 添加文档
kb = get_knowledge_integration()
await kb.add_task_documentation(
    task_id="tk-001",
    content="实现文档内容",
    source="技术文档"
)

# 搜索知识
results = await kb.search_task_knowledge("JWT")
```

## API 参考

### ContextIntegration

**save_task_context(task_id, content, role, metadata)**
- 保存任务上下文
- 参数:
  - task_id: 任务 ID
  - content: 上下文内容
  - role: "user" | "assistant"
  - metadata: 可选元数据

**retrieve_task_context(task_id, limit)**
- 检索任务上下文
- 返回: 上下文记录列表

**save_task_comment(task_id, comment, author)**
- 保存任务评论
- 参数:
  - task_id: 任务 ID
  - comment: 评论内容
  - author: 评论作者

**get_task_discussion(task_id)**
- 获取格式化的讨论历史
- 返回: Markdown 格式的讨论记录

### MemoryIntegration

**store_task_decision(task_id, decision, tags, metadata)**
- 存储技术决策
- 参数:
  - task_id: 任务 ID
  - decision: 决策内容
  - tags: 标签列表
  - metadata: 可选元数据

**store_task_learning(task_id, learning, tags)**
- 存储学习收获
- 参数:
  - task_id: 任务 ID
  - learning: 学习内容
  - tags: 标签列表

**store_task_solution(task_id, problem, solution, tags)**
- 存储问题解决方案
- 参数:
  - task_id: 任务 ID
  - problem: 问题描述
  - solution: 解决方案
  - tags: 标签列表

**search_task_memories(task_id, query, limit)**
- 搜索任务记忆
- 返回: 记忆列表

**get_task_knowledge(task_id)**
- 获取任务相关知识
- 返回: 格式化的知识列表

**search_similar_solutions(query, limit)**
- 搜索类似解决方案
- 返回: 解决方案列表

### KnowledgeIntegration

**add_task_documentation(task_id, content, source, metadata)**
- 添加任务文档
- 参数:
  - task_id: 任务 ID
  - content: 文档内容
  - source: 文档来源
  - metadata: 可选元数据

**add_task_solution(task_id, title, description, solution, tags)**
- 添加解决方案文档
- 参数:
  - task_id: 任务 ID
  - title: 方案标题
  - description: 问题描述
  - solution: 解决方案
  - tags: 标签列表

**search_task_knowledge(query, limit)**
- 搜索任务知识
- 返回: 知识列表

**search_similar_tasks(description, limit)**
- 搜索类似任务
- 返回: 类似任务列表

**add_task_lessons_learned(task_id, lessons, tags)**
- 添加经验教训
- 参数:
  - task_id: 任务 ID
  - lessons: 经验列表
  - tags: 标签列表

**get_task_references(task_id)**
- 获取参考文档
- 返回: 格式化的文档列表

## 集成状态

### v0.1.0 (当前)

✅ 已实现:
- 集成接口定义
- 辅助类实现
- 单元测试 (21 个)
- 使用文档

⏳ 待实现:
- MCP 跨插件调用
- 实际数据持久化
- 集成端到端测试

### v0.2.0+ (计划)

- [ ] 实现 MCP 跨插件通信协议
- [ ] 自动检测插件可用性
- [ ] 智能推荐相关知识
- [ ] 集成统一搜索界面

## 设计原则

### 1. 可选集成

集成是可选的,Task Plugin 可以独立运行:

```python
from task.integration import is_plugin_available

if await is_plugin_available("context"):
    # 使用集成
    await ctx.save_task_context(...)
else:
    # 降级处理
    pass
```

### 2. 优雅降级

集成失败不影响核心功能:

```python
try:
    await ctx.save_task_context(...)
except Exception as e:
    logger.warning(f"保存上下文失败: {e}")
    # 继续执行任务操作
```

### 3. 松耦合

使用辅助函数而非直接调用:

```python
# ✅ 推荐
ctx = get_context_integration()
await ctx.save_task_context(...)

# ❌ 不推荐
from context.server import handle_context_save
await handle_context_save(...)
```

### 4. 单一职责

每个集成模块只负责一个插件:

- `context.py`: 只处理 Context Plugin 集成
- `memory.py`: 只处理 Memory Plugin 集成
- `knowledge.py`: 只处理 Knowledge Plugin 集成

## 测试

### 运行测试

```bash
# 运行所有集成测试
uv run pytest tests/test_integration.py -v

# 运行特定测试
uv run pytest tests/test_integration.py::TestContextIntegration -v

# 测试覆盖率
uv run pytest tests/test_integration.py --cov=src/task/integration
```

### 测试覆盖

- Context 集成: 5 个测试
- Memory 集成: 7 个测试
- Knowledge 集成: 7 个测试
- 工作流测试: 2 个测试

**总计**: 21 个测试，全部通过

## 使用示例

详见:
- [集成指南](../../../examples/integration.md) - 完整使用示例
- [基本使用](../../../examples/basic_usage.md) - Task Plugin 基本功能
- [测试用例](../../../tests/test_integration.py) - 集成测试代码

## 常见问题

### Q: 集成是否必需？

A: 不是。Task Plugin 可以完全独立运行。集成是可选的增强功能。

### Q: 如何检查插件是否可用？

A: 使用 `is_plugin_available()` 函数（待实现）。当前版本返回 `False`。

### Q: 集成调用失败怎么办？

A: 建议使用 try-except 捕获异常，记录日志但不中断主流程。

### Q: 性能影响如何？

A: 集成调用是异步的，对主流程影响很小。建议批量操作以提高效率。

### Q: 如何添加新的集成？

A:
1. 在 `src/task/integration/` 创建新模块
2. 实现集成辅助类
3. 添加测试到 `tests/test_integration.py`
4. 更新本文档

## 贡献指南

欢迎贡献集成功能的改进:

1. Fork 仓库
2. 创建特性分支: `git checkout -b feature/new-integration`
3. 实现功能并测试
4. 提交 PR

## 许可证

MIT License - 详见 [LICENSE](../../../../LICENSE)

---

**最后更新**: 2025-01-15
**版本**: 0.1.0
