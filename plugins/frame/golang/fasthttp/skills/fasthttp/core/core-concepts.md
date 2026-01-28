# fasthttp 核心概念

fasthttp 的设计目标是最大化性能和最小化内存分配。理解这些核心概念对于正确使用 fasthttp 至关重要。

## 设计理念

### 核心优化技术

1. **零拷贝**：最小化内存复制
2. **对象池**：复用请求/响应对象
3. **字节优先**：使用 []byte 而非 string
4. **无反射**：避免运行时反射开销
5. **批量操作**：减少系统调用

### 性能对比

```
Framework        | Requests/sec | Latency (ms) | Memory (MB)
-----------------|--------------|--------------|------------
fasthttp         | 1,200,000    | 0.83         | 3.2
net/http         | 500,000      | 2.00         | 12.3
```

## 零拷贝机制

### 原理

零拷贝的核心是直接操作字节数组，避免不必要的数据复制：

```go
// ❌ net/http - 3 次拷贝
func handler(w http.ResponseWriter, r *http.Request) {
    body, _ := ioutil.ReadAll(r.Body)  // 拷贝 1: 请求体 → []byte
    str := string(body)                 // 拷贝 2: []byte → string
    w.Write([]byte(str))                // 拷贝 3: string → []byte
}

// ✅ fasthttp - 0 次拷贝
func handler(ctx *fasthttp.RequestCtx) {
    body := ctx.Request.Body()  // 直接引用，无拷贝
    ctx.SetBody(body)           // 直接传递，无拷贝
}
```

### 实践建议

```go
// ❌ 不好的做法
func badHandler(ctx *fasthttp.RequestCtx) {
    str := string(ctx.Path())  // 产生 string 分配
    ctx.WriteString(str)       // 又转换回 []byte
}

// ✅ 好的做法
func goodHandler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()  // []byte，无分配
    ctx.Write(path)     // 直接使用
}
```

## 对象池模式

### Acquire/Release 机制

fasthttp 使用 sync.Pool 来管理请求和响应对象：

```go
// 获取请求对象
req := fasthttp.AcquireRequest()
// 使用 req...
defer fasthttp.ReleaseRequest(req)  // 必须释放

// 获取响应对象
resp := fasthttp.AcquireResponse()
// 使用 resp...
defer fasthttp.ReleaseResponse(resp)  // 必须释放
```

### 为什么必须释放

```go
// ❌ 错误：忘记释放
func badClient() {
    req := fasthttp.AcquireRequest()
    req.SetRequestURI("http://example.com")
    // 忘记 ReleaseRequest(req)
    // 导致内存泄漏
}

// ✅ 正确：配对使用
func goodClient() {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)  // 确保释放

    req.SetRequestURI("http://example.com")
    // ...
}
```

### 自定义对象池

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 0, 1024)
    },
}

func handler(ctx *fasthttp.RequestCtx) {
    buf := bufferPool.Get().([]byte)
    defer func() {
        buf = buf[:0]  // 重置
        bufferPool.Put(buf)
    }()

    buf = append(buf, "Hello"...)
    ctx.SetBody(buf)
}
```

## RequestCtx 复用

### RequestCtx 的生命周期

RequestCtx 会在多个请求之间被复用，这是 fasthttp 性能的关键：

```go
func handler(ctx *fasthttp.RequestCtx) {
    // ✅ 正确：仅在此请求周期内使用
    name := ctx.UserValue("name")
    ctx.WriteString(name.(string))

    // ❌ 错误：保存 RequestCtx 的引用
    go func() {
        // 危险！ctx 可能被其他请求复用
        ctx.WriteString("async")
    }()

    // ❌ 错误：保存来自 ctx 的数据
    globalCache[string(ctx.Path())] = data  // string() 会分配
}
```

### 持久化数据

如果需要持久化数据，必须进行复制：

```go
// ❌ 错误：直接保存 []byte
var cache = make(map[string][]byte)
func handler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()  // []byte，会被复用
    cache["key"] = path  // 危险！
}

// ✅ 正确：复制数据
func handler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()
    data := make([]byte, len(path))
    copy(data, path)  // 复制
    cache["key"] = data
}
```

## 字节操作

### []byte vs string

fasthttp 优先使用 []byte 而非 string：

```go
// ❌ 避免 string 转换
path := string(ctx.Path())  // 分配新 string

// ✅ 使用 []byte
path := ctx.Path()  // 无分配

// 如果需要 string，使用 CopyString
pathStr := utils.CopyString(ctx.Path())
```

### 字节比较

```go
// ❌ 分配内存
if string(ctx.Path()) == "/users" {
    // ...
}

// ✅ 零分配比较
if bytes.Equal(ctx.Path(), []byte("/users")) {
    // ...
}

// 或使用 fasthttp 提供的工具
if ctx.IsGet() && bytes.HasPrefix(ctx.Path(), []byte("/api")) {
    // ...
}
```

## Server 结构

### Server 字段

```go
type Server struct {
    // 处理器
    Handler RequestHandler

    // 名称（用于日志）
    Name string

    // 缓冲区配置
    ReadBufferSize  int
    WriteBufferSize int

    // 超时配置
    ReadTimeout  time.Duration
    WriteTimeout time.Duration
    IdleTimeout  time.Duration

    // 连接限制
    MaxConnsPerIP      int
    MaxRequestsPerConn int

    // 请求体限制
    MaxRequestBodySize int

    // 并发控制
    Concurrency int

    // 日志
    Logger Logger

    // 其他配置...
}
```

### 配置建议

```go
s := &fasthttp.Server{
    Handler: requestHandler,
    Name:    "My Server",

    // 缓冲区：根据请求/响应大小调整
    ReadBufferSize:  4096,
    WriteBufferSize: 4096,

    // 超时：防止资源耗尽
    ReadTimeout:  5 * time.Second,
    WriteTimeout: 5 * time.Second,
    IdleTimeout:  10 * time.Second,

    // 连接限制：防止单个 IP 占用过多资源
    MaxConnsPerIP:      500,
    MaxRequestsPerConn: 1000,

    // 请求体限制：防止大请求攻击
    MaxRequestBodySize: 10 << 20, // 10MB

    // 并发：根据 CPU 核心数调整
    Concurrency: 256 * 1024,
}
```

## 性能陷阱

### 1. string 转换

```go
// ❌ 每次调用都分配
str := string(ctx.QueryArgs().Peek("key"))

// ✅ 保持 []byte
key := ctx.QueryArgs().Peek("key")
```

### 2. 子字节切片

```go
// ❌ 保留大切片的引用
body := ctx.PostBody()
smallPart := body[100:200]  // 保留对整个 body 的引用

// ✅ 复制需要的部分
smallPart = make([]byte, 100)
copy(smallPart, body[100:200])
```

### 3. Map 键使用

```go
// ❌ 使用 string 作为键会分配
cache[string(ctx.Path())] = value

// ✅ 使用 []byte
var cache = make(map[string][]byte)  // map[string] 可以用 []byte 访问
cache[string(ctx.Path())] = value  // 仍需转换

// 更好的方式：使用 bytes.Map
var cache = make(map[[32]byte]string)
```

## 调试技巧

### 内存分析

```go
import _ "net/http/pprof"

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()

    // 正常服务器代码
    fasthttp.ListenAndServe(":8080", handler)
}
```

### CPU 分析

```bash
# 使用 pprof
go tool pprof http://localhost:6060/debug/pprof/profile

# 或使用 go test
go test -cpuprofile=cpu.prof -memprofile=mem.prof
go tool pprof cpu.prof
```

## 最佳实践总结

1. **始终使用 Acquire/Release 配对**
2. **优先使用 []byte 而非 string**
3. **不要保存 RequestCtx 的引用**
4. **需要持久化时复制数据**
5. **使用 bytes.Equal 比较**
6. **避免不必要的类型转换**
7. **使用对象池减少分配**
8. **合理配置 Server 参数**
