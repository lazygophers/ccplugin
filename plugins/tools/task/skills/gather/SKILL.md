---
name: gather
description: 信息收集规范 - 收集项目信息、确认不确定部分的执行规范
user-invocable: false
context: fork
---

# 信息收集规范

信息收集是 loop 循环的第一步，负责收集项目上下文、理解需求、确认不确定部分。

## 执行目标

- 收集足够的项目信息以支持任务规划
- 确认所有不明确或不确定的需求
- 为下一步的计划设计提供完整输入

## 执行步骤

### 1. 读取项目文件

使用工具：Read, Glob, Grep

读取内容：
- 项目README、文档
- 相关代码文件
- 配置文件
- CLAUDE.md 中的规范要求
- 现有测试文件

### 2. 调用 Agent 收集信息

使用工具：Agent

调用场景：
```
import os

# 深度分析代码结构
Agent(
  subagent_type='Explore',
  task="分析项目架构和模块结构",
  background=True,
  context={
    "working_directory": os.getcwd()  # 继承 leader 的工作目录
  }
)

# 研究特定技术栈
Agent(
  subagent_type='技术栈相关 agent',
  task="研究技术栈实现方式",
  background=True,
  context={
    "working_directory": os.getcwd()  # 继承 leader 的工作目录
  }
)
```

Agent 执行内容：
- 分析项目架构
- 识别相关模块和文件
- 理解现有实现方式
- 识别技术约束

**执行要求**：
- 所有 agent 尽可能使用 `background=True` 在后台运行
- Agent 的工作目录必须与 leader 完全一致（通过 `working_directory` 传递）
- 后台运行可以提升执行效率，减少主线程阻塞

### 3. 确认不确定部分

使用工具：AskUserQuestion（仅 leader 可用）

确认内容：
- 不明确的需求细节
- 多个可选方案的选择
- 技术栈或库的选择
- 隐含的约束条件

Leader 提问要求：
- 提供足够的背景信息
- 列出已知信息和待确认信息
- 给出建议选项（如适用）
- 一次提问不超过 3 个相关问题

## 收集清单

必须收集的信息：
- [ ] 用户核心目标（做什么）
- [ ] 成功标准（怎样算完成）
- [ ] 技术约束（技术栈、版本、规范）
- [ ] 项目上下文（现有代码、架构、模块结构）
- [ ] 相关文件路径
- [ ] 依赖的第三方库或服务
- [ ] 测试覆盖情况

## Phase 0 理解快照

在收集信息后，生成**理解快照**并验证完整性。

### 理解快照格式

输出三要素：
1. **Intent（核心意图）**：一句话描述任务目标
2. **Ambiguities（模糊点）**：识别出的不明确要素
3. **Assumptions（假设）**：对模糊点的默认解读

**示例**：
```
=== 理解快照 ===
Intent: 实现用户认证功能，支持邮箱登录和密码重置
Ambiguities:
  - 密码加密算法未明确（bcrypt vs Argon2）
  - Token 过期时间未指定
Assumptions:
  - 默认使用 bcrypt（行业标准）
  - Token 过期时间 24 小时（常见实践）
```

### 完整性门禁（必须通过才能进入计划设计）

| 检查项 | 要求 | 未通过行为 |
|--------|------|-----------|
| 关键约束 | 至少识别 1 个硬性约束 | AskUserQuestion 确认 |
| 范围排除 | 至少定义 1 个明确不做的事 | 继续收集信息 |
| P0 成功指标 | 完成标准可自动验证 | 细化验收标准 |
| 假设注册 | 所有假设已列出待确认 | AskUserQuestion 批量确认 |

### 输出到用户

在进入计划设计前，输出理解快照并使用 AskUserQuestion 确认：

**问题模板**：
```
我对任务的理解如下：

**核心意图**：[Intent]

**识别的模糊点**：
- [Ambiguity 1]
- [Ambiguity 2]

**我的假设**：
- [Assumption 1]
- [Assumption 2]

**关键约束**：
- [Critical Constraint 1]

**明确不做**：
- [Excluded Scope 1]

请确认：
1. 核心意图是否准确？
2. 假设是否合理？
3. 是否有遗漏的约束或排除项？
```

## 输出要求

信息收集完成后，leader 应该掌握：
1. 完整的需求理解
2. 项目技术栈和架构
3. 相关文件和模块列表
4. 技术约束和规范要求
5. 所有不确定部分已确认

## 注意事项

- 不要收集过多无关信息，聚焦任务相关部分
- 不要假设用户意图，不确定时必须提问
- 不要跳过 CLAUDE.md 和项目规范的检查
- Agent 遇到问题时通过 SendMessage 上报给 leader，不直接提问
