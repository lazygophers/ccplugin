# golang-skills 风格 - 参考资源

本文档包含与 golang-style 规范相关的外部参考资源和实现示例。

## golang-skills 官方资源

### 核心库

- **[golang/utils](https://github.com/golang/utils)** - 综合工具库

  - `candy` - 函数式编程（Map/Filter/Each/Reverse/Unique/Sort）
  - `stringx` - 字符串转换（CamelCase/SnakeCase）
  - `osx` - 文件操作（IsFile/IsDir/Stat）
  - `json` - JSON 处理
  - `cryptox` - 加密/哈希
  - `xtime` - 时间处理
  - `defaults` - 默认值处理
  - `pterm` - 终端输出美化

- **[golang/log](https://github.com/golang/log)** - 高性能日志库
  - 支持多种日志级别（Info/Warn/Error/Fatal）
  - 高效的日志输出
  - 缓冲优化

### 项目示例

#### Linky Server（优先参考）

Linky 服务器实现了完整的 golang-skills 风格项目，包含：

- **全局状态模式**：所有有状态资源在 state 包中
- **三层架构**：API (Fiber handlers) → Impl (业务逻辑) → State (全局状态)
- **中间件包**：单独的 middleware 包实现所有中间件
- **函数式编程**：99% 场景都是纯函数，无复杂对象方法
- **错误处理**：统一日志 + 多行处理 + 无错误包装
- **消息管理**：WebSocket Hub 等有状态组件在 state 中

**关键文件参考**：

- 全局状态：`internal/state/table.go`
- Service 实现：`internal/impl/user.go`
- API 路由：`internal/api/router.go`
- 中间件：`internal/middleware/`
- 启动流程：`main.go`

#### Ice Cream Heaven 生态

Ice Cream Heaven 包含 14+ Go 项目，提供完整的项目示例：

- **统一错误系统**：错误码 -1/0/1000+
- **泛型模型**：类型安全的 GORM 操作
- **函数式 API**：流畅的函数调用风格
- **Goroutine 安全**：Safe concurrent patterns
- **装饰器模式**：功能组合和扩展

## 官方 Go 资源

### 必读

- **[Effective Go](https://golang.org/doc/effective_go)** - Go 官方风格指南
- **[Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)** - 代码审查意见

### 并发和性能

- **[Concurrency Patterns](https://go.dev/blog/pipelines)** - 并发模式
- **[Go Memory Model](https://golang.org/ref/mem)** - 内存模型
- **[Profiling Go Programs](https://go.dev/blog/profiling-go-programs)** - 性能分析

## 工具和框架

### golang-skills 生态中常用的库

- **Web Framework**：Fiber（轻量级、高性能）
- **Database**：GORM（类型安全、支持泛型）
- **Logging**：golang/log（高性能、统一格式）
- **Utilities**：golang/utils（多功能工具库）

### 补充库

- **Testing**：[testify](https://github.com/stretchr/testify) - 断言和 mock
- **Errors**：[errors](https://golang.org/pkg/errors/) - Go 1.13+ 错误处理
- **Context**：[context](https://golang.org/pkg/context/) - 上下文管理

## 性能优化参考

- **[High Performance Go](https://dave.cheney.net/high-performance-go-survey/2019-02)** - 性能优化调查
- **[Optimization in Go](https://go.dev/blog/pprof)** - 优化技巧
- **[Memory Optimization](https://golang.org/doc/diagnostics)** - 内存优化

## 设计模式

- **[Functional Options Pattern](https://dave.cheney.net/2014/10/17/functional-options-for-friendly-apis)** - Go 推荐的选项模式
- **[Design Patterns in Go](https://refactoring.guru/design-patterns/go)** - 设计模式实现

## 相关项目参考

### 参考实现位置

```
/Users/luoxin/persons/go/ice-cream-heaven/     - Ice Cream Heaven 生态
/Users/luoxin/persons/lyxamour/linky/server/   - Linky Server（优先）
```

### Linky Server 目录结构参考

```
server/
├── main.go                     # 启动入口
├── go.mod
├── go.sum
├── internal/
│   ├── state/                  # 全局状态（所有有状态资源）
│   │   ├── table.go           # 全局数据访问对象
│   │   ├── config.go          # 配置（有状态）
│   │   ├── database.go        # 数据库连接（有状态）
│   │   ├── cache.go           # 缓存（有状态）
│   │   └── init.go            # 初始化
│   ├── impl/                   # Service 层（业务逻辑）
│   │   ├── user.go
│   │   ├── user_test.go
│   │   └── ...
│   ├── api/                    # API 层（HTTP 路由）
│   │   └── router.go
│   └── middleware/             # 中间件（单独包）
│       ├── handler.go         # ToHandler 适配器
│       ├── logger.go
│       ├── auth.go
│       └── error.go
└── cmd/
    └── main.go                # 仅 main.go，无子目录
```

## 学习路径

1. **基础**：阅读 [Effective Go](https://golang.org/doc/effective_go)
2. **工具库**：学习 [golang/utils](https://github.com/golang/utils) 各个模块
3. **实战参考**：研读 [Linky Server](file:///Users/luoxin/persons/lyxamour/linky/server) 源码
4. **项目示例**：参考 [Ice Cream Heaven](file:///Users/luoxin/persons/go/ice-cream-heaven) 的多个项目
5. **性能优化**：实践 [profiling 和 optimization](https://go.dev/blog/profiling-go-programs)

## 相关文档

- [错误处理规范](patterns/error-handling.md)
- [函数设计规范](patterns/function-design.md)
- [分库分包规范](patterns/package-organization.md)
- [架构设计规范](patterns/architecture-design.md)
- [命名规范](patterns/naming-conventions.md)
- [设计模式概述](patterns/PATTERNS_OVERVIEW.md)

## 更新时间

最后更新于 2026-01-09
