---
name: fasthttp
description: fasthttp 高性能 HTTP 库开发规范和最佳实践
---

# fasthttp 高性能 HTTP 库开发规范

## 框架概述

fasthttp 是一个高性能 HTTP 库，相比 Go 标准库 net/http 提供 6-10 倍的性能提升。fasthttp 通过零拷贝、对象池等优化技术，实现极低的内存占用和高并发处理能力。

**核心特点：**
- 零拷贝机制（最小化内存分配）
- 对象池模式（复用请求/响应对象）
- []byte 优先（而非 string）
- 高并发支持（1.5M+ 并发连接）
- 与 net/http API 不兼容

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|----------|
| [核心概念](core/core-concepts.md) | 零拷贝、对象池、性能对比 | 框架入门 |
| [服务器开发](server/server.md) | 服务器配置、请求处理、多核优化 | 服务端开发 |
| [客户端开发](client/client.md) | 客户端使用、连接池、HostClient | 客户端开发 |
| [性能优化](performance/performance.md) | 零拷贝技巧、对象池、调优 | 性能调优 |
| [路由集成](routing-integration/routing-integration.md) | 路由器、中间件 | 功能扩展 |
| [测试](testing/testing.md) | 单元测试、基准测试 | 质量保证 |
| [最佳实践](best-practices/best-practices.md) | 对象池管理、字节操作、优雅关闭 | 架构设计 |
| [参考资源](references.md) | 官方文档、源码分析 | 深入学习 |

## 快速开始

### 设计理念

fasthttp 是一个高性能 HTTP 库，与 net/http 的主要区别：

| 特性 | net/http | fasthttp |
|------|----------|----------|
| 对象模型 | 每个请求创建新对象 | 复用对象（sync.Pool） |
| 字符串类型 | string | []byte |
| 性能提升 | 基准 | 6-10x |
| 并发连接 | 一般 | 1.5M+ |
| API 设计 | 标准库 | 高度优化 |

### 零拷贝机制

```go
// ❌ net/http - 多次拷贝
func handler(w http.ResponseWriter, r *http.Request) {
    body, _ := ioutil.ReadAll(r.Body)  // 拷贝 1
    str := string(body)                 // 拷贝 2
    w.Write([]byte(str))                // 拷贝 3
}

// ✅ fasthttp - 零拷贝
func handler(ctx *fasthttp.RequestCtx) {
    body := ctx.Request.Body()  // 直接引用
    ctx.SetBody(body)           // 直接传递
}
```

### 对象池模式

```go
// 使用 Acquire/Release
req := fasthttp.AcquireRequest()
defer fasthttp.ReleaseRequest(req)

resp := fasthttp.AcquireResponse()
defer fasthttp.ReleaseResponse(resp)
```

## 服务器开发

### 基础服务器

```go
package main

import "github.com/valyala/fasthttp"

func requestHandler(ctx *fasthttp.RequestCtx) {
    fmt.Fprintf(ctx, "Hello, %s!\n", ctx.UserValue("name"))
}

func main() {
    // 简单启动
    fasthttp.ListenAndServe(":8080", requestHandler)

    // 或使用 Server 配置
    s := &fasthttp.Server{
        Handler: requestHandler,
    }
    s.ListenAndServe(":8080")
}
```

### 生产级配置

```go
s := &fasthttp.Server{
    Handler:            requestHandler,
    Name:               "Production Server",

    // 缓冲区配置
    ReadBufferSize:     4096,
    WriteBufferSize:    4096,
    ReadTimeout:        5 * time.Second,
    WriteTimeout:       5 * time.Second,
    IdleTimeout:        10 * time.Second,

    // 连接限制
    MaxConnsPerIP:      500,
    MaxRequestsPerConn: 1000,
    MaxRequestBodySize: 10 << 20, // 10MB

    // 并发控制
    Concurrency:        256 * 1024,

    // 日志
    Logger:             customLogger,
}

s.ListenAndServe(":8080")
```

### 请求处理

```go
func requestHandler(ctx *fasthttp.RequestCtx) {
    // 获取请求信息
    path := ctx.Path()
    method := ctx.Method()
    body := ctx.Request.Body()

    // 查询参数
    queryArgs := ctx.QueryArgs()
    name := queryArgs.Peek("name")  // 返回 []byte

    // POST 参数
    postArgs := ctx.PostArgs()
    email := postArgs.Peek("email")

    // 请求头
    userAgent := ctx.Request.Header.Peek("User-Agent")

    // 设置响应
    ctx.SetContentType("application/json")
    ctx.SetStatusCode(200)
    ctx.SetBody([]byte(`{"status": "ok"}`))

    // 或使用 Write
    ctx.WriteString("OK")
}
```

### 多核优化

```go
import (
    "github.com/valyala/fasthttp"
    "runtime"
)

func main() {
    numCPUs := runtime.NumCPU()

    for i := 0; i < numCPUs; i++ {
        go func(n int) {
            runtime.LockOSThread()

            s := &fasthttp.Server{
                Handler: requestHandler,
                Name:    fmt.Sprintf("Worker %d", n),
            }

            ln, err := net.Listen("tcp4", ":8080")
            if err != nil {
                log.Fatal(err)
            }

            s.Serve(ln)
        }(i)
    }

    select {} // 永久阻塞
}
```

## 客户端开发

### 基础请求

```go
// 简单 GET
req := fasthttp.AcquireRequest()
defer fasthttp.ReleaseRequest(req)

req.SetRequestURI("http://example.com/")
req.Header.SetMethod("GET")

resp := fasthttp.AcquireResponse()
defer fasthttp.ReleaseResponse(resp)

if err := fasthttp.Do(req, resp); err != nil {
    log.Fatal(err)
}

fmt.Printf("Status: %d\n", resp.StatusCode())
fmt.Printf("Body: %s\n", resp.Body())
```

### POST 请求

```go
req := fasthttp.AcquireRequest()
defer fasthttp.ReleaseRequest(req)

req.SetRequestURI("http://example.com/")
req.Header.SetMethod("POST")
req.Header.SetContentType("application/json")
req.SetBody([]byte(`{"key": "value"}`))

resp := fasthttp.AcquireResponse()
defer fasthttp.ReleaseResponse(resp)

if err := fasthttp.Do(req, resp); err != nil {
    log.Fatal(err)
}
```

### 客户端配置

```go
// 创建客户端
client := &fasthttp.Client{
    Name: "MyClient",
    // 超时配置
    ReadTimeout:  5 * time.Second,
    WriteTimeout: 5 * time.Second,
    // 连接池
    MaxConnsPerHost: 100,
    // TLS 配置
    TLSConfig: &tls.Config{InsecureSkipVerify: true},
}

// 使用客户端
req := fasthttp.AcquireRequest()
resp := fasthttp.AcquireResponse()
err := client.Do(req, resp)
```

### 连接复用

```go
// 使用 HostClient 进行连接复用
c := &fasthttp.HostClient{
    Addr: "example.com:80",
    Name: "MyHostClient",
}

req := fasthttp.AcquireRequest()
req.SetRequestURI("http://example.com/")
resp := fasthttp.AcquireResponse()

err := c.Do(req, resp)
```

## 路由集成

### fasthttp-routing

```go
import "github.com/fasthttp/router"

router := router.New()

// 基础路由
router.GET("/", func(ctx *fasthttp.RequestCtx) {
    ctx.WriteString("Home")
})

// 路径参数
router.GET("/users/:id", func(ctx *fasthttp.RequestCtx) {
    userID := ctx.UserValue("id").(string)
    fmt.Fprintf(ctx, "User ID: %s", userID)
})

// 通配符
router.GET("/files/*filepath", func(ctx *fasthttp.RequestCtx) {
    filepath := ctx.UserValue("filepath").(string)
    fmt.Fprintf(ctx, "File: %s", filepath)
})

fasthttp.ListenAndServe(":8080", router.Handler)
```

### 中间件

```go
func middleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        start := time.Now()

        next(ctx)

        duration := time.Since(start)
        ctx.Logger().Printf("Request took %v", duration)
    }
}

// 使用
handler := middleware(requestHandler)
```

## 性能优化

### 零拷贝技巧

```go
// ❌ 不好的做法
func badHandler(ctx *fasthttp.RequestCtx) {
    str := string(ctx.Path())  // 分配新 string
    ctx.WriteString(str)
}

// ✅ 好的做法
func goodHandler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()  // []byte，无分配
    ctx.Write(path)
}
```

### 对象池使用

```go
// 内置对象池
req := fasthttp.AcquireRequest()
defer fasthttp.ReleaseRequest(req)

// 自定义对象池
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 0, 1024)
    },
}

func handler(ctx *fasthttp.RequestCtx) {
    buf := bufferPool.Get().([]byte)
    defer func() {
        buf = buf[:0]
        bufferPool.Put(buf)
    }()

    buf = append(buf, "Hello"...)
    ctx.SetBody(buf)
}
```

### 文件服务（零拷贝）

```go
func fileHandler(ctx *fasthttp.RequestCtx) {
    path := "/var/www" + string(ctx.Path())
    fasthttp.ServeFile(ctx, path)
}
```

### 性能测试

```bash
# 使用 wrk
wrk -t12 -c400 -d30s http://localhost:8080/api/users

# 使用 ab
ab -n 10000 -c 100 http://localhost:8080/api/users
```

## 生态集成

### 模板引擎

```go
import "html/template"

var templates = template.Must(template.ParseGlob("templates/*.html"))

func templateHandler(ctx *fasthttp.RequestCtx) {
    data := map[string]interface{}{
        "Title": "FastHTTP",
    }

    ctx.SetContentType("text/html")

    var buf bytes.Buffer
    if err := templates.ExecuteTemplate(&buf, "index.html", data); err != nil {
        ctx.Error("Internal Error", 500)
        return
    }

    ctx.SetBody(buf.Bytes())
}
```

### WebSocket

```go
import "github.com/gorilla/websocket"

var upgrader = websocket.Upgrader{
    ReadBufferSize:  1024,
    WriteBufferSize: 1024,
}

func websocketHandler(ctx *fasthttp.RequestCtx) {
    ctx.Hijack(func(conn net.Conn) {
        wsConn, err := upgrader.Upgrade(conn, nil)
        if err != nil {
            return
        }
        defer wsConn.Close()

        for {
            messageType, p, err := wsConn.ReadMessage()
            if err != nil {
                break
            }
            wsConn.WriteMessage(messageType, p)
        }
    })
}
```

### 代理服务器

```go
import "github.com/valyala/fasthttp/fasthttpproxy"

func main() {
    proxy := fasthttpproxy.FastHTTPSingleHostReverseProxy("https://backend.example.com")

    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.Request.Header.Set("X-API-Key", "secret-key")
        proxy(ctx)
        ctx.Response.Header.Set("Access-Control-Allow-Origin", "*")
    }

    fasthttp.ListenAndServe(":8080", handler)
}
```

## 最佳实践

### 1. 对象池管理

```go
// ✅ 正确使用
req := fasthttp.AcquireRequest()
defer fasthttp.ReleaseRequest(req)

// ❌ 错误：忘记释放
req := fasthttp.AcquireRequest()
// 忘记 ReleaseRequest
```

### 2. 字节操作

```go
// ✅ 使用 []byte
path := ctx.Path()

// ❌ 避免 string 转换
pathStr := string(ctx.Path())  // 产生分配
```

### 3. 错误处理

```go
func handler(ctx *fasthttp.RequestCtx) {
    // 正确错误处理
    if err != nil {
        ctx.Error("Internal Server Error", 500)
        return
    }

    // 或自定义错误
    ctx.SetStatusCode(404)
    ctx.SetBody([]byte(`{"error": "Not Found"}`))
}
```

### 4. 优雅关闭

```go
go func() {
    sigint := make(chan os.Signal, 1)
    signal.Notify(sigint, os.Interrupt, syscall.SIGTERM)
    <-sigint

    if err := s.Shutdown(); err != nil {
        log.Printf("Shutdown error: %v", err)
    }
}()
```

## 注意事项

1. **API 不兼容**：fasthttp 与 net/http API 不兼容
2. **Context 复用**：RequestCtx 会被复用，不要保存引用
3. **字节优先**：尽量使用 []byte 而非 string
4. **对象池**：必须使用 Acquire/Release 配对
5. **并发安全**：注意 RequestCtx 的并发使用

## 性能对比

```
Framework        | Requests/sec | Latency (ms) | Memory (MB)
-----------------|--------------|--------------|------------
fasthttp         | 1,200,000    | 0.83         | 3.2
net/http         | 500,000      | 2.00         | 12.3
```

## 参考资源

- [fasthttp GitHub](https://github.com/valyala/fasthttp)
- [fasthttp Package Documentation](https://pkg.go.dev/github.com/valyala/fasthttp)
- [fasthttp-routing](https://github.com/fasthttp/router)
- [Performance Analysis](https://github.com/valyala/fasthttp/tree/master/explorehash)
