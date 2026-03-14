---
name: core
description: Task 插件核心规范 - 任务管理生命周期、状态机、角色分工和基本概念
user-invocable: true
context: fork
---

# Task 插件核心规范

Task 插件提供任务管理框架，支持任务规划、执行、验证和迭代。不提供具体实现 agents，使用其他插件或用户自定义的 agents。

## 任务生命周期

任务状态转换：

```
pending → in_progress → completed
                     → failed → (重新规划或修复)
```

### 状态说明

- **pending**: 任务已创建，等待执行
- **in_progress**: 任务正在执行中
- **completed**: 任务已完成，验证通过
- **failed**: 任务执行失败，需要分析修复

## 角色分工

### Team Leader (/loop 命令)

职责：
- 创建和管理团队 (TeamCreate/TeamDelete)
- 调度所有工作（包括但不限于 6 步流程）
- 接收处理 SendMessage
- 统一执行 AskUserQuestion
- 编排任务执行顺序

### Agents（由其他插件或用户提供）

职责：
- 执行具体的任务（收集、规划、编码、测试、验证等）
- 通过 SendMessage 向 leader 上报结果或问题
- 不直接调用 AskUserQuestion
- 不调用其他 agents

## 设计原则

1. **框架优先** - 提供任务管理框架和规范，不提供具体实现 agents
2. **Agent 灵活** - 使用其他插件或用户自定义的 agents 执行具体任务
3. **Leader 统一** - /loop 命令作为 team leader 统一管理所有调度和提问
4. **消息上报** - Agents 通过 SendMessage 向 leader 上报，leader 通过 AskUserQuestion 向用户提问
5. **原子任务** - 每个任务必须是原子性的、不可再分的
6. **并行控制** - 最多 2 个任务并行，不修改同一文件或模块
7. **工作目录一致** - Agent 的工作目录必须与 leader 完全一致

## 决策优先级层次

当出现冲突或需要权衡时，遵循以下优先级：

**Safety（安全）** > **Correctness（正确性）** > **Efficiency（效率）** > **Completeness（完整性）**

### 实际应用示例

| 场景 | 冲突 | 决策 | 理由 |
|------|------|------|------|
| 用户输入验证 | 完整性（支持所有边界情况）vs 安全（严格过滤） | 选择安全 | 防止注入攻击 > 功能覆盖 |
| 测试覆盖 | 正确性（100%覆盖）vs 效率（快速交付） | 选择正确性 | 未测试的代码 = 隐藏 bug |
| 代码重构 | 效率（优化性能）vs 完整性（保留所有功能） | 选择效率 | 在不破坏功能前提下优化 |
| 依赖引入 | 完整性（使用成熟库）vs 安全（减少攻击面） | 选择安全 | 最小依赖原则 |

### 在失败调整中应用

当任务失败需要权衡时：

1. **优先检查安全性**：是否引入了 SQL 注入、XSS、命令注入等风险？
2. **其次检查正确性**：功能是否符合验收标准？测试是否通过？
3. **再考虑效率**：性能是否可接受？资源使用是否合理？
4. **最后考虑完整性**：边界情况是否全部覆盖？文档是否完善？

## 内置工具使用规范

### Task 管理工具

| 工具 | 用途 | 调用时机 |
|------|------|---------|
| TaskCreate | 创建任务 | 规划阶段创建子任务 |
| TaskUpdate | 更新任务状态和 metadata | 任务状态变更时 |
| TaskList | 列出所有任务 | 查询任务列表时 |
| TaskGet | 获取任务详情 | 查询单个任务时 |
| TaskStop | 停止任务执行 | 需要中断时 |
| TaskOutput | 读取任务输出 | 需要查看任务结果时 |

### Team 管理工具

| 工具 | 用途 | 调用时机 |
|------|------|---------|
| TeamCreate | 创建团队 | 步骤 4（任务执行）开始时，**仅当有多个任务时**创建 |
| TeamDelete | 删除团队 | 步骤 4（任务执行）结束时**立即**删除 |

**Team 使用规则**：
- 只有 1 个任务：不创建 team，直接使用 Agent 执行
- 有多个任务：创建 team，通过 team 管理并行/串行执行
- Team 生命周期**仅限于**步骤 4（任务执行）
- **⚠️ 步骤 4 结束时必须删除 team**，步骤 5 不应存在任何 team 成员

**常见问题**：
- 如果在步骤 5 或 Loop 完成时仍能看到 `@executor-*` 成员
- 说明步骤 4 的 TeamDelete 未执行
- 必须立即执行 `TeamDelete(team_id)` 补救

### 通信工具

| 工具 | 用途 | 调用时机 |
|------|------|---------|
| Agent | 调用 agent 执行任务 | 需要 agent 执行具体工作时 |
| SendMessage | 发送消息给 leader 或成员 | Agent 向 leader 上报时 |
| AskUserQuestion | 向用户提问 | Leader 需要用户确认或指导时 |

### Agent 工作目录规范

**⚠️ 严格要求**：Agent 的工作目录必须与 team leader 完全一致。

**实现方式**：
```python
import os

# 每次调用 Agent 时传递工作目录
Agent(
  subagent_type="...",
  task="...",
  background=True,
  context={
    "working_directory": os.getcwd(),  # 继承 leader 的当前目录
    ...
  }
)
```

**使用 tmux 的特殊要求**：
- 如果使用 tmux 启动 agent，必须显式指定启动目录为 leader 的工作目录
- 不允许使用 tmux 的默认目录（通常是 `~`）
- 不允许使用其他任何目录
- 示例：`tmux new-session -d -s agent-session -c /path/to/leader/directory`

**原因**：
- 确保 agent 访问的相对路径与 leader 相同
- 避免 "文件找不到" 错误
- 保证任务执行的一致性

## 任务元数据规范

每个任务的 metadata 必须包含：

```json
{
  "target_files": ["文件路径"],
  "agent_type": "agent 名称",
  "skills": ["skill1", "skill2"],
  "retry_count": 0,
  "verification_result": {},
  "failure_reason": "",
  "iteration": 1,
  "anchor_snapshot": {}
}
```

### anchor_snapshot 字段规范

`anchor_snapshot` 用于存储任务的理解快照，作为单一真相来源防止目标偏移。所有子字段均为可选，但主任务建议完整填写。

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `version` | string | 快照版本号，修改时递增 | `"v1"` |
| `intent` | string | 核心意图，一句话描述任务目标 | `"实现用户认证功能，支持邮箱登录和密码重置"` |
| `critical_constraints` | string[] | 关键约束列表，必须满足的硬性条件 | `["必须使用 Python 3.11+", "不允许引入新依赖"]` |
| `excluded_scope` | string[] | 明确不做的事情列表，防止范围蔓延 | `["不实现前端界面", "不处理并发场景"]` |
| `assumptions` | string[] | 假设列表，对模糊点的默认解读 | `["默认使用 SQLite", "用户已安装 Docker"]` |

**完整示例**：

```json
{
  "anchor_snapshot": {
    "version": "v1",
    "intent": "实现用户认证功能，支持邮箱登录和密码重置",
    "critical_constraints": [
      "必须使用 Python 3.11+",
      "不允许引入新的第三方依赖"
    ],
    "excluded_scope": [
      "不实现前端界面",
      "不处理并发场景"
    ],
    "assumptions": [
      "默认使用 SQLite 数据库",
      "用户已安装 Docker"
    ]
  }
}
```

**使用规则**：
- 修改 `anchor_snapshot` 时必须递增 `version`（v1 → v2）并通过 AskUserQuestion 获得用户确认
- 在验证阶段（Verify）读取 `anchor_snapshot` 检查意图对齐和约束满足情况
- 当新指令与 `intent` 语义冲突时，触发意图偏移检测

## 并行执行规范

### 并行条件

两个任务可以并行执行当且仅当：
1. 无依赖关系（通过 TaskUpdate addBlockedBy 建立）
2. 不修改同一文件
3. 不修改同一模块或包
4. 总并行数不超过 2

### 串行条件

任务必须串行执行如果：
1. 存在依赖关系
2. 修改同一文件或模块
3. 当前已有 2 个并行任务

## 失败处理原则

### 失败分类

1. **任务定义问题** - 任务拆分不合理，需要重新规划
2. **执行失败** - 代码错误、环境问题等，需要修复
3. **验证失败** - 不符合验收标准，需要调整

### 处理策略

- 第 1 次失败：分析原因，调整后重试
- 第 2 次失败：使用调试类 agent 深入诊断
- 第 3 次失败：重新规划任务拆分
- 仍然失败：向用户请求指导

## 验收标准规范

每个任务必须定义明确的验收标准，格式：

```
验收标准：
- [ ] 可自动验证的检查项 1
- [ ] 可自动验证的检查项 2
- [ ] 可自动验证的检查项 3
```

要求：
- 必须可自动验证（测试、编译、lint 等）
- 避免主观判断（如"代码质量好"）
- 每项独立可检查

## 子任务定义模板

```markdown
### T[N]: [标题]
- 描述：[做什么、为什么做]
- 输入：[文件/数据/前置任务输出]
- 输出：[文件变更/数据产出]
- 依赖：[T1, T2] 或 无
- 验收标准：
  - [ ] [可自动验证的条件]
- Agent类型：[agent名称]
- Skills：[skill1, skill2]
```