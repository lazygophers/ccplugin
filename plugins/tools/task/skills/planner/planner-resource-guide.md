# Planner 资源选择指南（Agent & Skills）

## 必填性

| 场景 | Agent | Skills |
|------|-------|--------|
| tasks 不为空 | **必填**（单个） | **必填**（至少1个） |
| tasks 为空 | 不需要 | 不需要 |

**格式**：`name（中文注释）@source` 或 `name（中文注释）`（项目专属无后缀）

## Agent 选择

### 可用 Agents

| Agent | 职责 | 适用场景 |
|-------|------|---------|
| `coder（开发者）` | 编写业务代码 | 新功能/重构 |
| `tester（测试员）` | 编写测试 | 单元/集成测试 |
| `devops（运维）` | 部署/CI/CD | 配置管理 |
| `writer（文档撰写者）` | 编写文档 | README/API文档 |
| `reviewer（审查员）` | 代码审查 | 质量门禁 |

### Explorer Agents

| Agent | 适用场景 |
|-------|---------|
| `explorer-general@task` | 首次接触项目/宏观理解 |
| `explorer-code@task` | 代码结构/符号/依赖分析 |
| `explorer-frontend@task` | 组件树/状态/路由/样式 |
| `explorer-backend@task` | API/数据模型/服务架构 |
| `explorer-database@task` | Schema/表关系/索引 |
| `explorer-api@task` | REST/GraphQL/gRPC端点 |
| `explorer-test@task` | 框架/覆盖率/质量 |
| `explorer-infrastructure@task` | Docker/K8s/CI-CD |
| `explorer-dependencies@task` | 依赖树/安全/许可证 |

继承关系：`general`(宏观) → `code`(基础) → `frontend/backend/database/api/test`(特化)

### Agent 发现机制

按优先级扫描：
1. **插件 agents**（`plugins/*/agents/*.md`）→ 标注 `@plugin-name`
2. **用户全局 agents**（`~/.claude/agents/*.md`）→ 标注 `@user`
3. **项目专属 agents**（`.claude/agents/*.md`）→ 无后缀

同名 agent 按上述优先级覆盖。选择原则：专用 > 通用 | 插件 > 用户 > 项目 | 最小能力原则。

## Skills 选择

### Skills 发现机制

扫描三个来源：
1. **插件级**：`~/.claude/plugins/*/skills/` → 标注 `@plugin-name`
2. **User级**：`~/.claude/skills/` → 标注 `@user`
3. **项目级**：`.claude/skills/` → 无后缀

### 通用 Skills

| 技术栈 | Skills | 适用场景 |
|--------|--------|---------|
| Python | `python:core` / `python:web` / `python:testing` | 功能/Web/测试 |
| Go | `golang:core` / `golang:testing` | 系统编程/测试 |
| TypeScript | `typescript:core` / `typescript:react` | 类型安全/React |
| 专用 | `documentation` / `code-review` / `requirements` | 文档/审查/需求 |

### 选择原则

- **按技术栈**：Python→`python:*`，Go→`golang:*`，TS→`typescript:*`
- **按任务**：核心→`*:core`，Web→`*:web`，测试→`*:testing`
- **组合使用**：同一任务可指定多个skills

### 常见模式

| 模式 | 任务组合 |
|------|---------|
| 全栈 | 后端`python:web` + 前端`typescript:react` + 测试`python:testing` |
| TDD | 测试`*:testing` → 实现`*:core` → 审查`code-review` |
| 文档驱动 | 需求`requirements` → 实现`*:core` → 文档`documentation` |

## 验证检查

1. ✓ agent 非空且含"（"中文注释
2. ✓ skills 为非空数组，每项含"（"
3. ✓ 来源标注与实际工具位置一致
4. ✓ 探索类任务使用 task:explorer-* agents
5. ✓ 实现类任务根据技术栈选择合适 agent
