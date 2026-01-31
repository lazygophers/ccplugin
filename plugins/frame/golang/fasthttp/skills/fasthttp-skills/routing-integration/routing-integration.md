# fasthttp-skills 路由集成

fasthttp-skills 本身不提供路由功能，需要集成第三方路由器来实现灵活的路由管理。

## fasthttp-routing

### 基础使用

```go
import "github.com/fasthttp/router"

func main() {
    r := router.New()

    // 基础路由
    r.GET("/", func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString("Home")
    })

    r.POST("/users", func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString("Create user")
    })

    fasthttp.ListenAndServe(":8080", r.Handler)
}
```

### 路径参数

```go
r := router.New()

// 单个参数
r.GET("/users/:id", func(ctx *fasthttp.RequestCtx) {
    userID := ctx.UserValue("id").(string)
    fmt.Fprintf(ctx, "User ID: %s", userID)
})

// 多个参数
r.GET("/users/:id/posts/:post_id", func(ctx *fasthttp.RequestCtx) {
    userID := ctx.UserValue("id").(string)
    postID := ctx.UserValue("post_id").(string)
    fmt.Fprintf(ctx, "User: %s, Post: %s", userID, postID)
})
```

### 通配符路由

```go
r := router.New()

// * 匹配剩余路径
r.GET("/files/*", func(ctx *fasthttp.RequestCtx) {
    filepath := ctx.UserValue("*").(string)
    fmt.Fprintf(ctx, "File: %s", filepath)
})

// 访问 /files/src/main.go
// 输出: File: src/main.go
```

### HTTP 方法

```go
r := router.New()

r.GET("/resource", getHandler)
r.POST("/resource", postHandler)
r.PUT("/resource", putHandler)
r.DELETE("/resource", deleteHandler)
r.PATCH("/resource", patchHandler)
r.HEAD("/resource", headHandler)
r.OPTIONS("/resource", optionsHandler)

// 匹配所有方法
r.Any("/any", anyHandler)
```

### 路由分组

```go
r := router.New()

// API 版本分组
v1 := r.Group("/api/v1")
v1.GET("/users", listUsers)
v1.POST("/users", createUser)
v1.GET("/users/:id", getUser)

// 嵌套分组
users := v1.Group("/users/:userId")
users.GET("/posts", listUserPosts)
users.POST("/posts", createUserPost)
```

### 尾部斜杠

```go
r := router.New()

// 严格尾部斜杠
r.GET("/users", handler)     // 只匹配 /users
r.GET("/users/", handler2)   // 只匹配 /users/

// 或使用 PanicHandler 处理
r.PanicHandler = func(ctx *fasthttp.RequestCtx, err interface{}) {
    ctx.SetStatusCode(500)
    ctx.SetBody([]byte("Internal Error"))
}
```

## 自定义路由器

### 简单路由器

```go
type Router struct {
    routes map[string]map[string]fasthttp.RequestHandler
    // method -> path -> handler
}

func NewRouter() *Router {
    return &Router{
        routes: make(map[string]map[string]fasthttp.RequestHandler),
    }
}

func (r *Router) Handle(method, path string, handler fasthttp.RequestHandler) {
    if r.routes[method] == nil {
        r.routes[method] = make(map[string]fasthttp.RequestHandler)
    }
    r.routes[method][path] = handler
}

func (r *Router) GET(path string, handler fasthttp.RequestHandler) {
    r.Handle("GET", path, handler)
}

func (r *Router) POST(path string, handler fasthttp.RequestHandler) {
    r.Handle("POST", path, handler)
}

func (r *Router) Handler() fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        method := string(ctx.Method())
        path := string(ctx.Path())

        if handlers, ok := r.routes[method]; ok {
            if handler, ok := handlers[path]; ok {
                handler(ctx)
                return
            }
        }

        ctx.Error("Not Found", 404)
    }
}

func main() {
    r := NewRouter()
    r.GET("/", func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString("Home")
    })
    r.POST("/users", func(ctx *fasthttp.RequestCtx) {
        ctx.WriteString("Create user")
    })

    fasthttp.ListenAndServe(":8080", r.Handler())
}
```

### 参数化路由器

```go
type ParamRoute struct {
    Template string
    Handler  fasthttp.RequestHandler
    Params   []string
}

type ParamRouter struct {
    routes []ParamRoute
}

func (r *ParamRouter) AddRoute(template string, handler fasthttp.RequestHandler) {
    // 解析参数
    parts := strings.Split(template, "/")
    var params []string
    for _, part := range parts {
        if strings.HasPrefix(part, ":") {
            params = append(params, part[1:])
        }
    }

    r.routes = append(r.routes, ParamRoute{
        Template: template,
        Handler:  handler,
        Params:   params,
    })
}

func (r *ParamRouter) Handler() fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        path := string(ctx.Path())

        for _, route := range r.routes {
            if r.match(route.Template, path) {
                // 提取参数
                params := r.extractParams(route.Template, path)
                for i, param := range route.Params {
                    ctx.SetUserValue(param, params[i])
                }
                route.Handler(ctx)
                return
            }
        }

        ctx.Error("Not Found", 404)
    }
}
```

## 中间件

### 基础中间件

```go
func middleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        // 前置处理
        start := time.Now()

        // 调用下一个处理器
        next(ctx)

        // 后置处理
        duration := time.Since(start)
        ctx.Response.Header.Set("X-Duration", duration.String())
    }
}
```

### 应用中间件

```go
// 单个路由
r.GET("/protected", middleware(handler))

// 路由组
api := r.Group("/api", middleware)
api.GET("/users", handler)

// 全局中间件
handler := middleware(globalHandler)
fasthttp.ListenAndServe(":8080", handler)
```

### 日志中间件

```go
func LoggerMiddleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
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

### 认证中间件

```go
func AuthMiddleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        token := ctx.Request.Header.Peek("Authorization")
        if len(token) == 0 {
            ctx.Error("Unauthorized", 401)
            return
        }

        // 验证 token
        if !validateToken(token) {
            ctx.Error("Invalid token", 401)
            return
        }

        next(ctx)
    }
}
```

### 限流中间件

```go
type RateLimiter struct {
    visitors map[string]*rate.Limiter
    mu       sync.RWMutex
    rate     rate.Limit
    burst    int
}

func NewRateLimiter(r rate.Limit, b int) *RateLimiter {
    return &RateLimiter{
        visitors: make(map[string]*rate.Limiter),
        rate:     r,
        burst:    b,
    }
}

func (rl *RateLimiter) Middleware(next fasthttp.RequestHandler) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        ip := ctx.RemoteIP().String()

        rl.mu.Lock()
        limiter, exists := rl.visitors[ip]
        if !exists {
            limiter = rate.NewLimiter(rl.rate, rl.burst)
            rl.visitors[ip] = limiter
        }
        rl.mu.Unlock()

        if !limiter.Allow() {
            ctx.Error("Rate limit exceeded", 429)
            return
        }

        next(ctx)
    }
}
```

## 其他路由器

### gorilla/mux 适配

```go
import "github.com/gorilla/mux"

func main() {
    r := mux.NewRouter()

    r.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("Hello"))
    }).Methods("GET")

    // 转换为 fasthttp.Handler
    handler := fasthttp.CompressHandler(
        fasthttpadaptor.NewFastHTTPHandler(r),
    )

    fasthttp.ListenAndServe(":8080", handler)
}
```

### httprouter 适配

```go
import "github.com/julienschmidt/httprouter"

func main() {
    router := httprouter.New()

    router.GET("/users/:id", func(w http.ResponseWriter, r *http.Request, ps httprouter.Params) {
        id := ps.ByName("id")
        w.Write([]byte("User: " + id))
    })

    handler := fasthttpadaptor.NewFastHTTPHandlerWithParams(func(
        ctx *fasthttp.RequestCtx,
        ps map[string]string,
    ) {
        // 转换参数
        params := make([]httprouter.Param, 0, len(ps))
        for k, v := range ps {
            params = append(params, httprouter.Param{Key: k, Value: v})
        }

        // 创建 httprouter 的参数
        // 需要适配器支持
    })
}
```

## URL 生成

### 路由命名

```go
type NamedRouter struct {
    *router.Router
    names map[string]string
}

func (r *NamedRouter) Named(name, path string, handler fasthttp.RequestHandler) {
    r.names[name] = path
    r.Handler(method, path, handler)
}

func (r *NamedRouter) URL(name string, params map[string]string) string {
    path := r.names[name]
    for key, value := range params {
        path = strings.ReplaceAll(path, ":"+key, value)
    }
    return path
}
```

## 静态文件

### 文件服务器

```go
func main() {
    r := router.New()

    // 静态文件
    r.ServeFiles("/static", "./public")

    // 单个文件
    r.GET("/favicon.ico", func(ctx *fasthttp.RequestCtx) {
        fasthttp.ServeFile(ctx, "./public/favicon.ico")
    })

    fasthttp.ListenAndServe(":8080", r.Handler)
}
```

### 自定义文件服务

```go
func FileServer(route string, root string) fasthttp.RequestHandler {
    return func(ctx *fasthttp.RequestCtx) {
        path := string(ctx.Path())

        // 移除路由前缀
        if strings.HasPrefix(path, route) {
            path = path[len(route):]
        }

        // 安全处理
        if strings.Contains(path, "..") {
            ctx.Error("Invalid path", 400)
            return
        }

        filePath := filepath.Join(root, path)
        fasthttp.ServeFile(ctx, filePath)
    }
}

func main() {
    r := router.New()
    r.GET("/files/*", FileServer("/files", "./public"))
    fasthttp.ListenAndServe(":8080", r.Handler)
}
```

## 最佳实践

1. **使用成熟的路由库**：如 fasthttp/router
2. **避免过度嵌套**：路由层级保持在 3 层以内
3. **RESTful 风格**：使用 HTTP 方法和资源路径
4. **中间件顺序**：认证 → 限流 → 日志 → 处理器
5. **参数验证**：在中间件中验证参数
6. **错误处理**：统一错误响应格式
