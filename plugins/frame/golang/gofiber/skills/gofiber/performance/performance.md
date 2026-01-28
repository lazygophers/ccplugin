# Fiber 性能优化

Fiber 基于 fasthttp 构建，设计为零内存分配框架。正确使用性能优化技术可以进一步提升应用性能。

## 零分配模式

### Immutable 配置

```go
// 默认模式（推荐）
app := fiber.New(fiber.Config{
    Immutable: false,
})

// 在此模式下，Context 会被复用
func handler(c *fiber.Ctx) error {
    name := c.Params("name")  // []byte，无分配
    return c.SendString(name)
}
```

### 字符串持久化

```go
import "github.com/gofiber/fiber/v2/utils"

func handler(c *fiber.Ctx) error {
    // ❌ 错误：可能分配内存
    name := string(c.Params("name"))

    // ❌ 错误：保存了会被复用的 Context 数据
    go func() {
        process(c.Params("name"))  // 危险！
    }()

    // ✅ 正确：需要持久化时复制
    name := utils.CopyString(c.Params("name"))
    go func() {
        process(name)  // 安全
    }()

    return nil
}
```

### 零分配响应

```go
// ❌ 字符串拼接产生分配
func badHandler(c *fiber.Ctx) error {
    message := "Hello, " + c.Params("name") + "!"
    return c.SendString(message)
}

// ✅ 直接使用 []byte
func goodHandler(c *fiber.Ctx) error {
    c.Write([]byte("Hello, "))
    c.Write(c.Params("name"))
    c.Write([]byte("!"))
    return nil
}
```

## 对象池

### 使用 sync.Pool

```go
var userPool = sync.Pool{
    New: func() interface{} {
        return new(User)
    },
}

func handler(c *fiber.Ctx) error {
    // 从池中获取
    user := userPool.Get().(*User)
    defer func() {
        *user = User{}  // 重置
        userPool.Put(user)
    }()

    if err := c.BodyParser(user); err != nil {
        return err
    }

    return c.JSON(user)
}
```

### 字节缓冲池

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return make([]byte, 0, 1024)
    },
}

func handler(c *fiber.Ctx) error {
    buf := bufferPool.Get().([]byte)
    defer func() {
        buf = buf[:0]  // 重置长度
        bufferPool.Put(buf)
    }()

    buf = append(buf, "Hello, "...)
    buf = append(buf, c.Params("name")...)
    buf = append(buf, '!')

    return c.Send(buf)
}
```

## 缓存策略

### 内存缓存

```go
import "github.com/patrickmn/go-cache"

var memCache = cache.New(5*time.Minute, 10*time.Minute)

func getUser(id string) (*User, error) {
    // 尝试从缓存获取
    if x, found := memCache.Get(id); found {
        return x.(*User), nil
    }

    // 缓存未命中，从数据库获取
    user, err := dbGetUser(id)
    if err != nil {
        return nil, err
    }

    // 存入缓存
    memCache.Set(id, user, cache.DefaultExpiration)
    return user, nil
}
```

### Redis 缓存

```go
import "github.com/redis/go-redis/v9"

var redisClient = redis.NewClient(&redis.Options{
    Addr: "localhost:6379",
})

func getUser(ctx context.Context, id string) (*User, error) {
    // 尝试从 Redis 获取
    cached, err := redisClient.Get(ctx, "user:"+id).Bytes()
    if err == nil {
        var user User
        if err := json.Unmarshal(cached, &user); err == nil {
            return &user, nil
        }
    }

    // 从数据库获取
    user, err := dbGetUser(id)
    if err != nil {
        return nil, err
    }

    // 存入 Redis
    data, _ := json.Marshal(user)
    redisClient.Set(ctx, "user:"+id, data, 5*time.Minute)

    return user, nil
}
```

### 响应缓存

```go
import "github.com/gofiber/fiber/v2/middleware/cache"

app.Use(cache.New(cache.Config{
    Expiration:   5 * time.Minute,
    CacheControl: true,
}))

// 或自定义缓存键
app.Use(cache.New(cache.Config{
    Next: func(c *fiber.Ctx) bool {
        return c.Query("no-cache") == "true"
    },
    Expiration:   5 * time.Minute,
    KeyGenerator: func(c *fiber.Ctx) string {
        return utils.CopyString(c.Path() + "?" + c.Context().QueryArgs().String())
    },
}))
```

## 压缩

### Gzip 压缩

```go
import "github.com/gofiber/fiber/v2/middleware/compress"

app.Use(compress.New(compress.Config{
    Level: compress.LevelBestSpeed, // -1 到 9
}))

// 或使用最佳压缩
app.Use(compress.New(compress.Config{
    Level: compress.LevelBestCompression,
}))
```

### 自定义压缩

```go
app.Use(compress.New(compress.Config{
    Level: compress.LevelBestSpeed,
    // 排除特定路径
    ExcludedPaths:     []string{"/api/v1/download"},
    // 排除特定扩展名
    ExcludedExtensions: []string{".jpg", ".png", ".gif", ".pdf"},
}))
```

## 并发处理

### Goroutine 池

```go
import "github.com/panjf2000/ants/v2"

var pool, _ = ants.NewPool(100)

func handler(c *fiber.Ctx) error {
    var wg sync.WaitGroup
    var results []string

    for _, id := range getUserIDs() {
        wg.Add(1)
        id := id  // 捕获变量
        pool.Submit(func() {
            defer wg.Done()
            user := fetchUser(id)
            results = append(results, user.Name)
        })
    }

    wg.Wait()
    return c.JSON(results)
}
```

### Worker 模式

```go
func worker(jobs <-chan Job, results chan<- Result) {
    for j := range jobs {
        results <- process(j)
    }
}

func main() {
    jobs := make(chan Job, 1000)
    results := make(chan Result, 1000)

    // 启动 workers
    for w := 1; w <= 5; w++ {
        go worker(jobs, results)
    }

    app := fiber.New()

    app.Get("/process", func(c *fiber.Ctx) error {
        job := createJob(c)
        jobs <- job
        result := <-results
        return c.JSON(result)
    })
}
```

## JSON 性能

### 使用 jsoniter

```go
import jsoniter "github.com/json-iterator/go"

var fastJson = jsoniter.ConfigFastest

func handler(c *fiber.Ctx) error {
    data := map[string]string{"message": "hello"}
    bytes, _ := fastJson.Marshal(data)
    return c.Send(bytes)
}
```

### 流式 JSON

```go
func streamUsers(c *fiber.Ctx) error {
    c.Set("Content-Type", "application/json")
    c.Write([]byte("["))

    first := true
    for user := range userIterator() {
        if !first {
            c.Write([]byte(","))
        }
        first = false

        data, _ := json.Marshal(user)
        c.Write(data)
    }

    c.Write([]byte("]"))
    return nil
}
```

## 数据库优化

### 连接池

```go
import "gorm.io/gorm"

db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
    // 连接池配置
    ConnPool: &sql.DB{
        MaxIdleConns:    10,
        MaxOpenConns:    100,
        ConnMaxLifetime: time.Hour,
    },
})
```

### 批量操作

```go
// ❌ N+1 查询
func getOrders() []Order {
    var orders []Order
    db.Find(&orders)

    for _, order := range orders {
        db.Preload("User").First(&order, order.ID)
    }
    return orders
}

// ✅ 预加载
func getOrders() []Order {
    var orders []Order
    db.Preload("User").Find(&orders)
    return orders
}
```

## 性能监控

### 中间件计时

```go
func TimingMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        start := time.Now()
        defer func() {
            duration := time.Since(start)
            log.Printf("%s %s took %v", c.Method(), c.Path(), duration)
        }()
        return c.Next()
    }
}
```

### Prometheus 指标

```go
import "github.com/vegh1010/fiber-prometheus"

app := fiber.New()

// Prometheus 中间件
prometheus := fiberPrometheus.New("my_app")
prometheus.RegisterAt(app, "/metrics")
app.Use(prometheus.Middleware)
```

## 基准测试

```go
func BenchmarkHandler(b *testing.B) {
    app := fiber.New()
    app.Get("/", handler)

    b.ResetTimer()
    b.ReportAllocs()

    for i := 0; i < b.N; i++ {
        req := httptest.NewRequest("GET", "/", nil)
        resp, err := app.Test(req)
        if err != nil || resp.StatusCode != 200 {
            b.Fatal(err)
        }
    }
}
```

## 性能最佳实践

### 1. 避免反射

```go
// ❌ 慢
func slowHandler(c *fiber.Ctx) error {
    var data interface{}
    json.Unmarshal(c.Body(), &data)
    return c.JSON(data)
}

// ✅ 快
func fastHandler(c *fiber.Ctx) error {
    var data map[string]interface{}
    json.Unmarshal(c.Body(), &data)
    return c.JSON(data)
}
```

### 2. 重用缓冲区

```go
// ✅ 重用缓冲区
var buf = make([]byte, 0, 1024)

func handler(c *fiber.Ctx) error {
    buf = buf[:0]  // 重置
    buf = append(buf, c.Body()...)
    return c.Send(buf)
}
```

### 3. 预分配容量

```go
// ✅ 预分配
users := make([]User, 0, 100)
for _, id := range ids {
    users = append(users, getUser(id))
}
```

### 4. 使用高效的数据结构

```go
// ✅ 使用 map 而非 slice 查找
userMap := make(map[int64]*User)
for _, user := range users {
    userMap[user.ID] = user
}

// O(1) 查找
user := userMap[id]
```
