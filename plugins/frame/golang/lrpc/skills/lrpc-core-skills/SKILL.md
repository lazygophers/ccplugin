---
name: lrpc-core-skills
description: lrpc 高性能 RPC 框架核心开发规范 - 基于 fasthttp 的轻量级 RPC 框架，提供服务端/客户端、路由注册、中间件系统、编解码器和配置管理
---

# lrpc-core - lrpc 框架核心

基于 fasthttp 的高性能 RPC 框架，提供完整的微服务开发能力。

## 特性

- ⚡ **高性能** - 基于 fasthttp，零拷贝，对象池
- 🎯 **路由系统** - 静态/参数/通配符/全捕获路由
- 🔌 **中间件** - 认证、限流、压缩、指标、恢复
- 📦 **编解码** - JSON、Protobuf、MessagePack
- 🔧 **配置管理** - 结构化配置，环境变量支持
- 🧪 **类型安全** - 反射处理器自动签名转换

## 核心组件

### 1. 应用初始化 (app.go)

```go
package main

import (
    "github.com/lazygophers/lrpc"
    "github.com/lazygophers/lrpc/app"
)

func main() {
    a := app.New()
    a.SetName("my-service")
    a.SetVersion("1.0.0")

    server := lrpc.NewServer()
    server.GET("/hello", Hello)

    a.SetServer(server)
    a.Run()
}

func Hello(ctx *lrpc.Context) error {
    return ctx.JSON(lrpc.H{
        "message": "Hello, World!",
    })
}
```

### 2. 服务端 (server.go)

#### 创建服务端

```go
import "github.com/lazygophers/lrpc"

// 默认配置
server := lrpc.NewServer()

// 自定义配置
server := lrpc.NewServer(
    lrpc.WithAddr(":8080"),
    lrpc.WithReadTimeout(30*time.Second),
    lrpc.WithWriteTimeout(30*time.Second),
    lrpc.WithMaxRequestBodySize(10<<20), // 10MB
)
```

#### 注册路由

```go
// 静态路由
server.GET("/", HomeHandler)
server.POST("/users", CreateUser)
server.PUT("/users/:id", UpdateUser)
server.DELETE("/users/:id", DeleteUser)

// 参数路由
server.GET("/users/:id", GetUser)  // /users/123

// 通配符路由
server.GET("/files/*filepath", FileHandler)  // /files/static/style.css

// 全捕获路由
server.GET("/*", CatchAllHandler)
```

#### 路由优先级

1. 静态路由（`/users`）
2. 正则路由（`/users/:id`）
3. 通配符路由（`/files/*`）
4. 全捕获路由（`/*`）

### 3. 客户端 (client.go)

#### 创建客户端

```go
import "github.com/lazygophers/lrpc/client"

// 默认配置
c := client.New()

// 自定义配置
c := client.New(
    client.WithAddr("http://localhost:8080"),
    client.WithMaxConnsPerHost(100),
    client.WithDialTimeout(10*time.Second),
)
```

#### 发送请求

```go
// GET 请求
resp, err := c.GET(ctx, "/api/users")
if err != nil {
    return err
}
defer resp.Body.Close()

// POST JSON
body := lrpc.H{"name": "John", "email": "john@example.com"}
resp, err := c.POSTJSON(ctx, "/api/users", body)

// PUT JSON
resp, err := c.PUTJSON(ctx, "/api/users/1", lrpc.H{"name": "Jane"})

// DELETE 请求
resp, err := c.DELETE(ctx, "/api/users/1")
```

### 4. 上下文 (context.go)

#### Context 方法

```go
func Handler(ctx *lrpc.Context) error {
    // 请求数据
    ctx.Method()           // HTTP 方法
    ctx.Path()             // 请求路径
    ctx.QueryArgs()        // 查询参数
    ctx.PostArgs()         // POST 表单
    ctx.RequestBody()      // 请求体

    // 路径参数
    ctx.Param("id")        // :id 参数值

    // Header
    ctx.Request.Header.Get("Authorization")

    // 响应
    return ctx.JSON(lrpc.H{"status": "ok"})           // JSON
    return ctx.XML(lrpc.H{"status": "ok"})            // XML
    return ctx.String("Hello")                        // 文本
    return ctx.Status(404).Send("Not Found")          // 状态码

    // 设置 Cookie
    ctx.SetCookie(&fasthttp.Cookie{
        Key:     "session",
        Value:   "xxx",
        Expires: time.Now().Add(24 * time.Hour),
    })

    return nil
}
```

### 5. 路由器 (router.go)

#### 路由分组

```go
// API v1 组
v1 := server.Group("/api/v1")
v1.GET("/users", GetUsers)
v1.POST("/users", CreateUser)

// API v2 组
v2 := server.Group("/api/v2")
v2.GET("/users", GetUsersV2)

// 中间件分组
admin := server.Group("/admin", AuthMiddleware, AdminMiddleware)
admin.GET("/dashboard", Dashboard)
```

#### 路由命名

```go
// 命名路由
server.GET("/users/:id", GetUser).Name("user-detail")

// 获取路由 URL
url := server.NamedRoute("user-detail", lrpc.H{"id": "123"})
// /users/123
```

### 6. 中间件系统

#### 内置中间件

```go
import (
    "github.com/lazygophers/lrpc/middleware/auth"
    "github.com/lazygophers/lrpc/middleware/security"
    "github.com/lazygophers/lrpc/middleware/compress"
    "github.com/lazygophers/lrpc/middleware/metrics"
    "github.com/lazygophers/lrpc/middleware/health"
    "github.com/lazygophers/lrpc/middleware/recover"
)

// 认证中间件
server.Use(auth.JWT("secret-key"))
server.Use(auth.BasicAuth("user", "pass"))

// 安全中间件
server.Use(security.CORS())
server.Use(security.RateLimit(100, time.Minute))
server.Use(security.IPWhitelist("127.0.0.1", "192.168.1.0/24"))

// 压缩中间件
server.Use(compress.Gzip())

// 监控中间件
server.Use(metrics.Prometheus())
server.Use(health.Check())

// 恢复中间件
server.Use(recover.New())
```

#### 自定义中间件

```go
func LoggerMiddleware() lrpc.HandlerFunc {
    return func(ctx *lrpc.Context) error {
        start := time.Now()

        // 处理请求
        if err := ctx.Next(); err != nil {
            return err
        }

        // 记录日志
        duration := time.Since(start)
        log.Printf("%s %s %v",
            ctx.Method(),
            ctx.Path(),
            duration,
        )

        return nil
    }
}

server.Use(LoggerMiddleware())
```

### 7. 编解码器 (codec)

#### JSON 编解码

```go
import "github.com/lazygophers/lrpc/codec/json"

// 默认使用 JSON
server := lrpc.NewServer(
    lrpc.WithCodec(json.Codec()),
)
```

#### Protobuf 编解码

```go
import "github.com/lazygophers/lrpc/codec/protobuf"

server := lrpc.NewServer(
    lrpc.WithCodec(protobuf.Codec()),
)
```

#### MessagePack 编解码

```go
import "github.com/lazygophers/lrpc/codec/msgpack"

server := lrpc.NewServer(
    lrpc.WithCodec(msgpack.Codec()),
)
```

#### 自定义编解码器

```go
type MyCodec struct{}

func (c *MyCodec) Encode(v interface{}) ([]byte, error) {
    // 自定义编码逻辑
    return json.Marshal(v)
}

func (c *MyCodec) Decode(data []byte, v interface{}) error {
    // 自定义解码逻辑
    return json.Unmarshal(data, v)
}

server := lrpc.NewServer(
    lrpc.WithCodec(&MyCodec{}),
)
```

### 8. 配置管理 (config.go)

#### 配置结构

```go
type Config struct {
    Server ServerConfig `yaml:"server"`
    DB     DBConfig     `yaml:"db"`
    Redis  RedisConfig  `yaml:"redis"`
}

type ServerConfig struct {
    Host string `yaml:"host" env:"SERVER_HOST"`
    Port int    `yaml:"port" env:"SERVER_PORT"`
}

// 加载配置
var cfg Config

// 从文件加载
err := config.LoadFile("config.yaml", &cfg)

// 从环境变量加载
err := config.LoadEnv(&cfg)
```

#### 配置热更新

```go
config.WatchFile("config.yaml", func(cfg *Config) {
    log.Info("配置已更新")
    // 重新初始化组件
})
```

## 最佳实践

### 1. 项目结构

```
project/
├── cmd/
│   └── server/
│       └── main.go          # 入口
├── internal/
│   ├── handler/             # 处理器
│   ├── middleware/          # 中间件
│   ├── service/             # 业务逻辑
│   └── repository/          # 数据访问
├── pkg/
│   └── model/               # 公共模型
├── config/
│   └── config.yaml          # 配置文件
└── go.mod
```

### 2. 错误处理

```go
func GetUser(ctx *lrpc.Context) error {
    id := ctx.Param("id")

    user, err := service.GetUser(id)
    if err != nil {
        // 业务错误
        if errors.Is(err, ErrUserNotFound) {
            return ctx.Status(404).JSON(lrpc.H{
                "error": "user not found",
            })
        }
        // 系统错误
        return ctx.Status(500).JSON(lrpc.H{
            "error": "internal server error",
        })
    }

    return ctx.JSON(user)
}
```

### 3. 优雅关闭

```go
func main() {
    a := app.New()
    server := lrpc.NewServer()

    a.SetServer(server)

    // 信号处理
    a.Notify(os.Interrupt, syscall.SIGTERM)

    // 优雅关闭
    a.ShutdownTimeout = 30 * time.Second

    a.Run()
}
```

### 4. 并发安全

```go
// 中间件必须是并发安全的
func MyMiddleware() lrpc.HandlerFunc {
    // 不要在闭包外共享可变状态
    var counter int64  // ❌ 错误

    return func(ctx *lrpc.Context) error {
        // 使用原子操作
        atomic.AddInt64(&counter, 1)  // ✅ 正确
        return ctx.Next()
    }
}
```

## 性能优化

### 1. 连接池配置

```go
client := client.New(
    client.WithMaxConnsPerHost(100),
    client.WithMaxIdleConnDuration(90 * time.Second),
)
```

### 2. 对象池

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func Handler(ctx *lrpc.Context) error {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer bufferPool.Put(buf)
    buf.Reset()

    // 使用 buf
    return nil
}
```

### 3. 零拷贝

```go
// ❌ 字符串到字节拷贝
data := []byte(str)

// ✅ 零拷贝转换
data := unsafe.StringData(str)
```

## 参考资源

- [lrpc GitHub](https://github.com/lazygophers/lrpc)
- [fasthttp 文档](https://github.com/valyala/fasthttp)
- [Go 最佳实践](https://go.dev/doc/effective_go)
