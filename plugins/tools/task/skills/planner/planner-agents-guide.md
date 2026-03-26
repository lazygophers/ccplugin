# Planner Agent 选择指南

本文档包含 Agent 的选择指南和使用示例。

## 可用 Agents

| Agent | 职责 | 适用场景 | 示例任务 |
|-------|------|---------|---------|
| `coder（开发者）` | 编写业务代码、实现功能 | 新功能开发、重构 | 实现 API 接口、添加新功能 |
| `tester（测试员）` | 编写测试、验证质量 | 单元测试、集成测试 | 编写测试用例、验证功能 |
| `devops（运维）` | 部署、CI/CD、基础设施 | 部署脚本、配置管理 | 配置 CI/CD、部署应用 |
| `writer（文档撰写者）` | 编写文档、README、API 文档 | 文档更新、API 说明 | 编写 README、API 文档 |
| `reviewer（审查员）` | 代码审查、质量检查 | Code Review、质量门禁 | 审查代码、检查质量 |

## Explorer Agents（探索代理）

| Agent | 职责 | 适用场景 | 示例任务 |
|-------|------|---------|---------|
| `explorer-general（通用探索）@task` | 项目宏观理解、技术栈识别、目录结构概览 | 首次接触项目、快速了解全貌 | 了解项目架构、识别技术栈 |
| `explorer-code（代码探索）@task` | 代码结构分析、符号索引、依赖追踪、模式识别 | 深度代码分析、重构前调研 | 分析模块依赖、识别设计模式 |
| `explorer-frontend（前端探索）@task` | React/Vue 组件树、状态管理、路由、样式体系 | 前端项目分析 | 分析组件树、追踪状态管理 |
| `explorer-backend（后端探索）@task` | API 路由、数据模型、服务架构、中间件链 | 后端项目分析 | 映射 API 端点、分析数据模型 |
| `explorer-database（数据库探索）@task` | Schema 结构、表关系、索引评估、迁移历史 | 数据库架构分析 | 分析表结构、追踪外键关系 |
| `explorer-api（API 探索）@task` | REST/GraphQL/gRPC 端点、参数、认证机制 | API 设计分析 | 映射 API 端点、分析认证方式 |
| `explorer-test（测试探索）@task` | 测试框架、覆盖率、测试质量、缺口识别 | 测试体系分析 | 评估覆盖率、识别测试缺口 |
| `explorer-infrastructure（基础设施探索）@task` | Docker/K8s、CI/CD、云服务、环境配置 | DevOps 分析 | 分析部署配置、识别云服务 |
| `explorer-dependencies（依赖探索）@task` | 依赖树、安全审计、版本管理、许可证合规 | 依赖分析 | 检查安全漏洞、分析许可证 |

### Explorer 选择决策树

```
项目类型判断：
├── 首次接触 / 不确定项目类型
│   └── explorer-general（通用探索）
│       → 输出项目概览后，根据 project_type 继续选择
│
├── 需要代码级分析（非特定领域）
│   └── explorer-code（代码探索）
│       → 符号索引、依赖追踪、模式识别
│
├── 前端项目（React/Vue/Svelte/Angular）
│   └── explorer-frontend（前端探索）
│       → 继承 code 能力 + 组件树/状态/路由分析
│
├── 后端项目（Go/Python/Node.js/Java）
│   └── explorer-backend（后端探索）
│       → 继承 code 能力 + API/模型/服务分析
│
├── 数据库架构分析
│   └── explorer-database（数据库探索）
│       → 继承 code 能力 + Schema/关系/索引/迁移分析
│
├── API 设计分析
│   └── explorer-api（API 探索）
│       → 继承 code 能力 + REST/GraphQL/gRPC 端点分析
│
├── 测试体系分析
│   └── explorer-test（测试探索）
│       → 继承 code 能力 + 框架/覆盖率/质量评估
│
├── DevOps / 基础设施分析
│   └── explorer-infrastructure（基础设施探索）
│       → Docker/K8s/CI-CD/云服务分析
│
└── 依赖和供应链分析
    └── explorer-dependencies（依赖探索）
        → 依赖树/安全审计/许可证分析
```

### Explorer 继承关系

```
explorer-general（宏观）
    ↓
explorer-code（基础层）
    ├─→ explorer-frontend（前端特化，继承 code 能力）
    ├─→ explorer-backend（后端特化，继承 code 能力）
    ├─→ explorer-database（数据库特化，继承 code 能力）
    ├─→ explorer-api（API 特化，继承 code 能力）
    └─→ explorer-test（测试特化，继承 code 能力）

独立层（不继承 code）：
    ├─→ explorer-infrastructure（基础设施，配置文件分析）
    └─→ explorer-dependencies（依赖分析，包管理器分析）
```

### Explorer 使用示例

```json
{
  "tasks": [
    {
      "id": "T0",
      "description": "了解项目全貌和技术栈",
      "agent": "explorer-general（通用探索）@task"
    },
    {
      "id": "T1",
      "description": "分析前端组件架构和状态管理",
      "agent": "explorer-frontend（前端探索）@task",
      "dependencies": ["T0"]
    },
    {
      "id": "T2",
      "description": "分析后端 API 路由和数据模型",
      "agent": "explorer-backend（后端探索）@task",
      "dependencies": ["T0"]
    }
  ]
}
```

## Agent 选择原则

**根据任务类型选择**：
- 代码实现 → `coder（开发者）`
- 测试编写 → `tester（测试员）`
- 部署配置 → `devops（运维）`
- 文档编写 → `writer（文档撰写者）`
- 质量检查 → `reviewer（审查员）`

**多角色协作**：
```json
{
  "tasks": [
    {
      "id": "T1",
      "description": "实现用户认证功能",
      "agent": "coder（开发者）"
    },
    {
      "id": "T2",
      "description": "编写认证测试",
      "agent": "tester（测试员）",
      "dependencies": ["T1"]
    },
    {
      "id": "T3",
      "description": "编写 API 文档",
      "agent": "writer（文档撰写者）",
      "dependencies": ["T1"]
    }
  ]
}
```

---

## 自定义 Agent

### 何时需要自定义

**自定义 Agent**：
- 项目有特殊角色需求
- 需要专门的技能组合
- 现有 Agent 不满足需求

### 命名规范

**Agent 命名**：
- 格式：`角色名（中文说明）`
- 示例：`data-engineer（数据工程师）`

### 自定义示例

```json
{
  "tasks": [
    {
      "description": "数据清洗和处理",
      "agent": "data-engineer（数据工程师）",
      "skills": ["python:data（数据处理）"]
    },
    {
      "description": "机器学习模型训练",
      "agent": "ml-engineer（机器学习工程师）",
      "skills": ["python:ml（机器学习）"]
    }
  ]
}
```
