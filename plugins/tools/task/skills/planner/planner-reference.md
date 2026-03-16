# Planner 参考指南

本文档包含 Agent 和 Skills 的选择指南。

## Agent 选择指南

### 可用 Agents

| Agent | 职责 | 适用场景 | 示例任务 |
|-------|------|---------|---------|
| `coder（开发者）` | 编写业务代码、实现功能 | 新功能开发、重构 | 实现 API 接口、添加新功能 |
| `tester（测试员）` | 编写测试、验证质量 | 单元测试、集成测试 | 编写测试用例、验证功能 |
| `devops（运维）` | 部署、CI/CD、基础设施 | 部署脚本、配置管理 | 配置 CI/CD、部署应用 |
| `writer（文档撰写者）` | 编写文档、README、API 文档 | 文档更新、API 说明 | 编写 README、API 文档 |
| `reviewer（审查员）` | 代码审查、质量检查 | Code Review、质量门禁 | 审查代码、检查质量 |

### Agent 选择原则

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

## Skills 选择指南

### 通用 Skills

#### Python 相关

| Skill | 说明 | 适用场景 |
|-------|------|---------|
| `python:core（核心功能）` | Python 核心开发 | 基础功能实现、数据处理 |
| `python:web（Web开发）` | FastAPI、Django 等 | Web 应用、API 开发 |
| `python:testing（测试）` | pytest、单元测试 | 测试编写、质量保证 |

#### Go 相关

| Skill | 说明 | 适用场景 |
|-------|------|---------|
| `golang:core（核心功能）` | Go 核心开发 | 基础功能实现、系统编程 |
| `golang:testing（测试）` | Go 测试框架 | 单元测试、基准测试 |

#### TypeScript 相关

| Skill | 说明 | 适用场景 |
|-------|------|---------|
| `typescript:core（核心功能）` | TypeScript 开发 | 基础功能实现、类型安全 |
| `typescript:react（React开发）` | React 组件开发 | 前端组件、UI 开发 |

#### JavaScript 相关

| Skill | 说明 | 适用场景 |
|-------|------|---------|
| `javascript:core（核心功能）` | JavaScript 开发 | 基础功能实现、脚本编写 |
| `javascript:vue（Vue开发）` | Vue 组件开发 | 前端组件、Vue 应用 |

### 专用 Skills

| Skill | 说明 | 适用场景 |
|-------|------|---------|
| `documentation（文档编写）` | 文档撰写 | README、API 文档、用户手册 |
| `code-review（代码审查）` | 代码质量检查 | Code Review、质量门禁 |
| `requirements（需求分析）` | 需求分析 | 需求收集、用户故事 |

### Skills 选择原则

**根据技术栈选择**：
- Python 项目 → `python:*`
- Go 项目 → `golang:*`
- TypeScript 项目 → `typescript:*`
- JavaScript 项目 → `javascript:*`

**根据任务性质选择**：
- 核心功能开发 → `*:core（核心功能）`
- Web 开发 → `*:web（Web开发）`
- 测试编写 → `*:testing（测试）`
- 文档编写 → `documentation（文档编写）`

**组合使用**：
```json
{
  "id": "T1",
  "description": "实现并测试用户认证",
  "agent": "coder（开发者）",
  "skills": [
    "python:core（核心功能）",
    "python:testing（测试）"
  ]
}
```

---

## 选择示例

### 示例 1: Python Web 应用

```json
{
  "tasks": [
    {
      "id": "T1",
      "description": "实现 FastAPI 用户认证",
      "agent": "coder（开发者）",
      "skills": ["python:web（Web开发）"]
    },
    {
      "id": "T2",
      "description": "编写认证测试",
      "agent": "tester（测试员）",
      "skills": ["python:testing（测试）"]
    },
    {
      "id": "T3",
      "description": "编写 API 文档",
      "agent": "writer（文档撰写者）",
      "skills": ["documentation（文档编写）"]
    }
  ]
}
```

### 示例 2: Go 微服务

```json
{
  "tasks": [
    {
      "id": "T1",
      "description": "实现 gRPC 服务",
      "agent": "coder（开发者）",
      "skills": ["golang:core（核心功能）"]
    },
    {
      "id": "T2",
      "description": "编写服务测试",
      "agent": "tester（测试员）",
      "skills": ["golang:testing（测试）"]
    },
    {
      "id": "T3",
      "description": "配置 Kubernetes 部署",
      "agent": "devops（运维）",
      "skills": []  # DevOps 通常不需要特定 skills
    }
  ]
}
```

### 示例 3: React 前端应用

```json
{
  "tasks": [
    {
      "id": "T1",
      "description": "实现登录组件",
      "agent": "coder（开发者）",
      "skills": ["typescript:react（React开发）"]
    },
    {
      "id": "T2",
      "description": "编写组件测试",
      "agent": "tester（测试员）",
      "skills": ["typescript:testing（测试）"]
    },
    {
      "id": "T3",
      "description": "编写组件文档",
      "agent": "writer（文档撰写者）",
      "skills": ["documentation（文档编写）"]
    }
  ]
}
```

---

## 常见组合模式

### 模式 1: 全栈开发

```json
{
  "tasks": [
    {
      "description": "后端 API 开发",
      "agent": "coder（开发者）",
      "skills": ["python:web（Web开发）"]
    },
    {
      "description": "前端页面开发",
      "agent": "coder（开发者）",
      "skills": ["typescript:react（React开发）"]
    },
    {
      "description": "集成测试",
      "agent": "tester（测试员）",
      "skills": ["python:testing（测试）", "typescript:testing（测试）"]
    }
  ]
}
```

### 模式 2: TDD 开发

```json
{
  "tasks": [
    {
      "description": "编写测试用例",
      "agent": "tester（测试员）",
      "skills": ["golang:testing（测试）"]
    },
    {
      "description": "实现功能代码",
      "agent": "coder（开发者）",
      "skills": ["golang:core（核心功能）"],
      "dependencies": ["T1"]
    },
    {
      "description": "代码审查",
      "agent": "reviewer（审查员）",
      "skills": ["code-review（代码审查）"],
      "dependencies": ["T2"]
    }
  ]
}
```

### 模式 3: 文档驱动开发

```json
{
  "tasks": [
    {
      "description": "编写需求文档",
      "agent": "writer（文档撰写者）",
      "skills": ["requirements（需求分析）"]
    },
    {
      "description": "实现功能",
      "agent": "coder（开发者）",
      "skills": ["python:core（核心功能）"],
      "dependencies": ["T1"]
    },
    {
      "description": "编写用户手册",
      "agent": "writer（文档撰写者）",
      "skills": ["documentation（文档编写）"],
      "dependencies": ["T2"]
    }
  ]
}
```

---

## 自定义 Agent 和 Skills

### 何时需要自定义

**自定义 Agent**：
- 项目有特殊角色需求
- 需要专门的技能组合
- 现有 Agent 不满足需求

**自定义 Skills**：
- 使用特定技术栈
- 需要专门的技能
- 现有 Skills 不满足需求

### 命名规范

**Agent 命名**：
- 格式：`角色名（中文说明）`
- 示例：`data-engineer（数据工程师）`

**Skills 命名**：
- 格式：`技术栈:领域（中文说明）`
- 示例：`rust:core（核心功能）`

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
