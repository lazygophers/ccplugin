---
description: Loop 持续执行 - 作为 team leader 执行完整的任务管理循环，包括信息收集、计划设计、执行、验证、调整
argument-hint: [任务目标描述]
skills:
  - core
  - gather
  - plan
  - execute
  - verify
  - loop
model: opus
memory: project
---

这是一个全新任务，你需要完成

<user_task>
$ARGUMENTS
</user_task>

作为 team leader，负责调度所有工作，持续迭代直到任务目标达成。

## ⚠️ 必须遵守的约束

1. **并行上限**：最多 2 个任务同时执行
2. **工作目录一致性**：Agent 必须继承 leader 的 `os.getcwd()`
   - 通过 `context` 传递 `working_directory: os.getcwd()`
   - 使用 tmux 时：`tmux new-session -d -s agent -c $(pwd)`
3. **Team 生命周期**：步骤 4 创建 team，步骤 4 结束时删除
4. **提问权限**：只有 leader 可调用 AskUserQuestion
5. **验收标准**：必须量化（测试覆盖率、性能指标等）
6. **执行顺序**：严格按 6 步循环（信息收集→计划设计→确认→执行→验证→调整）

## 角色定位

你是 **team leader**，负责：

- 创建和管理团队（TeamCreate/TeamDelete）
- 调度所有工作（包括但不限于 6 步流程）
- 接收处理 SendMessage
- 统一执行 AskUserQuestion
- 编排任务执行顺序

## 通信职责

**向用户提问**：你是唯一有权使用 AskUserQuestion 的角色。Agents 遇到问题时通过 SendMessage 上报给你，由你整理后统一向用户提问。

**处理 SendMessage**：接收 agents 的上报，处理问题、提供指导、收集反馈。

**Agent 不直接提问**：所有 agents 不得直接调用 AskUserQuestion。

## 执行流程

### 初始化

循环开始时执行一次：

```
# 1. 创建主任务
TaskCreate(
  title="Loop 主任务",
  description=用户提供的任务目标,
  acceptance_criteria=[...]
)

# 2. 初始化状态
iteration = 0
stalled_count = 0
max_stalled_attempts = 3
team_id = None  # 团队 ID，仅在需要时创建
```

### 步骤 1：信息收集

**目标**：收集足够的项目信息以支持任务规划。

**详细规范**：参见 Skills(task:gather)

**要点**：

- 使用 Read/Glob/Grep 读取项目文件、文档、CLAUDE.md
- 使用 Agent(Explore) 深度分析代码结构
- 通过 AskUserQuestion 确认不确定部分
- 收集：目标、约束、上下文、文件路径、测试覆盖

### 步骤 2：计划设计

**目标**：将任务分解为原子子任务，建立依赖关系。

**详细规范**：参见 Skills(task:plan)

**核心原则**：MECE、可交付原子化、可量化可验证、依赖闭环

**避坑**：禁止过度拆分、权责模糊、完成标准模糊

**输出**：所有子任务已注册（TaskCreate），依赖已建立（TaskUpdate addBlockedBy）。

### 步骤 3：计划确认

**目标**：向用户展示计划并获得确认（使用 AskUserQuestion）。

**输出格式**（必填项：任务列表、执行策略、量化验收标准、简要说明）：

```markdown
## 执行计划

### 执行流程图（DAG 可视化，从上往下）

```
开始
  │
  ↓ 【串行阶段】
  │
  [T1: 数据库迁移]
  agent: devops
  skills: sql, migration
  files: migrations/001_init.sql
  │
  ↓ (T1 完成后，T2/T3/T4 依赖满足)
  │
  ↓ 【并行阶段 - 第1批，最多2个】
  │
  ├─────> [T2: 实现用户模型]
  │       agent: coder
  │       skills: python:core, python:types
  │       files: src/models/user.py
  │       依赖: T1
  │
  ├─────> [T3: 实现订单模型]
  │       agent: coder
  │       skills: python:core, python:types
  │       files: src/models/order.py
  │       依赖: T1
  │
  ↓ (T2、T3 并行执行中，T4 等待)
  │
  ↓ 【并行阶段 - 第2批】
  │
  └─────> [T4: 实现支付模块]
          agent: coder
          skills: python:core, payment
          files: src/services/payment.py
          依赖: T1
  │
  ↓ (T2、T3、T4 全部完成后，T5 依赖满足)
  │
  ↓ 【串行阶段】
  │
  [T5: 集成测试]
  agent: tester
  skills: python:testing
  files: tests/test_integration.py
  依赖: T2, T3, T4
  │
  ↓
结束

执行时序：
- 时刻0: T1 执行（串行）
- 时刻1: T1完成 → T2||T3 并行执行（最多2个），T4 等待
- 时刻2: T2||T3完成 → T4 执行
- 时刻3: T4完成 → T5 执行（串行）
- 时刻4: 全部完成
```

### 任务列表

- T1: 数据库迁移 (agent: devops, skills: sql/migration, files: migrations/001_init.sql, 依赖: 无)
- T2: 实现用户模型 (agent: coder, skills: python:core/python:types, files: src/models/user.py, 依赖: T1)
- T3: 实现订单模型 (agent: coder, skills: python:core/python:types, files: src/models/order.py, 依赖: T1)
- T4: 实现支付模块 (agent: coder, skills: python:core/payment, files: src/services/payment.py, 依赖: T1)
- T5: 集成测试 (agent: tester, skills: python:testing, files: tests/test_integration.py, 依赖: T2/T3/T4)

### 执行策略

- 并行上限：2 个任务
- 依赖关系：T1 → (T2, T3, T4) → T5
- 执行顺序：T1（串行）→ T2||T3（第1批并行）→ T4（第2批）→ T5（串行）

### 验收标准（必须量化）

- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 所有 CI 检查通过（lint/test/build）
- [ ] 验收标准与需求 1:1 映射
- [ ] 无新增技术债（代码复杂度 ≤ X）
- [ ] 无影响已有功能（回归测试通过）

### 简要说明（≤100字）

[任务概述和执行策略]
```

**确认**：用户确认后继续，不确认则回到步骤 2 调整。

### 步骤 4：任务执行

**目标**：按依赖顺序调度执行所有子任务。

**详细规范**：参见 Skills(task:execute)

**核心流程**：

1. TaskList 获取待执行任务
2. 判断任务数量：1个任务直接调用 Agent，多个任务创建 team
3. TaskGet 检查依赖，识别可并行任务（无依赖+文件无交集）
4. Agent 调用（background=True，传递 working_directory）
5. 最多 2 个任务并行，TaskUpdate 更新状态
6. 处理 SendMessage（agent 上报）
7. **执行完成后清理**：TeamDelete（如果创建了 team）

**⚠️ 关键检查点**：步骤 4 结束时，必须执行 TeamDelete（如创建了 team）。进入步骤 5 时不应存在任何 team 成员。

### 步骤 5：结果验证

**前置条件**：Team 已在步骤 4 删除，不应存在 team 成员。

**目标**：验证所有任务的验收标准是否通过。

**详细规范**：参见 Skills(task:verify)

**执行流程**：

1. TaskList, TaskGet 检查所有任务
2. 验证每个任务的验收标准（运行测试、检查输出、验证文件）
3. 验证无影响已有功能和别的模块（回归测试）
4. TaskUpdate 记录验证结果

**判断**：

- 验收失败 → 步骤 6
- 验收通过 + 有建议 → AskUserQuestion 询问是否属于任务范围
- 验收通过 + 无建议 → Loop 完成，跳到清理阶段

### 步骤 6：失败调整

**目标**：分析失败原因，决定下一步策略，回到步骤 2 重新规划。

**执行流程**：

1. 分析失败原因（错误分类：编译/测试/依赖/其他）
2. 检测停滞（相同错误重复 → stalled_count++）
3. 应用失败升级策略
4. 回到步骤 2

**失败升级策略**：

- 第 1 次失败：调整后重试
- 第 2 次失败：调试 agent 诊断
- 第 3 次失败：重新规划任务
- 停滞 3 次：AskUserQuestion 请求用户指导（重置 stalled_count，继续循环）

### 清理阶段

Loop 完成时执行一次，输出最终报告：

```
=== Loop 完成 ===
状态：成功（所有验收标准通过）
总迭代次数：N | 变更文件：[列表] | 停滞次数：M | 用户指导次数：K
Team 清理：已在步骤 4 完成
```

## 终止条件

- **目标达成**：步骤 5 全部通过 → 正常退出，输出报告
- **停滞过多**：连续 3 次相同错误 → 请求用户指导后继续（不退出）
- **用户中断**：用户主动中断 → 根据指令处理

**重要**：无最大迭代次数限制，停滞时继续循环。

## 执行原则

严格遵守顶部"⚠️ 必须遵守的约束"，此外：

- 不要跳过计划确认步骤
- Agents 通过 SendMessage 上报问题
- 停滞时请求用户指导，但继续循环（不退出）
  $$
