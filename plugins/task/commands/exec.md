---
description: 执行任务 - 获取任务详情、执行、验证验收标准、标记完成
argument-hint: [task-id/keyword] [options]
allowed-tools: Read, Edit, Write, Bash(uv*, uvx*)
model: sonnet
---

# exec

## 命令描述

获取任务详情，自动选择最合适的 Agent 执行任务，对比验收标准进行验证，验证通过后标记任务完成。

## 工作流描述

1. **任务获取**：通过 `uvx --from git+https://github.com/lazygophers/ccplugin task show <id>` 获取任务详情和验收标准
2. **依赖检查**：检查任务的前置依赖是否已完成
3. **任务分析**：分析任务类型、复杂度、验收标准
4. **Agent 选择**：自动选择最合适的 Agent（语言专用优先）
5. **任务执行**：由选定的 Agent 执行任务
6. **结果验证**：执行完成后，对比验收标准进行验证
7. **状态更新**：验证通过后，通过 `uvx --from git+https://github.com/lazygophers/ccplugin task done <id>` 标记完成

## 命令执行方式

### 使用方法

```bash
/exec [task-id] [options]
```

### 执行时机

- 从任务列表中选择待执行的任务
- 快速执行下一个待处理任务
- 验证任务完成情况
- 跟踪单个任务的执行进度

### 执行参数

| 参数          | 说明                       | 示例                    |
| ------------- | -------------------------- | ----------------------- |
| `<task-id>`   | 任务 ID                    | `abc123`                |
| `--next`      | 执行下一个待处理任务       | `/exec --next`          |
| `--dry-run`   | 预览任务信息不执行         | `/exec abc123 --dry-run` |
| `--agent`     | 指定 Agent（覆盖自动选择） | `--agent golang-developer` |
| `--no-mark`   | 执行不标记完成             | `/exec abc123 --no-mark` |

## 任务执行流程

### 1. 任务预检查

通过 `uvx --from git+https://github.com/lazygophers/ccplugin task show <id>` 获取任务信息：

```
✓ 任务存在: abc123 ✓
✓ 状态检查: pending → ready to execute ✓
✓ 依赖检查:
  - 依赖任务 dep001 已完成 ✓
  - 依赖任务 dep002 已完成 ✓
✓ 准备情况: 一切就绪 ✓
```

如果依赖未完成，提示并允许跳过或中断。

### 2. 任务信息展示和 Agent 选择

```
📋 任务信息：abc123

📝 标题: 实现登录 API
📂 类型: feature
⏱️  状态: pending
👤 分配: 待开发

📋 描述:
基于 JWT 的用户登录功能实现

✅ 验收标准:
1. 接受用户名和密码登录
2. 返回有效的 JWT token
3. 实现错误处理和频率限制

🤖 推荐 Agent: golang-developer
  原因: Go 项目，后端 API 开发
  备选: backend-expert

确认执行? (y/n)
```

### 3. 执行任务

选定的 Agent 将：
- 了解任务的完整上下文（类型、描述、验收标准）
- 获取相关代码库信息
- 按照验收标准实现功能
- 编写必要的测试
- 更新相关文档

### 4. 验收标准检查

```
🎯 验收标准检查

✅ 标准 1: 接受用户名和密码登录
   验证: 实现了 POST /api/auth/login 端点，接受 username 和 password

✅ 标准 2: 返回有效的 JWT token
   验证: 成功返回正确格式的 JWT token

✅ 标准 3: 实现错误处理和频率限制
   验证: 实现了 bcrypt 校验和基于 IP 的速率限制

通过: 3/3 ✓
```

若验收标准未全部通过，显示失败项目并中止，需要继续修复后重新执行。

### 5. 状态更新

验收通过后，通过 `uvx --from git+https://github.com/lazygophers/ccplugin task done <id>` 标记完成：

```
✅ 任务执行完成

📊 执行摘要:
- 代码变更: 5 个文件
- 新增测试: 3 个单元测试
- 文档更新: API 文档已更新
- 提交: 1 个 git 提交

⏱️  执行时间: 实际 4.5 小时

✅ 验收标准: 3/3 通过

📝 执行日志: .claude/exec-<task-id>.log

🚀 后续建议:
1. 代码审查: /code-review
2. 测试覆盖率检查
3. 执行下一个任务: /exec --next
```

## 使用示例

### 1. 执行指定任务

```bash
/exec abc123
```

系统将：
- 获取 abc123 任务的详情：`uvx --from git+https://github.com/lazygophers/ccplugin task show abc123`
- 检查依赖是否完成
- 自动选择合适的 Agent 执行
- 对比验收标准进行验证
- 验证通过后标记完成：`uvx --from git+https://github.com/lazygophers/ccplugin task done abc123`

### 2. 预览任务信息（不执行）

```bash
/exec abc123 --dry-run
```

输出：

```
📋 任务信息预览 (未执行)

ID: abc123
标题: 实现登录 API
类型: feature
状态: pending

📝 描述:
基于 JWT 的用户登录功能实现

✅ 验收标准:
1. 接受用户名和密码登录
2. 返回有效的 JWT token
3. 实现错误处理和频率限制

🔗 依赖: 无

🤖 推荐 Agent: golang-developer
```

### 3. 执行下一个待处理任务

```bash
/exec --next
```

系统将：
- 通过 `uvx --from git+https://github.com/lazygophers/ccplugin task list` 获取所有任务
- 找到第一个待处理（pending）的任务
- 自动执行该任务

### 4. 指定 Agent 执行

```bash
/exec abc123 --agent python-developer
```

跳过自动选择，直接使用指定的 Agent 执行任务。

### 5. 执行但不标记完成

```bash
/exec abc123 --no-mark
```

执行任务并验证，但不调用 `task done` 标记完成。用于需要手动审查后再标记的情况。

## Agent 智能选择规则

### 优先级：语言专用 > 任务专用 > 通用

| 任务类型识别                | 主要 Agent                           | 备选 Agent                |
| --------------------------- | ------------------------------------ | ------------------------- |
| 后端/API/业务逻辑           | golang-developer / python-developer  | backend-expert            |
| 前端/页面/组件/UI           | react-developer / vue-developer      | frontend-expert           |
| 数据库/表设计/模型/迁移     | database-expert                      | developer                 |
| 架构设计/模块化/系统设计    | architect                            | microservices-architect   |
| 测试/单元/集成/E2E          | golang-tester / react-tester         | tester                    |
| 代码审查                    | code-reviewer                        | -                         |
| 性能优化                    | performance-optimizer                | -                         |
| 安全审计                    | security-auditor                     | -                         |
| 部署/CI-CD                  | devops-expert                        | -                         |
| 文档编写                    | doc-writer                           | -                         |

### 选择逻辑

1. 根据任务标题、描述、类型字段识别任务性质
2. 优先选择语言专用 Agent（如 golang-developer）
3. 如果无合适语言专用，选择任务专用 Agent（如 database-expert）
4. 最后回退到通用 Agent（如 developer）

## 执行结果处理

### 执行成功

验收标准全部通过时：
- 自动调用 `task done <id>` 标记完成
- 记录执行时间和日志
- 显示后续建议（代码审查、下一个任务等）

### 执行失败

验收标准未通过时：
```
⚠️  任务执行未通过

❌ 验收标准检查:
- 标准 1: ✓ 通过
- 标准 2: ✗ 未通过 (返回 token 格式不正确)
- 标准 3: ✓ 通过

⚡ 问题诊断:
JWT token 结构错误，需要调整生成逻辑

🔧 建议:
1. 检查 JWT 生成器实现
2. 验证 token 格式和过期时间
3. 查看相关测试用例

📝 执行日志: .claude/exec-<task-id>.log

💡 下一步:
  - 继续修复问题后重新执行: /exec <task-id>
  - 标记为阻塞状态: uvx --from git+https://github.com/lazygophers/ccplugin task up <task-id> --status blocked
```

需要返工后重新执行。

## 依赖检查

执行前自动检查任务的前置依赖：

```bash
# 获取任务信息时，检查依赖字段
uvx --from git+https://github.com/lazygophers/ccplugin task show <id>
```

如果存在未完成的依赖：
- 提示依赖任务的 ID 和状态
- 允许继续执行（可能依赖已实际完成但未在系统中标记）
- 或中断当前执行

## 状态更新方式

### 标记完成

验证通过时调用：
```bash
uvx --from git+https://github.com/lazygophers/ccplugin task done <task-id>
```

### 手动更新状态（高级用法）

如需手动更新任务状态为其他值：
```bash
# 标记为进行中
uvx --from git+https://github.com/lazygophers/ccplugin task up <task-id> --status in_progress

# 标记为已阻塞
uvx --from git+https://github.com/lazygophers/ccplugin task up <task-id> --status blocked

# 标记为已取消
uvx --from git+https://github.com/lazygophers/ccplugin task up <task-id> --status cancelled
```

## 执行监控和日志

每次执行会生成日志文件：`.claude/exec-<task-id>.log`

日志包含：
- 执行开始和结束时间
- Agent 选择理由
- 执行过程中的关键步骤
- 验收标准检查结果
- 遇到的问题和解决方案
- 相关的 git 提交信息

## 与其他命令的关系

- **前置**：`/plan` 创建任务
- **配套**：`uvx --from git+https://github.com/lazygophers/ccplugin task list` 查看任务列表
- **后续**：`/code-review` 代码审查，运行测试
- **同步**：通过 `task show`、`task list` 获取最新任务数据

## 注意事项

1. **任务环境**：执行前会自动设置项目环境
2. **并行执行**：不建议同时执行相同任务的多个副本
3. **中断处理**：支持 Ctrl+C 中断，但已完成的工作不会回滚
4. **验收标准**：必须满足所有验收标准才能标记为完成
5. **依赖关系**：正确的依赖关系有助于任务执行顺序的优化

## 常见问题

### Q: 如何处理任务执行失败？
**A**: 执行失败时显示失败项目和诊断建议，修复问题后可重新执行同一任务。系统不会自动标记完成，需要全部验收标准通过才能标记。

### Q: 如何查看任务的详细信息？
**A**: 使用 `--dry-run` 参数预览任务，或者直接调用 `uvx --from git+https://github.com/lazygophers/ccplugin task show <task-id>` 查看完整信息。

### Q: 如何手动标记任务完成？
**A**: 验收通过后会自动调用 `task done`。如果需要手动标记，可使用 `uvx --from git+https://github.com/lazygophers/ccplugin task up <task-id> --status completed`。

### Q: 支持同时执行多个任务吗？
**A**: 当前只支持逐个执行任务。如需并行开发，建议在不同的工作会话中执行不同任务。

### Q: 任务执行中途如何中止？
**A**: 按 Ctrl+C 中止当前执行。已完成的工作会保留，中止后可继续修复或重新执行。
