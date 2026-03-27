# Planner Agent 选择指南

## 可用 Agents

| Agent | 职责 | 适用场景 |
|-------|------|---------|
| `coder（开发者）` | 编写业务代码 | 新功能/重构 |
| `tester（测试员）` | 编写测试 | 单元/集成测试 |
| `devops（运维）` | 部署/CI/CD | 配置管理 |
| `writer（文档撰写者）` | 编写文档 | README/API文档 |
| `reviewer（审查员）` | 代码审查 | 质量门禁 |

## Explorer Agents

| Agent | 职责 | 适用场景 |
|-------|------|---------|
| `explorer-general@task` | 宏观理解/技术栈识别 | 首次接触项目 |
| `explorer-code@task` | 代码结构/符号/依赖 | 深度代码分析 |
| `explorer-frontend@task` | 组件树/状态/路由/样式 | 前端项目 |
| `explorer-backend@task` | API/数据模型/服务架构 | 后端项目 |
| `explorer-database@task` | Schema/表关系/索引 | 数据库分析 |
| `explorer-api@task` | REST/GraphQL/gRPC端点 | API设计 |
| `explorer-test@task` | 框架/覆盖率/质量 | 测试体系 |
| `explorer-infrastructure@task` | Docker/K8s/CI-CD | DevOps |
| `explorer-dependencies@task` | 依赖树/安全/许可证 | 依赖分析 |

### Explorer选择

首次接触→`general` → 根据project_type选择专用explorer。继承关系：`general`(宏观) → `code`(基础) → `frontend/backend/database/api/test`(特化)。`infrastructure/dependencies`独立。

## 选择原则

按任务类型：代码→coder | 测试→tester | 部署→devops | 文档→writer | 审查→reviewer

## 自定义Agent

命名：`角色名（中文说明）`，如`data-engineer（数据工程师）`
