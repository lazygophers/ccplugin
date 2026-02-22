---
name: golang-skills
description: Golang 开发规范和最佳实践指导，包括代码风格、项目结构、依赖管理、测试策略和性能优化等
---

# Golang 开发规范

## 快速导航

| 文档                                                 | 内容                                                 | 适用场景       |
| ---------------------------------------------------- | ---------------------------------------------------- | -------------- |
| **SKILL.md**                                         | 核心理念、优先包、强制规范速览                       | 快速入门       |
| [development-practices.md](development-practices.md) | 强制规范、优先包使用、错误处理、命名、日志、性能优化 | 日常编码       |
| [architecture-tooling.md](architecture-tooling.md)   | 架构设计、项目结构、代码生成、依赖管理、工具链       | 项目架构和部署 |
| [coding-standards/](coding-standards/)               | 编码规范（错误处理、函数式编程、命名、格式、注释）   | 代码规范参考   |
| [examples/](examples/)                               | 代码示例（good/bad）                                 | 学习参考       |

## 核心理念

Golang 生态追求**高性能、低分配、简洁优雅**，通过精选的工具库和最佳实践，帮助开发者写出高质量的 Go 代码。

**三个支柱**：

1. **零分配** - 尽可能减少内存分配
2. **函数式** - 优先使用函数式编程范式
3. **工程化** - 追求项目结构清晰、可维护性强

## 版本与环境

- **Go 版本**：1.25+ 推荐
- **依赖管理**：go.mod

## 优先包速查

| 用途         | 推荐包               | 用法                |
| ------------ | -------------------- | ------------------- |
| 性能原子操作 | `go.uber.org/atomic` | `atomic.NewInt64()` |

## 核心约定

### 强制规范

- 所有 error 必须记录日志（禁止单行 if）
- 使用全局 State 模式而非 Repository 接口
- 严禁直接返回函数结果而不处理错误
- 严禁使用 `context.Context`
- API Handler 仅做 HTTP 适配，逻辑委托给 Service 层

### 项目结构（三层架构）

```
internal/
├── state/       # 全局状态：数据库、缓存、配置
├── impl/        # Service 层：业务逻辑实现
├── api/         # API 层：HTTP 路由和 Handler
└── middleware/  # 中间件：日志、认证、错误处理
```

## 最佳实践概览

**错误处理**

```go
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)  // 必须记录日志
    return err
}
```

**集合操作**

```go
nameList := candy.Map(userList, func(u *User) string { return u.Name })
// 不允许: for _, u := range users { names = append(names, u.Name) }
```

**命名规范**

```go
type User struct {
    Id        int64  // 主键
    IsActive  bool   // 布尔用 Is/Has 前缀
    Status    int32  // 状态用数字
    CreatedAt time.Time
}
```

## 扩展文档

参见 [development-practices.md](development-practices.md) 了解完整的强制规范、优先包使用、错误处理、函数式编程、命名规范、日志和性能优化指南。
参见 [architecture-tooling.md](architecture-tooling.md) 了解全局状态模式、三层架构、项目结构、代码生成、依赖管理和开发工具链的详细说明。

### 编码规范

- [错误处理规范](coding-standards/error-handling.md) - 错误处理原则、日志规范、错误判断
- [函数式编程规范](coding-standards/functional-programming.md) - 函数式编程原则、Candy 库使用
- [命名规范](coding-standards/naming-conventions.md) - 字段命名、函数命名、包命名、文件命名
- [代码格式规范](coding-standards/code-formatting.md) - 代码格式化、导入规范、注释规范
- [注释规范](coding-standards/comment-standards.md) - 注释原则、注释格式、注释内容

### 项目规范

- [项目结构规范](coding-standards/project-structure.md) - 项目目录布局、包组织规则、文件命名
- [测试规范](coding-standards/testing-standards.md) - 单元测试、集成测试、端到端测试
- [文档规范](coding-standards/documentation-standards.md) - README、API 文档、代码注释
- [版本控制规范](coding-standards/version-control-standards.md) - Git 使用规范、分支管理、提交规范
- [代码审查规范](coding-standards/code-review-standards.md) - 审查原则、审查清单、审查流程

### 代码示例

- [代码示例](examples/) - 符合和不符合规范的代码示例（good/bad）
