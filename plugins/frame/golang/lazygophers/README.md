# lazygophers - Go 全栈开发插件

基于 fasthttp-skills 的轻量级 RPC 框架，提供完整的微服务开发能力。

## 特性

- ⚡ **高性能** - 基于 fasthttp，零拷贝，对象池
- 🎯 **路由系统** - 静态/参数/通配符/全捕获路由
- 🔌 **中间件** - 认证、限流、压缩、指标、恢复
- 📦 **编解码** - JSON、Protobuf、MessagePack
- 🔧 **配置管理** - 结构化配置，环境变量支持
- 🧪 **类型安全** - 反射处理器自动签名转换

## 技术栈

- **lrpc** - 高性能 RPC 框架
- **fasthttp** - HTTP 服务器
- **lazygophers/log** - 结构化日志
- **lazygophers/crypto** - 加密库
- **lazygophers/utils** - 工具库集

## 文档结构

```
skills/
├── lrpc-core/                    # 核心框架
├── lrpc-log/                     # 日志模块
├── lrpc-cryptox/                 # 加解密工具（AES/RSA/ECDSA/ECDH/Hash/HMAC/UUID/ULID）
├── lrpc-string/                  # 字符串操作
├── lrpc-json/                    # JSON 处理
├── lrpc-network/                 # 网络工具
├── lrpc-anyx/                    # any 类型转换
├── lrpc-candy/                   # 泛型工具函数
├── lrpc-human/                   # 人类友好格式
├── lrpc-randx/                   # 随机数生成
├── lrpc-validator/               # 验证器
├── in-memory-cache/              # 纯内存缓存（11 种算法）
├── lrpc-redis-cache/             # Redis/Memcached 缓存中间件
├── lrpc-utils-cache/             # 纯缓存算法
├── lrpc-wait/                    # 并发控制（信号量池/Worker/Async）
├── lrpc-routine/                 # 协程管理
├── lrpc-hystrix/                 # 熔断器
├── lrpc-runtime/                 # 运行时环境
├── lrpc-app/                     # 应用配置（运行模式/构建信息）
├── lrpc-config/                  # 配置文件管理
├── lrpc-defaults/                # 默认值设置
├── lrpc-osx/                     # 操作系统工具
├── lrpc-xtime/                   # 时间处理（农历/节气/日历）
├── lrpc-queue/                   # 消息队列
├── lrpc-i18n/                    # 国际化中间件
├── lrpc-xerror/                  # 错误处理中间件
├── lrpc-database/                # 关系型数据库
└── lrpc-mongo/                   # MongoDB
```

## 快速开始

### 创建服务端

```go
package main

import (
    "github.com/lazygophers/lrpc"
    "github.com/lazygophers/lrpc/app"
)

func main() {
    a := app.New()
    server := lrpc.NewServer()

    // 注册路由
    server.GET("/", func(ctx *lrpc.Context) error {
        return ctx.JSON(lrpc.H{"message": "Hello, World!"})
    })

    a.SetServer(server)
    a.Run()
}
```

### 创建客户端

```go
import "github.com/lazygophers/lrpc/client"

c := client.New(client.WithAddr("http://localhost:8080"))

resp, err := c.GET(ctx, "/api/users")
if err != nil {
    return err
}
defer resp.Body.Close()
```

### 使用中间件

```go
import (
    "github.com/lazygophers/lrpc/middleware/auth"
    "github.com/lazygophers/lrpc/middleware/security"
    "github.com/lazygophers/lrpc/middleware/recover"
)

server := lrpc.NewServer()

// 全局中间件
server.Use(recover.New())
server.Use(auth.JWT("secret-key"))
server.Use(security.CORS())
server.Use(security.RateLimit(100, time.Minute))
```

## 工具库

### 日志（Skills(lrpc-log)）

```go
import "github.com/lazygophers/log"

logger := log.GetLogger("my-module")
logger.Info("server started",
    log.Field("addr", ":8080"),
    log.Field("mode", "production"),
)
```

### 加解密（Skills(lrpc-crypto)）

```go
import "github.com/lazygophers/crypto"

// AES-256-GCM 加密
key := crypto.GenerateAESKey()
iv := crypto.GenerateRandomBytes(12)
ciphertext, _ := crypto.AESGCMEncrypt(key, iv, plaintext)
```

### 字符串操作（Skills(lrpc-string)）

```go
import "github.com/lazygophers/utils/stringx"

// 零拷贝转换
b := stringx.ToBytes("hello")

// 命名转换
snake := stringx.Camel2Snake("GetUserID")  // "get_user_id"
```

### JSON 处理（Skills(lrpc-json)）

```go
import "github.com/lazygophers/utils/json"

// 平台优化（Linux/macOS 使用 sonic）
data, _ := jsonx.Marshal(user)

// 文件操作
jsonx.MarshalToFile("config.json", cfg)
```

### 纯内存缓存（Skills(in-memory-cache)）

```go
import "github.com/lazygophers/cache"

// LRU 缓存（87M+ ops/sec）
c := cache.New[cache.LRU, string, int](1000)
c.Set("key", 100)
if value, ok := c.Get("key"); ok {
    fmt.Println(value)
}
```

### Redis/Memcached 缓存（Skills(lrpc-redis-cache)）

```go
import "github.com/lazygophers/lrpc/middleware/cache"

// 初始化 Redis 缓存
redisClient := redis.NewClient(&redis.Options{
    Addr: "localhost:6379",
})

cacheMiddleware := cache.New(cache.Config{
    Client:     redisClient,
    Type:       cache.Redis,
    DefaultTTL: 5 * time.Minute,
})

server.Use(cacheMiddleware)

// CacheAside 模式
func GetUser(ctx *lrpc.Context, cache *cache.Cache) error {
    var user User
    found, _ := cache.Get("user:123", &user)
    if found {
        return ctx.JSON(user)
    }

    user, err := db.GetUser("123")
    cache.Set("user:123", user, 10*time.Minute)

    return ctx.JSON(user)
}
```

### 网络工具（Skills(lrpc-network)）

```go
import "github.com/lazygophers/utils/urlx"

// 获取监听 IP
ip, _ := urlx.GetListenIp()

// 提取真实客户端 IP
realIP := urlx.RealIpFromHeader(r.Header)

// URL 参数排序
sorted, _ := urlx.SortQuery(urlStr)
```

## 中间件

### 国际化（Skills(lrpc-i18n)）

```go
import "github.com/lazygophers/lrpc/middleware/i18n"

// 初始化中间件
i18nMiddleware := i18n.New(
    i18n.WithLanguages("en", "zh-CN", "ja"),
    i18n.WithDefaultLanguage("en"),
    i18n.WithLoadPath("./locales"),
)

server.Use(i18nMiddleware)

// 在 Handler 中使用
func Handler(ctx *lrpc.Context) error {
    message := i18n.T(ctx, "hello")  // 翻译
    return ctx.JSON(lrpc.H{"message": message})
}
```

### 错误处理（Skills(lrpc-xerror)）

```go
import "github.com/lazygophers/lrpc/middleware/xerror"

// 初始化中间件
errorMiddleware := xerror.New(
    xerror.WithDebugMode(true),
    xerror.WithLogErrors(true),
)

server.Use(errorMiddleware)

// 在 Handler 中返回错误
func Handler(ctx *lrpc.Context) error {
    if err != nil {
        return xerror.Error(CodeNotFound, "User not found")
    }
    return ctx.JSON(data)
}
```

### 数据库访问（Skills(lrpc-database)）

```go
import "github.com/lazygophers/lrpc/middleware/storage/db"

// 初始化数据库
db, _ := database.New(database.Config{
    Type:     "mysql",
    Host:     "localhost",
    Port:     3306,
    Database: "mydb",
    Username: "user",
    Password: "pass",
})

// 查询数据
var users []User
db.Where("age > ?", 18).Find(&users)

// 事务处理
db.Transaction(func(tx *database.DB) error {
    tx.Create(&user)
    tx.Create(&config)
    return nil
})
```

### MongoDB（Skills(lrpc-mongo)）

```go
import "github.com/lazygophers/lrpc/middleware/storage/mongo"

// 初始化 MongoDB
client, _ := mongo.New(mongo.Config{
    Host:     "localhost",
    Port:     27017,
    Database: "mydb",
})

// 插入文档
collection := db.Collection("users")
collection.InsertOne(ctx, bson.M{"name": "John", "age": 30})

// 聚合查询
pipeline := mongo.Pipeline{
    bson.D{{"$match", bson.D{{"age", bson.D{{"$gt", 18}}}}}},
    bson.D{{"$group", bson.D{{"_id", "$status"}, {"count", bson.D{{"$sum", 1}}}}}},
}
cursor, _ := collection.Aggregate(ctx, pipeline)
```

## 目录结构

```
plugins/frame/golang/lazygophers/
├── .claude-plugin/
│   └── plugin.json                # 插件元数据
├── hooks/
│   └── hooks.json                 # Hook 配置
├── scripts/
│   ├── main.py                    # CLI 入口
│   └── hooks.py                   # Hook 处理
├── skills/
│   ├── lrpc-core/                 # 核心框架
│   ├── lrpc-log/                  # 日志模块
│   ├── lrpc-cryptox/              # 加解密工具（AES/RSA/ECDSA/ECDH/Hash/HMAC）
│   ├── lrpc-string/               # 字符串操作
│   ├── lrpc-json/                 # JSON 处理
│   ├── lrpc-network/              # 网络工具
│   ├── lrpc-anyx/                 # any 类型转换
│   ├── lrpc-candy/                # 泛型工具函数
│   ├── lrpc-human/                # 人类友好格式
│   ├── lrpc-randx/                # 随机数生成
│   ├── lrpc-validator/            # 验证器
│   ├── in-memory-cache/           # 纯内存缓存（11 种算法）
│   ├── lrpc-redis-cache/          # Redis/Memcached 缓存中间件
│   ├── lrpc-utils-cache/          # 纯缓存算法
│   ├── lrpc-wait/                 # 并发控制（信号量池/Worker/Async）
│   ├── lrpc-routine/              # 协程管理
│   ├── lrpc-hystrix/              # 熔断器
│   ├── lrpc-runtime/              # 运行时环境
│   ├── lrpc-app/                  # 应用配置（运行模式/构建信息）
│   ├── lrpc-config/               # 配置文件管理
│   ├── lrpc-defaults/             # 默认值设置
│   ├── lrpc-osx/                  # 操作系统工具
│   ├── lrpc-xtime/                # 时间处理（农历/节气/日历）
│   ├── lrpc-queue/                # 消息队列
│   ├── lrpc-i18n/                 # 国际化中间件
│   ├── lrpc-xerror/               # 错误处理中间件
│   ├── lrpc-database/             # 关系型数据库
│   └── lrpc-mongo/                # MongoDB
├── AGENT.md                       # 行为规范
└── README.md                      # 本文件
```

## 参考资源

- [lrpc GitHub](https://github.com/lazygophers/lrpc)
- [lazygophers/log GitHub](https://github.com/lazygophers/log)
- [lazygophers/crypto GitHub](https://github.com/lazygophers/crypto)
- [lazygophers/cache GitHub](https://github.com/lazygophers/cache)
- [lazygophers/utils GitHub](https://github.com/lazygophers/utils)
- [fasthttp-skills GitHub](https://github.com/valyala/fasthttp)

## 许可证

AGPL-3.0-or-later
