# Market Plugin MCP 工具参考

> 基于实际实现代码
> 版本：0.1.0
> 状态：框架实现（存储后端待开发）

## 概述

Market Plugin 当前提供 8 个 MCP 工具，分为 4 个功能类别。所有工具已完成接口实现和参数验证，存储后端将在后续版本实现。

## 工具清单

| 工具名称 | 类别 | 接口状态 | 存储后端 | 计划版本 |
|---------|------|---------|---------|---------|
| `memory_store` | 记忆管理 | ✅ 已实现 | ⚠️ 待开发 | v0.2.0 |
| `memory_search` | 记忆管理 | ✅ 已实现 | ⚠️ 待开发 | v0.2.0 |
| `context_save` | 上下文管理 | ✅ 已实现 | ⚠️ 待开发 | v0.3.0 |
| `context_retrieve` | 上下文管理 | ✅ 已实现 | ⚠️ 待开发 | v0.3.0 |
| `task_create` | 任务管理 | ✅ 已实现 | ⚠️ 待开发 | v0.4.0 |
| `task_list` | 任务管理 | ✅ 已实现 | ⚠️ 待开发 | v0.4.0 |
| `knowledge_add` | 知识库管理 | ✅ 已实现 | ⚠️ 待开发 | v0.5.0 |
| `knowledge_search` | 知识库管理 | ✅ 已实现 | ⚠️ 待开发 | v0.5.0 |

## 详细参考

详细的参数说明、返回值和使用示例，请参考代码文件：

**源文件位置**：`src/market/server.py`

### 工具定义位置

- 记忆管理：第 38-87 行
- 上下文管理：第 90-134 行
- 任务管理：第 137-188 行
- 知识库管理：第 191-229 行

### 处理器实现位置

- `_handle_memory_store`: 第 261-271 行
- `_handle_memory_search`: 第 273-283 行
- `_handle_context_save`: 第 286-296 行
- `_handle_context_retrieve`: 第 298-308 行
- `_handle_task_create`: 第 311-323 行
- `_handle_task_list`: 第 325-335 行
- `_handle_knowledge_add`: 第 338-348 行
- `_handle_knowledge_search`: 第 350-360 行

## 测试覆盖

所有工具均有单元测试覆盖：

**测试文件**：`tests/test_server.py`

```bash
# 运行测试
uv run pytest tests/test_server.py -v

# 测试结果
✓ test_memory_store          # 记忆存储测试
✓ test_memory_search         # 记忆搜索测试
✓ test_context_save          # 上下文保存测试
✓ test_context_retrieve      # 上下文检索测试
✓ test_task_create           # 任务创建测试
✓ test_task_list             # 任务列表测试
✓ test_knowledge_add         # 知识添加测试
✓ test_knowledge_search      # 知识搜索测试
```

## 配置控制

通过环境变量控制工具可用性：

```bash
# 启用/禁用功能模块
ENABLE_MEMORY=true       # 控制 memory_* 工具
ENABLE_CONTEXT=true      # 控制 context_* 工具
ENABLE_TASK=true         # 控制 task_* 工具
ENABLE_KNOWLEDGE=true    # 控制 knowledge_* 工具
```

禁用后，对应工具不会在 `list_tools()` 中返回。

## 当前行为

### v0.1.0（当前版本）

所有工具调用均返回确认消息，但不实际持久化数据：

**存储类工具**：
- ✅ 接受并验证参数
- ✅ 返回成功确认消息
- ⚠️ 不实际存储数据

**检索类工具**：
- ✅ 接受并验证参数
- ✅ 返回提示消息
- ⚠️ 不实际查询数据

### v0.2.0+（计划）

将连接实际存储后端并实现完整功能。详见项目路线图。

---

**代码文件**：
- 主实现：`src/market/server.py`
- 类型定义：`src/market/types.py`
- 配置管理：`src/market/config.py`
- 测试代码：`tests/test_server.py`

**参考文档**：
- [Claude Code 插件能力](./插件能力说明.md)
- [项目 README](../README.md)

---

**最后更新**：2025-01-15
**维护者**：luoxin
