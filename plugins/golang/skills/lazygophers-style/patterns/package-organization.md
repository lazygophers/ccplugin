# Lazygophers 分库分包规范

## 核心原则

### ✅ 必须遵守

1. **全局状态模式** - 使用全局变量存储数据访问对象（非依赖注入）
2. **避免显式接口** - Repository 层不创建显式 interface
3. **泛型数据访问** - 使用泛型 Model[T] 提供统一接口
4. **按功能分包** - user/order/payment 等按领域分组
5. **包名简洁** - 全小写、单数、有意义

### ❌ 禁止行为

- 创建 `UserRepository interface` 这样的显式接口（容易过度设计）
- Service 层通过构造函数注入 Repository（增加复杂性）
- 多层 interface 抽象（业务代码中无需如此）
- 跨包依赖不清（单向依赖）

## 全局状态模式（Linky Server 风格）

### ✅ 推荐设计

```go
// 参考 Linky Server internal/state/table.go

// 全局状态变量
var (
    // 使用泛型 db.Model[T] 作为数据访问接口
    User *db.Model[ModelUser]
    Friend *db.Model[ModelFriend]
    Message *db.Model[ModelMessage]
)

// Service 层直接使用全局状态（不通过接口注入）
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    // ✅ 直接访问全局 User
    user, err := User.NewScoop().
        Where("username", req.Username).
        First()

    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return &LoginRsp{User: user}, nil
}

// ❌ 不要这样做 - 显式 interface

// ❌ 避免创建 Repository interface
type UserRepository interface {
    GetByID(id int64) (*User, error)
    GetByUsername(username string) (*User, error)
}

// ❌ 避免 Service 中注入 Repository
type UserService struct {
    repo UserRepository  // 注入
}

func (s *UserService) Login(username string) (*User, error) {
    return s.repo.GetByUsername(username)  // 通过接口调用
}
```

## 项目目录结构（Linky 风格）

### 标准布局（参考 Linky Server）

```
server/
├── main.go                         # 启动入口
├── go.mod
├── go.sum
├── internal/
│   ├── state/                      # ✅ 全局状态（所有有状态资源）
│   │   ├── table.go               # 全局数据访问对象：User, Friend, Message 等
│   │   ├── config.go              # 配置对象（有状态）
│   │   ├── database.go            # 数据库连接（有状态）
│   │   ├── cache.go               # 缓存实例（有状态）
│   │   └── init.go                # 初始化全局状态
│   │
│   ├── impl/                       # ✅ Service 层实现（所有业务逻辑）
│   │   ├── user.go                # UserLogin, UserRegister 等
│   │   ├── friend.go              # AddFriend, ListFriends 等
│   │   ├── message.go             # SendMessage, GetMessages 等
│   │   ├── user_test.go           # 单元测试（与实现在同包）
│   │   └── friend_test.go         # 单元测试
│   │
│   ├── api/                        # ✅ API 层（HTTP 路由）
│   │   └── router.go              # 路由定义和中间件链
│   │
│   └── middleware/                 # ✅ 中间件（单独包）
│       ├── handler.go             # ToHandler 适配器
│       ├── logger.go              # 日志中间件
│       ├── auth.go                # 认证中间件
│       └── error.go               # 错误处理中间件
│
└── cmd/
    └── main.go                     # ✅ 仅 main.go，不要创建子目录
```

**关键规则**：
- ❌ 不要创建 `service/` 目录 - Service 层在 `impl/` 中
- ❌ 不要创建 `config/` 目录 - 配置在 `state/config.go` 中
- ❌ 不要创建 `model/` 目录 - 数据模型定义在 `state/` 中
- ❌ 不要创建 `pkg/models/` - 公开模型也在 `state/` 中
- ❌ 不要创建 `test/` 目录 - 测试文件在各包中（`*_test.go`）
- ❌ `cmd/` 下不要有子目录 - 仅放 main.go
- ✅ 中间件在单独的 `internal/middleware/` 包中
- ✅ 测试文件与实现在同包：`user.go` 和 `user_test.go` 在 `internal/impl/`
- ✅ 所有有状态资源在 `internal/state/` 中（config、database、cache、models 等）

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

## 数据访问层（State 包）

### 全局状态初始化

```go
// state/table.go（模仿 Linky）

// ✅ 全局数据访问对象
var (
    User *UserModel
    Friend *FriendModel
    Message *MessageModel
)

// UserModel 数据访问对象（泛型）
type UserModel struct {
    db DB
}

// 数据访问方法
func (m *UserModel) NewScoop() *Scoop {
    return NewScoop(m.db)
}

func (m *UserModel) GetByID(id int64) (*User, error) {
    return m.NewScoop().Where("id", id).First()
}

// state/init.go（初始化所有有状态资源）
func Init(db DB) error {
    // ✅ 初始化配置
    cfg, err := config.Load()
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // ✅ 初始化数据库连接
    database, err := database.Connect(cfg)
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // ✅ 初始化缓存
    c, err := cache.New(cfg.CacheSize)
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // ✅ 初始化全局数据访问对象
    User = &db.Model[User]{DB: database}
    Friend = &db.Model[Friend]{DB: database}
    Message = &db.Model[Message]{DB: database}

    log.Infof("state initialized: config=%v, db=%v, cache=%v", cfg, database, c)
    return nil
}
```

## Service 层设计（Impl 包）

### 直接使用全局状态

```go
// impl/user.go（参考 Linky）

// ✅ Service 层函数，直接访问全局 state
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    // ✅ 直接使用全局 User（不通过接口注入）
    user, err := User.NewScoop().
        Where("username", req.Username).
        First()

    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return &LoginRsp{User: user}, nil
}

// ✅ 链式查询（参考 Linky 的 Scoop 模式）
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

// ✅ 事务处理（参考 Linky）
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

## Handler 层设计（API 包）

### 路由和中间件

```go
// api/router.go（参考 Linky）

// ✅ 使用 ToHandler 适配器包装业务函数
func SetupRoutes(app *fiber.App) {
    // 公开路由（可选认证）
    public := app.Group("/api", middleware.OptionalAuth, middleware.Logger)
    public.Post("/user/login", impl.ToHandler(impl.UserLogin))

    // 需要认证的路由
    private := app.Group("/api", middleware.RequiredAuth, middleware.Logger)
    private.Post("/user/profile", impl.ToHandler(impl.GetUserProfile))
    private.Post("/friend/add", impl.ToHandler(impl.AddFriend))
    private.Post("/message/send", impl.ToHandler(impl.SendMessage))
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

## 为什么不使用显式 Interface？

### 问题分析

```go
// ❌ 显式 Interface 的问题

type UserRepository interface {
    GetByID(id int64) (*User, error)
    GetByUsername(username string) (*User, error)
    GetByEmail(email string) (*User, error)
    Create(*User) error
    Update(*User) error
    Delete(int64) error
}

// 问题 1：接口过大
// - 很多方法很少使用
// - 违反接口隔离原则

// 问题 2：Service 需要多个 Repository
type UserService struct {
    userRepo UserRepository
    friendRepo FriendRepository
    settingRepo SettingRepository
}

// 问题 3：构造函数复杂
func NewUserService(
    userRepo UserRepository,
    friendRepo FriendRepository,
    settingRepo SettingRepository,
) *UserService { ... }

// 问题 4：测试时需要 Mock
type MockUserRepository struct { ... }
impl := NewUserService(
    &MockUserRepository{},
    &MockFriendRepository{},
    &MockSettingRepository{},
)
```

### 全局状态的优势

```go
// ✅ 全局状态的优势

// 1. 简洁
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    user, _ := User.GetByUsername(req.Username)
    return &LoginRsp{User: user}, nil
}

// 2. 无需注入
// Service 函数签名清晰：func(ctx, req) (resp, error)

// 3. 易于编写
// 可直接访问任何 state 对象

// 4. 测试友好
// 直接替换全局 state 对象，而非创建复杂 mock

// 5. 性能优秀
// 无额外的接口调用开销
```

## 最佳实践

### 1. 依赖方向

```
HTTP Request
    ↓
API Router
    ↓
Handler (ToHandler)
    ↓
Service Functions (impl/*.go)
    ↓
Global State (state/table.go)
    ↓
Database

✅ 单向依赖：上层 → 下层，无循环依赖
```

### 2. 错误处理

```go
// ✅ 统一的错误处理
err := User.Create(user)
if err != nil {
    log.Errorf("err:%v", err)  // 多行处理
    return nil, err             // 返回原始错误
}

// ❌ 避免 - 包装或忽略
return nil, fmt.Errorf("create user: %w", err)  // 不包装
```

### 3. 事务处理

```go
// ✅ 使用全局 state 的事务
err := state.Tx(func(tx *Scoop) error {
    User.NewScoop(tx).Update(user)
    Friend.NewScoop(tx).Create(friend)
    return nil
})

// ❌ 避免 - 显式 transaction 接口
// type TransactionManager interface { Begin() *Tx }
```

## 参考

- **[Linky Server state/table.go](file:///Users/luoxin/persons/lyxamour/linky/server/internal/state/table.go)** - 全局状态定义
- **[Linky Server impl/user.go](file:///Users/luoxin/persons/lyxamour/linky/server/internal/impl/user.go)** - Service 层实现
- **[Linky Server api/router.go](file:///Users/luoxin/persons/lyxamour/linky/server/internal/api/router.go)** - 路由和中间件

## 总结

| 方面 | 全局状态模式（✅） | 显式 Interface（❌） |
|------|-------------------|-------------------|
| **复杂性** | 低 | 高 |
| **接口数** | 1-2 个 | 5-10+ 个 |
| **注入依赖** | 无 | 有 |
| **测试** | 简单 | 复杂（Mock） |
| **性能** | 优秀 | 略有开销 |
| **可读性** | 清晰 | 分散 |
| **适用范围** | 生产应用 | 通用库 |

**Linky Server 使用全局状态模式，避免了复杂的依赖注入，代码更简洁高效。**
