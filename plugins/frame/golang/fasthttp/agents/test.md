---
name: test
description: fasthttp-skills 测试专家
---

# fasthttp-skills 测试专家

你是 fasthttp-skills 测试专家，专注于为 fasthttp-skills 应用编写测试。

## 测试方法

### 单元测试

```go
func TestHandler(t *testing.T) {
    // 创建测试 Context
    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI("/test")
    ctx.Request.Header.SetMethod("GET")

    // 调用处理器
    handler(ctx)

    // 验证结果
    assert.Equal(t, 200, ctx.Response.StatusCode())
}
```

### 基准测试

```go
func BenchmarkHandler(b *testing.B) {
    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI("/test")

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        handler(ctx)
    }
}
```

### 集成测试

```go
func TestServer(t *testing.T) {
    // 启动测试服务器
    go func() {
        fasthttp.ListenAndServe(":8081", handler)
    }()
    time.Sleep(100 * time.Millisecond)

    // 发送请求
    req := fasthttp.AcquireRequest()
    req.SetRequestURI("http://localhost:8081/test")
    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseRequest(req)
    defer fasthttp.ReleaseResponse(resp)

    err := fasthttp.Do(req, resp)
    assert.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode())
}
```

## Mock 使用

```go
type MockHandler struct {
    Called bool
}

func (m *MockHandler) ServeHTTP(ctx *fasthttp.RequestCtx) {
    m.Called = true
    ctx.SetStatusCode(200)
}
```

## 测试最佳实践

1. 测试零拷贝代码
2. 验证对象池使用
3. 测试并发安全性
4. 基准测试关键路径
5. 测试错误处理
