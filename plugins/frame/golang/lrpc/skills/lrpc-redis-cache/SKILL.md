---
name: lrpc-redis-cache
description: lrpc cache 中间件 - Redis/Memcached 第三方缓存集成，支持缓存穿透/击穿/雪崩防护
---

# lrpc-redis-cache - 第三方缓存中间件

提供 Redis/Memcached 等第三方缓存的统一访问抽象，支持缓存穿透、击穿、雪崩防护。

## 特性

- 📦 **统一接口** - Redis、Memcached 相同 API
- 🔄 **多种模式** - 缓存更新策略（CacheAside/WriteThrough/WriteBehind）
- 🛡️ **缓存保护** - 穿透/击穿/雪崩防护
- 📊 **分布式锁** - Redisson 集成
- 🧵 **连接池** - 自动管理连接
- 💾 **序列化** - JSON/Protobuf/MessagePack

## 基础使用

### 初始化 Redis 缓存

```go
import (
    "github.com/lazygophers/lrpc/middleware/cache"
    "github.com/redis/go-redis/v9"
)

// 创建 Redis 客户端
redisClient := redis.NewClient(&redis.Options{
    Addr:     "localhost:6379",
    Password: "",
    DB:       0,
    // 连接池配置
    PoolSize:     100,
    MinIdleConns: 10,
})

// 创建缓存中间件
cacheMiddleware := cache.New(cache.Config{
    Client:      redisClient,
    Type:        cache.Redis,
    DefaultTTL:  5 * time.Minute,
    KeyPrefix:   "app:",
})

// 注册到服务器
server := lrpc.NewServer()
server.Use(cacheMiddleware)
```

### 初始化 Memcached 缓存

```go
import "github.com/bradfitz/gomemcache/memcache"

// 创建 Memcached 客户端
memcachedClient := memcache.New("localhost:11211")

// 创建缓存中间件
cacheMiddleware := cache.New(cache.Config{
    Client:      memcachedClient,
    Type:        cache.Memcached,
    DefaultTTL:  5 * time.Minute,
    KeyPrefix:   "app:",
})
```

## CacheAside 模式（推荐）

```go
import "github.com/lazygophers/lrpc/middleware/cache"

// 在 Handler 中使用
func GetUser(ctx *lrpc.Context, cache *cache.Cache) error {
    userID := ctx.Query("id")

    // 1. 尝试从缓存获取
    var user User
    key := fmt.Sprintf("user:%s", userID)

    found, err := cache.Get(key, &user)
    if err != nil {
        return err
    }

    if found {
        return ctx.JSON(user)
    }

    // 2. 缓存未命中，查询数据库
    user, err = db.GetUser(userID)
    if err != nil {
        return err
    }

    // 3. 写入缓存
    if err := cache.Set(key, user, 10*time.Minute); err != nil {
        // 缓存失败不影响主流程
        log.Error("cache set error", log.Field("error", err))
    }

    return ctx.JSON(user)
}
```

## 缓存策略

### CacheAside（旁路缓存）

```go
// 读：先读缓存，未命中读数据库，再写缓存
// 写：先写数据库，再删除缓存

func GetProduct(ctx *lrpc.Context, cache *cache.Cache) error {
    productID := ctx.Param("id")

    // 1. 读缓存
    var product Product
    found, _ := cache.Get("product:"+productID, &product)

    if found {
        return ctx.JSON(product)
    }

    // 2. 查询数据库
    product, err := db.GetProduct(productID)
    if err != nil {
        return err
    }

    // 3. 写入缓存
    cache.Set("product:"+productID, product, 10*time.Minute)

    return ctx.JSON(product)
}

func UpdateProduct(ctx *lrpc.Context, cache *cache.Cache) error {
    var req UpdateProductRequest
    if err := ctx.Bind(&req); err != nil {
        return err
    }

    // 1. 更新数据库
    if err := db.UpdateProduct(req); err != nil {
        return err
    }

    // 2. 删除缓存（而非更新）
    cache.Delete("product:" + req.ID)

    return ctx.JSON(lrpc.H{"success": true})
}
```

### WriteThrough（写穿透）

```go
// 写操作同时写缓存和数据库

func SetConfig(ctx *lrpc.Context, cache *cache.Cache) error {
    var config Config
    if err := ctx.Bind(&config); err != nil {
        return err
    }

    // 同时写入缓存和数据库
    if err := cache.Set("config:"+config.Key, config, 1*time.Hour); err != nil {
        return err
    }

    if err := db.SetConfig(config); err != nil {
        return err
    }

    return ctx.JSON(config)
}
```

### WriteBehind（写回/异步写）

```go
// 先写缓存，异步批量写数据库

func CreateOrder(ctx *lrpc.Context, cache *cache.Cache) error {
    var order Order
    if err := ctx.Bind(&order); err != nil {
        return err
    }

    // 写入缓存
    cache.Set("order:"+order.ID, order, 30*time.Minute)

    // 异步写入数据库
    go func() {
        if err := db.CreateOrder(order); err != nil {
            log.Error("create order error", log.Field("error", err))
        }
    }()

    return ctx.JSON(order)
}
```

## 缓存保护

### 缓存穿透防护

```go
import "github.com/lazygophers/lrpc/middleware/cache"

// 布隆过滤器初始化
cacheMiddleware := cache.New(cache.Config{
    Client:      redisClient,
    Type:        cache.Redis,
    EnableBloomFilter: true,  // 启用布隆过滤器
    BloomFilterSize: 1000000,
})

// 方案1：布隆过滤器
func GetUser(ctx *lrpc.Context, cache *cache.Cache) error {
    userID := ctx.Param("id")

    // 布隆过滤器检查
    exists, err := cache.BloomExists("user:" + userID)
    if err != nil {
        return err
    }
    if !exists {
        // 不存在的数据直接返回
        return xerror.Error(CodeNotFound, "User not found")
    }

    // 查询缓存
    var user User
    found, err := cache.Get("user:"+userID, &user)
    if found {
        return ctx.JSON(user)
    }

    // 查询数据库
    user, err = db.GetUser(userID)
    if err != nil {
        return err
    }

    cache.Set("user:"+userID, user, 10*time.Minute)
    return ctx.JSON(user)
}

// 方案2：缓存空值
func GetProduct(ctx *lrpc.Context, cache *cache.Cache) error {
    productID := ctx.Param("id")

    var product Product
    found, _ := cache.Get("product:"+productID, &product)

    if found {
        if product.ID == "" {  // 空值表示不存在
            return xerror.Error(CodeNotFound, "Product not found")
        }
        return ctx.JSON(product)
    }

    product, err := db.GetProduct(productID)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            // 缓存空值，短 TTL
            cache.Set("product:"+productID, Product{}, 30*time.Second)
            return xerror.Error(CodeNotFound, "Product not found")
        }
        return err
    }

    cache.Set("product:"+productID, product, 10*time.Minute)
    return ctx.JSON(product)
}
```

### 缓存击穿防护

```go
// 方案1：互斥锁
func GetHotData(ctx *lrpc.Context, cache *cache.Cache) error {
    key := "hot_data:" + ctx.Param("id")

    var data Data
    found, _ := cache.Get(key, &data)
    if found {
        return ctx.JSON(data)
    }

    // 获取分布式锁
    lock, err := cache.Lock(key, 10*time.Second)
    if err != nil {
        return err
    }
    defer lock.Unlock()

    // 双重检查
    found, _ = cache.Get(key, &data)
    if found {
        return ctx.JSON(data)
    }

    // 查询数据库
    data, err = db.GetHotData(ctx.Param("id"))
    if err != nil {
        return err
    }

    cache.Set(key, data, 10*time.Minute)
    return ctx.JSON(data)
}

// 方案2：逻辑过期
func GetConfig(ctx *lrpc.Context, cache *cache.Cache) error {
    key := "config:" + ctx.Param("key")

    var item CacheItem
    found, _ := cache.Get(key, &item)

    if found {
        if time.Now().Before(item.ExpireTime) {
            return ctx.JSON(item.Data)
        }

        // 异步刷新
        go func() {
            data, err := db.GetConfig(ctx.Param("key"))
            if err == nil {
                cache.Set(key, CacheItem{
                    Data:       data,
                    ExpireTime: time.Now().Add(10 * time.Minute),
                }, 20*time.Minute)
            }
        }()

        return ctx.JSON(item.Data)
    }

    // 首次加载
    data, err := db.GetConfig(ctx.Param("key"))
    if err != nil {
        return err
    }

    cache.Set(key, CacheItem{
        Data:       data,
        ExpireTime: time.Now().Add(10 * time.Minute),
    }, 20*time.Minute)

    return ctx.JSON(data)
}
```

### 缓存雪崩防护

```go
// 方案1：随机 TTL
func SetWithRandomTTL(cache *cache.Cache, key string, value interface{}, baseTTL time.Duration) {
    randomTTL := baseTTL + time.Duration(rand.Intn(600))*time.Second
    cache.Set(key, value, randomTTL)
}

// 方案2：多级缓存
type MultiLevelCache struct {
    l1 *cache.Cache  // 本地缓存（in-memory）
    l2 *cache.Cache  // Redis 缓存
}

func (m *MultiLevelCache) Get(ctx context.Context, key string, dest interface{}) (bool, error) {
    // L1：本地缓存
    found, err := m.l1.Get(key, dest)
    if err == nil && found {
        return true, nil
    }

    // L2：Redis 缓存
    found, err = m.l2.Get(key, dest)
    if err == nil && found {
        // 回写 L1
        m.l1.Set(key, dest, 1*time.Minute)
        return true, nil
    }

    return false, nil
}

// 方案3：缓存预热
func WarmUpCache(cache *cache.Cache) {
    // 应用启动时预加载热点数据
    hotKeys := []string{"user:1", "user:2", "product:100"}

    for _, key := range hotKeys {
        var data interface{}
        if err := db.Get(key, &data); err == nil {
            cache.Set(key, data, 10*time.Minute)
        }
    }
}
```

## 分布式锁

```go
import "github.com/lazygophers/lrpc/middleware/cache"

// 获取锁
func ProcessOrder(ctx *lrpc.Context, cache *cache.Cache) error {
    orderID := ctx.Param("id")
    lockKey := "lock:order:" + orderID

    // 获取锁，10秒过期
    lock, err := cache.Lock(lockKey, 10*time.Second)
    if err != nil {
        return xerror.Error(CodeConflict, "Order is being processed")
    }
    defer lock.Unlock()

    // 处理订单
    order, err := db.GetOrder(orderID)
    if err != nil {
        return err
    }

    // 业务逻辑
    order.Status = "processing"
    db.UpdateOrder(order)

    return ctx.JSON(order)
}

// Redlock 算法（多节点锁）
func RedlockLock(cache *cache.Cache, key string, expiry time.Duration) (*cache.Lock, error) {
    // 在多个 Redis 节点上获取锁
    // 成功获取 N/2 + 1 个节点即算成功
    return cache.Redlock(key, expiry)
}
```

## 批量操作

```go
// 批量获取（MGET）
func GetUsers(ctx *lrpc.Context, cache *cache.Cache) error {
    userIDs := []string{"1", "2", "3"}
    keys := make([]string, len(userIDs))
    for i, id := range userIDs {
        keys[i] = "user:" + id
    }

    // 批量获取
    users := make(map[string]User)
    missing := cache.MGet(keys, users)

    // 查询缺失的数据
    if len(missing) > 0 {
        results, err := db.GetUsersByIDs(missing)
        if err != nil {
            return err
        }

        // 批量写入缓存
        items := make(map[string]interface{})
        for _, user := range results {
            items["user:"+user.ID] = user
        }
        cache.MSet(items, 10*time.Minute)
    }

    return ctx.JSON(users)
}

// 批量设置（MSET）
func SetUsers(cache *cache.Cache, users []User) {
    items := make(map[string]interface{})
    for _, user := range users {
        items["user:"+user.ID] = user
    }

    cache.MSet(items, 10*time.Minute)
}
```

## 缓存统计

```go
// 获取缓存统计
stats := cacheMiddleware.Stats()

fmt.Println("Hits:", stats.Hits)
fmt.Println("Misses:", stats.Misses)
fmt.Println("HitRate:", stats.HitRate())
fmt.Println("Sets:", stats.Sets)
fmt.Println("Deletes:", stats.Deletes)
```

## 最佳实践

### 1. Key 设计

```go
// ✅ 层级清晰
user:123
user:123:profile
user:123:orders
product:456
product:456:reviews

// ✅ 带前缀
app:user:123
app:product:456

// ❌ 避免过长
this_is_a_very_long_key_name_that_includes_unnecessary_information:123

// ❌ 避免特殊字符
user:123:profile:data
```

### 2. TTL 选择

```go
// ✅ 根据数据更新频率设置
cache.Set("hot_data", data, 1*time.Minute)        // 热数据，短 TTL
cache.Set("config", data, 1*time.Hour)            // 配置，长 TTL
cache.Set("static", data, 24*time.Hour)           // 静态资源，极长 TTL

// ❌ 避免所有数据相同 TTL
cache.Set("user", user, 10*time.Minute)
cache.Set("product", product, 10*time.Minute)
cache.Set("order", order, 10*time.Minute)
```

### 3. 缓存更新策略

```go
// ✅ CacheAside + Delete
func UpdateUser(user User) error {
    // 1. 更新数据库
    if err := db.UpdateUser(user); err != nil {
        return err
    }

    // 2. 删除缓存
    cache.Delete("user:" + user.ID)

    return nil
}

// ❌ 避免同时更新缓存和数据库（数据不一致）
func UpdateUserWrong(user User) error {
    db.UpdateUser(user)
    cache.Set("user:"+user.ID, user, 10*time.Minute)  // 可能失败
    return nil
}
```

### 4. 大对象处理

```go
// ✅ 分片存储
func SetLargeObject(cache *cache.Cache, id string, data []byte) {
    chunkSize := 1024 * 1024  // 1MB
    for i := 0; i < len(data); i += chunkSize {
        end := i + chunkSize
        if end > len(data) {
            end = len(data)
        }
        cache.Set(fmt.Sprintf("large:%s:%d", id, i/chunkSize), data[i:end], 1*time.Hour)
    }
}

// ✅ 压缩存储
import "github.com/klauspost/compress/gzip"

func SetCompressed(cache *cache.Cache, key string, data interface{}) error {
    var buf bytes.Buffer
    gzipWriter := gzip.NewWriter(&buf)

    if err := json.NewEncoder(gzipWriter).Encode(data); err != nil {
        return err
    }
    gzipWriter.Close()

    return cache.Set(key, buf.Bytes(), 1*time.Hour)
}
```

## 性能优化

### 1. Pipeline（管道）

```go
// ✅ 使用 Pipeline 减少网络往返
pipe := redisClient.Pipeline()

incr := pipe.Incr(ctx, "counter")
expire := pipe.Expire(ctx, "counter", 1*time.Hour)

cmds, err := pipe.Exec(ctx)
if err != nil {
    return err
}

fmt.Println(incr.Val())
fmt.Println(expire.Val())
```

### 2. 连接池配置

```go
// ✅ 根据并发量调整
redisClient := redis.NewClient(&redis.Options{
    Addr:         "localhost:6379",
    PoolSize:     100,              // 连接池大小
    MinIdleConns: 10,               // 最小空闲连接
    MaxRetries:   3,                // 最大重试次数
    DialTimeout:  5 * time.Second,  // 连接超时
    ReadTimeout:  3 * time.Second,  // 读超时
    WriteTimeout: 3 * time.Second,  // 写超时
    PoolTimeout:  4 * time.Second,  // 获取连接超时
})
```

### 3. 监控指标

```go
// 缓存命中率监控
type CacheMonitor struct {
    cache *cache.Cache
}

func (m *CacheMonitor) Start() {
    ticker := time.NewTicker(1 * time.Minute)
    go func() {
        for range ticker.C {
            stats := m.cache.Stats()
            log.Info("cache stats",
                log.Field("hits", stats.Hits),
                log.Field("misses", stats.Misses),
                log.Field("hit_rate", stats.HitRate()),
            )

            // 命中率低于阈值告警
            if stats.HitRate() < 0.8 {
                log.Warn("cache hit rate low")
            }
        }
    }()
}
```

## 参考资源

- [lazygophers/lrpc cache](https://github.com/lazygophers/lrpc/tree/master/middleware/cache)
- [go-redis](https://github.com/redis/go-redis)
- [Redis 文档](https://redis.io/docs/)
- [Memcached](https://memcached.org/)
