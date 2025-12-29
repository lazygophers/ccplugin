# Task Plugin - 任务管理插件

> 版本：0.2.0 | 基于 MCP 的智能任务管理系统

完整的开发任务管理解决方案，提供任务创建、依赖管理、智能规划和拆解功能。

## ✨ 核心特性

### 🤖 智能 Agents（新增）

| Agent | 功能 | 使用场景 |
|-------|------|---------|
| **task-planner** | 需求分析 → 任务规划 | 接到新需求时调用 |
| **task-decomposer** | 大型任务 → 子任务拆解 | 任务过于复杂时调用 |

### ⚡ 自动化 Hooks（新增）

- **SessionStart hook**：会话开始时自动初始化工作空间（如需要）
- **真零配置**：新项目自动创建数据库，无需任何手动操作

### 📋 用户 Commands

| Command | 功能 | 说明 |
|---------|------|------|
| `/task-add` | 创建任务 | 支持 title/description/priority/tags |
| `/task-list` | 列出任务 | 多维度过滤（status/priority/type） |
| `/task-update` | 更新任务 | 修改状态/优先级/负责人 |
| `/task-ready` | 查找可执行任务 | 自动过滤被依赖阻塞的任务 |
| `/task-stats` | 任务统计 | 按状态/类型/优先级分布 |
| `/task-export` ✨ | 导出文档 | 生成 Markdown 任务清单 |

### 🛠️ MCP 工具（15个）

**任务管理**：
- `task_create`, `task_list`, `task_show`, `task_update`
- `task_close`, `task_reopen`, `task_delete`

**依赖管理**：
- `task_dep_add`, `task_dep_remove`, `task_dep_list`
- 支持依赖类型：blocks（硬阻塞）、related（软关联）、parent-child（层级）、discovered-from（发现）

**查询工具**：
- `task_ready`（就绪任务）、`task_blocked`（阻塞任务）、`task_stats`（统计）

**工作空间**：
- `workspace_init`, `workspace_info`

### 💾 技术实现

- ✅ SQLAlchemy 2.0 持久化存储
- ✅ Alembic 数据库迁移
- ✅ Repository 模式数据访问
- ✅ Pydantic 类型安全
- ✅ 70+ 单元测试（覆盖率 ≥95%）
- ✅ 多工作空间隔离

---

## 🚀 快速开始

### 典型工作流

```
1️⃣ 需求规划
   用户：请帮我规划"实现用户认证功能"的任务
   → Claude 调用 task-planner agent
   → 生成：5个结构化任务 + 依赖关系 + 优先级评估

2️⃣ 任务拆解
   用户：将 tk-001（设计认证架构）拆解为子任务
   → Claude 调用 task-decomposer agent
   → 生成：4个子任务 + 依赖链 + 并行建议

3️⃣ 执行跟踪
   用户：/task-ready
   → 显示：2个可立即执行的任务（tk-001-1, tk-006）

   用户：开始处理 tk-001-1
   → 更新任务状态为 in_progress

4️⃣ 进度查看
   用户：/task-stats
   → 显示：总任务9个，待处理6个，进行中1个，完成2个（22.2%）

5️⃣ 导出文档
   用户：/task-export
   → 生成：docs/tasks.md（Markdown 格式任务清单）
```

详细使用示例请参考 [使用示例文档](./docs/使用示例.md)。

---

## 📦 安装

### 前置要求

- Python ≥ 3.10
- uv 包管理器（推荐）或 pip
- Claude Code ≥ 1.0.0

### 方式 1：从 Marketplace 安装（推荐）

```bash
# 1. 在 Claude Code 中添加 marketplace
/plugin marketplace add lazygophers/ccplugin

# 2. 安装 task 插件
/plugin install task@cc-plugin-marketplace

# 3. 验证安装
/plugin list
/help  # 查看 task 相关命令
```

### 方式 2：本地开发安装

**步骤 1：安装 Python 依赖**

```bash
# 进入插件目录
cd plugins/task

# 创建虚拟环境
uv venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
uv pip install -e ".[dev]"

# 验证 MCP 服务器
uv run python -m task.server
```

**步骤 2：启动 Claude Code 并加载插件**

```bash
# 方式 A：启动时指定插件目录（推荐）
cd /path/to/ccplugin
claude --plugin-dir ./plugins/task

# 方式 B：使用插件命令安装（本地）
# 在 Claude Code 中执行：
/plugin marketplace add /path/to/ccplugin
/plugin install task@ccplugin --scope project
```

**步骤 3：验证安装**

在 Claude Code 中执行：

```bash
/plugin list              # 确认 task 插件已加载
/help                     # 查看可用命令
/agents                   # 查看 task-planner, task-decomposer
```

### 方式 3：项目级配置（团队协作）

在项目根目录创建 `.claude/settings.json`：

```json
{
  "plugins": {
    "task": {
      "enabled": true,
      "source": "lazygophers/ccplugin/plugins/task"
    }
  }
}
```

团队成员克隆项目后自动加载插件。

---

## 📖 核心功能详解

### 1. Agents - 智能规划与拆解

#### task-planner（任务规划专家）

**用途**：将模糊需求转化为结构化任务计划

**工作流程**：
1. 需求收集与澄清
2. 任务设计（分解、优先级、依赖）
3. 计划输出（创建任务、设置依赖）

**输出**：
- 任务概览（总数、优先级分布）
- 执行顺序建议
- 关键路径识别
- 风险提示

**调用方式**：
- 直接描述需求，Claude 会根据上下文自动调用
- 或明确要求："请用 task-planner 规划这个需求"

#### task-decomposer（任务拆解专家）

**用途**：将大型任务拆解为可管理的子任务

**拆解策略**：
- 按层次：前端 → 后端 → 数据库 → 测试 → 文档
- 按模块：用户模块 → 订单模块 → 支付模块
- 按阶段：设计 → 实现 → 测试 → 部署

**输出**：
- 任务树（父子关系）
- 子任务列表（含验收标准）
- 依赖关系链
- 并行执行建议

**调用方式**：
- 提供任务ID："将 tk-abc123 拆解为子任务"
- 或描述任务："将用户管理模块拆解"

更多详情请参考 [agents 目录](./agents/)。

---

### 2. Hooks - 自动化体验

#### SessionStart Hook（自动初始化）

**触发时机**：Claude Code 会话开始时

**功能**：
- 检查 `.task_data/` 目录是否存在
- **未初始化则自动调用初始化（无需手动操作）**
- 已初始化则静默通过

**实现**：
- 配置文件：`hooks/hooks.json`
- 脚本：`./hooks/scripts/check-workspace.sh`
- 自动调用：`WorkspaceManager(auto_init=True)`

**优点**：
- 🚀 **真正的零配置**：新项目自动初始化，无需手动操作
- ✅ **幂等性**：重复初始化不会报错
- 🔇 **静默运行**：已初始化项目无任何输出

更多详情请参考 [hooks 目录](./hooks/)。

---

### 3. 任务管理核心

#### 任务属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `id` | string | 任务唯一标识（tk-xxx） |
| `title` | string | 任务标题（1-200字符） |
| `description` | string | 任务描述 |
| `task_type` | enum | bug/feature/task/epic/chore |
| `status` | enum | open/in_progress/blocked/deferred/closed |
| `priority` | int | 0-4（0=Critical, 4=Backlog） |
| `assignee` | string | 负责人 |
| `tags` | array | 标签列表 |
| `dependencies` | array | 依赖任务ID列表 |

#### 依赖类型

- **blocks**：硬阻塞（必须先完成，影响 `task_ready` 结果）
- **related**：软关联（参考关系）
- **parent-child**：层级关系（epic → 子任务）
- **discovered-from**：发现关系（在某任务中发现的新任务）

#### 工作流模式

```
开始工作: task_ready → 选任务 → task_update(status=in_progress)
创建任务: task_create → 设置属性 → (可选)task_dep_add
进度追踪: task_list(status=in_progress) → task_stats
完成任务: task_update(status=closed) 或 task_close
```

---

### 4. 导出功能

#### task-export Command

**功能**：导出任务到 Markdown 文档

**输出格式**：
```markdown
# 项目任务清单

生成时间：2025-12-29

## 任务统计
- 总任务数：15
- 待处理：5
- 进行中：3
- 已完成：7

## 待处理任务（优先级排序）

| ID | 标题 | 优先级 | 负责人 | 标签 |
|----|------|--------|--------|------|
| tk-abc123 | 实现用户登录 | P1 | Alice | backend, auth |
...
```

**调用方式**：
```
/task-export
```

可选参数：status/priority/assignee/task_type（过滤）

---

## 🛠️ 开发

### 项目结构

```
plugins/task/
├── agents/                  # Agents（智能规划与拆解）
│   ├── task-planner.md
│   └── task-decomposer.md
├── hooks/                   # Hooks（自动化）
│   ├── hooks.json
│   └── scripts/
│       └── check-workspace.sh
├── .claude-plugin/          # 插件配置
│   └── plugin.json
├── commands/                # 用户命令
│   ├── task-add.md
│   ├── task-list.md
│   ├── task-update.md
│   ├── task-ready.md
│   ├── task-stats.md
│   └── task-export.md
├── skills/                  # 技能（自动激活）
│   └── task-management.md
├── src/task/                # 源代码
│   ├── __init__.py
│   ├── __main__.py
│   ├── server.py            # MCP Server（15个工具）
│   ├── types.py             # Pydantic 类型
│   ├── models.py            # SQLAlchemy 模型
│   ├── database.py          # 数据库管理
│   ├── repository.py        # Repository 层
│   ├── mappers.py           # 数据映射
│   └── workspace.py         # 工作空间管理
├── alembic/                 # 数据库迁移
├── tests/                   # 测试套件（70+ 测试）
├── docs/                    # 文档
│   ├── 快速开始.md
│   ├── 工具参考.md
│   ├── 架构设计.md
│   ├── 使用示例.md（新增）
│   └── ...
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

# 运行测试
uv run pytest -v

# 覆盖率报告
uv run pytest --cov=src/task --cov-report=html
open htmlcov/index.html
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
# 创建迁移
uv run alembic revision --autogenerate -m "描述"

# 升级到最新
uv run alembic upgrade head

# 降级一个版本
uv run alembic downgrade -1
```

---

## 📊 技术栈

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | ≥3.10 | 运行环境 |
| mcp | ≥1.1.0 | MCP SDK |
| pydantic | ≥2.0 | 类型安全和数据验证 |
| sqlalchemy | ≥2.0 | ORM 框架 |
| alembic | ≥1.12.0 | 数据库迁移 |
| pytest | ≥7.0 | 测试框架 |
| black | ≥23.0 | 代码格式化 |
| ruff | ≥0.1.0 | 代码检查 |
| mypy | ≥1.0 | 类型检查 |

---

## 🧪 测试

### 测试覆盖

- **总测试文件**：5个
- **总测试用例**：70+
- **目标覆盖率**：≥95%
- **测试隔离**：每个测试独立临时数据库

### 测试范围

- ✅ Repository 层（25+ 测试）
- ✅ Mapper 层（20+ 测试）
- ✅ Database 层（10+ 测试）
- ✅ Workspace 层（15+ 测试）

### 运行测试

```bash
# 所有测试
uv run pytest

# 特定模块
uv run pytest tests/test_repository.py -v

# 覆盖率报告
uv run pytest --cov=src/task --cov-report=term-missing

# 覆盖率要求
uv run pytest --cov=src/task --cov-fail-under=95
```

---

## 🔍 验证安装

### 检查插件是否正确加载

```bash
# 查看已安装插件
/plugin list
# 应显示：task (v0.2.0)

# 查看可用命令
/help
# 应包含：/task-add, /task-list, /task-update, /task-ready, /task-stats, /task-export

# 查看 agents
/agents
# 应包含：task-planner, task-decomposer

# 测试 MCP 工具（在 Claude Code 中）
请列出当前任务
# Claude 会自动调用 task_list 工具
```

### 调试模式

如遇问题，使用调试模式查看详细日志：

```bash
claude --debug --plugin-dir ./plugins/task
```

---

## 🗺️ 路线图

### v0.2.0（当前）- 完整功能

- [x] SQLAlchemy 持久化存储
- [x] Alembic 迁移系统
- [x] Repository 模式
- [x] 工作空间管理
- [x] 15个 MCP 工具
- [x] 2个智能 Agents（planner/decomposer）
- [x] 自动化 Hooks（SessionStart）
- [x] 6个用户 Commands（含 export）
- [x] 70+ 单元测试
- [x] Marketplace 分发支持
- [x] 完整文档

### v0.3.0（计划）- 依赖管理增强

- [ ] NetworkX 图算法
- [ ] 依赖图可视化
- [ ] 循环依赖检测优化
- [ ] 拓扑排序
- [ ] 依赖影响分析

### v0.4.0（计划）- 状态流转

- [ ] 状态机引擎
- [ ] 状态转换验证
- [ ] 自动状态推导
- [ ] 状态历史记录

### v0.5.0（计划）- 调度与报表

- [ ] 优先级调度器
- [ ] 就绪任务队列
- [ ] 任务统计报表
- [ ] 完成率分析
- [ ] 性能指标

---

## 📚 文档

### 用户文档

- 📖 [快速开始](./docs/快速开始.md) - 安装配置和基本使用
- 🎯 [使用示例](./docs/使用示例.md) - 完整工作流演示
- 🛠️ [工具参考](./docs/工具参考.md) - MCP 工具详细说明

### Agents & Hooks

- 🤖 [Agents](./agents/) - 智能规划与拆解（task-planner, task-decomposer）
- ⚡ [Hooks](./hooks/) - 自动化功能（SessionStart hook）

### 开发文档

- 🏗️ [架构设计](./docs/架构设计.md) - 系统架构和设计决策
- 📋 [实现计划](./docs/实现计划.md) - 开发路线图
- 📏 [开发规范](./docs/开发规范.md) - 编码规范和最佳实践
- 🧪 [测试文档](./tests/README.md) - 测试套件说明
- 📝 [变更日志](./CHANGELOG.md) - 版本更新历史

---

## 🎯 插件集成

Task Plugin 可与其他插件集成：

- **Context Plugin**：保存任务讨论到会话上下文
- **Memory Plugin**：存储任务知识到知识图谱
- **Knowledge Plugin**：添加任务文档到向量数据库

详细说明请参考 [集成指南](./examples/integration.md)。

---

## 📄 许可证

MIT License - 详见 [LICENSE](../../LICENSE)

---

## 💬 支持

如有问题或建议，请在 [GitHub Issues](https://github.com/lazygophers/ccplugin/issues) 提交。

---

## 👤 作者

**luoxin**

---

**版本**：0.2.0
**最后更新**：2025-12-29
**维护者**：luoxin
