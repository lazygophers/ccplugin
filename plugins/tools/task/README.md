# Task - 任务管理插件

<overview>

Task 是一个任务管理框架插件，提供规划、执行、验证和迭代的完整流程。它不绑定任何具体的执行 agents，而是让用户灵活选择其他插件或自定义 agents 来完成实际工作。这种设计使得框架可以适配任意技术栈和项目类型。

核心理念是基于 PDCA 循环（计划-执行-检查-改进）的持续迭代。通过 /loop 命令，Task 以 team leader 角色统一管理所有调度和用户交互，agents 只需通过 SendMessage 向 leader 上报，leader 通过 AskUserQuestion 与用户沟通。

</overview>

<getting_started>

## 安装与命令

```bash
/plugin install task@ccplugin-market
```

| 命令 | 说明 |
|------|------|
| `/loop [任务目标]` | 进入循环迭代模式，作为 team leader 执行完整流程 |
| `/add [补充内容]` | 补充任务说明、纠正方向或添加约束 |
| `/cancel` | 取消当前执行，保留已完成工作 |

## 典型工作流

```
用户：/loop 实现用户认证功能

→ 初始化（Initialization）
  - 初始化状态变量和执行环境
  - 列出可用资源（skills、agents）

→ 计划设计（Planning / Plan）
  - 分析项目结构和技术栈
  - 分解为原子子任务（MECE 原则）
  - 建立依赖关系（DAG）
  - 为每个任务分配 agent 和 skills（带中文注释）
  - 定义可量化的验收标准

→ 计划确认（Plan Confirmation）
  - 生成计划文档（Markdown）
  - 输出执行流程图和验收标准
  - 用户确认计划

→ 任务执行（Execution / Do）
  - 判断任务数量（1 个任务不创建 team，多个任务创建 team）
  - 按依赖顺序调度执行
  - 支持并行/串行编排（最多 2 个并行）
  - 实时输出进度
  - 执行完成后删除 team（如果创建了）

→ 结果验证（Verification / Check）
  - 检查所有验收标准（acceptance_criteria）
  - 验收标准失败 → 失败调整
  - 验收标准通过 + 有建议事项 → 询问用户是否纳入任务
    - 用户确认需要 → 继续迭代（回到计划设计）
    - 用户确认不需要 → 完成
  - 验收标准通过 + 无建议 → 完成

→ 失败调整（Adjustment / Act）
  - 分析失败原因和停滞模式
  - 应用分级升级策略（retry → debug → replan → ask_user）
  - 指数退避（0秒 → 2秒 → 4秒）
  - 回到相应阶段（任务执行 或 计划设计）

→ 全部完成（Completion / Finalization）
  - 调用 finalizer agent 清理资源
  - 输出最终报告和统计信息
  - （team 已在任务执行阶段结束时删除）
```

## 计划输出示例

步骤 3 会输出 ASCII 流程图展示任务依赖关系：

```
## 执行计划

### 执行流程图
┌─────────────────────────────────────┐
│ T1: 实现用户模型                      │
│ agent: coder                        │
│ files: src/models/user.py           │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ T2: 实现 API 接口                    │
│ agent: coder                        │
│ files: src/api/auth.py              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ T3: 编写测试                         │
│ agent: tester                       │
│ files: tests/test_auth.py           │
└─────────────────────────────────────┘

### 验收标准
- [ ] 所有测试通过
- [ ] Lint 无错误
- [ ] 功能符合需求

### 简要说明
分 3 个子任务实现用户认证功能，先建模型再实现接口最后补测试。
```

</getting_started>

<core_concepts>

## 设计原则

Task 插件的架构围绕几个关键决策展开。框架与执行分离是最核心的设计——Task 只负责流程编排，具体任务由外部 agents 完成，这样同一个框架可以驱动 golang、python、flutter 等不同技术栈的 agents。

/loop 命令作为唯一的 team leader，统一管理所有调度和用户交互。agents 不能直接向用户提问，必须通过 SendMessage 上报给 leader，由 leader 决定是否需要用户介入。这种集中式通信避免了多 agent 同时向用户提问造成的混乱。

任务拆分遵循原子性原则，每个子任务必须不可再分。并行执行时最多 2 个任务同时运行，且不能修改同一文件或模块。Team 按需创建——单任务不创建 team，多任务在执行阶段创建，执行完成后立即删除。

## Agent 来源

Task 插件不提供执行 agents，而是使用以下来源：其他插件提供的专业 agents（如 golang、python、flutter 插件），用户或项目自定义的 agents，以及通用 agents（如 general-purpose、Explore）。

## 终止条件

| 条件 | 触发 | 行为 |
|------|------|------|
| 目标达成 | 结果验证全部通过 | 正常退出，输出报告 |
| 停滞过多 | 连续 3 次相同错误 | 请求用户指导后继续（不退出） |
| 用户中断 | 用户主动中断 | 根据用户指令处理 |

循环没有最大迭代次数限制。停滞时请求用户指导，但不退出循环；获得用户指导后重置停滞计数器，继续执行。

</core_concepts>

<reference>

## 目录结构

```
task/
├── agents/          # Agent 定义
│   ├── planner.md
│   ├── verifier.md
│   └── adjuster.md
├── skills/
│   ├── adjuster/       # 失败调整规范
│   ├── deep-iteration/ # 深度迭代规范
│   ├── execute/        # 任务执行规范
│   ├── finalizer/      # 完成清理规范
│   ├── loop/           # 循环控制规范
│   ├── planner/        # 计划设计规范
│   └── verifier/       # 结果验证规范
├── docs/            # 文档
└── README.md
```

## Skills

| Skill | 说明 |
|-------|------|
| planner | 计划设计规范 - 收集项目信息、任务分解、依赖建模、agents/skills 分配 |
| execute | 任务执行规范 - 并行编排、团队管理、进度跟踪 |
| verifier | 结果验证规范 - 检查任务验收标准、验证完成情况、判断终止条件 |
| adjuster | 失败调整规范 - 分析失败原因、检测停滞、应用升级策略 |
| loop | Loop 持续执行 - 基于 PDCA 循环的完整任务管理流程 |

</reference>

## 许可证

AGPL-3.0-or-later
