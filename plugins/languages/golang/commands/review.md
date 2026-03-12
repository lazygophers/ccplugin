---
description: 代码审查工作流：检查规范、测试覆盖、lint 问题、性能问题
model: sonnet
memory: project
---

# Go 代码审查工作流

执行完整的代码审查流程。

## 审查步骤

### 1. 功能正确性

- [ ] 代码实现了预期的功能
- [ ] 边界条件已处理
- [ ] 错误处理完善
- [ ] 无逻辑错误
- [ ] 无潜在的 bug

### 2. 代码质量

- [ ] 代码符合编码规范
- [ ] 命名清晰有意义
- [ ] 代码结构清晰
- [ ] 无重复代码
- [ ] 代码简洁易懂

### 3. Skills 规范检查

- [ ] 所有 error 多行处理并记录日志
- [ ] 集合操作使用 candy 库（无手动 for 循环）
- [ ] 字符串转换使用 stringx 库
- [ ] 文件检查使用 osx 库
- [ ] 命名符合规范（Id/Uid/IsActive/CreatedAt）
- [ ] 没有使用 context.Context
- [ ] 没有使用 Repository 接口

### 4. 测试覆盖

- [ ] 单元测试覆盖关键逻辑
- [ ] 集成测试覆盖关键流程
- [ ] 测试用例充分
- [ ] 测试代码质量高
- [ ] 无测试失败

### 5. 性能考虑

- [ ] 无性能瓶颈
- [ ] 内存使用合理
- [ ] 无不必要的分配
- [ ] 并发安全
- [ ] 数据库查询优化

### 6. 安全性

- [ ] 无 SQL 注入风险
- [ ] 无 XSS 风险
- [ ] 无 CSRF 风险
- [ ] 敏感信息加密
- [ ] 访问控制完善

## 运行命令

```bash
gofmt -l .
goimports -l .
go vet ./...
golangci-lint run
go test -v -race -cover ./...
```

## 执行检查清单

### 审查前准备

- [ ] 确认代码已提交到 Git（或暂存区）
- [ ] 确认开发环境已配置（Go 版本、依赖库）
- [ ] 确认必要的 Skills 已加载（core, error, libs, naming）

### 功能正确性检查

- [ ] 代码实现了预期的功能
- [ ] 边界条件已处理（空值、零值、极值）
- [ ] 错误处理完善（所有 error 多行处理并记录日志）
- [ ] 无逻辑错误
- [ ] 无潜在的 bug（空指针、数组越界、死锁）

### 代码质量检查

- [ ] 代码符合编码规范（gofmt, goimports）
- [ ] 命名清晰有意义（符合 naming skill）
- [ ] 代码结构清晰（单一职责、低耦合）
- [ ] 无重复代码（DRY 原则）
- [ ] 代码简洁易懂（避免过度设计）

### Skills 规范检查

- [ ] 所有 error 多行处理并记录日志（`Skills(golang:error)`）
- [ ] 集合操作使用 candy 库（无手动 for 循环，`Skills(golang:libs)`）
- [ ] 字符串转换使用 stringx 库（`Skills(golang:libs)`）
- [ ] 文件检查使用 osx 库（`Skills(golang:libs)`）
- [ ] 命名符合规范（Id/Uid/IsActive/CreatedAt，`Skills(golang:naming)`）
- [ ] 没有使用 context.Context（`Skills(golang:core)`）
- [ ] 没有使用 Repository 接口（`Skills(golang:structure)`）

### 测试覆盖检查

- [ ] 单元测试覆盖关键逻辑（核心函数、边界条件）
- [ ] 集成测试覆盖关键流程（API 端到端）
- [ ] 测试用例充分（正常、边界、异常情况）
- [ ] 测试代码质量高（表驱动测试、AAA 模式）
- [ ] 无测试失败（`go test -v -race -cover ./...`）

### 性能考虑检查

- [ ] 无性能瓶颈（N+1 查询、低效算法）
- [ ] 内存使用合理（避免大量内存分配）
- [ ] 无不必要的分配（使用 sync.Pool 复用对象）
- [ ] 并发安全（使用 atomic, sync.Mutex 正确）
- [ ] 数据库查询优化（索引、批量操作）

### 安全性检查

- [ ] 无 SQL 注入风险（使用参数化查询）
- [ ] 无 XSS 风险（输出转义）
- [ ] 无 CSRF 风险（Token 验证）
- [ ] 敏感信息加密（密码、Token）
- [ ] 访问控制完善（权限验证）

### 命令执行检查

- [ ] `gofmt -l .` 无输出（代码已格式化）
- [ ] `goimports -l .` 无输出（导入已整理）
- [ ] `go vet ./...` 无错误（静态检查通过）
- [ ] `golangci-lint run` 无错误（Lint 检查通过）
- [ ] `go test -v -race -cover ./...` 全部通过（测试通过）

### 审查报告生成检查

- [ ] 报告包含所有问题（文件路径、行号、问题描述）
- [ ] 每个问题附修复建议
- [ ] 区分**问题**（必须修复）和**建议**（可选优化）
- [ ] 提供明确的结论（通过/需要修改）

## 工具调用说明

### 必需命令

| 命令 | 用途 | 调用时机 |
|------|------|---------|
| `gofmt -l .` | 检查代码格式 | 代码质量检查时 |
| `goimports -l .` | 检查导入顺序 | 代码质量检查时 |
| `go vet ./...` | 静态代码检查 | 代码质量检查时 |
| `golangci-lint run` | Lint 检查 | 代码质量检查时 |
| `go test -v -race -cover ./...` | 运行测试 | 测试覆盖检查时 |

### Skills 引用

| Skill | 用途 | 必需性 |
|------|------|--------|
| `Skills(golang:core)` | 核心规范 | **必需** |
| `Skills(golang:error)` | 错误处理规范 | **必需** |
| `Skills(golang:libs)` | 优先库规范 | **必需** |
| `Skills(golang:naming)` | 命名规范 | **必需** |
| `Skills(golang:structure)` | 项目结构规范 | 推荐 |
| `Skills(golang:testing)` | 测试规范 | 推荐 |
| `Skills(golang:concurrency)` | 并发规范 | 按需 |

## 输出格式

```markdown
## 审查结果

### 问题（必须修复）

1. **问题描述**
   - 位置：file.go:123
   - 建议：修复方案

### 建议（可选优化）

1. 优化建议
   - 位置：utils.go:45
   - 理由：性能优化建议

### 结论

- [ ] 通过
- [ ] 需要修改
```

## 注意事项

### 审查质量保证

- 严格遵守 golang skills 规范
- 所有 error 必须多行处理并记录日志
- 优先使用 stringx/candy/osx 库
- 命名必须符合规范（Id/Uid/IsActive/CreatedAt）

### 常见问题

- ❌ 单行 if err != nil（违反 error skill）
- ❌ 手动 for 循环遍历集合（未使用 candy）
- ❌ 使用 context.Context（违反 core skill）
- ❌ 使用 Repository 接口（违反 structure skill）
- ❌ 命名不规范（userId 应为 UserId）

### 最佳实践

- ✅ 使用自动化工具进行客观检查
- ✅ 问题描述包含文件路径和行号
- ✅ 提供具体的修复建议
- ✅ 区分必须修复和建议优化
- ✅ 审查报告结构清晰易读
