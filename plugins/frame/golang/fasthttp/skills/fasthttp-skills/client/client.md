# fasthttp-skills 客户端开发

fasthttp-skills 提供高性能的 HTTP 客户端，适用于高频率请求场景。

## 基础请求

### GET 请求

```go
func main() {
    // 获取请求和响应对象
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    // 设置请求
    req.SetRequestURI("http://example.com/")
    req.Header.SetMethod("GET")

    // 发送请求
    if err := fasthttp.Do(req, resp); err != nil {
        log.Fatal(err)
    }

    // 处理响应
    fmt.Printf("Status: %d\n", resp.StatusCode())
    fmt.Printf("Body: %s\n", resp.Body())
}
```

### POST 请求

```go
func main() {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    // 设置请求
    req.SetRequestURI("http://example.com/api")
    req.Header.SetMethod("POST")
    req.Header.SetContentType("application/json")
    req.SetBody([]byte(`{"key": "value"}`))

    // 发送请求
    if err := fasthttp.Do(req, resp); err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Response: %s\n", resp.Body())
}
```

## Client 配置

### 基础配置

```go
func main() {
    // 创建客户端
    client := &fasthttp.Client{
        Name: "MyClient",
        // 超时配置
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 5 * time.Second,
        // 连接池
        MaxConnsPerHost: 100,
    }

    // 使用客户端
    statusCode, body, err := client.Get(nil, "http://example.com/")
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Status: %d\n", statusCode)
    fmt.Printf("Body: %s\n", body)
}
```

### 完整配置

```go
func main() {
    client := &fasthttp.Client{
        Name: "MyClient",

        // 超时配置
        ReadTimeout:                   5 * time.Second,
        WriteTimeout:                  5 * time.Second,
        MaxConnDuration:               30 * time.Second,

        // 连接池配置
        MaxConnsPerHost:               100,
        MaxIdleConnDuration:           10 * time.Second,

        // TLS 配置
        TLSConfig: &tls.Config{
            InsecureSkipVerify: false,
            MinVersion:            tls.VersionTLS12,
        },

        // DNS 缓存
        MaxConnsPerHost:              100,
        MaxIdleConnDuration:          10 * time.Second,

        // 其他
        DisableHeaderNamesNormalizing: false,
        DisablePathNormalizing:       false,
    }

    // 使用客户端...
}
```

## HostClient

### 连接复用

```go
func main() {
    // 创建 HostClient（连接复用）
    c := &fasthttp.HostClient{
        Addr: "example.com:80",
        Name: "MyHostClient",
    }

    // 发送请求
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    req.SetRequestURI("http://example.com/")

    if err := c.Do(req, resp); err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Status: %d\n", resp.StatusCode())
}
```

### HostClient 优势

- 连接复用：减少 TCP 握手开销
- 适用于单个主机的大量请求
- 更低延迟和更高吞吐量

## LCProxyClient

### 代理支持

```go
func main() {
    // 使用代理
    proxyAddr := "proxy.example.com:8080"

    client := &fasthttp.HostClient{
        Addr: "example.com:80",
        Proxy: fasthttp.ProxyConfig{
            Addr: proxyAddr,
        },
    }

    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    req.SetRequestURI("http://example.com/")

    if err := client.Do(req, resp); err != nil {
        log.Fatal(err)
    }
}
```

## 请求头

### 设置请求头

```go
func main() {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    // 设置请求头
    req.Header.SetMethod("GET")
    req.Header.Set("User-Agent", "MyClient/1.0")
    req.Header.Set("Accept", "application/json")
    req.Header.Set("Authorization", "Bearer token")

    // 批量设置
    req.Header.Set("X-Custom-Header", "value")

    // 或使用 SetBytesV
    req.Header.SetBytesV("X-Custom-Header", []byte("value"))

    req.SetRequestURI("http://example.com/")

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    fasthttp.Do(req, resp)
}
```

### Cookie 处理

```go
func main() {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    // 设置 Cookie
    req.Header.SetCookie("session", "abc123")
    req.Header.SetCookie("user_id", "12345")

    // 获取响应的 Cookie
    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    req.SetRequestURI("http://example.com/")
    fasthttp.Do(req, resp)

    // 读取 Cookie
    cookies := resp.Header.Peek("Set-Cookie")
    fmt.Printf("Cookies: %s\n", cookies)
}
```

## 表单提交

### URL 编码表单

```go
func main() {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    req.SetRequestURI("http://example.com/form")
    req.Header.SetMethod("POST")
    req.Header.SetContentType("application/x-www-form-urlencoded")

    // 设置表单数据
    args := req.PostArgs()
    args.Set("username", "john")
    args.Set("email", "john@example.com")
    args.Set("age", "30")

    // 发送请求
    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    if err := fasthttp.Do(req, resp); err != nil {
        log.Fatal(err)
    }
}
```

### Multipart 表单

```go
func main() {
    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    req.SetRequestURI("http://example.com/upload")
    req.Header.SetMethod("POST")

    // 创建 multipart 表单
    body, err := fasthttp.CreateMultipartFormBoundary()
    if err != nil {
        log.Fatal(err)
    }

    // 设置 boundary
    req.Header.SetContentType("multipart/form-data; boundary=" + body)

    // 添加表单字段
    req.SetBodyStream(bytes.NewReader([]byte(
        "--"+body+"\r\n"+
        "Content-Disposition: form-data; name=\"field\"\r\n\r\n"+
        "value\r\n"+
        "--"+body+"--\r\n",
    )), -1)

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    fasthttp.Do(req, resp)
}
```

## 重定向处理

### 自动跟随重定向

```go
func main() {
    // 默认最多跟随 10 次重定向
    statusCode, body, err := fasthttp.Get(nil, "http://example.com/redirect")
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Final status: %d\n", statusCode)
    fmt.Printf("Body: %s\n", body)
}
```

### 禁用重定向

```go
func main() {
    client := &fasthttp.Client{
        // 禁止重定向
        NoDefaultRedirectHeader: true,
    }

    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    req.SetRequestURI("http://example.com/redirect")

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    if err := client.Do(req, resp); err != nil {
        log.Fatal(err)
    }

    // 检查是否是重定向
    if resp.StatusCode() == fasthttp.StatusFound {
        location := resp.Header.Peek("Location")
        fmt.Printf("Redirect to: %s\n", location)
    }
}
```

## 并发请求

### Goroutine 并发

```go
func main() {
    urls := []string{
        "http://example.com/1",
        "http://example.com/2",
        "http://example.com/3",
    }

    var wg sync.WaitGroup
    for _, url := range urls {
        wg.Add(1)
        go func(url string) {
            defer wg.Done()

            statusCode, body, err := fasthttp.Get(nil, url)
            if err != nil {
                log.Printf("Error fetching %s: %v", url, err)
                return
            }

            log.Printf("%s: %d", url, statusCode)
        }(url)
    }

    wg.Wait()
}
```

### Worker Pool

```go
func main() {
    urls := make(chan string, 100)

    // 启动 workers
    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for url := range urls {
                statusCode, _, err := fasthttp.Get(nil, url)
                if err != nil {
                    log.Printf("Error: %v", err)
                    continue
                }
                log.Printf("Fetched: %s (%d)", url, statusCode)
            }
        }()
    }

    // 添加 URL
    for i := 0; i < 100; i++ {
        urls <- fmt.Sprintf("http://example.com/%d", i)
    }
    close(urls)

    wg.Wait()
}
```

## 性能优化

### 连接池

```go
func main() {
    // 配置连接池
    client := &fasthttp.Client{
        MaxConnsPerHost:     100,  // 每个主机最大连接数
        MaxIdleConnDuration: 10 * time.Second,
    }

    // 复用连接的请求
    for i := 0; i < 1000; i++ {
        statusCode, _, err := client.Get(nil, "http://example.com/")
        if err != nil {
            log.Fatal(err)
        }
        _ = statusCode
    }
}
```

### Pipeline

```go
func main() {
    // fasthttp-skills 不直接支持 HTTP pipelining
    // 使用并发代替
    client := &fasthttp.Client{
        MaxConnsPerHost: 100,
    }

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(i int) {
            defer wg.Done()
            statusCode, _, _ := client.Get(
                nil,
                fmt.Sprintf("http://example.com/%d", i),
            )
            _ = statusCode
        }(i)
    }

    wg.Wait()
}
```

## 错误处理

### 重试机制

```go
func GetWithRetry(url string, maxRetries int) ([]byte, error) {
    var body []byte
    var err error

    for i := 0; i < maxRetries; i++ {
        statusCode, b, e := fasthttp.Get(nil, url)
        if e == nil && statusCode == fasthttp.StatusOK {
            return b, nil
        }

        err = e
        time.Sleep(time.Duration(i+1) * time.Second)
    }

    return body, fmt.Errorf("max retries exceeded: %w", err)
}

func main() {
    body, err := GetWithRetry("http://example.com/", 3)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Body: %s\n", body)
}
```

### 超时控制

```go
func main() {
    client := &fasthttp.Client{
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 5 * time.Second,
    }

    req := fasthttp.AcquireRequest()
    defer fasthttp.ReleaseRequest(req)

    req.SetRequestURI("http://example.com/")

    resp := fasthttp.AcquireResponse()
    defer fasthttp.ReleaseResponse(resp)

    err := client.DoTimeout(req, resp, 10*time.Second)
    if err != nil {
        log.Fatal(err)
    }
}
```
