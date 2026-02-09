# 代理协作模式

## 单代理模式

### 独立执行

```
@dev 实现登录功能
```

**特点：**
- 单一代理完成任务
- 上下文隔离（fork）
- 自主决策

## 多代理协作

### 协调者模式

```
@orchestrator 管理项目
  └─> @dev 开发功能
  └─> @test 编写测试
  └─> @review 审查代码
```

### 链式模式

```
@researcher 调研方案
  ↓
@planner 制定计划
  ↓
@dev 执行开发
  ↓
@review 最终审查
```

## 代理通信

### Task 工具调用

```markdown
# 协调代理

你是项目协调者，负责协调多个代理完成复杂任务。

## 能力

- 任务分解
- 代理调度
- 结果整合

## 工作流程

1. 分解任务为子任务
2. 调用合适代理
3. 收集结果
4. 整合报告
```

### SendMessage 通信

```markdown
# Team 代理

你是团队领导，协调团队成员工作。

## 成员

- @researcher - 研究员
- @developer - 开发者
- @reviewer - 审查员

## 协作流程

1. 使用 `@researcher` 调研需求
2. 使用 `@developer` 实现功能
3. 使用 `@reviewer` 审查代码
4. 使用 `SendMessage` 协调成员
```

## 并行执行

### 适用场景

- 独立的调查
- 多个不相关的研究区域
- 同时探索不同模块

```
Research the authentication, database, and API modules in parallel using separate subagents
```

**注意：** 许多 subagents 返回详细结果会消耗大量上下文。

## 协作示例

### 完整工作流

```markdown
# 项目经理

你是项目经理，负责协调完成整个项目。

## 团队

- @explorer - 探索代码库
- @architect - 设计架构
- @developer - 实现功能
- @tester - 编写测试
- @reviewer - 审查代码

## 工作流程

### 阶段 1：理解需求
1. 使用 `@explorer` 了解现有代码
2. 使用 `@architect` 设计方案

### 阶段 2：实现功能
3. 使用 `@developer` 编写代码
4. 使用 `@tester` 验证功能

### 阶段 3：质量保证
5. 使用 `@reviewer` 审查代码
6. 整合所有结果
```

## 上下文管理

### Fork 模式（推荐）

```yaml
---
name: dev
description: 开发代理
context: fork      # 独立上下文
tools:
  - Read
  - Write
  - Bash
---
```

**优势：**
- 不污染主会话
- 独立错误恢复
- 清晰的边界

### Inherit 模式

```yaml
---
name: assistant
description: 助手代理
context: inherit   # 继承上下文
tools:
  - Read
  - Write
---
```

**使用场景：**
- 需要访问主会话状态
- 轻量级任务
- 协作调试
