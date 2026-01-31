# fasthttp-skills 最佳实践

遵循这些最佳实践可以正确、高效地使用 fasthttp。

## 对象池管理

### Acquire/Release 配对

```go
// ✅ 正确：配对使用
func goodClient() {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    // 使用 req 和 resp...
}

// ❌ 错误：忘记释放
func badClient() {
    req := fasthttp.AcquireRequest()
    // 忘记 ReleaseRequest(req)
    // 导致内存泄漏
}
```

### defer 保证释放

```go
func makeRequest(url string) error {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)  // 确保释放

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)  // 确保释放

    req.SetRequestURI(url)

    if err := fasthttp.Do(req, resp); err != nil {
        return err  // defer 仍然会执行
    }

    return nil
}
```

## 字节操作

### 优先使用 []byte

```go
// ✅ 好的做法：使用 []byte
func handler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()  // []byte
    query := ctx.QueryArgs().Peek("q")  // []byte

    // 使用 []byte 操作
    if bytes.Equal(path, []byte("/users")) {
        ctx.WriteString("Users")
    }
}

// ❌ 不好的做法：转换为 string
func handler(ctx *fasthttp.RequestCtx) {
    path := string(ctx.Path())  // 产生分配
    query := string(ctx.QueryArgs().Peek("q"))  // 产生分配

    if path == "/users" {  // string 比较
        ctx.WriteString("Users")
    }
}
```

### 字符串持久化

```go
// ❌ 错误：保存会被复用的 []byte
var cache = make(map[string][]byte)

func handler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()
    cache["key"] = path  // path 会被复用，危险！
}

// ✅ 正确：复制数据
func handler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()
    data := make([]byte, len(path))
    copy(data, path)  // 复制
    cache["key"] = data
}

// ✅ 或使用 CopyString（转为 string）
func handler(ctx *fasthttp.RequestCtx) {
    path := fasthttp.WrapString(ctx.Path())
    cache[string(path)] = data
}
```

## RequestCtx 使用

### 不保存引用

```go
// ❌ 错误：在 goroutine 中使用 RequestCtx
func handler(ctx *fasthttp.RequestCtx) {
    go func() {
        // ctx 可能已被其他请求复用
        ctx.WriteString("async")
    }()
}

// ✅ 正确：提取需要的数据
func handler(ctx *fasthttp.RequestCtx) {
    path := make([]byte, len(ctx.Path()))
    copy(path, ctx.Path())

    go func() {
        process(path)  // 使用副本
    }()
}
```

### 设置 UserValue

```go
func handler(ctx *fasthttp.RequestCtx) {
    // ✅ 设置基础类型
    ctx.SetUserValue("id", "123")

    // ✅ 设置可以被持久化的数据
    ctx.SetUserValue("user", &User{ID: 123, Name: "John"})

    // ❌ 不要设置 []byte 引用
    // ctx.SetUserValue("path", ctx.Path())  // 危险！
}
```

## 错误处理

### 统一错误响应

```go
func errorResponse(ctx *fasthttp.RequestCtx, statusCode int, message string) {
    ctx.SetStatusCode(statusCode)
    ctx.SetContentType("application/json")
    ctx.SetBody([]byte(fmt.Sprintf(`{"error": "%s"}`, message)))
}

func handler(ctx *fasthttp.RequestCtx) {
    user, err := getUser(ctx)
    if err != nil {
        errorResponse(ctx, 404, "User not found")
        return
    }

    // 正常处理...
}
```

### Panic 恢复

```go
func recoveryMiddleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("Panic recovered: %v\n%s", r, debug.Stack())
                ctx.SetStatusCode(500)
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

## 性能优化

### 连接复用

```go
// ✅ 使用 HostClient
client := &fasthttp.HostClient{
    Addr: "api.example.com:80",
}

for i := 0; i < 1000; i++ {
    req := fasthttp.AcquireRequest()
    resp := fasthttp.AcquireResponse()

    req.SetRequestURI("http://api.example.com/endpoint")
    client.Do(req, resp)

    fasthttp.ReleaseRequest(req)
    fasthttp.ReleaseResponse(resp)
}

// ❌ 每次创建新连接（慢）
for i := 0; i < 1000; i++ {
    fasthttp.Get(nil, "http://api.example.com/endpoint")
}
```

### 批量操作

```go
// ✅ 批量写入
func handler(ctx *fasthttp.RequestCtx) {
    var buf []byte
    buf = append(buf, `{"users": [`...)
    for i, user := range users {
        if i > 0 {
            buf = append(buf, ',')
        }
        data, _ := json.Marshal(user)
        buf = append(buf, data...)
    }
    buf = append(buf, `]}`...)

    ctx.SetBody(buf)
}

// ❌ 多次 Write
func handler(ctx *fasthttp.RequestCtx) {
    ctx.WriteString(`{"users": [`)
    for i, user := range users {
        if i > 0 {
            ctx.WriteString(`,`)
        }
        data, _ := json.Marshal(user)
        ctx.Write(data)
    }
    ctx.WriteString(`]}`)
}
```

## 资源管理

### 优雅关闭

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

### 超时控制

```go
func main() {
    s := &fasthttp.Server{
        Handler: requestHandler,
        // 读取超时
        ReadTimeout: 5 * time.Second,
        // 写入超时
        WriteTimeout: 5 * time.Second,
        // 空闲超时
        IdleTimeout: 10 * time.Second,
    }
    s.ListenAndServe(":8080")
}
```

## 安全实践

### 请求大小限制

```go
func main() {
    s := &fasthttp.Server{
        Handler: requestHandler,
        // 限制请求体大小
        MaxRequestBodySize: 10 << 20,  // 10MB
    }
    s.ListenAndServe(":8080")
}
```

### 连接限制

```go
func main() {
    s := &fasthttp.Server{
        Handler: requestHandler,
        // 单 IP 最大连接数
        MaxConnsPerIP: 100,
        // 单连接最大请求数
        MaxRequestsPerConn: 1000,
    }
    s.ListenAndServe(":8080")
}
```

### 头部验证

```go
func validateHeaders(ctx *fasthttp.RequestCtx) error {
    // 验证 Content-Length
    contentLength := ctx.Request.Header.ContentLength()
    if contentLength > 10<<20 {  // 10MB
        return fmt.Errorf("request too large")
    }

    // 验证 Host
    host := ctx.Host()
    if len(host) == 0 {
        return fmt.Errorf("missing host header")
    }

    return nil
}
```

## 日志记录

### 结构化日志

```go
func loggingMiddleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        start := time.Now()

        next(ctx)

        log.Printf("%s %s - %d - %v",
            ctx.Method(),
            ctx.Path(),
            ctx.Response.StatusCode(),
            time.Since(start),
        )
    }
}
```

### 错误日志

```go
func handler(ctx *fasthttp.RequestCtx) {
    if err := processRequest(ctx); err != nil {
        log.Printf("Error processing request: %v", err)
        ctx.SetStatusCode(500)
        return
    }
}
```

## 测试建议

### 单元测试

```go
func TestHandler(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.SetBody([]byte("OK"))
    }

    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI("/test")

    handler(ctx)

    if ctx.Response.StatusCode() != 200 {
        t.Errorf("expected 200, got %d", ctx.Response.StatusCode())
    }
}
```

### 基准测试

```go
func BenchmarkHandler(b *testing.B) {
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.SetBody([]byte("OK"))
    }

    ctx := &fasthttp.RequestCtx{}

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ctx.Request.Reset()
        handler(ctx)
    }
}
```

## 最佳实践清单

- [ ] 总是使用 Acquire/Release 配对
- [ ] defer Release 确保释放
- [ ] 优先使用 []byte 而非 string
- [ ] 不保存 RequestCtx 的引用
- [ ] 需要持久化时复制数据
- [ ] 使用 HostClient 复用连接
- [ ] 设置合理的超时
- [ ] 限制请求大小
- [ ] 限制单 IP 连接数
- [ ] 实现优雅关闭
- [ ] 添加日志记录
- [ ] 实现 panic 恢复
- [ ] 统一错误处理
- [ ] 编写单元测试
- [ ] 进行性能测试
