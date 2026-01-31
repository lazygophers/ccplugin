# Fiber 路由系统

Fiber 提供强大且灵活的路由系统，支持路径参数、路由约束、通配符和路由分组。

## 基础路由

### HTTP 方法

```go
app := fiber.New()

// 所有标准 HTTP 方法
app.Get("/", handler)
app.Post("/", handler)
app.Put("/", handler)
app.Delete("/", handler)
app.Patch("/", handler)
app.Options("/", handler)
app.Head("/", handler)

// 匹配所有方法
app.All("/", handler)

// 添加路由（运行时）
app.Add("GET", "/path", handler)
```

### 处理器注册

```go
// 直接注册处理器
app.Get("/users", func(c *fiber.Ctx) error {
    return c.JSON(fiber.Map{"users": []string{}})
})

// 注册命名函数
func listUsers(c *fiber.Ctx) error {
    return c.JSON(fiber.Map{"users": []string{}})
}
app.Get("/users", listUsers)
```

## 路径参数

### 命名参数

```go
// 单个参数
app.Get("/users/:id", func(c *fiber.Ctx) error {
    id := c.Params("id")
    return c.SendString("User ID: " + id)
})

// 多个参数
app.Get("/users/:id/posts/:post_id", func(c *fiber.Ctx) error {
    userID := c.Params("id")
    postID := c.Params("post_id")
    return c.JSON(fiber.Map{
        "user": userID,
        "post": postID,
    })
})

// 可选参数
app.Get("/users/:id?", func(c *fiber.Ctx) error {
    id := c.Params("id")
    if id == "" {
        return c.SendString("All users")
    }
    return c.SendString("User: " + id)
})
```

### 通配符

```go
// * 匹配任意内容（包括分隔符）
app.Get("/files/*", func(c *fiber.Ctx) error {
    filepath := c.Params("*")
    return c.SendString("File: " + filepath)
})

// + 匹配任意内容（贪婪但非可选）
app.Get("/files/+", func(c *fiber.Ctx) error {
    files := c.Params("+")
    return c.SendString("Files: " + files)
})

// 示例
// GET /files/src/main.go → "File: src/main.go"
// GET /files/a/b/c → "File: a/b/c"
```

## 路由约束（v2.37.0+）

路由约束允许在路由定义时验证参数类型和格式。

### 整数约束

```go
app.Get("/user/:id<int>", func(c *fiber.Ctx) error {
    id := c.Params("id")
    return c.SendString("User ID: " + id)
})

// 可选整数参数
app.Get("/user/:id<int>?", func(c *fiber.Ctx) error {
    id := c.Params("id")
    if id == "" {
        return c.SendString("No ID provided")
    }
    return c.SendString("User ID: " + id)
})

// 示例
// GET /user/123 → "User ID: 123"
// GET /user/abc → 404 Not Found
```

### 布尔值约束

```go
app.Get("/active/:active<bool>", handler)

// 示例
// GET /active/true → active = "true"
// GET /active/false → active = "false"
// GET /active/yes → 404 Not Found
```

### 长度约束

```go
// 最小长度
app.Get("/username/:name<minLen(4)>", handler)

// 最大长度
app.Get("/filename/:name<maxLen(8)>", handler)

// 固定长度
app.Get("/code/:code<len(12)>", handler)

// 示例
// GET /username/john → OK
// GET /username/jo → 404 (less than 4)
// GET /filename/abcdefghi → 404 (more than 8)
```

### 范围约束

```go
// 数值范围
app.Get("/age/:age<min(18);max(120)>", handler)

// 示例
// GET /age/25 → OK
// GET /age/15 → 404 (less than 18)
// GET /age/150 → 404 (more than 120)
```

### 正则约束

```go
// 自定义正则
app.Get("/date/:date<regex(\\d{4}-\\d{2}-\\d{2})>", handler)
app.Get("/email/:email<regex([a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,})>", handler)

// 示例
// GET /date/2023-12-25 → OK
// GET /date/2023/12/25 → 404 (doesn't match regex)
```

### 组合约束

```go
// 多个约束组合
app.Get("/test/:test<min(100);maxLen(5)>", handler)

// 可选参数的约束
app.Get("/user/:id<int>?", handler)

// 示例
// GET /test/1000 → 404 (more than 5 characters)
// GET /test/99 → 404 (less than 100)
// GET /user → OK (optional, no id)
// GET /user/123 → OK
```

## 路由分组

### 基础分组

```go
// 创建路由组
api := app.Group("/api")

v1 := api.Group("/v1")
v1.Get("/users", listUsers)
v1.Post("/users", createUser)

v2 := api.Group("/v2")
v2.Get("/users", listUsersV2)
```

### 嵌套分组

```go
// 嵌套路由组
users := app.Group("/api/v1/users", func(c *fiber.Ctx) error {
    c.Set("X-API-Version", "v1")
    return c.Next()
})

{
    users.Get("/", listUsers)
    users.Post("/", createUser)
    users.Get("/:id", getUser)
    users.Put("/:id", updateUser)
    users.Delete("/:id", deleteUser)

    // 用户文章（深度嵌套）
    posts := users.Group("/:userId/posts")
    {
        posts.Get("/", listUserPosts)
        posts.Post("/", createUserPost)
        posts.Get("/:postId", getUserPost)
    }
}
```

### 分组中间件

```go
// 为整个组应用中间件
api := app.Group("/api", func(c *fiber.Ctx) error {
    c.Set("X-Group", "api")
    return c.Next()
})

api.Use(authMiddleware)
api.Use(loggerMiddleware)

v1 := api.Group("/v1")
v1.Get("/users", listUsers)

// 或在创建组时应用
authenticated := app.Group("/authenticated", AuthMiddleware())
authenticated.Get("/profile", getProfile)
```

## 路由命名

```go
// 命名路由
app.Get("/users/:id", handler).Name("user.detail")

// 获取路由 URL
url := app.Route("user.detail", fiber.Map{"id": "123"})
// /users/123

// 在模板中使用
<a href="{{ url_for "user.detail" "id" "123" }}">User 123</a>
```

## 路由元数据

```go
// 添加路由元数据
app.Get("/users", handler, middleware).MetaData(fiber.MetaData{
    "permission": "users.read",
    "rateLimit":  100,
})
```

## 路由顺序

路由按注册顺序匹配，更具体的路由应该先注册：

```go
// ✅ 正确顺序
app.Get("/users/special", specialHandler)  // 先匹配
app.Get("/users/:id", userHandler)         // 后匹配

// ❌ 错误顺序
app.Get("/users/:id", userHandler)         // 会匹配所有
app.Get("/users/special", specialHandler)  // 永远不会到达
```

## 路由前缀

```go
// 设置全局路由前缀
app := fiber.New()
app.Static("/", "./public")

// 使用子路径挂载
subApp := fiber.New()
subApp.Get("/", func(c *fiber.Ctx) error {
    return c.SendString("Sub app")
})

app.Mount("/api", subApp)

// /api/ → "Sub app"
```

## 静态文件

```go
// 服务静态文件
app.Static("/", "./public")

// 自�认路由前缀
app.Static("/assets", "./assets")

// 自定义索引文件
app.Static("/", "./public", fiber.Static{
    Index:         "index.html",
    Browse:        false,
    Compress:      true,
    ByteRange:     true,
    Download:      false,
})

// 单个文件
app.Get("/download", func(c *fiber.Ctx) error {
    return c.Download("./files/report.pdf")
})
```

## 路由列表

```go
// 打印所有路由
app.Stack()

// 按方法打印
for _, route := range app.Stack() {
    for _, r := range route {
        fmt.Printf("%s %s\n", r.Method, r.Path)
    }
}

// 启动时打印路由
app := fiber.New(fiber.Config{
    EnablePrintRoutes: true,
})
```
