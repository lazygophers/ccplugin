# fasthttp 测试

fasthttp 提供测试支持，可以方便地进行单元测试和集成测试。

## Handler 测试

### 基础测试

```go
package main

import (
    "testing"
    "github.com/valyala/fasthttp"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestHandler(t *testing.T) {
    // 创建 handler
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.SetStatusCode(200)
        ctx.SetBody([]byte("OK"))
    }

    // 创建测试上下文
    ctx := &fasthttp.RequestCtx{}

    // 调用 handler
    handler(ctx)

    // 验证
    assert.Equal(t, 200, ctx.Response.StatusCode())
    assert.Equal(t, []byte("OK"), ctx.Response.Body())
}
```

### 设置请求

```go
func TestHandlerWithRequest(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        method := ctx.Method()
        path := ctx.Path()

        ctx.WriteString(fmt.Sprintf("%s %s", method, path))
    }

    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI("/users/123")
    ctx.Request.Header.SetMethod("GET")

    handler(ctx)

    assert.Equal(t, []byte("GET /users/123"), ctx.Response.Body())
}
```

### 请求体测试

```go
func TestHandlerWithBody(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        body := ctx.PostBody()
        ctx.SetBody(body)
    }

    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI("/users")
    ctx.Request.Header.SetMethod("POST")
    ctx.Request.SetBody([]byte(`{"name":"John"}`))

    handler(ctx)

    assert.Equal(t, []byte(`{"name":"John"}`), ctx.Response.Body())
}
```

### 查询参数测试

```go
func TestHandlerWithQuery(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        name := ctx.QueryArgs().Peek("name")
        ctx.SetBody(name)
    }

    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI("/search?name=John")

    handler(ctx)

    assert.Equal(t, []byte("John"), ctx.Response.Body())
}
```

### 路径参数测试

```go
func TestHandlerWithParams(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        id := ctx.UserValue("id")
        ctx.WriteString(id.(string))
    }

    ctx := &fasthttp.RequestCtx{}
    ctx.SetUserValue("id", "123")

    handler(ctx)

    assert.Equal(t, []byte("123"), ctx.Response.Body())
}
```

## 中间件测试

### 基础中间件测试

```go
func TestAuthMiddleware(t *testing.T) {
    next := func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString("Authenticated")
    }

    middleware := AuthMiddleware(next)

    // 测试有 token
    ctx := &fasthttp.RequestCtx{}
    ctx.Request.Header.Set("Authorization", "Bearer valid-token")

    middleware(ctx)

    assert.Equal(t, []byte("Authenticated"), ctx.Response.Body())
    assert.Equal(t, 200, ctx.Response.StatusCode())
}

func TestAuthMiddlewareUnauthorized(t *testing.T) {
    next := func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString("Should not reach here")
    }

    middleware := AuthMiddleware(next)

    // 测试无 token
    ctx := &fasthttp.RequestCtx{}

    middleware(ctx)

    assert.Equal(t, 401, ctx.Response.StatusCode())
    assert.NotContains(t, string(ctx.Response.Body()), "Should not reach")
}
```

## 客户端测试

### 模拟服务器

```go
func TestClient(t *testing.T) {
    // 启动测试服务器
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.SetBody([]byte("Response"))
    }

    go fasthttp.ListenAndServe(":8081", handler)
    defer fasthttp.Serve(":8081", nil) // 停止服务器

    // 等待服务器启动
    time.Sleep(100 * time.Millisecond)

    // 客户端请求
    statusCode, body, err := fasthttp.Get(nil, "http://localhost:8081/")

    require.NoError(t, err)
    assert.Equal(t, 200, statusCode)
    assert.Equal(t, []byte("Response"), body)
}
```

### Mock 测试

```go
type MockClient struct {
    Response *fasthttp.Response
    Error    error
}

func (m *MockClient) Do(req *fasthttp.Request, resp *fasthttp.Response) error {
    if m.Response != nil {
        *resp = *m.Response
    }
    return m.Error
}

func TestWithMock(t *testing.T) {
    mockResp := &fasthttp.Response{}
    mockResp.SetBody([]byte("Mock response"))
    mockResp.SetStatusCode(200)

    mock := &MockClient{Response: mockResp}

    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    err := mock.Do(req, resp)

    require.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode())
    assert.Equal(t, []byte("Mock response"), resp.Body())
}
```

## 基准测试

### Handler 基准测试

```go
func BenchmarkHandler(b *testing.B) {
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.SetBody([]byte("OK"))
    }

    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI("/test")

    b.ResetTimer()
    b.ReportAllocs()

    for i := 0; i < b.N; i++ {
        ctx.Request.Reset()
        handler(ctx)
    }
}
```

### 客户端基准测试

```go
func BenchmarkClient(b *testing.B) {
    // 启动测试服务器
    go fasthttp.ListenAndServe(":8082", func(ctx *fasthttp.RequestCtx) {
        ctx.SetBody([]byte("OK"))
    })
    defer fasthttp.Serve(":8082", nil)

    time.Sleep(100 * time.Millisecond)

    b.ResetTimer()
    b.ReportAllocs()

    for i := 0; i < b.N; i++ {
        fasthttp.Get(nil, "http://localhost:8082/")
    }
}
```

### 并发基准测试

```go
func BenchmarkConcurrent(b *testing.B) {
    go fasthttp.ListenAndServe(":8083", func(ctx *fasthttp.RequestCtx) {
        ctx.SetBody([]byte("OK"))
    })
    defer fasthttp.Serve(":8083", nil)

    time.Sleep(100 * time.Millisecond)

    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            fasthttp.Get(nil, "http://localhost:8083/")
        }
    })
}
```

## 表驱动测试

### 参数化测试

```go
func TestPathValidation(t *testing.T) {
    tests := []struct {
    name    string
    path    string
    valid   bool
    }{
        {"valid path", "/users/123", true},
        {"invalid path", "/users/abc", false},
        {"empty path", "", false},
        {"root path", "/", true},
    }

    handler := func(ctx *fasthttp.RequestCtx) {
        path := ctx.UserValue("id")
        if path == nil {
            ctx.SetStatusCode(400)
            return
        }

        // 验证 id 是数字
        id := path.(string)
        for _, c := range id {
            if c < '0' || c > '9' {
                ctx.SetStatusCode(400)
                return
            }
        }

        ctx.SetStatusCode(200)
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            ctx := &fasthttp.RequestCtx{}
            ctx.Request.SetRequestURI(tt.path)

            handler(ctx)

            if tt.valid {
                assert.Equal(t, 200, ctx.Response.StatusCode())
            } else {
                assert.NotEqual(t, 200, ctx.Response.StatusCode())
            }
        })
    }
}
```

### 方法测试

```go
func TestHTTPMethods(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString(string(ctx.Method()))
    }

    methods := []string{"GET", "POST", "PUT", "DELETE"}

    for _, method := range methods {
        t.Run(method, func(t *testing.T) {
            ctx := &fasthttp.RequestCtx{}
            ctx.Request.Header.SetMethod(method)
            ctx.Request.SetRequestURI("/test")

            handler(ctx)

            assert.Equal(t, []byte(method), ctx.Response.Body())
        })
    }
}
```

## 集成测试

### 完整流程测试

```go
func TestAPIIntegration(t *testing.T) {
    // 设置路由
    r := router.New()
    r.GET("/users/:id", func(ctx *fasthttp.RequestCtx) {
        id := ctx.UserValue("id").(string)
        ctx.SetBody([]byte(`{"id":"` + id + `","name":"John"}`))
    })
    r.POST("/users", func(ctx *fasthttp.RequestCtx) {
        ctx.SetStatusCode(201)
        ctx.SetBody([]byte(`{"id":"123"}`))
    })

    // 启动服务器
    go fasthttp.ListenAndServe(":8084", r.Handler)
    defer fasthttp.Serve(":8084", nil)

    time.Sleep(100 * time.Millisecond)

    // 测试 GET
    statusCode, body, err := fasthttp.Get(nil, "http://localhost:8084/users/123")

    require.NoError(t, err)
    assert.Equal(t, 200, statusCode)
    assert.Contains(t, string(body), `"id":"123"`)

    // 测试 POST
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    req.SetRequestURI("http://localhost:8084/users")
    req.Header.SetMethod("POST")
    req.SetBody([]byte(`{"name":"Jane"}`))

    err = fasthttp.Do(req, resp)
    require.NoError(t, err)

    assert.Equal(t, 201, resp.StatusCode())
    assert.Contains(t, string(resp.Body()), `"id":"123"`)
}
```

## 辅助函数

### 创建测试上下文

```go
func NewTestContext(method, uri string) *fasthttp.RequestCtx {
    ctx := &fasthttp.RequestCtx{}
    ctx.Request.SetRequestURI(uri)
    ctx.Request.Header.SetMethod(method)
    return ctx
}

func TestHandlerHelper(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString("OK")
    }

    ctx := NewTestContext("GET", "/test")
    handler(ctx)

    assert.Equal(t, []byte("OK"), ctx.Response.Body())
}
```

### 断言辅助函数

```go
func AssertStatusCode(t *testing.T, ctx *fasthttp.RequestCtx, expected int) {
    t.Helper()
    assert.Equal(t, expected, ctx.Response.StatusCode(), "status code mismatch")
}

func AssertBody(t *testing.T, ctx *fasthttp.RequestCtx, expected []byte) {
    t.Helper()
    assert.Equal(t, expected, ctx.Response.Body(), "body mismatch")
}

func TestHandlerWithHelpers(t *testing.T) {
    handler := func(ctx *fasthttp.RequestCtx) {
        ctx.SetStatusCode(200)
        ctx.SetBody([]byte("OK"))
    }

    ctx := NewTestContext("GET", "/test")
    handler(ctx)

    AssertStatusCode(t, ctx, 200)
    AssertBody(t, ctx, []byte("OK"))
}
```

## 测试最佳实践

1. **使用表驱动测试**：覆盖多种情况
2. **独立测试**：每个测试独立运行
3. **使用断言库**：testify 提供更好的错误信息
4. **基准测试**：关注性能变化
5. **并发测试**：验证并发安全性
6. **Mock 外部依赖**：隔离测试
7. **测试辅助函数**：减少重复代码
