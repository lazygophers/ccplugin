# Task - 任务管理插件

提供任务规划、分解、执行、编排和验收的完整生命周期管理。支持 Agentic Loop 持续执行、多任务并行编排和自动化验收。

## 功能概览

- **任务规划**：将复杂任务分解为结构化的子任务 DAG
- **任务执行**：按依赖顺序调度执行，支持并行分组
- **Agentic Loop**：Gather-Act-Verify-Adjust 循环模式，持续迭代直到目标达成
- **质量验收**：对照验收标准逐项审查，输出结构化报告
- **进度追踪**：通过命令输出追踪执行进度和阻塞情况

## 快速开始

### 安装

```bash
/plugin install task@ccplugin-market
```

### 命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `/plan` | 规划任务，分解为子任务 | `/plan 实现用户认证模块` |
| `/exec` | 执行已确认的任务计划 | `/exec` |
| `/add` | 补充/纠正当前任务 | `/add 数据库用 PostgreSQL` |
| `/cancel` | 取消当前执行 | `/cancel` |
| `/loop` | 进入 Agentic Loop 迭代模式 | `/loop 修复所有失败的测试` |
| `/review` | 审查已完成的任务质量 | `/review 全部` |

### 典型工作流

**流程 1：规划 → 执行 → 审查**

```
用户：/plan 为项目添加 JWT 认证
  → planner 分解为 5 个子任务
  → 用户确认计划

用户：/exec
  → 按依赖顺序调度执行（使用 loop 模式编排）
  → executor 完成每个子任务并自验证

用户：/review 全部
  → reviewer 逐项审查验收标准
  → 输出审查报告
```

**流程 2：Loop 迭代修复**

```
用户：/loop 修复 CI 中失败的 3 个测试
  → 迭代 1: 收集失败信息 → 修复 auth.py → 验证（2个仍失败）
  → 迭代 2: 聚焦 session → 修复 session.py → 验证（1个仍失败）
  → 迭代 3: 聚焦 permission → 修复 permission.py → 验证（全部通过）
  → 完成
```

## 插件架构

### Agents（智能代理）

| Agent | 角色 | 职责 |
|-------|------|------|
| **planner** | 规划师 | 需求分析、任务分解、依赖建模 |
| **executor** | 执行者 | 按计划执行具体任务并自验证 |
| **reviewer** | 审查员 | 质量审查、验收检查、报告生成 |
| **debugger** | 调试员 | 问题诊断、根因分析、修复执行 |

**注意**：编排（Orchestration）职责已整合到 `/loop` 命令中，由 loop 命令作为团队 Leader 负责多任务调度、并行管理和进度追踪。

### Skills（技能规范）

| Skill | 说明 |
|-------|------|
| **core** | 任务管理核心规范 - 生命周期、状态机、角色分工 |
| **planning** | 任务规划方法论 - 分解策略、DAG 建模 |
| **execution** | 执行最佳实践 - Gather-Act-Verify、最小变更 |
| **verification** | 验收规范 - 标准定义、质量检查清单 |
| **orchestration** | 编排规范 - 并行调度、异常处理 |
| **loop** | Agentic Loop 规范 - 循环模式、终止条件 |

### Commands（命令）

| Command | 触发方式 | 用途 |
|---------|---------|------|
| `/add` | 手动 | 补充/纠正/调整当前任务 |
| `/cancel` | 手动 | 取消当前执行，保留已完成工作 |
| `/loop` | 手动 | 进入持续迭代执行 |
| `/plan` | 手动 | 创建任务执行计划 |
| `/exec` | 手动 | 执行已确认的计划 |
| `/review` | 手动 | 审查完成质量 |

## 设计理念

### 借鉴来源

- **oh-my-openagent**：纪律代理分工、Oracle 验证、意图分类门控、三次失败升级
- **Claude Code Tasks**：TaskCreate/TeamCreate 内置工具、DAG 依赖管理
- **Agentic Loop 模式**：Gather-Act-Verify-Adjust 四阶段循环

### 核心原则

1. **规划先行** - 复杂任务先规划后执行，简单任务跳过规划
2. **意图门控** - 先分类任务复杂度，决定规划深度和执行策略
3. **纪律分工** - 不同阶段由专业 Agent 负责，loop 命令作为 Leader 统一管理
4. **Oracle 验证** - 任务完成由独立 reviewer 验证，不信任自评
5. **三次升级** - 失败后逐级升级（executor → debugger → planner → 用户）
6. **最小并行** - 并行数不超过 2，不修改同一文件或包
7. **统一提问** - Agent 不直接提问，由 loop Leader 通过 AskUserQuestion 统一提问

## 目录结构

```
task/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── planner.md          # 任务规划师
│   ├── executor.md         # 任务执行者
│   ├── reviewer.md         # 任务审查员
│   └── debugger.md         # 任务调试员
├── commands/
│   ├── add.md              # 补充当前任务命令
│   ├── cancel.md           # 取消执行命令
│   ├── loop.md             # Agentic Loop 命令
│   ├── plan.md             # 任务规划命令
│   ├── exec.md             # 任务执行命令
│   ├── review.md           # 质量审查命令
├── skills/
│   ├── core/SKILL.md       # 核心规范
│   ├── planning/SKILL.md   # 规划方法论
│   ├── execution/SKILL.md  # 执行最佳实践
│   ├── verification/SKILL.md # 验收规范
│   ├── orchestration/SKILL.md # 编排规范
│   └── loop/SKILL.md       # Loop 规范
├── docs/
└── README.md
```

## 许可证

AGPL-3.0-or-later
