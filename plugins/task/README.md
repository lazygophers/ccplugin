# Task Plugin - 任务管理插件

> 版本：0.2.0 | 基于 MCP 的任务管理系统，支持 CRUD、依赖管理和统计功能

开发任务的创建、管理和依赖跟踪系统。

## 功能特性

### ✅ 核心功能 (v0.2.0)

**任务管理**:
- **任务 CRUD** - 创建、查询、更新、关闭、重新打开、删除
- **任务列表** - 支持状态、类型、优先级、标签、负责人等多维度过滤
- **任务详情** - 完整的任务信息展示，包含依赖关系

**依赖管理**:
- **依赖添加/移除** - 管理任务间的依赖关系
- **依赖类型** - 支持 blocks、related、parent-child、discovered-from
- **依赖查询** - 查看任务的所有依赖和被依赖关系

**查询工具**:
- **就绪任务** - 查找没有阻塞依赖的可执行任务
- **阻塞任务** - 查找被依赖阻塞的任务
- **任务统计** - 按状态、类型、优先级统计任务分布

**工作空间**:
- **多工作空间隔离** - 每个项目独立数据库
- **工作空间管理** - 初始化、查看信息、删除
- **安全验证** - 防止路径穿越和敏感目录访问

### 📊 技术实现

- **当前版本 (v0.2.0)**:
  - ✅ SQLAlchemy 2.0 持久化存储
  - ✅ Alembic 数据库迁移
  - ✅ Repository 模式数据访问
  - ✅ 完整的单元测试（70+ 测试用例，目标覆盖率 ≥95%）

- **计划版本**:
  - v0.3.0 - 依赖图算法优化（NetworkX）
  - v0.4.0 - 状态流转引擎
  - v0.5.0 - 优先级调度器和报表

## 安装

### 前置要求

- Python ≥ 3.10
- uv 包管理器（推荐）或 pip
- Claude Code ≥ 1.0.0

### 安装步骤

```bash
# 1. 进入插件目录
cd plugins/task

# 2. 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

# 3. 安装依赖（包含开发依赖）
uv pip install -e ".[dev]"

# 4. 验证安装
uv run python -m task --help

# 5. 运行测试
uv run pytest -v
```

### 配置 Claude Code

在 `~/.claude/settings.json` 或项目的 `.claude-plugin/plugin.json` 中添加：

```json
{
  "mcpServers": {
    "task": {
      "command": "uv",
      "args": ["run", "python", "-m", "task"],
      "env": {
        "LOG_LEVEL": "INFO",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## 快速开始

### 基本使用

```
在 Claude Code 中：

# 创建任务
创建一个任务：实现用户认证功能

# 列出任务
列出所有任务

# 查看详情
显示任务 tk-xxx 的详情

# 更新任务
更新任务 tk-xxx：状态改为 in_progress

# 关闭任务
关闭任务 tk-xxx
```

### 依赖管理

```
# 添加依赖
添加依赖：任务 tk-aaa 依赖任务 tk-bbb

# 查看就绪任务
列出所有就绪任务

# 查看阻塞任务
列出所有被阻塞的任务
```

### 工作空间管理

```
# 初始化工作空间
初始化工作空间：/path/to/project

# 查看工作空间信息
显示工作空间信息
```

详细使用说明请参考 [快速开始指南](./docs/快速开始.md)。

## 插件集成

Task Plugin 可以与其他 Claude Code 插件集成，提供更强大的任务管理能力。

### 支持的集成

- **Context Plugin** - 保存任务讨论和决策到会话上下文
- **Memory Plugin** - 将任务知识存储到知识图谱
- **Knowledge Plugin** - 添加任务文档到向量数据库

### 快速示例

```python
from task.integration.context import get_context_integration
from task.integration.memory import get_memory_integration
from task.integration.knowledge import get_knowledge_integration

# Context: 保存任务讨论
ctx = get_context_integration()
await ctx.save_task_context(
    task_id="tk-001",
    content="讨论了实现方案",
    role="assistant"
)

# Memory: 存储技术决策
mem = get_memory_integration()
await mem.store_task_decision(
    task_id="tk-001",
    decision="使用 JWT 身份验证",
    tags=["authentication"]
)

# Knowledge: 添加文档
kb = get_knowledge_integration()
await kb.add_task_documentation(
    task_id="tk-001",
    content="实现文档",
    source="技术文档"
)
```

### 集成特性

- ✅ 集成接口定义 (v0.1.0)
- ✅ 辅助类实现 (v0.1.0)
- ✅ 单元测试 (21 个测试)
- ⏳ MCP 跨插件调用 (v0.2.0+)
- ⏳ 自动同步和推荐 (v0.2.0+)

详细文档:
- [集成指南](./examples/integration.md) - 完整使用示例和工作流
- [集成 API](./src/task/integration/README.md) - API 参考文档

## 开发

### 项目结构

```
plugins/task/
├── .claude-plugin/
│   └── plugin.json          # 插件配置
├── src/task/
│   ├── __init__.py          # 公共 API
│   ├── __main__.py          # 入口点
│   ├── server.py            # MCP Server (14+ 工具)
│   ├── types.py             # Pydantic 类型定义
│   ├── models.py            # SQLAlchemy 模型
│   ├── database.py          # 数据库管理
│   ├── repository.py        # Repository 层
│   ├── mappers.py           # 数据映射器
│   └── workspace.py         # 工作空间管理
├── alembic/                 # 数据库迁移
│   ├── versions/            # 迁移脚本
│   └── env.py               # Alembic 环境
├── tests/                   # 测试套件（70+ 测试）
│   ├── conftest.py          # pytest fixtures
│   ├── test_repository.py  # Repository 测试
│   ├── test_mappers.py     # Mapper 测试
│   ├── test_database.py    # Database 测试
│   └── test_workspace.py   # Workspace 测试
├── docs/                    # 文档
│   ├── 快速开始.md
│   ├── 工具参考.md
│   ├── 架构设计.md
│   ├── 实现计划.md
│   └── 开发规范.md
├── pyproject.toml           # Python 配置
├── alembic.ini              # Alembic 配置
├── CHANGELOG.md             # 变更日志
└── README.md                # 本文件
```

### 开发工作流

```bash
# 代码格式化
uv run black src/

# 代码检查
uv run ruff check src/ --fix

# 类型检查（严格模式）
uv run mypy src/ --strict

# 运行所有测试
uv run pytest -v

# 测试覆盖率
uv run pytest --cov=src/task --cov-report=html
open htmlcov/index.html

# 运行特定测试
uv run pytest tests/test_repository.py -v
```

### 调试 MCP Server

```bash
# 直接运行
uv run python -m task

# 调试模式
export LOG_LEVEL=DEBUG
uv run python -m task
```

### 数据库迁移

```bash
# 创建新迁移
uv run alembic revision --autogenerate -m "描述变更"

# 升级到最新版本
uv run alembic upgrade head

# 降级一个版本
uv run alembic downgrade -1

# 查看迁移历史
uv run alembic history
```

## MCP 工具参考

Task Plugin 提供以下 MCP 工具：

| 类别 | 工具名 | 描述 |
|------|--------|------|
| **任务 CRUD** | `task_create` | 创建新任务 |
| | `task_list` | 列出和过滤任务 |
| | `task_show` | 显示任务详情 |
| | `task_update` | 更新任务属性 |
| | `task_close` | 关闭任务 |
| | `task_reopen` | 重新打开任务 |
| | `task_delete` | 删除任务 |
| **依赖管理** | `task_dep_add` | 添加依赖关系 |
| | `task_dep_remove` | 移除依赖关系 |
| | `task_dep_list` | 列出依赖关系 |
| **查询工具** | `task_ready` | 查找就绪任务 |
| | `task_blocked` | 查找阻塞任务 |
| | `task_stats` | 任务统计 |
| **工作空间** | `workspace_init` | 初始化工作空间 |
| | `workspace_info` | 工作空间信息 |

详细的工具参数和使用示例请参考 [工具参考文档](./docs/工具参考.md)。

## 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 运行环境 |
| mcp | ≥1.1.0 | MCP SDK |
| pydantic | ≥2.0 | 数据验证和类型安全 |
| sqlalchemy | ≥2.0 | ORM 框架 |
| alembic | ≥1.12.0 | 数据库迁移工具 |
| pytest | ≥7.0 | 测试框架 |
| black | ≥23.0 | 代码格式化 |
| ruff | ≥0.1.0 | 代码检查 |
| mypy | ≥1.0 | 类型检查 |

## 测试

### 测试套件

- **总测试文件**: 5 个（含 conftest.py）
- **总测试用例**: 70+ 个
- **目标覆盖率**: ≥ 95%
- **测试隔离**: 每个测试使用独立的临时数据库

### 测试覆盖范围

- ✅ Repository 层（25+ 测试）- CRUD、查询、事务
- ✅ Mapper 层（20+ 测试）- 数据转换、枚举、边界情况
- ✅ Database 层（10+ 测试）- 初始化、健康检查、优化
- ✅ Workspace 层（15+ 测试）- 隔离、安全、管理

### 运行测试

```bash
# 所有测试
uv run pytest

# 特定模块
uv run pytest tests/test_repository.py -v

# 详细输出
uv run pytest -v

# 覆盖率报告
uv run pytest --cov=src/task --cov-report=term-missing

# HTML 覆盖率报告
uv run pytest --cov=src/task --cov-report=html
open htmlcov/index.html

# 覆盖率要求
uv run pytest --cov=src/task --cov-fail-under=95
```

详细的测试说明请参考 [测试文档](./tests/README.md)。

## 路线图

### v0.2.0 (当前) - 存储实现
- [x] SQLAlchemy 数据库模型
- [x] Alembic 迁移系统
- [x] Repository 模式实现
- [x] 数据映射层
- [x] 工作空间管理
- [x] MCP 工具集成
- [x] 完整的单元测试（70+ 测试）
- [x] 详细文档

### v0.3.0 (计划) - 依赖管理增强
- [ ] NetworkX 图算法集成
- [ ] 依赖图可视化
- [ ] 循环依赖检测优化
- [ ] 拓扑排序
- [ ] 依赖影响分析

### v0.4.0 (计划) - 状态流转
- [ ] 状态机引擎
- [ ] 状态转换验证
- [ ] 自动状态推导
- [ ] 状态历史记录

### v0.5.0 (计划) - 调度与报表
- [ ] 优先级调度器
- [ ] 就绪任务队列
- [ ] 任务统计报表
- [ ] 完成率分析
- [ ] 性能指标

## 文档

- 📖 [快速开始](./docs/快速开始.md) - 安装、配置和基本使用
- 🛠️ [工具参考](./docs/工具参考.md) - MCP 工具详细说明
- 🏗️ [架构设计](./docs/架构设计.md) - 系统架构和设计决策
- 📋 [实现计划](./docs/实现计划.md) - 开发路线图
- 📏 [开发规范](./docs/开发规范.md) - 编码规范和最佳实践
- 🧪 [测试文档](./tests/README.md) - 测试套件说明
- 📝 [变更日志](./CHANGELOG.md) - 版本更新历史

## 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 支持

如有问题或建议，请在 [GitHub Issues](https://github.com/lazygophers/ccplugin/issues) 上创建 issue。

## 作者

luoxin

---

**版本**: 0.2.0
**最后更新**: 2025-12-28
**维护者**: luoxin
