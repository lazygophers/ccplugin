# Fiber 中间件

中间件是 Fiber 框架的核心功能，用于在请求处理前后执行自定义逻辑。

## 中间件基础

### 中间件结构

```go
func middleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // 请求前处理
        fmt.Println("Before handler")

        // 调用下一个处理器
        if err := c.Next(); err != nil {
            return err
        }

        // 响应后处理
        fmt.Println("After handler")
        return nil
    }
}
```

### Next() 流程

```
Request → Middleware1 (Before) → Middleware2 (Before) → Handler
                                                    ↓
Middleware2 (After) ← Middleware1 (After) ← Response
```

```go
func middleware1() fiber.Handler {
    return func(c *fiber.Ctx) error {
        log.Println("Middleware 1: Before")

        // 调用下一个处理器
        if err := c.Next(); err != nil {
            return err
        }

        log.Println("Middleware 1: After")
        return nil
    }
}

func middleware2() fiber.Handler {
    return func(c *fiber.Ctx) error {
        log.Println("Middleware 2: Before")
        if err := c.Next(); err != nil {
            return err
        }
        log.Println("Middleware 2: After")
        return nil
    }
}
```

## 中间件使用

### 全局中间件

```go
app.Use(middleware())

// 多个全局中间件
app.Use(middleware1())
app.Use(middleware2())

// 或链式调用
app.Use(middleware1()).Use(middleware2())
```

### 路由组中间件

```go
api := app.Group("/api", func(c *fiber.Ctx) error {
    c.Set("X-API-Version", "v1")
    return c.Next()
})

api.Use(authMiddleware)
api.Use(loggerMiddleware)

v1 := api.Group("/v1")
v1.Get("/users", listUsers)
```

### 单个路由中间件

```go
app.Get("/protected", authMiddleware(), handler)

// 多个中间件
app.Get("/protected",
    authMiddleware(),
    rateLimitMiddleware(),
    handler,
)
```

### 路由组 + 单个路由

```go
// 组级中间件应用于所有子路由
authenticated := app.Group("/auth", AuthMiddleware())

// 单个路由额外中间件
authenticated.Get("/admin", AdminOnly(), adminHandler)
authenticated.Get("/profile", profileHandler)
```

## 内置中间件

### Logger（日志）

```go
import "github.com/gofiber/fiber/v2/middleware/logger"

// 默认配置
app.Use(logger.New())

// 自定义配置
app.Use(logger.New(logger.Config{
    // 日志格式
    Format: "[${time}] ${status} - ${method} ${path}\n",
    // 时区
    TimeFormat: "2006-01-02 15:04:05",
    TimeZone:   "Asia/Shanghai",
    // 输出
    Output:     os.Stdout,
    // 标签
    Tags: []string{"time", "status", "method", "path", "latency", "ip"},
}))

// 自定义格式
app.Use(logger.New(logger.Config{
    Format: "[${ip}] ${status} ${method} ${path} - ${latency}\n",
}))

// 仅记录特定状态码
app.Use(logger.New(logger.Config{
    Next: func(c *fiber.Ctx) bool {
        // 跳过 200 状态码
        return c.Response().StatusCode() == 200
    },
}))
```

### CORS（跨域）

```go
import "github.com/gofiber/fiber/v2/middleware/cors"

// 默认配置（允许所有来源）
app.Use(cors.New())

// 自定义配置
app.Use(cors.New(cors.Config{
    // 允许的来源
    AllowOrigins:     "https://example.com,https://www.example.com",
    AllowOriginsFunc: func(origin string) bool {
        return origin == "https://trusted.com"
    },
    // 允许的方法
    AllowMethods:     "GET,POST,PUT,DELETE,OPTIONS",
    // 允许的请求头
    AllowHeaders:     "Origin,Content-Type,Accept,Authorization",
    // 暴露的响应头
    ExposeHeaders:    "Content-Length",
    // 允许凭证
    AllowCredentials: true,
    // 预检请求缓存时间
    MaxAge:           86400,
}))
```

### Compress（压缩）

```go
import "github.com/gofiber/fiber/v2/middleware/compress"

// 默认配置
app.Use(compress.New())

// 自定义配置
app.Use(compress.New(compress.Config{
    // 压缩级别
    Level: compress.LevelBestSpeed, // -1, 0-9
    // 最小压缩大小
    MinLength:    512,
    // 排除的路径
    ExcludedPaths: []string{"/api/v1"},
}))
```

### Recover（恢复）

```go
import "github.com/gofiber/fiber/v2/middleware/recover"

// 默认配置
app.Use(recover.New())

// 自定义配置
app.Use(recover.New(recover.Config{
    // 堆栈跟踪
    EnableStackTrace: true,
    // 仅开发环境
    StackTraceHandler: func(c *fiber.Ctx, e interface{}) {
        if os.Getenv("ENV") == "development" {
            log.Println(e)
        }
    },
}))
```

### Limiter（限流）

```go
import "github.com/gofiber/fiber/v2/middleware/limiter"

// 默认配置
app.Use(limiter.New())

// 自定义配置
app.Use(limiter.New(limiter.Config{
    // 最大请求数
    Max:        100,
    // 时间窗口
    Expiration: 1 * time.Minute,
    // Key 生成函数
    KeyGenerator: func(c *fiber.Ctx) string {
        return c.Get("X-API-Key")
    },
    // 限制响应
    LimitReached: func(c *fiber.Ctx) error {
        return c.Status(fiber.StatusTooManyRequests).JSON(
            fiber.Map{"error": "rate limit exceeded"},
        )
    },
    // 存储
    Storage: nil, // 使用内存
}))

// 基于 IP 的限流
app.Use(limiter.New(limiter.Config{
    Max:        10,
    Expiration: 1 * time.Minute,
    KeyGenerator: func(c *fiber.Ctx) string {
        return c.IP()
    },
}))
```

### CSRF（跨站请求伪造）

```go
import "github.com/gofiber/fiber/v2/middleware/csrf"

// 默认配置
app.Use(csrf.New())

// 自定义配置
app.Use(csrf.New(csrf.Config{
    // Secret
    Secret:    "my-secret-key",
    // Cookie 名称
    CookieName: "csrf_",
    // Cookie 过期时间
    CookieExpires: 24 * time.Hour,
    // Cookie 安全
    CookieSecure:   true,
    CookieHTTPOnly: true,
    // 上下文键
    ContextKey: "csrf",
    // Token 长度
    TokenLength: 32,
}))
```

### Helmet（安全头）

```go
import "github.com/gofiber/fiber/v2/middleware/helmet"

app.Use(helmet.New())
```

### Session（会话）

```go
import "github.com/gofiber/fiber/v2/middleware/session"

// 创建 session 存储
store := session.New()

app.Get("/", func(c *fiber.Ctx) error {
    // 获取 session
    sess, err := store.Get(c)
    if err != nil {
        return err
    }

    // 设置值
    sess.Set("name", "John")
    sess.Set("age", 30)

    // 保存 session
    if err := sess.Save(); err != nil {
        return err
    }

    return c.SendString("Session set")
})

app.Get("/get", func(c *fiber.Ctx) error {
    sess, err := store.Get(c)
    if err != nil {
        return err
    }

    name := sess.Get("name")
    return c.SendString("Name: " + name)
})
```

## 自定义中间件

### 认证中间件

```go
func AuthMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // 获取 Token
        token := c.Get("Authorization")
        if token == "" {
            return c.Status(fiber.StatusUnauthorized).JSON(
                fiber.Map{"error": "missing authorization header"},
            )
        }

        // 移除 "Bearer " 前缀
        if strings.HasPrefix(token, "Bearer ") {
            token = token[7:]
        }

        // 验证 Token
        claims, err := validateToken(token)
        if err != nil {
            return c.Status(fiber.StatusUnauthorized).JSON(
                fiber.Map{"error": "invalid token"},
            )
        }

        // 存储用户信息
        c.Locals("userID", claims.UserID)
        c.Locals("role", claims.Role)

        return c.Next()
    }
}

// 使用
app.Get("/protected", AuthMiddleware(), protectedHandler)
```

### 角色中间件

```go
func RoleMiddleware(roles ...string) fiber.Handler {
    return func(c *fiber.Ctx) error {
        userRole := c.Locals("role")

        for _, role := range roles {
            if userRole == role {
                return c.Next()
            }
        }

        return c.Status(fiber.StatusForbidden).JSON(
            fiber.Map{"error": "insufficient permissions"},
        )
    }
}

// 使用
app.Get("/admin",
    AuthMiddleware(),
    RoleMiddleware("admin"),
    adminHandler,
)
```

### 限流中间件（自定义）

```go
import "golang.org/x/time/rate"

func RateLimitMiddleware(r rate.Limit, b int) fiber.Handler {
    limiter := rate.NewLimiter(r, b)

    return func(c *fiber.Ctx) error {
        if !limiter.Allow() {
            return c.Status(fiber.StatusTooManyRequests).JSON(
                fiber.Map{"error": "rate limit exceeded"},
            )
        }
        return c.Next()
    }
}

// 使用
app.Use(RateLimitMiddleware(10, 20))
```

### 日志中间件（自定义）

```go
func LoggerMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        start := time.Now()

        // 继续处理
        if err := c.Next(); err != nil {
            return err
        }

        // 记录日志
        duration := time.Since(start)
        log.Printf("%s %s | %d | %v",
            c.Method(),
            c.Path(),
            c.Response().StatusCode(),
            duration,
        )

        return nil
    }
}
```

### 错误处理中间件

```go
func ErrorHandlerMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // 继续处理
        c.Next()

        // 检查是否有错误
        if len(c.Errors()) > 0 {
            err := c.Errors().Last()
            return c.Status(fiber.StatusInternalServerError).JSON(
                fiber.Map{"error": err.Message},
            )
        }

        return nil
    }
}
```

## 中间件最佳实践

### 1. 中间件顺序很重要

```go
// ✅ 正确顺序
app.Use(recover.New())        // 1. 恢复 panic
app.Use(logger.New())         // 2. 记录日志
app.Use(cors.New())           // 3. CORS
app.Use(compress.New())       // 4. 压缩

// ❌ 错误顺序（logger 无法记录压缩前的信息）
app.Use(compress.New())
app.Use(logger.New())
```

### 2. 使用 Next 跳过中间件

```go
// 只在 API 路由上执行
app.Use(func(c *fiber.Ctx) error {
    if !strings.HasPrefix(c.Path(), "/api") {
        return c.Next()
    }
    // API 专用逻辑
    return c.Next()
})
```

### 3. 中间件不应持有状态

```go
// ❌ 错误：持有连接状态
var connections = make(map[string]*fiber.Ctx)

func trackingMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        connections[c.IP()] = c  // 危险！
        return c.Next()
    }
}

// ✅ 正确：不持有 Context
var requestCount = make(map[string]int64)

func trackingMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        ip := c.IP()
        requestCount[ip]++
        return c.Next()
    }
}
```
