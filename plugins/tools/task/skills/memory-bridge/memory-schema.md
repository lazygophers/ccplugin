# 记忆数据模型（Memory Schema）

## 概述

本文档定义 Memory Bridge 使用的三层记忆数据模型，基于认知科学中的记忆系统理论和 [Agentic Context Engineering](https://arxiv.org/html/2602.20478v1) 框架。

## 三层记忆架构

```
┌─────────────────────────────────────────────────────────┐
│                    记忆系统架构                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │  短期记忆 (Working Memory)                     │    │
│  │  - 当前会话状态                                │    │
│  │  - 临时变量和中间结果                          │    │
│  │  - 生命周期：会话期间                          │    │
│  │  URI: task://sessions/{session_id}           │    │
│  │  Priority: 0 (最高)                           │    │
│  └───────────────────────────────────────────────┘    │
│                        ↓                               │
│  ┌───────────────────────────────────────────────┐    │
│  │  情节记忆 (Episodic Memory)                    │    │
│  │  - 任务执行历史                                │    │
│  │  - 成功/失败经验                               │    │
│  │  - 规划模式和策略                              │    │
│  │  - 生命周期：永久（可归档）                    │    │
│  │  URI: workflow://task-episodes/{type}/{id}   │    │
│  │  Priority: 3-4                                │    │
│  └───────────────────────────────────────────────┘    │
│                        ↓                               │
│  ┌───────────────────────────────────────────────┐    │
│  │  语义记忆 (Semantic Memory)                    │    │
│  │  - 项目架构知识                                │    │
│  │  - 代码风格约定                                │    │
│  │  - 技术栈信息                                  │    │
│  │  - 生命周期：永久                              │    │
│  │  URI: project://knowledge/{domain}/{topic}   │    │
│  │  Priority: 1-2                                │    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 1. 短期记忆（Working Memory）

### URI 路径格式
```
task://sessions/{session_id}
```

### 数据结构
```json
{
  "session_id": "a1b2c3d4e5f6",
  "user_task": "实现用户登录功能",
  "task_type": "feature",
  "phase": "execution",
  "iteration": 2,
  "context": {
    "replan_trigger": "verifier",
    "stalled_count": 0,
    "guidance_count": 1
  },
  "plan_md_path": ".claude/plans/实现用户登录功能-2.md",
  "created_at": "2026-03-21T10:00:00",
  "last_updated": "2026-03-21T10:15:00",
  "additional_state": {
    "verification_status": "suggestions",
    "verification_report": "功能基本实现，建议优化错误处理"
  }
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `session_id` | string | 是 | 会话唯一标识（MD5[:12]） |
| `user_task` | string | 是 | 用户任务描述 |
| `task_type` | string | 否 | 任务类型（feature/bugfix/refactor/docs/test） |
| `phase` | string | 是 | 当前阶段（planning/confirmation/execution/verification/adjustment/completion） |
| `iteration` | integer | 是 | 当前迭代号 |
| `context` | object | 是 | 上下文状态（replan_trigger等） |
| `plan_md_path` | string | 否 | 计划文档路径 |
| `created_at` | string | 是 | 创建时间（ISO 8601） |
| `last_updated` | string | 是 | 最后更新时间（ISO 8601） |
| `additional_state` | object | 否 | 额外状态信息 |

### 生命周期管理

- **创建**：Loop 初始化阶段创建
- **更新**：每个阶段转换时更新
- **归档**：任务完成后移动到 `workflow://task-episodes/{type}/{session_id}` 作为情节记忆
- **清理**：归档后删除短期记忆

### 优先级设置
- **Priority**: 0（最高，始终加载）
- **Disclosure**: "When resuming interrupted tasks"

## 2. 情节记忆（Episodic Memory）

### URI 路径格式
```
workflow://task-episodes/{task_type}/{episode_id}
```

**任务类型枚举**：
- `feature` - 新功能开发
- `bugfix` - Bug 修复
- `refactor` - 代码重构
- `docs` - 文档编写
- `test` - 测试编写
- `optimization` - 性能优化
- `migration` - 迁移升级

### 数据结构
```json
{
  "episode_id": "e7f8g9h0i1j2",
  "task_desc": "实现用户登录功能，支持邮箱和手机号登录",
  "task_type": "feature",
  "plan": {
    "task_count": 4,
    "report": "分为验证、数据库、接口、前端四个子任务",
    "agents": ["code:typescript", "code:typescript", "test:jest"],
    "skills": ["edit", "write", "test"]
  },
  "result": "success",
  "metrics": {
    "duration_minutes": 25,
    "iterations": 2,
    "stalled_count": 0,
    "guidance_count": 1
  },
  "agents_used": ["code:typescript", "test:jest"],
  "skills_used": ["edit", "write", "test", "lint"],
  "changed_files": [
    "src/auth/login.service.ts",
    "src/auth/login.controller.ts",
    "tests/auth/login.test.ts"
  ],
  "timestamp": "2026-03-21T11:00:00",
  "tags": ["authentication", "validation", "database"]
}
```

### 失败情节额外字段
```json
{
  "result": "failed",
  "failure": {
    "reason": "依赖注入配置错误导致服务启动失败",
    "error_type": "ConfigurationError",
    "failed_tasks": ["T2", "T3"],
    "recovery_action": {
      "type": "manual_fix",
      "description": "修复 app.module.ts 中的依赖注入配置",
      "command": null
    },
    "recovery_success": true,
    "lessons_learned": "在修改依赖注入配置时需要同步更新 module 导入"
  }
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `episode_id` | string | 是 | 情节唯一标识（MD5[:12]） |
| `task_desc` | string | 是 | 任务描述 |
| `task_type` | string | 是 | 任务类型 |
| `plan` | object | 是 | 执行计划摘要 |
| `result` | string | 是 | 结果（success/failed） |
| `metrics` | object | 是 | 执行指标 |
| `agents_used` | array | 是 | 使用的 Agents 列表 |
| `skills_used` | array | 是 | 使用的 Skills 列表 |
| `changed_files` | array | 否 | 变更的文件列表 |
| `timestamp` | string | 是 | 完成时间（ISO 8601） |
| `tags` | array | 否 | 标签（用于分类和检索） |
| `failure` | object | 否 | 失败信息（仅失败情节） |

### 生命周期管理

- **创建**：任务完成或失败时从短期记忆提升
- **更新**：失败后成功修复时更新 `recovery_success`
- **归档**：超过 100 条同类型情节时，按优先级归档低价值记录
- **清理**：不删除，仅归档（priority 降为 9）

### 优先级设置
- **成功情节**: Priority 3
- **失败情节（未修复）**: Priority 4
- **失败情节（已修复）**: Priority 3
- **Disclosure**: `"When planning {task_type} tasks similar to: {task_desc[:50]}..."`

## 3. 语义记忆（Semantic Memory）

### URI 路径格式
```
project://knowledge/{domain}/{topic}
```

**领域枚举**：
- `architecture` - 架构设计
- `conventions` - 代码约定
- `tech-stack` - 技术栈
- `patterns` - 设计模式
- `testing` - 测试策略
- `deployment` - 部署流程

### 数据结构示例

#### 架构决策记录
```json
{
  "uri": "project://knowledge/architecture/repository-pattern",
  "domain": "architecture",
  "topic": "repository-pattern",
  "title": "Repository 模式约定",
  "content": "项目采用 Repository 模式隔离数据访问层...",
  "related_files": [
    "src/repositories/base.repository.ts",
    "src/repositories/user.repository.ts"
  ],
  "decision_date": "2026-01-15",
  "status": "active",
  "priority": 1
}
```

#### 代码风格约定
```json
{
  "uri": "project://knowledge/conventions/naming",
  "domain": "conventions",
  "topic": "naming",
  "title": "命名规范",
  "content": "- 接口以 I 开头\n- 抽象类以 Abstract 开头\n- DTO 以 Dto 结尾...",
  "examples": [
    "interface IUserRepository",
    "abstract class AbstractService",
    "class CreateUserDto"
  ],
  "priority": 2
}
```

#### 技术栈信息
```json
{
  "uri": "project://knowledge/tech-stack/backend",
  "domain": "tech-stack",
  "topic": "backend",
  "title": "后端技术栈",
  "content": "- Node.js 20.x\n- NestJS 10.x\n- TypeORM 0.3.x\n- PostgreSQL 15.x",
  "dependencies": {
    "@nestjs/core": "^10.0.0",
    "@nestjs/typeorm": "^10.0.0",
    "typeorm": "^0.3.0"
  },
  "priority": 1
}
```

### 字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `uri` | string | 是 | 唯一标识（URI 路径） |
| `domain` | string | 是 | 知识领域 |
| `topic` | string | 是 | 具体主题 |
| `title` | string | 是 | 标题 |
| `content` | string | 是 | 知识内容（Markdown） |
| `related_files` | array | 否 | 相关文件路径 |
| `examples` | array | 否 | 示例代码或模式 |
| `priority` | integer | 是 | 优先级（1-2 为核心知识） |
| `status` | string | 否 | 状态（active/deprecated/draft） |
| `tags` | array | 否 | 标签 |
| `created_at` | string | 否 | 创建时间 |
| `updated_at` | string | 否 | 更新时间 |

### 生命周期管理

- **创建**：手动创建或从情节记忆提炼
- **更新**：项目约定变更时手动更新
- **归档**：过时的知识（如旧版本技术栈）标记为 `deprecated`
- **清理**：不删除，保留历史记录

### 优先级设置
- **核心知识**: Priority 1（始终加载）
- **重要知识**: Priority 2（始终加载）
- **参考知识**: Priority 3（按需加载）
- **Disclosure**: `"When working on {domain} related tasks"`

## URI 命名空间总结

| 命名空间 | 用途 | 优先级范围 | 生命周期 |
|----------|------|-----------|---------|
| `task://sessions/*` | 短期记忆 | 0 | 会话期间 |
| `workflow://task-episodes/*` | 情节记忆 | 3-4 | 永久（可归档） |
| `project://knowledge/*` | 语义记忆 | 1-3 | 永久 |
| `user://preferences/*` | 用户偏好 | 1-2 | 永久 |
| `system://boot` | 系统初始化 | 0 | 永久 |

## 数据一致性规则

1. **必需字段验证**：创建记忆时必须包含所有必需字段
2. **URI 唯一性**：同一 URI 路径只能有一条记忆
3. **引用完整性**：情节记忆引用的 session_id 必须在短期记忆或已归档
4. **时间戳格式**：所有时间戳使用 ISO 8601 格式（`YYYY-MM-DDTHH:MM:SS`）
5. **枚举值验证**：`task_type`、`result`、`phase` 等枚举字段必须使用预定义值
6. **优先级范围**：优先级必须在 0-10 之间

## 记忆大小限制

| 记忆类型 | 单条内容上限 | 总数建议上限 |
|---------|-------------|-------------|
| 短期记忆 | 10 KB | 1（当前会话） |
| 情节记忆 | 50 KB | 500（每类型） |
| 语义记忆 | 100 KB | 200（总计） |

超过限制时触发归档策略：
- 情节记忆：按时间和使用频率归档
- 语义记忆：提示用户拆分为多个主题
