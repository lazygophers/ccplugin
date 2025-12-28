# CC Plugin Marketplace - Claude Code 插件市场开发指南

> 项目：CC Plugin Marketplace - 插件市场 (4个独立插件)
> 技术栈：Python 3.10+ | MCP SDK | uv | Pydantic
> 版本：0.1.0

## 项目概述

CC Plugin Marketplace 是一个 Claude Code 插件市场，包含 4 个独立的插件：

1. **Memory Plugin** - 基于知识图谱的记忆管理
2. **Context Plugin** - 会话上下文持久化
3. **Task Plugin** - 开发任务管理
4. **Knowledge Plugin** - 向量数据库知识库

## 当前状态

### v0.1.0（当前版本）

**已实现**：
- ✅ 8 个 MCP 工具的完整接口
- ✅ 参数验证（Pydantic）
- ✅ 统一错误处理
- ✅ 配置管理（环境变量）
- ✅ 单元测试（10/10 通过，75% 覆盖率）

**待实现**：
- ⚠️ 数据持久化存储后端
- ⚠️ NetworkX 知识图谱（记忆）
- ⚠️ SQLAlchemy 关系存储（上下文/任务）
- ⚠️ ChromaDB 向量检索（知识库）

## 项目结构

```
ccplugin/                    # 插件市场根目录
├── marketplace.json         # 市场元数据
├── README.md                # 市场说明
├── CLAUDE.md                # 本文件
├── LICENSE                  # MIT 许可证
├── plugins/                 # 独立插件
│   ├── memory/              # 记忆管理插件
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json
│   │   ├── src/memory/
│   │   │   ├── __init__.py
│   │   │   ├── __main__.py
│   │   │   ├── server.py
│   │   │   └── types.py
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   ├── context/             # 上下文管理插件
│   │   ├── .claude-plugin/
│   │   ├── src/context/
│   │   ├── tests/
│   │   └── README.md
│   ├── task/                # 任务管理插件
│   │   ├── .claude-plugin/
│   │   ├── src/task/
│   │   └── README.md
│   └── knowledge/           # 知识库管理插件
│       ├── .claude-plugin/
│       ├── src/knowledge/
│       └── README.md
└── docs/                    # 市场文档
    ├── 插件能力说明.md
    ├── MCP工具参考.md
    └── 快速开始.md
```

## 技术栈

### 已集成

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 运行环境 |
| mcp | ≥1.1.0 | Model Context Protocol SDK |
| pydantic | ≥2.0 | 数据验证和类型安全 |
| httpx | ≥0.24.0 | HTTP 客户端 |
| pytest | ≥7.0 | 测试框架 |
| black | ≥23.0 | 代码格式化 |
| ruff | ≥0.1.0 | 代码检查 |
| mypy | ≥1.0 | 类型检查 |

### 计划集成（v0.2.0+）

| 依赖 | 版本 | 用途 |
|------|------|------|
| chromadb | ≥0.4.0 | 向量数据库（知识库） |
| networkx | ≥3.0 | 知识图谱（记忆管理） |
| sqlalchemy | ≥2.0 | 关系数据库 ORM（上下文/任务） |

## 开发指南

### 环境设置

```bash
# 1. 克隆仓库
git clone https://github.com/lazygophers/ccplugin.git
cd ccplugin

# 2. 进入特定插件目录
cd plugins/memory  # 或 context, task, knowledge

# 3. 创建虚拟环境
uv venv
source .venv/bin/activate

# 4. 安装依赖
uv pip install -e ".[dev]"

# 5. 运行测试
uv run pytest -v
```

### 开发工作流

```bash
# 代码格式化
uv run black src/

# 代码检查
uv run ruff check src/ --fix

# 类型检查
uv run mypy src/

# 运行测试（带覆盖率）
uv run pytest --cov=src/market --cov-report=term-missing
```

### 调试 MCP Server

```bash
# 方式 1：直接运行
uv run python -m market.server

# 方式 2：调试模式
export LOG_LEVEL=DEBUG
uv run python -m market.server
```

## 配置说明

### 环境变量

```bash
# 功能开关（默认全部启用）
ENABLE_MEMORY=true       # 记忆管理
ENABLE_CONTEXT=true      # 上下文管理
ENABLE_TASK=true         # 任务管理
ENABLE_KNOWLEDGE=true    # 知识库管理

# 日志配置
LOG_LEVEL=INFO           # DEBUG/INFO/WARNING/ERROR/CRITICAL
DEBUG=false              # 调试模式

# 存储配置（v0.2.0+）
MARKET_STORAGE_PATH=./.market_data
VECTOR_DB_PATH=./.market_data/vectordb
GRAPH_DB_PATH=./.market_data/graphdb

# 性能配置
MAX_TIMEOUT=30.0         # 最大超时（秒）
```

### 插件配置（.claude-plugin/plugin.json）

```json
{
  "mcpServers": {
    "market-server": {
      "command": "uv",
      "args": ["run", "python", "-m", "market.server"],
      "env": {
        "LOG_LEVEL": "info",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## MCP 工具说明

### 记忆管理（2 个工具）

| 工具名 | 参数 | 状态 | 用途 |
|-------|------|------|------|
| `memory_store` | content, tags, metadata | ✅ 框架 | 存储记忆项 |
| `memory_search` | query, tags, limit | ✅ 框架 | 搜索记忆 |

### 上下文管理（2 个工具）

| 工具名 | 参数 | 状态 | 用途 |
|-------|------|------|------|
| `context_save` | session_id, content, role | ✅ 框架 | 保存上下文 |
| `context_retrieve` | session_id, limit | ✅ 框架 | 检索上下文 |

### 任务管理（2 个工具）

| 工具名 | 参数 | 状态 | 用途 |
|-------|------|------|------|
| `task_create` | title, description, priority, tags | ✅ 框架 | 创建任务 |
| `task_list` | status, tags | ✅ 框架 | 列出任务 |

### 知识库管理（2 个工具）

| 工具名 | 参数 | 状态 | 用途 |
|-------|------|------|------|
| `knowledge_add` | content, source, metadata | ✅ 框架 | 添加知识 |
| `knowledge_search` | query, limit | ✅ 框架 | 搜索知识 |

## 开发路线图

### v0.2.0 - 记忆管理（计划）
- [ ] NetworkX 知识图谱存储
- [ ] 记忆关系建模（节点+边）
- [ ] 标签索引和图遍历查询
- [ ] 记忆合并去重算法

### v0.3.0 - 上下文管理（计划）
- [ ] SQLAlchemy 会话持久化
- [ ] 上下文压缩算法
- [ ] 智能摘要生成
- [ ] 跨会话上下文恢复

### v0.4.0 - 任务管理（计划）
- [ ] 任务依赖关系图
- [ ] 状态流转规则引擎
- [ ] 优先级调度器
- [ ] 任务统计和报表

### v0.5.0 - 知识库管理（计划）
- [ ] ChromaDB 向量存储
- [ ] 语义相似度搜索优化
- [ ] 多源知识同步
- [ ] 知识图谱整合

## 代码规范

### Python 编码规范

- **命名**：遵循 PEP 8（snake_case 变量/函数，PascalCase 类）
- **类型注解**：所有函数必须有类型注解
- **文档字符串**：公开 API 必须有 docstring
- **行长度**：最大 100 字符（black 配置）

### Git 提交规范

```
<类型>: <简短描述>

<详细描述>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**类型**：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `test`: 测试相关
- `refactor`: 重构
- `chore`: 杂项

## 测试策略

### 单元测试

- 位置：`tests/test_server.py`
- 覆盖：所有 MCP 工具接口
- 框架：pytest + pytest-asyncio
- 目标覆盖率：≥80%

### 集成测试（v0.2.0+）

- 存储后端集成测试
- 端到端工具调用测试
- 并发安全测试

### 运行测试

```bash
# 运行所有测试
uv run pytest -v

# 运行特定测试
uv run pytest tests/test_server.py::test_memory_store -v

# 生成覆盖率报告
uv run pytest --cov=src/market --cov-report=html
```

## 文档

### 用户文档

- **[快速开始](./docs/快速开始.md)** - 安装和基本使用
- **[MCP工具参考](./docs/MCP工具参考.md)** - 工具详细说明
- **[插件能力说明](./docs/插件能力说明.md)** - Claude Code 插件系统能力

### 开发文档

- **[README.md](./README.md)** - 项目总览
- **[CLAUDE.md](./CLAUDE.md)** - 本文件（开发指南）
- **代码注释** - 源代码中的 docstring

## 贡献指南

### 开发流程

1. Fork 仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 编写代码和测试
4. 确保测试通过：`uv run pytest`
5. 格式化代码：`uv run black src/`
6. 提交变更：`git commit -m "feat: add amazing feature"`
7. 推送分支：`git push origin feature/amazing-feature`
8. 创建 Pull Request

### 代码审查标准

- ✅ 所有测试必须通过
- ✅ 代码覆盖率不低于当前水平
- ✅ 遵循代码规范（black + ruff）
- ✅ 类型检查通过（mypy）
- ✅ 有清晰的提交消息
- ✅ 更新相关文档

## 故障排查

### 常见问题

#### MCP Server 无法启动

**症状**：Claude Code 报告 MCP server 启动失败

**排查步骤**：
1. 检查 Python 版本：`python --version`（应 ≥3.10）
2. 检查依赖安装：`uv pip list | grep mcp`
3. 查看日志：设置 `LOG_LEVEL=DEBUG` 重新启动
4. 验证路径：确认 `.claude-plugin/plugin.json` 中的路径正确

#### 工具未显示

**症状**：调用工具时提示工具不存在

**排查步骤**：
1. 检查功能开关：`echo $ENABLE_MEMORY`（应为 `true`）
2. 重启 Claude Code
3. 检查插件配置：`~/.claude/settings.json`

#### 导入错误

**症状**：`ModuleNotFoundError: No module named 'market'`

**解决方法**：
```bash
# 确保在虚拟环境中
source .venv/bin/activate

# 重新安装
uv pip install -e ".[dev]"
```

## 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

## 联系方式

- **作者**：luoxin
- **仓库**：https://github.com/lazygophers/ccplugin
- **问题反馈**：https://github.com/lazygophers/ccplugin/issues

---

**最后更新**：2025-01-15
**维护者**：luoxin
**版本**：0.1.0
