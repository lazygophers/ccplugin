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

## Agent 发现机制

Planner 按以下优先级扫描可用 agents：

1. **插件提供的 agents**（`plugins/*/agents/*.md`）
   - 标注后缀：`@plugin-name`（如 `explorer-general@task`）
   - 特点：专业领域能力、经过测试、可跨项目复用

2. **用户全局 agents**（`~/.claude/agents/*.md`）
   - 标注后缀：`@user`（如 `security-auditor@user`）
   - 特点：个人工作习惯、跨项目通用工具

3. **项目专属 agents**（`.claude/agents/*.md`）
   - 无后缀（如 `payment-processor`）
   - 特点：业务逻辑强绑定、不适合复用

**扫描规则**：
- 同名 agent 按上述优先级覆盖（插件 > 用户 > 项目）
- 无后缀 agent 视为项目专属
- 插件 agent 必须在其 `agents/` 目录下声明才生效

## 专用 vs 通用 Agent 判断标准

| 维度 | 专用 Agent（如 `explorer-frontend@task`） | 通用 Agent（如 `coder`） |
|------|------------------------------------------|------------------------|
| **技术栈绑定** | 强绑定（React/Vue/Angular） | 无绑定（任意语言） |
| **工具依赖** | 需要特定工具（如 webpack-bundle-analyzer） | 使用通用工具 |
| **输出格式** | 标准化结构（如组件树 JSON） | 灵活输出 |
| **复用场景** | 同类项目（所有前端项目） | 所有项目 |

**选择建议**：
- 需要领域知识（如前端状态管理、数据库索引）→ 专用 agent
- 重复执行的标准化任务（如依赖扫描）→ 专用 agent
- 临时性、业务逻辑强的任务 → 通用 agent

## Agent 优先级策略

当多个 agent 都能完成任务时，按以下规则选择：

1. **专用 > 通用**
   - 如前端任务优先用 `explorer-frontend@task` 而非 `explorer-code@task`

2. **插件 > 用户 > 项目**
   - 同名情况下，插件 agent 覆盖用户和项目 agent

3. **最小能力原则**
   - 不要用 `explorer-backend@task` 去做通用代码扫描

4. **避免重复造轮子**
   - 检查插件/用户 agents 是否已有类似能力再创建项目 agent

## 来源标注规范

**规范**：
```
agent_name@source
```

**示例**：
- `explorer-general@task` → 来自 task 插件
- `security-auditor@user` → 来自用户全局目录
- `payment-processor` → 项目专属，无后缀

**用途**：
- 帮助 planner 识别 agent 来源和优先级
- 避免命名冲突
- 便于跨项目引用插件能力

## 自定义Agent

命名：`角色名（中文说明）`，如`data-engineer（数据工程师）`
