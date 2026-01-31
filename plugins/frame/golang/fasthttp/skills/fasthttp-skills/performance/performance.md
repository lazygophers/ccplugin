# fasthttp-skills 性能优化

fasthttp-skills 的性能优势来自于其零拷贝设计和对象池模式。正确使用这些特性可以最大化性能。

## 零拷贝技巧

### 避免字符串转换

```go
// ❌ 不好的做法
func badHandler(ctx *fasthttp.RequestCtx) {
    str := string(ctx.Path())  // 分配新 string
    ctx.WriteString(str)       // 再次转换回 []byte
}

// ✅ 好的做法
func goodHandler(ctx *fasthttp.RequestCtx) {
    path := ctx.Path()  // []byte，无分配
    ctx.Write(path)     // 直接使用
}
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

// 或使用 fasthttp-skills 提供的方法
if ctx.IsGet() && bytes.HasPrefix(ctx.Path(), []byte("/api")) {
    // ...
}
```

### 子字节处理

```go
// ❌ 保留大切片的引用
body := ctx.PostBody()  // 可能很大
smallPart := body[100:200]  // 保留对整个 body 的引用，无法 GC

// ✅ 复制需要的部分
smallPart = make([]byte, 100)
copy(smallPart, body[100:200])  // 只复制需要的部分，大 body 可以被 GC
```

## 对象池使用

### 内置对象池

```go
// 客户端使用
func makeRequest(url string) error {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    req.SetRequestURI(url)
    return fasthttp.Do(req, resp)
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
        buf = buf[:0]  // 重置长度
        bufferPool.Put(buf)
    }()

    // 使用 buffer
    buf = append(buf, "Hello"...)
    buf = append(buf, ctx.Path()...)
    ctx.SetBody(buf)
}
```

### 结构体池

```go
var userPool = sync.Pool{
    New: func() interface{} {
        return new(User)
    },
}

func handler(ctx *fasthttp.RequestCtx) {
    user := userPool.Get().(*User)
    defer func() {
        *user = User{}  // 重置
        userPool.Put(user)
    }()

    // 解析到 user
    user.ID = 123
    user.Name = string(ctx.QueryArgs().Peek("name"))

    // 使用 user...
}
```

## 内存分配优化

### 预分配容量

```go
// ❌ 多次重新分配
var data []byte
for i := 0; i < 100; i++ {
    data = append(data, []byte("chunk")...)
}

// ✅ 预分配容量
data := make([]byte, 0, 600)
for i := 0; i < 100; i++ {
    data = append(data, []byte("chunk")...)
}
```

### 重用缓冲区

```go
var (
    responseBuf = make([]byte, 0, 4096)
    responseMtx sync.Mutex
)

func handler(ctx *fasthttp.RequestCtx) {
    responseMtx.Lock()
    responseBuf = responseBuf[:0]

    // 填充数据
    responseBuf = append(responseBuf, `{"status": "ok", "data": [`...)
    responseBuf = append(responseBuf, ctx.Path()...)
    responseBuf = append(responseBuf, `]}`...)

    // 复制数据（因为 responseBuf 会被重用）
    resp := make([]byte, len(responseBuf))
    copy(resp, responseBuf)

    responseMtx.Unlock()

    ctx.SetBody(resp)
}
```

## 字符串处理

### 最小化 string() 转换

```go
// ❌ 频繁转换
for i := 0; i < 1000; i++ {
    key := string(ctx.QueryArgs().Peek("key"))
    process(key)
}

// ✅ 转换一次
key := string(ctx.QueryArgs().Peek("key"))
for i := 0; i < 1000; i++ {
    process(key)
}

// 或使用 []byte 版本
keyBytes := ctx.QueryArgs().Peek("key")
for i := 0; i < 1000; i++ {
    processBytes(keyBytes)
}
```

### CopyString 工具

```go
import "github.com/valyala/fasthttp/util"

func handler(ctx *fasthttp.RequestCtx) {
    // 需要持久化时使用
    path := util.CopyString(ctx.Path())  // 复制到新 string
    go func() {
        process(path)  // 安全使用
    }()
}
```

## 文件服务优化

### 零拷贝文件服务

```go
// ✅ 使用 fasthttp.ServeFile
func fileHandler(ctx *fasthttp.RequestCtx) {
    path := "/var/www" + string(ctx.Path())
    fasthttp.ServeFile(ctx, path)  // 零拷贝
}

// 或使用 ServeFileUncompressed
func fileHandler(ctx *fasthttp.RequestCtx) {
    path := "/var/www" + string(ctx.Path())
    fasthttp.ServeFileUncompressed(ctx, path)
}
```

### 发送文件

```go
// ❌ 读取到内存再发送
func badFileHandler(ctx *fasthttp.RequestCtx) {
    data, _ := os.ReadFile("/var/www/file.txt")
    ctx.SetBody(data)  // 分配内存
}

// ✅ 直接发送文件
func goodFileHandler(ctx *fasthttp.RequestCtx) {
    fasthttp.ServeFile(ctx, "/var/www/file.txt")
}
```

## 批量操作

### 批量写入

```go
// ❌ 多次 Write
ctx.WriteString("{")
ctx.WriteString("\"status\": \"ok\"")
ctx.WriteString("}")

// ✅ 一次性写入
ctx.SetBody([]byte(`{"status": "ok"}`))

// 或使用 Write
ctx.Write([]byte("{\"status\": \"ok\"}"))
```

### 合并缓冲区

```go
// ❌ 多次分配
parts := [][]byte{[]byte("Hello"), []byte(" "), []byte("World")}
for _, part := range parts {
    ctx.Write(part)
}

// ✅ 预分配一次
totalLen := 0
for _, part := range parts {
    totalLen += len(part)
}
result := make([]byte, 0, totalLen)
for _, part := range parts {
    result = append(result, part...)
}
ctx.SetBody(result)
```

## 连接优化

### 连接复用

```go
// ✅ 使用 HostClient 复用连接
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
```

### 并发控制

```go
// ✅ 使用信号量控制并发
type Semaphore chan struct{}

func NewSemaphore(n int) Semaphore {
    return make(chan struct{}, n)
}

func (s Semaphore) Acquire() {
    s <- struct{}{}
}

func (s Semaphore) Release() {
    <-s
}

func main() {
    sem := NewSemaphore(100)  // 最多 100 并发

    for i := 0; i < 10000; i++ {
        go func(i int) {
            sem.Acquire()
            defer sem.Release()

            // 执行请求
            makeRequest(i)
        }(i)
    }
}
```

## 性能测试

### 基准测试

```go
func BenchmarkHandler(b *testing.B) {
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.SetBody([]byte("OK"))
    }

    b.ResetTimer()
    b.ReportAllocs()

    for i := 0; i < b.N; i++ {
        ctx := &fasthttp.RequestCtx{}
        handler(ctx)
    }
}
```

### wrk 测试

```bash
# 安装 wrk
git-skills clone https://github.com/wg/wrk.git
cd wrk && make

# 测试
wrk -t12 -c400 -d30s http://localhost:8080/api/users
```

### ab 测试

```bash
# Apache Bench
ab -n 100000 -c 100 http://localhost:8080/api/users
```

## 性能分析

### CPU 分析

```go
import _ "net/http/pprof"

func main() {
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()

    fasthttp.ListenAndServe(":8080", handler)
}
```

```bash
# 采集 CPU profile
go tool pprof http://localhost:6060/debug/pprof/profile

# 分析
go tool pprof cpu.prof
```

### 内存分析

```bash
# 采集内存 profile
curl http://localhost:6060/debug/pprof/heap > heap.prof

# 分析
go tool pprof heap.prof
```

## 常见性能陷阱

### 1. 频繁 string 转换

```go
// ❌ 每次都转换
for _, item := range items {
    key := string(item.Key)
    cache[key] = item
}

// ✅ 批量处理
itemsMap := make(map[string]Item)
for _, item := range items {
    itemsMap[string(item.Key)] = item
}
```

### 2. 不必要的拷贝

```go
// ❌ 不必要的拷贝
func process(data []byte) {
    copy := make([]byte, len(data))
    copy(copy, data)
    // 使用 copy
}

// ✅ 直接使用
func process(data []byte) {
    // 使用 data（如果不被其他地方引用）
}
```

### 3. 小对象频繁分配

```go
// ❌ 频繁分配小对象
func handler(ctx *fasthttp.RequestCtx) {
    for i := 0; i < 100; i++ {
        data := make([]byte, 64)
        // 使用 data
    }
}

// ✅ 使用对象池
var byteSlice64Pool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 64)
    },
}

func handler(ctx *fasthttp.RequestCtx) {
    for i := 0; i < 100; i++ {
        data := byteSlice64Pool.Get().([]byte)
        defer byteSlice64Pool.Put(data)
        // 使用 data
    }
}
```

## 性能清单

- [ ] 避免 string() 转换
- [ ] 使用 []byte 进行比较和操作
- [ ] 正确使用 Acquire/Release
- [ ] 使用 sync.Pool 重用对象
- [ ] 预分配缓冲区容量
- [ ] 使用 HostClient 复用连接
- [ ] 批量操作减少系统调用
- [ ] 避免不必要的数据拷贝
- [ ] 使用 fasthttp.ServeFile 服务文件
- [ ] 定期进行性能分析
