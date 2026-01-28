---
name: lrpc-network
description: lazygophers/utils/urlx 网络工具库规范 - IP 地址处理、真实 IP 提取、URL 参数排序、网卡信息获取
---

# lrpc-network - 网络工具库

网络和 URL 处理工具库，提供 IP 地址处理、真实 IP 提取和 URL 操作功能。

## 特性

- 🌐 **IP 地址处理** - 网卡 IP、内网判断
- 🔍 **真实 IP 提取** - 支持 13+ 种代理头
- 🔗 **URL 参数排序** - 签名验证
- ⚡ **高性能** - 零分配字符串操作

## IP 地址处理

### 获取网卡 IP

```go
import "github.com/lazygophers/utils/urlx"

// 通过网卡名称获取 IP
ip, err := urlx.GetInterfaceIpByName("eth0")
if err != nil {
    return err
}
fmt.Println(ip)  // 192.168.1.100

// macOS 网卡
ip, err := urlx.GetInterfaceIpByName("en0")

// 回环网卡
ip, err := urlx.GetInterfaceIpByName("lo")
```

### 通过地址列表获取 IP

```go
import (
    "net"
    "github.com/lazygophers/utils/urlx"
)

// 获取所有网卡地址
addrs, _ := net.InterfaceAddrs()

// 提取 IPv4
ipv4, err := urlx.GetInterfaceIpByAddrs(addrs, false)
if err != nil {
    return err
}
fmt.Println(ipv4)  // 192.168.1.100

// 提取 IPv6
ipv6, err := urlx.GetInterfaceIpByAddrs(addrs, true)
```

### 自动选择监听 IP

```go
// 自动检测合适的 IP 地址
// 优先级：eth0 > en0 > loopback
ip, err := urlx.GetListenIp()
if err != nil {
    return err
}

serverAddr := fmt.Sprintf("%s:8080", ip)
listener, _ := net.Listen("tcp", serverAddr)
```

### 判断内网 IP

```go
// 判断是否为内网 IP（RFC1918 + loopback + link-local）
isLocal := urlx.IsLocalIp("192.168.1.100")   // true
isLocal := urlx.IsLocalIp("10.0.0.1")       // true
isLocal := urlx.IsLocalIp("172.16.0.1")     // true
isLocal := urlx.IsLocalIp("127.0.0.1")      // true
isLocal := urlx.IsLocalIp("169.254.0.1")    // true
isLocal := urlx.IsLocalIp("8.8.8.8")        // false
```

### 支持的内网 IP 段

| 范围 | 说明 |
|------|------|
| 10.0.0.0/8 | 私有网络 A 类 |
| 172.16.0.0/12 | 私有网络 B 类 |
| 192.168.0.0/16 | 私有网络 C 类 |
| 127.0.0.0/8 | 回环地址 |
| 169.254.0.0/16 | 链路本地 |

## 真实 IP 提取

### 从 HTTP 头提取

```go
import "github.com/lazygophers/utils/urlx"

// 从 http.Request 提取真实客户端 IP
func GetRealIP(r *http.Request) string {
    return urlx.RealIpFromHeader(r.Header)
}

// 使用示例
http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
    realIP := urlx.RealIpFromHeader(r.Header)
    fmt.Fprintf(w, "Your IP: %s\n", realIP)
})
```

### 支持的代理头

RealIpFromHeader 按优先级检查以下头部：

1. `X-Forwarded-For` - Cloudflare, AWS ALB
2. `X-Real-Ip` - Nginx
3. `CF-Connecting-IP` - Cloudflare
4. `True-Client-Ip` - Akamai
5. `X-Client-IP` - Squid
6. `X-Forwarded` - 非标准
7. `Forwarded-For` - 非标准
8. `Forwarded` - RFC 7239
9. `X-Cluster-Client-Ip` - 集群
10. `Fastly-Client-Ip` - Fastly
11. `Cf-Pseudo-IPv4` - Cloudflare pseudo IPv4
12. `X-Akamai-Edge-Sight` - Akamai
13. `WL-Proxy-Client-IP` - WebLogic

### 处理多级代理

```go
// X-Forwarded-For: client, proxy1, proxy2
// RealIpFromHeader 返回第一个非内网 IP

header := http.Header{}
header.Set("X-Forwarded-For", "192.168.1.100, 203.0.113.1, 198.51.100.1")

realIP := urlx.RealIpFromHeader(header)
// 返回: 203.0.113.1（跳过内网 IP 192.168.1.100）
```

### 自定义提取逻辑

```go
// 如果默认逻辑不满足需求，可以自定义
func CustomGetRealIP(r *http.Request) string {
    // 1. 尝试自定义头部
    if ip := r.Header.Get("X-Custom-IP"); ip != "" {
        return ip
    }

    // 2. 使用默认逻辑
    return urlx.RealIpFromHeader(r.Header)
}
```

### IP 白名单验证

```go
// 验证真实 IP 是否在白名单中
func CheckWhitelist(r *http.Request, whitelist []string) bool {
    realIP := urlx.RealIpFromHeader(r.Header)

    for _, allowed := range whitelist {
        if realIP == allowed {
            return true
        }
    }

    return false
}

// 使用
allowedIPs := []string{"203.0.113.1", "198.51.100.1"}
if !CheckWhitelist(r, allowedIPs) {
    http.Error(w, "Forbidden", http.StatusForbidden)
    return
}
```

## URL 参数排序

### 排序查询参数

```go
import "github.com/lazygophers/utils/urlx"

// 原始 URL
urlStr := "https://example.com/api?c=3&a=1&b=2"

// 排序查询参数
sorted, err := urlx.SortQuery(urlStr)
if err != nil {
    return err
}

fmt.Println(sorted)
// https://example.com/api?a=1&b=2&c=3
```

### 应用场景：签名验证

```go
// 生成签名
func GenerateSignature(urlStr string, secret string) string {
    // 1. 排序查询参数
    sortedURL, _ := urlx.SortQuery(urlStr)

    // 2. 提取查询部分
    u, _ := url.Parse(sortedURL)
    query := u.Query().Encode()

    // 3. 计算签名
    h := hmac.New(sha256.New, []byte(secret))
    h.Write([]byte(query))
    return hex.EncodeToString(h.Sum(nil))
}

// 验证签名
func VerifySignature(urlStr, secret, signature string) bool {
    expected := GenerateSignature(urlStr, secret)
    return hmac.Equal([]byte(expected), []byte(signature))
}
```

### 缓存键生成

```go
// 生成缓存键（忽略参数顺序）
func GetCacheKey(urlStr string) string {
    sortedURL, _ := urlx.SortQuery(urlStr)
    return sortedURL
}

// 以下两个 URL 生成相同的缓存键
key1 := GetCacheKey("https://api.example.com?b=2&a=1")
key2 := GetCacheKey("https://api.example.com?a=1&b=2")
// key1 == key2
```

### 处理特殊字符

```go
// URL 编码会被保留
urlStr := "https://example.com?name=John%20Doe&age=30"
sorted, _ := urlx.SortQuery(urlStr)
// https://example.com?age=30&name=John%20Doe
```

## 完整示例：反向代理

```go
package main

import (
    "fmt"
    "net/http"
    "github.com/lazygophers/utils/urlx"
)

func main() {
    // 获取监听地址
    listenIP, _ := urlx.GetListenIp()
    addr := fmt.Sprintf("%s:8080", listenIP)

    // 启动服务器
    server := &http.Server{
        Addr: addr,
        Handler: &handler{},
    }

    fmt.Printf("Listening on %s\n", addr)
    server.ListenAndServe()
}

type handler struct{}

func (h *handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    // 获取真实客户端 IP
    realIP := urlx.RealIpFromHeader(r.Header)

    // 判断是否为内网 IP
    isLocal := urlx.IsLocalIp(realIP)

    // 构造响应
    fmt.Fprintf(w, "Real IP: %s\n", realIP)
    fmt.Fprintf(w, "Is Local: %v\n", isLocal)

    // 显示原始请求头（调试用）
    fmt.Fprintf(w, "\nHeaders:\n")
    for k, v := range r.Header {
        fmt.Fprintf(w, "  %s: %s\n", k, v)
    }
}
```

## 完整示例：签名验证中间件

```go
package middleware

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "net/http"
    "github.com/lazygophers/utils/urlx"
)

// SignatureMiddleware 验证请求签名
func SignatureMiddleware(secret string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            // 1. 获取签名
            signature := r.Header.Get("X-Signature")
            if signature == "" {
                http.Error(w, "missing signature", http.StatusUnauthorized)
                return
            }

            // 2. 重建 URL（确保参数顺序一致）
            urlStr := r.URL.String()

            // 3. 计算期望签名
            expectedSig := generateSignature(urlStr, secret)

            // 4. 验证签名
            if !hmac.Equal([]byte(expectedSig), []byte(signature)) {
                http.Error(w, "invalid signature", http.StatusForbidden)
                return
            }

            // 5. 签名验证通过，继续处理
            next.ServeHTTP(w, r)
        })
    }
}

func generateSignature(urlStr, secret string) string {
    // 排序查询参数
    sortedURL, _ := urlx.SortQuery(urlStr)

    // 提取查询部分
    u, _ := url.Parse(sortedURL)
    query := u.Query().Encode()

    // 计算 HMAC-SHA256
    h := hmac.New(sha256.New, []byte(secret))
    h.Write([]byte(query))
    return hex.EncodeToString(h.Sum(nil))
}
```

## 最佳实践

### 1. 服务监听

```go
// ✅ 使用 GetListenIp 自动选择
ip, _ := urlx.GetListenIp()
server := fmt.Sprintf("%s:8080", ip)

// ❌ 硬编码 IP
server := "192.168.1.100:8080"
```

### 2. 日志记录

```go
// ✅ 记录真实 IP
func LogRequest(r *http.Request) {
    realIP := urlx.RealIpFromHeader(r.Header)
    log.Info("request",
        log.Field("ip", realIP),
        log.Field("path", r.URL.Path),
    )
}

// ❌ 记录代理 IP
log.Info("request", log.Field("ip", r.RemoteAddr))
```

### 3. IP 限制

```go
// ✅ 基于真实 IP 限制
func RateLimitMiddleware() http.Handler {
    return func(w http.ResponseWriter, r *http.Request) {
        realIP := urlx.RealIpFromHeader(r.Header)

        if isRateLimited(realIP) {
            http.Error(w, "too many requests", http.StatusTooManyRequests)
            return
        }

        next.ServeHTTP(w, r)
    }
}
```

### 4. 签名验证

```go
// ✅ 验证前排序参数
sortedURL, _ := urlx.SortQuery(urlStr)
signature := computeSignature(sortedURL)

// ❌ 直接使用原始 URL（参数顺序可能不同）
signature := computeSignature(urlStr)
```

## 性能注意事项

1. **GetListenIp** - 涉及系统调用，不应在热路径频繁调用
2. **RealIpFromHeader** - 纯字符串操作，性能开销很小
3. **SortQuery** - 需要解析和重建 URL，有性能开销

## 参考资源

- [lazygophers/utils/urlx GitHub](https://github.com/lazygophers/utils/tree/main/urlx)
- [RFC 1918 - 私有地址](https://tools.ietf.org/html/rfc1918)
- [RFC 7239 - Forwarded Header](https://tools.ietf.org/html/rfc7239)
