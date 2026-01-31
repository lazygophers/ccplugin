---
name: gofiber-skills
description: Go Fiber Web 框架开发规范和最佳实践
---

# Go Fiber Web 框架开发规范

## 框架概述

Fiber 是一个基于 Express.js 设计灵感的 Go Web 框架，构建在 fasthttp 之上，提供高性能的 HTTP 服务。Fiber 的设计目标是简化 Web 开发，同时保持极低的内存占用和快速的执行速度。

**核心特点：**
- 零内存分配路由
- 静态类型、无反射
- 强大的路由系统（支持参数、约束、通配符）
- 丰富的中间件生态
- 简洁的 API 设计

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|----------|
| [核心概念](core/core-concepts.md) | App, Router, Context, Handler | 框架入门 |
| [路由系统](routing/routing.md) | 路由定义、参数、约束、分组 | API 设计 |
| [中间件](middleware/middleware.md) | 中间件开发、内置中间件 | 功能扩展 |
| [数据绑定](data-binding/data-binding.md) | 请求解析、数据验证 | 数据处理 |
| [性能优化](performance/performance.md) | 零分配、对象池、缓存 | 性能调优 |
| [测试](testing/testing.md) | 单元测试、集成测试 | 质量保证 |
| [部署](deployment/deployment.md) | 配置、监控、优雅关闭 | 生产部署 |
| [最佳实践](best-practices/best-practices.md) | 项目结构、错误处理、安全 | 架构设计 |
| [参考资源](references.md) | 官方文档、教程、社区 | 深入学习 |

## 快速开始

```go
package main

import "github.com/gofiber/fiber/v2"

func main() {
    // 创建应用实例
    app := fiber.New(fiber.Config{
        AppName: "My Fiber App",
    })

    // 定义路由
    app.Get("/", func(c *fiber.Ctx) error {
        return c.JSON(fiber.Map{"message": "Hello, Fiber!"})
    })

    // 启动服务器
    app.Listen(":3000")
}
```

## 核心概念

### App（应用实例）

App 是 Fiber 的核心实例，管理路由、中间件和服务器配置。

```go
app := fiber.New(fiber.Config{
    AppName:               "My App",
    Prefork:               false,
    StrictRouting:         true,
    CaseSensitive:         true,
    Immutable:             false,
    BodyLimit:             4 * 1024 * 1024,
    ReadTimeout:           5 * time.Second,
    WriteTimeout:          5 * time.Second,
    IdleTimeout:           30 * time.Second,
    DisableStartupMessage: false,
    EnablePrintRoutes:     true,
})
```

### Context（上下文）

Context 是请求/响应周期的核心，会被复用。不要保存引用。

```go
func handler(c *fiber.Ctx) error {
    // 请求信息
    method := c.Method()
    path := c.Path()
    ip := c.IP()

    // 路径参数
    id := c.Params("id")

    // 查询参数
    search := c.Query("search")
    page := c.Query("page", "1")

    // 响应
    return c.JSON(fiber.Map{"message": "ok"})
}
```

**重要提示**：Context 会被复用，如需持久化数据，使用 `utils.CopyString()`。

### Handler（处理器）

```go
type Handler func(*fiber.Ctx) error

func userHandler(c *fiber.Ctx) error {
    userID := c.Params("id")
    user, err := getUserByID(userID)
    if err != nil {
        return fiber.NewError(fiber.StatusNotFound, "User not found")
    }
    return c.JSON(user)
}
```

## 路由系统

Fiber 提供强大且灵活的路由系统：

```go
// 基础路由
app.Get("/", handler)
app.Post("/", handler)
app.Put("/", handler)
app.Delete("/", handler)

// 路径参数
app.Get("/users/:id", handler)

// 可选参数
app.Get("/users/:id?", handler)

// 通配符
app.Get("/files/*", handler)

// 路由约束（v2.37.0+）
app.Get("/user/:id<int>", handler)
app.Get("/age/:age<min(18);max(120)>", handler)

// 路由分组
api := app.Group("/api")
v1 := api.Group("/v1")
v1.Get("/users", listUsers)
```

详见 [路由系统](routing/routing.md)。

## 中间件

```go
// 自定义中间件
func middleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // 前置处理
        fmt.Println("Before")

        // 调用下一个处理器
        if err := c.Next(); err != nil {
            return err
        }

        // 后置处理
        fmt.Println("After")
        return nil
    }
}

// 使用中间件
app.Use(middleware())

// 内置中间件
import "github.com/gofiber/fiber/v2/middleware/logger"
app.Use(logger.New())
```

详见 [中间件开发](middleware/middleware.md)。

## 性能优化

Fiber 基于零分配设计，提供多种性能优化手段：

```go
// 零分配模式
app := fiber.New(fiber.Config{
    Immutable: false,
})

// 对象池
var userPool = sync.Pool{
    New: func() interface{} {
        return new(User)
    },
}

// 缓存
import "github.com/patrickmn/go-cache"
var cache = cache.New(5*time.Minute, 10*time.Minute)
```

详见 [性能优化](performance/performance.md)。

## 注意事项

1. **Context 复用**：不要持有 Context 引用
2. **与 net/http 不兼容**：Fiber 基于 fasthttp
3. **字符串持久化**：使用 `utils.CopyString()`
4. **路由约束**：需要 v2.37.0+ 版本
5. **零分配模式**：理解并正确使用

## 下一步

- 阅读 [核心概念](core/core-concepts.md) 了解框架基础
- 查看 [最佳实践](best-practices/best-practices.md) 学习架构设计
- 参考 [官方文档](https://docs.gofiber.io/) 获取更多信息
