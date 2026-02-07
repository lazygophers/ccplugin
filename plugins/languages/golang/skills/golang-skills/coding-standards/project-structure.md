# Golang 项目结构规范

## 核心原则

### ✅ 必须遵守

1. **三层架构** - API (HTTP handlers) → Impl (业务逻辑) → State (全局数据访问)
2. **全局状态模式** - 使用全局变量存储数据访问对象，而非依赖注入
3. **单向依赖** - 上层依赖下层，无循环依赖
4. **包名简洁** - 全小写、单数、有意义
5. **文件组织** - 按功能模块组织文件

### ❌ 禁止行为

- 创建 `service/` 目录 - Service 层在 `impl/` 中
- 创建 `config/` 目录 - 配置在 `state/` 中
- 创建 `model/` 目录 - 数据模型定义在 `state/` 中
- 创建 `pkg/models/` - 公开模型也在 `state/` 中
- 创建 `test/` 目录 - 测试文件在各包中（`*_test.go`）
- `cmd/` 下有子目录 - 仅放 main.go

## 推荐目录布局

### 标准布局

```
server/
├── main.go                         # 启动入口
├── go.mod
├── go.sum
├── Makefile                        # 构建脚本
├── README.md
├── .gitignore
├── internal/
│   ├── state/                      # 全局状态（所有有状态资源）
│   │   ├── table.go               # 全局数据访问对象：User, Friend, Message 等
│   │   ├── config.go              # 配置对象（有状态）
│   │   ├── database.go            # 数据库连接（有状态）
│   │   ├── cache.go               # 缓存实例（有状态）
│   │   └── init.go                # 初始化全局状态
│   │
│   ├── impl/                       # Service 层实现（所有业务逻辑）
│   │   ├── user.go                # UserLogin, UserRegister 等
│   │   ├── user_test.go           # 单元测试（与实现在同包）
│   │   ├── friend.go              # AddFriend, ListFriends 等
│   │   ├── friend_test.go         # 单元测试
│   │   └── ...
│   │
│   ├── api/                        # API 层（HTTP 路由）
│   │   └── router.go              # 路由定义和中间件链
│   │
│   └── middleware/                 # 中间件（单独包）
│       ├── handler.go             # ToHandler 适配器
│       ├── logger.go              # 日志中间件
│       ├── auth.go                # 认证中间件
│       └── error.go               # 错误处理中间件
│
└── cmd/
    └── main.go                     # 仅 main.go，不要创建子目录
```

## State 文件夹规则

### 所有有状态资源都在 state 中

State 包存放所有有状态资源，包括：

```go
// state/table.go - 全局数据访问对象
var (
    User    *db.Model[User]
    Friend  *db.Model[Friend]
    Message *db.Model[Message]
)

// state/config.go - 配置对象（有状态）
var Config *AppConfig

// state/database.go - 数据库连接（有状态）
var DB *gorm.DB

// state/cache.go - 缓存实例（有状态）
var Cache *Cache

// state/websocket.go - WebSocket Hub（有状态）
var Hub *websocket.Hub

// state/queue.go - 消息队列（有状态）
var Queue *MessageQueue
```

**规则**：

- ✅ 任何有状态的东西都放在 state 中
- ✅ Config、Database、Cache、Hub、Queue 等全部在 state
- ✅ state/init.go 中统一初始化这些资源
- ✅ state 包是应用唯一的"有状态保管所"

**示例**：

```go
// state/init.go
func Init(configPath string) error {
    // 1. 初始化配置
    cfg, err := loadConfig(configPath)
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }
    Config = cfg

    // 2. 初始化数据库
    db, err := gorm.Open(cfg.DatabaseDSN)
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }
    DB = db

    // 3. 初始化缓存
    c, err := NewCache(cfg.CacheSize)
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }
    Cache = c

    // 4. 初始化全局模型
    User = &db.Model[User]{DB: db}
    Friend = &db.Model[Friend]{DB: db}

    log.Infof("state initialized")
    return nil
}
```

## Impl 文件夹规则

### Service 层实现

```go
// impl/user.go

// ✅ Service 层函数，直接访问全局 state
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    // ✅ 直接使用全局 User（不通过接口）
    user, err := User.NewScoop().
        Where("username", req.Username).
        First()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return &LoginRsp{User: user}, nil
}

// ✅ 链式查询（Scoop 模式）
func FriendSync(ctx *fiber.Ctx, req *SyncReq) (*SyncRsp, error) {
    uid := GetUid(ctx)

    friends, err := Friend.NewScoop().
        Where("uid", uid).
        In("status", []int{StatusActive, StatusPending}).
        Order("updated DESC").
        Limit(100).
        Find()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return &SyncRsp{Friends: friends}, nil
}

// ✅ 事务处理
func UpdateSettings(ctx *fiber.Ctx, req *UpdateReq) error {
    uid := GetUid(ctx)

    // 使用全局 state 执行事务
    return state.Tx(func(tx *Scoop) error {
        // 查询现有设置
        settings, err := UserSetting.NewScoop(tx).
            Where("uid", uid).
            Find()

        // 更新设置
        for _, setting := range req.Settings {
            err = UserSetting.NewScoop(tx).Update(setting)
            if err != nil {
                return err
            }
        }

        return nil
    })
}
```

## API 文件夹规则

### 路由和中间件

```go
// api/router.go

// ✅ 使用 ToHandler 适配器包装业务函数
func SetupRoutes(app *fiber.App) {
    // 公开路由（可选认证）
    public := app.Group("/api", middleware.OptionalAuth, middleware.Logger)
    public.Post("/Login", impl.ToHandler(impl.UserLogin))
    public.Post("/Register", impl.ToHandler(impl.UserRegister))

    // 需要认证的路由
    private := app.Group("/api", middleware.Auth, middleware.Logger)
    private.Post("/GetUserProfile", impl.ToHandler(impl.GetUserProfile))
    private.Post("/AddFriend", impl.ToHandler(impl.AddFriend))
    private.Post("/SendMessage", impl.ToHandler(impl.SendMessage))
}

// ✅ ToHandler 适配器（支持多种函数签名）
func ToHandler(fn interface{}) fiber.Handler {
    return func(ctx *fiber.Ctx) error {
        // 自动：
        // 1. 解析请求
        // 2. 调用业务函数
        // 3. 序列化响应
        // 4. 处理错误
    }
}
```

## Middleware 文件夹规则

### 中间件实现

```go
// middleware/logger.go

// ✅ 日志中间件
func Logger(ctx *fiber.Ctx) error {
    start := time.Now()

    err := ctx.Next()

    duration := time.Since(start)
    log.Infof("%s %s %d %v", ctx.Method(), ctx.Path(), ctx.Response().StatusCode(), duration)

    return err
}

// middleware/auth.go

// ✅ 认证中间件
func Auth(ctx *fiber.Ctx) error {
    token := ctx.Get("Authorization")
    if token == "" {
        return ctx.Status(401).JSON(fiber.Map{
            "code":    401,
            "message": "Unauthorized",
        })
    }

    uid, err := validateToken(token)
    if err != nil {
        log.Errorf("err:%v", err)
        return ctx.Status(401).JSON(fiber.Map{
            "code":    401,
            "message": "Unauthorized",
        })
    }

    ctx.Locals("uid", uid)
    return ctx.Next()
}
```

## 包组织规则

### 包命名

```go
// ✅ 推荐 - 简洁清晰
package state     // 全局状态
package impl      // 业务实现
package api       // API 路由
package model     // 数据模型
package config    // 配置
package log       // 日志

// ❌ 避免 - 冗长或不清晰
package user_service    // 应该用 impl，user 由函数名表示
package models          // 应该用 model（单数）
package service         // 应该用 impl（实现）
package repository      // 使用全局状态而非显式接口
```

### 文件组织

```
// ✅ 推荐 - 按功能模块组织
impl/
├── user.go           # 用户相关函数
├── user_test.go      # 用户测试
├── friend.go         # 好友相关函数
├── friend_test.go    # 好友测试
├── message.go        # 消息相关函数
└── message_test.go   # 消息测试

// ❌ 避免 - 脱离上下文的文件名
impl/
├── handlers.go       # 应该分成 user.go, order.go
├── services.go       # 应该分成 user.go, order.go
└── utils.go          # 应该按功能分散到各模块
```

## 依赖关系设计

### 单向依赖流

```
HTTP Request
    ↓
API Router (api/router.go)
    ↓
Handler (impl/handler.go)  ← ToHandler 适配器
    ↓
Impl Functions (impl/*.go)  ← 业务逻辑
    ↓
Global State (state/table.go)  ← 全局数据访问
    ↓
Database
```

**规则**：

- ✅ 上层只能调用下层
- ✅ 下层不能调用上层
- ✅ 同层可以相互调用
- ❌ 禁止循环依赖
- ❌ 禁止跨层调用

## 检查清单

提交代码前，确保：

- [ ] 项目结构遵循推荐布局
- [ ] 所有有状态资源在 `internal/state/` 中
- [ ] Service 层在 `internal/impl/` 中
- [ ] API 层在 `internal/api/` 中
- [ ] 中间件在 `internal/middleware/` 中
- [ ] 测试文件与实现在同包（`*_test.go`）
- [ ] `cmd/` 下只有 main.go，无子目录
- [ ] 包名全小写、单数、有意义
- [ ] 文件按功能模块组织
- [ ] 依赖关系单向，无循环依赖
