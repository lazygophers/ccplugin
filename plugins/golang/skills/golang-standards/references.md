# Golang 标准规范 - 参考资源

本文档包含与 golang-standards 规范相关的外部参考资源和链接。

## 官方资源

### 必读（核心规范）

- **[Effective Go](https://golang.org/doc/effective_go)** - Go 官方风格指南，涵盖命名、格式、注释、错误处理等
- **[Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)** - Go 代码审查意见，常见的错误和最佳实践

### 高级主题

- **[Concurrency Patterns](https://go.dev/blog/pipelines)** - Go 并发模式深入讲解
- **[Error Handling in Go](https://go.dev/blog/error-handling-and-go)** - Go 错误处理的官方讨论
- **[Context Package](https://go.dev/blog/context)** - Context 包的使用和最佳实践

## 项目结构参考

### 推荐布局

- **[Standard Go Project Layout](https://github.com/golang-standards/project-layout)** - Go 项目标准目录结构
- **[Go Package Layout](https://rakyll.org/style-packages/)** - 包设计和组织原则

## 工具和检查

### 代码格式化和检查

- **[gofmt](https://golang.org/cmd/gofmt/)** - 官方代码格式化工具
- **[goimports](https://pkg.go.dev/golang.org/x/tools/cmd/goimports)** - 自动管理 imports
- **[go vet](https://golang.org/cmd/vet/)** - 官方代码检查工具
- **[golangci-lint](https://golangci-lint.run/)** - Go linter 集合

### 测试工具

- **[testing Package](https://golang.org/pkg/testing/)** - Go 标准测试包
- **[testify](https://github.com/stretchr/testify)** - 断言和 mock 库
- **[GoMock](https://github.com/golang/mock)** - 接口 mock 工具

## 性能优化参考

- **[High Performance Go](https://dave.cheney.net/high-performance-go-survey/2019-02)** - Go 性能优化调查和讨论
- **[Go Memory Model](https://golang.org/ref/mem)** - Go 内存模型（并发必读）
- **[Profiling and Optimization](https://go.dev/blog/profiling-go-programs)** - Go 性能分析

## 常见库

### 日志

- **[log Package](https://golang.org/pkg/log/)** - 标准库日志包
- **[logrus](https://github.com/sirupsen/logrus)** - 流行的日志库
- **[zap](https://github.com/uber-go/zap)** - 高性能日志库（Uber）

### HTTP 框架

- **[net/http](https://golang.org/pkg/net/http/)** - 标准库 HTTP 包（推荐）
- **[Fiber](https://gofiber.io/)** - 轻量级 Web 框架
- **[Gin](https://github.com/gin-gonic/gin)** - 高性能 Web 框架
- **[Echo](https://echo.labstack.com/)** - 高效能 Web 框架

### 数据库

- **[database/sql](https://golang.org/pkg/database/sql/)** - 标准库数据库包
- **[GORM](https://gorm.io/)** - 功能强大的 ORM
- **[sqlc](https://sqlc.dev/)** - 类型安全的 SQL 代码生成

### 错误处理

- **[errors Package](https://golang.org/pkg/errors/)** - Go 1.13+ 错误包装（errors.Is, errors.As）
- **[pkg/errors](https://github.com/pkg/errors)** - 功能丰富的错误库

## 安全性参考

- **[Go Security Best Practices](https://golang.org/doc/security)** - Go 官方安全建议
- **[OWASP Top 10](https://owasp.org/www-project-top-ten/)** - Web 应用安全漏洞排行

## 设计模式参考

- **[Design Patterns in Go](https://refactoring.guru/design-patterns/go)** - Go 中的设计模式实现
- **[Functional Options Pattern](https://dave.cheney.net/2014/10/17/functional-options-for-friendly-apis)** - Go 推荐的选项模式

## 相关项目

### 参考实现

- **[Go Standard Library](https://github.com/golang/go)** - Go 标准库源码
- **[Kubernetes](https://github.com/kubernetes/kubernetes)** - 大型 Go 项目参考

## 学习资源

### 教程和书籍

- **[The Go Programming Language](https://gopl.io/)** - Go 经典教材
- **[Go by Example](https://gobyexample.com/)** - Go 示例学习
- **[Go Tips](https://github.com/golang/go/wiki)** - Go Wiki 中的技巧和讨论

## 相关文档

- [错误处理规范](patterns/error-handling.md)
- [函数规范](patterns/function-design.md)
- [分库分包规范](patterns/package-organization.md)
- [架构设计规范](patterns/architecture-design.md)
- [命名规范](patterns/naming-conventions.md)

## 更新时间

最后更新于 2026-01-09
