# fasthttp-skills 服务器开发

fasthttp-skills 服务器提供高性能的 HTTP 服务，正确配置和使用可以最大化性能。

## 基础服务器

### 简单启动

```go
package main

import (
    "fmt"
    "github.com/valyala/fasthttp"
)

func requestHandler(ctx *fasthttp.RequestCtx) {
    fmt.Fprintf(ctx, "Hello, %s!\n", ctx.UserValue("name"))
}

func main() {
    // 最简单的启动方式
    fasthttp.ListenAndServe(":8080", requestHandler)
}
```

### 使用 Server 配置

```go
func main() {
    s := &fasthttp.Server{
        Handler: requestHandler,
        Name:    "My Server",
    }
    s.ListenAndServe(":8080")
}
```

## 生产级配置

### 完整配置

```go
func main() {
    s := &fasthttp.Server{
        Handler: requestHandler,
        Name:    "Production Server",

        // 缓冲区配置
        ReadBufferSize:  4096,
        WriteBufferSize: 4096,

        // 超时配置
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 5 * time.Second,
        IdleTimeout:  10 * time.Second,

        // 连接限制
        MaxConnsPerIP:      500,
        MaxRequestsPerConn: 1000,

        // 请求体限制
        MaxRequestBodySize: 10 << 20, // 10MB

        // 并发控制
        Concurrency: 256 * 1024,

        // 日志
        Logger: customLogger,
    }

    if err := s.ListenAndServe(":8080"); err != nil {
        log.Fatal(err)
    }
}
```

### 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| ReadBufferSize | 4096 | 读缓冲区大小（字节） |
| WriteBufferSize | 4096 | 写缓冲区大小（字节） |
| ReadTimeout | 0（无限制） | 读取超时 |
| WriteTimeout | 0（无限制） | 写入超时 |
| IdleTimeout | 0（无限制） | 空闲连接超时 |
| MaxConnsPerIP | 0（无限制） | 单 IP 最大连接数 |
| MaxRequestsPerConn | 0（无限制） | 单连接最大请求数 |
| MaxRequestBodySize | 4<<20 (4MB) | 最大请求体大小 |
| Concurrency | 256 * 1024 | 最大并发连接数 |

## 请求处理

### Handler 类型

```go
type RequestHandler func(*RequestCtx)
```

### 获取请求信息

```go
func requestHandler(ctx *fasthttp.RequestCtx) {
    // HTTP 方法
    method := ctx.Method()
    // method: []byte("GET")

    // 请求路径
    path := ctx.Path()
    // path: []byte("/users/123")

    // 完整 URI
    uri := ctx.URI()
    // uri.String(): "http://example.com/users/123?foo=bar"

    // 查询参数
    queryArgs := ctx.QueryArgs()
    name := queryArgs.Peek("name")  // []byte
    name = queryArgs.Has("name")    // bool

    // POST 参数
    postArgs := ctx.PostArgs()
    email := postArgs.Peek("email")

    // 请求头
    userAgent := ctx.Request.Header.Peek("User-Agent")

    // 请求体
    body := ctx.Request.Body()

    // 设置响应
    ctx.SetContentType("application/json")
    ctx.SetStatusCode(200)
    ctx.SetBody([]byte(`{"status": "ok"}`))

    // 或使用 Write
    ctx.WriteString("OK")
}
```

### 路径参数

```go
// 使用路由器时获取路径参数
func requestHandler(ctx *fasthttp.RequestCtx) {
    id := ctx.UserValue("id")
    userID := id.(string)
    fmt.Fprintf(ctx, "User ID: %s", userID)
}
```

## 多核优化

### 原生模式

```go
func main() {
    // fasthttp-skills 默认使用所有 CPU 核心
    s := &fasthttp.Server{
        Handler:     requestHandler,
        Concurrency: runtime.NumCPU() * 1024,
    }
    s.ListenAndServe(":8080")
}
```

### 手动多进程

```go
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

### 注意事项

手动多进程模式通常不需要，fasthttp 的默认实现已经优化了多核使用。仅在特殊场景下使用。

## TLS/HTTPS 支持

### 基础 TLS

```go
func main() {
    certFile := "cert.pem"
    keyFile := "key.pem"

    if err := fasthttp.ListenAndServeTLS(
        ":443",
        certFile,
        keyFile,
        requestHandler,
    ); err != nil {
        log.Fatal(err)
    }
}
```

### TLS 配置

```go
func main() {
    cert, err := tls.LoadX509KeyPair("cert.pem", "key.pem")
    if err != nil {
        log.Fatal(err)
    }

    s := &fasthttp.Server{
        Handler: requestHandler,
        TLSConfig: &tls.Config{
            Certificates: []tls.Certificate{cert},
            // 禁用旧版本 TLS
            MinVersion: tls.VersionTLS12,
            // 优选密码套件
            CipherSuites: []uint16{
                tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
                tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
            },
        },
    }

    if err := s.ListenAndServeTLS(":443", "", ""); err != nil {
        log.Fatal(err)
    }
}
```

## 优雅关闭

### 信号处理

```go
func main() {
    s := &fasthttp.Server{
        Handler: requestHandler,
    }

    go func() {
        if err := s.ListenAndServe(":8080"); err != nil {
            log.Printf("Server error: %v", err)
        }
    }()

    // 监听关闭信号
    sigint := make(chan os.Signal, 1)
    signal.Notify(sigint, os.Interrupt, syscall.SIGTERM)
    <-sigint

    log.Println("Shutting down...")
    if err := s.Shutdown(); err != nil {
        log.Printf("Shutdown error: %v", err)
    }
}
```

### 超时关闭

```go
go func() {
    <-sigint

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := s.ShutdownWithContext(ctx); err != nil {
        log.Printf("Shutdown timeout: %v", err)
    }
}()
```

## 监控和日志

### 自定义 Logger

```go
type MyLogger struct{}

func (l *MyLogger) Printf(format string, args ...interface{}) {
    log.Printf(format, args...)
}

func main() {
    s := &fasthttp.Server{
        Handler: requestHandler,
        Logger:  &MyLogger{},
    }
    s.ListenAndServe(":8080")
}
```

### 请求计数

```go
var (
    requestCount uint64
)

func requestHandler(ctx *fasthttp.RequestCtx) {
    atomic.AddUint64(&requestCount, 1)
    ctx.WriteString(fmt.Sprintf("Request #%d", atomic.LoadUint64(&requestCount)))
}
```

## 错误处理

### 自定义错误页面

```go
func errorHandler(ctx *fasthttp.RequestCtx, err error) {
    statusCode := fasthttp.StatusInternalServerError
    if _, ok := err.(*fasthttp.ErrSmallBuffer); ok {
        statusCode = fasthttp.StatusRequestEntityTooLarge
    }

    ctx.SetStatusCode(statusCode)
    ctx.SetContentType("application/json")
    ctx.SetBody([]byte(fmt.Sprintf(`{"error": "%s"}`, err.Error())))
}

func main() {
    s := &fasthttp.Server{
        Handler:          requestHandler,
        ErrorHandler:     errorHandler,
    }
    s.ListenAndServe(":8080")
}
```

### Panic 恢复

```go
func recoveryMiddleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("Panic recovered: %v", r)
                ctx.SetStatusCode(fasthttp.StatusInternalServerError)
                ctx.SetBody([]byte(`{"error": "internal server error"}`))
            }
        }()
        next(ctx)
    }
}

func main() {
    handler := recoveryMiddleware(requestHandler)
    fasthttp.ListenAndServe(":8080", handler)
}
```

## 虚拟主机

### 多域名支持

```go
func main() {
    // 虚拟主机映射
    handlers := make(map[string]fasthttp.RequestHandler)
    handlers["example.com"] = exampleHandler
    handlers["api.example.com"] = apiHandler

    // 主处理器
    mainHandler := func(ctx *fasthttp.RequestCtx) {
        host := string(ctx.Host())
        handler := handlers[host]
        if handler == nil {
            ctx.Error("Not Found", fasthttp.StatusNotFound)
            return
        }
        handler(ctx)
    }

    fasthttp.ListenAndServe(":8080", mainHandler)
}
```

## HTTP/2 支持

fasthttp-skills 本身不支持 HTTP/2，但可以通过反向代理（如 Nginx）实现：

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
    }
}
```
