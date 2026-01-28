# Fiber 核心概念

## App（应用实例）

App 是 Fiber 框架的核心，管理整个应用的生命周期、路由、中间件和配置。

### 创建应用

```go
import "github.com/gofiber/fiber/v2"

// 创建默认应用
app := fiber.New()

// 创建带配置的应用
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
    DisableHeaderNormalizing: false,
    EnableTrustedProxyCheck: false,
})
```

### 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| AppName | string | - | 应用名称 |
| Prefork | bool | false | 启用 Prefork 模式（多进程） |
| StrictRouting | bool | false | 严格路由（/foo 和 /foo/ 不同） |
| CaseSensitive | bool | false | 路由区分大小写 |
| Immutable | bool | false | 不可变模式（零分配） |
| BodyLimit | int | 4 * 1024 * 1024 | 请求体大小限制（字节） |
| ReadTimeout | time.Duration | nil | 读取超时 |
| WriteTimeout | time.Duration | nil | 写入超时 |
| IdleTimeout | time.Duration | nil | 空闲超时 |
| DisableStartupMessage | bool | false | 禁用启动消息 |
| EnablePrintRoutes | bool | false | 打印所有路由 |

### 应用方法

```go
// 监听端口
app.Listen(":3000")

// 监听 TLS
app.Listen(":3000", "cert.pem", "key.pem")

// 优雅关闭
app.Shutdown()

// 添加路由
app.Get("/", handler)

// 使用中间件
app.Use(middleware())

// 路由分组
api := app.Group("/api")
```

## Context（上下文）

Context 是 Fiber 中最重要的概念，代表 HTTP 请求/响应周期。**Context 会被复用，不要保存引用。**

### 请求信息

```go
func handler(c *fiber.Ctx) error {
    // HTTP 方法
    method := c.Method()  // "GET", "POST", etc.

    // 请求路径
    path := c.Path()      // "/users/123"

    // 完整 URL
    url := c.URL()        // "http://example.com/users/123?foo=bar"

    // 协议
    protocol := c.Protocol() // "http", "https"

    // 主机
    host := c.Hostname()  // "example.com"

    // IP 地址
    ip := c.IP()          // "127.0.0.1"

    // 请求头
    userAgent := c.Get("User-Agent")
    contentType := c.Get("Content-Type")
    allHeaders := c.GetReqHeaders()

    return nil
}
```

### 路径参数

```go
// 定义路由
app.Get("/users/:id", handler)
app.Get("/files/*", handler)

func handler(c *fiber.Ctx) error {
    // 获取路径参数
    id := c.Params("id")           // "123"
    wildcard := c.Params("*")      // 所有通配符内容

    // 带默认值
    name := c.Params("name", "guest")

    return nil
}
```

### 查询参数

```go
func handler(c *fiber.Ctx) error {
    // 获取查询参数
    search := c.Query("search")
    page := c.Query("page", "1")  // 默认值 "1"

    // 获取所有查询参数
    allQueries := c.Queries()

    // 获取数组参数（tags[]=a&tags[]=b）
    tags := c.Query("tags[]")

    return nil
}
```

### 请求体

```go
func handler(c *fiber.Ctx) error {
    // 原始请求体
    body := c.Body()

    // 解析 JSON
    var user User
    if err := c.BodyParser(&user); err != nil {
        return err
    }

    // 解析 XML
    var data Data
    if err := c.Parser(&data); err != nil {
        return err
    }

    return nil
}
```

### 响应

```go
func handler(c *fiber.Ctx) error {
    // 设置状态码
    c.Status(200)

    // 设置响应头
    c.Set("Content-Type", "application/json")
    c.Set("X-Custom-Header", "value")

    // JSON 响应
    return c.JSON(fiber.Map{"message": "ok"})

    // 或使用结构体
    return c.JSON(User{Name: "John"})

    // 字符串响应
    return c.SendString("Hello")

    // HTML 响应
    return c.SendString("<h1>Hello</h1>")

    // 文件响应
    return c.SendFile("./index.html")

    // 自定义状态码
    return c.Status(404).SendString("Not Found")
}
```

### 本地存储

```go
func handler(c *fiber.Ctx) error {
    // 存储数据（仅在当前请求周期有效）
    c.Locals("userID", "123")
    c.Locals("user", user)

    // 获取数据
    userID := c.Locals("userID")
    user, ok := c.Locals("user").(*User)

    return nil
}
```

### Cookies

```go
func handler(c *fiber.Ctx) error {
    // 设置 Cookie
    c.Cookie(&fiber.Cookie{
        Name:     "session",
        Value:    "abc123",
        Expires:  time.Now().Add(24 * time.Hour),
        HTTPOnly: true,
        Secure:   true,
        SameSite: "Strict",
    })

    // 获取 Cookie
    session := c.Cookies("session")

    return nil
}
```

## Handler（处理器）

Handler 是处理请求的函数类型：

```go
type Handler func(*fiber.Ctx) error
```

### 处理器模式

```go
// 简单处理器
func helloHandler(c *fiber.Ctx) error {
    return c.SendString("Hello, World!")
}

// 带业务逻辑的处理器
func getUserHandler(c *fiber.Ctx) error {
    userID := c.Params("id")

    user, err := userService.GetByID(userID)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return fiber.NewError(fiber.StatusNotFound, "User not found")
        }
        return fiber.ErrInternalServerError
    }

    return c.JSON(user)
}

// 处理器链
func authMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        token := c.Get("Authorization")
        if token == "" {
            return c.Status(fiber.StatusUnauthorized).JSON(
                fiber.Map{"error": "missing token"},
            )
        }
        return c.Next()
    }
}

func protectedHandler(c *fiber.Ctx) error {
    return c.JSON(fiber.Map{"message": "authenticated"})
}
```

## Fiber.Error

Fiber 提供了内置的错误类型：

```go
// 创建错误
err := fiber.NewError(fiber.StatusNotFound, "User not found")

// 预定义错误
fiber.ErrBadRequest            // 400
fiber.ErrUnauthorized          // 401
fiber.ErrForbidden             // 403
fiber.ErrNotFound              // 404
fiber.ErrMethodNotAllowed      // 405
fiber.ErrTimeout               // 408
fiber.ErrConflict              // 409
fiber.ErrInternalServerError   // 500
fiber.ErrNotImplemented         // 501
fiber.ErrBadGateway            // 502
fiber.ErrServiceUnavailable    // 503

// 返回错误
func handler(c *fiber.Ctx) error {
    return fiber.ErrBadRequest
}
```

## 生命周期

### 请求生命周期

```
Request → Middleware 1 → Middleware 2 → Handler → Response
           ↓ Next()        ↓ Next()
```

```go
func middleware1() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // 请求前
        log.Println("Middleware 1: Before")

        // 调用下一个处理器
        if err := c.Next(); err != nil {
            return err
        }

        // 响应后
        log.Println("Middleware 1: After")
        return nil
    }
}
```

### 应用生命周期

```go
// Hook: 启动前
app.Hooks().OnListen(func(listenData fiber.ListenData) error {
    log.Println("Server starting on", listenData.Host)
    return nil
})

// Hook: 关闭时
app.Hooks().OnShutdown(func() error {
    log.Println("Server shutting down")
    return nil
})

// Hook: 路由命名
app.Hooks().OnRoute(func(route fiber.Route) error {
    log.Printf("Route: %s %s", route.Method, route.Path)
    return nil
})

// Hook: 发生错误
app.Hooks().OnError(func(err error) {
    log.Printf("Error: %v", err)
})
```

## 工具函数

Fiber 提供了实用工具：

```go
import "github.com/gofiber/fiber/v2/utils"

// 字符串复制（用于持久化 Context 数据）
name := utils.CopyString(c.Params("name"))

// 转换为字符串
str := utils.ToString(bytes)

// 转换为整数
num := utils.ToInt(stringBytes)

// 转换为布尔值
flag := utils.ToBool(stringBytes)

// UUID 生成
id := utils.UUID()

// 解析 IP
ip := utils.ParseIP("127.0.0.1")
```
