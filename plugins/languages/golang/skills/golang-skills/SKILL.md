---
name: golang-skills
description: Golang 开发规范和最佳实践指导，包括代码风格、项目结构、依赖管理、测试策略和性能优化等
---

# Golang 生态开发规范

## 快速导航

| 文档                                                 | 内容                                                 | 适用场景       |
| ---------------------------------------------------- | ---------------------------------------------------- | -------------- |
| **SKILL.md**                                         | 核心理念、优先包、强制规范速览                       | 快速入门       |
| [development-practices.md](development-practices.md) | 强制规范、优先包使用、错误处理、命名、日志、性能优化 | 日常编码       |
| [architecture-tooling.md](architecture-tooling.md)   | 架构设计、项目结构、代码生成、依赖管理、工具链       | 项目架构和部署 |

## 核心理念

Golang 生态追求**高性能、低分配、简洁优雅**，通过精选的工具库和最佳实践，帮助开发者写出高质量的 Go 代码。

**三个支柱**：

1. **零分配** - 尽可能减少内存分配
2. **函数式** - 优先使用函数式编程范式
3. **工程化** - 追求项目结构清晰、可维护性强

## 版本与环境

- **Go 版本**：1.25+ 推荐
- **Go 工具链**：最新 1.x 版本
- **依赖管理**：go.mod + go.sum
- **测试框架**：testing + testify（可选）

## 优先包速查

| 用途         | 推荐包               | 用法                           |
| ------------ | -------------------- | ------------------------------ |
| 字符串转换   | `stringx`            | `stringx.ToCamel("user_name")` |
| 集合操作     | `candy`              | `candy.Map/Filter/Each`        |
| 文件操作     | `osx`                | `osx.IsFile(path)`             |
| 类型转换     | `candy`              | `candy.ToInt64(v)`             |
| 日志记录     | `golang/log`         | `log.Infof/Errorf`             |
| 性能原子操作 | `go.uber.org/atomic` | `atomic.NewInt64()`            |

## 核心约定

### 强制规范

- ✅ 所有字符串转换使用 `stringx` 包
- ✅ 所有集合操作使用 `candy` 包（不允许手动循环）
- ✅ 所有文件操作使用 `osx` 包
- ✅ 所有 error 必须记录日志（禁止单行 if）
- ✅ 使用全局 State 模式而非 Repository 接口
- ✅ Service 层函数遵循 `func Xxx(ctx context.Context, ...) error` 签名
- ✅ API Handler 仅做 HTTP 适配，逻辑委托给 Service 层

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
names := candy.Map(users, func(u *User) string { return u.Name })
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

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **本规范** - 中优先级
3. **传统 Go 实践** - 最低优先级
