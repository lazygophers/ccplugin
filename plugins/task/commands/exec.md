---
description: 执行任务 - 从开发计划中读取任务并自动选择合适的 Agent 执行
argument-hint: [task-id/keyword]
allowed-tools: Read, Edit, Write, Bash(uv*)
---

# task-execute

## 命令描述

从开发计划中读取任务，分析任务类型，自动选择最合适的 Agent 执行任务，并记录执行结果。

## 工作流描述

1. **任务读取**：从 `@.claude/开发计划.md` 读取任务信息
2. **任务匹配**：根据 ID 或关键词匹配目标任务
3. **任务分析**：分析任务类型、复杂度、依赖关系
4. **Agent 选择**：自动选择最合适的 Agent（语言专用优先）
5. **任务执行**：由选定的 Agent 执行任务
6. **结果验证**：验证任务输出是否满足验收标准
7. **状态更新**：更新计划中的任务状态和执行时间

## 命令执行方式

### 使用方法

```bash
/task-execute [task-id/keyword] [options]
```

### 执行时机

- 从开发计划中选择任务开始开发
- 需要快速执行下一个计划中的任务
- 验证任务完成情况
- 跟踪任务执行进度

### 执行参数

| 参数          | 说明                       | 示例                             |
| ------------- | -------------------------- | -------------------------------- |
| `<task-id>`   | 任务 ID（TX.Y.Z 格式）     | `T1.1.1`                         |
| `<keyword>`   | 任务关键词                 | `用户认证`                       |
| `--next`      | 执行下一个待开发任务       | `/task-execute --next`           |
| `--dry-run`   | 预览任务信息不执行         | `/task-execute T1.1.1 --dry-run` |
| `--agent`     | 指定 Agent（覆盖自动选择） | `--agent golang-developer`       |
| `--no-update` | 执行不更新计划             | `--no-update`                    |

## Agent 智能选择规则

### 优先级：语言专用 > 任务专用 > 通用

| 任务类型识别                | 主要 Agent                                          | 备选 Agent                       |
| --------------------------- | --------------------------------------------------- | -------------------------------- |
| 后端/API/服务/认证/业务逻辑 | golang-developer / python-developer                 | backend-expert / developer       |
| 前端/页面/组件/UI/交互      | react-developer / vue-developer / flutter-developer | frontend-expert / ui-ux-reviewer |
| 数据库/表设计/模型/迁移     | database-expert                                     | developer                        |
| 架构设计/模块化/系统设计    | architect                                           | microservices-architect          |
| 测试/单元/集成/E2E          | golang-tester / react-tester / python-tester        | tester                           |
| 代码审查                    | code-reviewer                                       | -                                |
| 性能优化                    | performance-optimizer                               | -                                |
| 安全审计                    | security-auditor                                    | -                                |
| 部署/CI-CD/容器             | devops-expert                                       | -                                |
| 文档编写                    | doc-writer                                          | -                                |

## 执行流程

### 1. 任务预检查

```
✓ 任务存在: T1.1.1 ✓
✓ 状态检查: pending → ready to execute ✓
✓ 依赖检查:
  - T1.1.1 无前置依赖 ✓
✓ 准备情况: 一切就绪 ✓
```

### 2. Agent 选择和确认

```
📋 任务: T1.1.1 实现登录API

🔍 任务分析:
- 类型: 后端 (API 实现)
- 复杂度: 中等
- 验收标准: 3 个
- 工作量: 4-6h

🤖 推荐 Agent: golang-developer
- 原因: Go 项目，后端 API 开发
- 备选: backend-expert

确认执行? (y/n)
```

### 3. 执行任务

选择的 Agent 将：

- 了解任务的完整上下文
- 阅读相关代码库部分
- 按照验收标准实现功能
- 编写必要的测试
- 更新相关文档

### 4. 验收标准检查

```
🎯 验收标准检查

✅ 标准 1: 接受用户名和密码登录
   验证: 实现了 POST /api/auth/login 端点

✅ 标准 2: 返回 JWT token
   验证: 成功返回有效的 JWT token

✅ 标准 3: 错误处理和频率限制
   验证: 实现了 bcrypt 校验和速率限制

通过: 3/3 ✓
```

### 5. 状态更新

```
📝 计划状态更新

任务 T1.1.1:
  状态: pending → completed ✓
  耗时: 实际 4.5h (预估 4-6h) ✓
  完成时间: 2025-01-06 18:30:00

📊 计划进度更新:
  总任务: 25
  已完成: 11 (+1)
  进行中: 3
  待开发: 11 (-1)
  完成率: 40% → 44% ✓
```

## 使用示例

### 1. 指定任务 ID 执行

```bash
/task-execute T1.1.1
```

### 2. 使用关键词匹配

```bash
# 搜索包含"登录"的任务
/task-execute 登录

# 搜索包含多个关键词的任务
/task-execute "用户认证"
```

### 3. 执行下一个待开发任务

```bash
/task-execute --next
```

输出：

```
🎯 下一个待开发任务: T1.1.2 实现注册功能

继续执行? (y/n)
```

### 4. 预览任务信息

```bash
/task-execute T1.1.1 --dry-run
```

输出：

```
📋 任务信息预览 (未执行)

ID: T1.1.1
标题: 实现登录API
父任务: T1.1 (MVP: 基础登录)
优先级: 高

📝 描述:
基于 JWT 的用户认证系统

✅ 验收标准:
1. 接受用户名和密码登录
2. 返回 JWT token
3. 实现错误处理和频率限制

🔗 依赖: 无
⏱️  工作量: 4-6h

🤖 推荐 Agent: golang-developer
```

### 5. 指定 Agent 执行

```bash
/task-execute T1.1.1 --agent python-developer
```

### 6. 执行但不更新计划

```bash
/task-execute T1.1.1 --no-update
```

## 任务互动模式

### 交互式选择（无参数）

```bash
/task-execute
```

输出：

```
📋 选择要执行的任务

🔴 待开发 (11 个):
 1. T1.1.1 实现登录API (高优先级, 4-6h)
 2. T1.1.2 实现注册功能 (高优先级, 3-4h)
 3. T1.1.3 实现用户退出 (中优先级, 2h)
 ...

请输入任务编号或 ID (1-11, q 退出):
```

## 任务执行结果追踪

### 执行完成后

```
✅ 任务执行完成

📊 执行摘要:
- 代码变更: 5 个文件修改
- 新增测试: 3 个单元测试
- 文档更新: API 文档已更新
- 提交: 1 个 git 提交

🎯 验收标准: 3/3 通过 ✓

⏱️  执行时间: 4.5h (预估: 4-6h)

📝 执行日志: .claude/execution-T1.1.1.md

🚀 后续建议:
1. Code Review: /code-review
2. 测试覆盖率: /test
3. 执行下一个任务: /task-execute --next
```

### 失败或异常

```
⚠️  任务执行中止

❌ 验收标准未通过:
- 标准 1: ✓
- 标准 2: ✗ (返回 token 格式不正确)
- 标准 3: ✓

⚡ 问题诊断:
JWT token 结构错误，需要调整生成逻辑

🔧 建议:
1. 检查 JWT 生成器实现
2. 验证 token 格式
3. 运行测试: pytest tests/auth_test.py

📝 执行日志: .claude/execution-T1.1.1.md

状态: 标记为需返工 (需修复后重新执行)
```

## 执行监控和日志

每次执行会生成日志文件：`.claude/execution-<task-id>.md`

日志包含：

- 执行时间和耗时
- Agent 选择理由
- 执行过程和变更
- 验收标准检查结果
- 遇到的问题和解决方案
- 相关的 git 提交和代码行数

## 与其他命令的关系

- **前置**：`/plan-create` 或 `/plan-update` 创建任务
- **配套**：`/plan-review` 审查计划
- **后续**：`/code-review` 代码审查，`/test` 测试
- **同步**：`/plan-sync` 同步计划和任务数据库
- **报告**：`/progress-report` 生成进度报告

## 相关 Skills

- `code-review-standards` - 代码审查标准
- `test-strategy` - 测试策略
- `project-onboarding` - 项目结构

## 执行脚本

```bash
uv run scripts/task_execute.py "$@"
```

## 安全机制

### 依赖检查

- 执行前自动检查前置任务是否完成
- 发现未完成的依赖时提示并允许跳过

### 状态保护

- 已完成的任务不能重复执行（除非明确重置）
- 进行中的任务可以继续执行

### 变更跟踪

- 所有执行都记录在 git 中
- 每次执行生成对应的执行日志
- 支持查看执行历史

## 注意事项

1. **任务环境**：执行前会自动设置项目环境
2. **并行执行**：不建议同时执行相同任务的多个副本
3. **状态同步**：执行完成后自动更新计划文件
4. **中断处理**：支持 Ctrl+C 中断，保存当前进度
5. **验收标准**：必须满足所有验收标准才能标记为完成
