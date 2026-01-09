# Lazygophers 架构设计规范

基于 Linky Server 的生产级架构设计。强调**全局状态模式**，避免复杂的依赖注入。

## 核心架构原则

### ✅ 必须遵守

1. **三层结构** - API (HTTP handlers) → Service/Impl (业务逻辑) → State (全局数据访问)
2. **全局状态模式** - 使用全局变量存储数据访问对象，而非依赖注入
3. **无显式 interface** - Repository 层不创建显式接口，直接使用全局 State
4. **单向依赖** - 上层依赖下层，无循环依赖
5. **启动流程** - State Init → Service Preparation → API Run

### ❌ 禁止行为

- 使用依赖注入注入 Repository
- 创建 `UserRepository interface` 这样的显式接口
- 多层 interface 抽象
- 跨包依赖不清（必须单向）
- Service 层通过构造函数注入依赖

## 三层架构设计

### 架构模型

```
┌─────────────────────────────────────────┐
│         API 层 (HTTP handlers)          │
│   - Fiber routes & middleware           │
│   - Request validation                  │
│   - Response formatting                 │
└────────────────┬────────────────────────┘
                 │ 调用
┌────────────────▼────────────────────────┐
│   Service/Impl 层 (业务逻辑)            │
│   - 纯业务逻辑函数                      │
│   - 不关心 HTTP 或数据库细节            │
│   - 直接使用全局 State                  │
└────────────────┬────────────────────────┘
                 │ 访问
┌────────────────▼────────────────────────┐
│    State 层 (全局数据访问)              │
│   - 全局状态变量 (User, Friend etc)     │
│   - db.Model[T] 泛型数据访问接口        │
│   - 链式查询 (Scoop 模式)               │
└──────────────────────────────────────────┘
```

## API 层设计

### 路由定义

```go
// api/router.go（参考 Linky）

func SetupRoutes(app *fiber.App) {
    // 公开路由
    public := app.Group("/api", middleware.OptionalAuth, middleware.Logger)
    public.Post("/user/login", impl.ToHandler(impl.UserLogin))
    public.Post("/user/register", impl.ToHandler(impl.UserRegister))

    // 需要认证的路由
    private := app.Group("/api", middleware.RequiredAuth, middleware.Logger)
    private.Post("/user/profile", impl.ToHandler(impl.GetUserProfile))
    private.Post("/friend/add", impl.ToHandler(impl.AddFriend))
    private.Post("/message/send", impl.ToHandler(impl.SendMessage))
}
```

### 中间件链

```go
// middleware/middleware.go

// ✅ 中间件链式调用（参考 Linky）
func ChainMiddleware(handler fiber.Handler, middlewares ...func(fiber.Handler) fiber.Handler) fiber.Handler {
    for i := len(middlewares) - 1; i >= 0; i-- {
        handler = middlewares[i](handler)
    }
    return handler
}

// 使用
route.Post("/endpoint", ChainMiddleware(
    impl.ToHandler(impl.SomeHandler),
    middleware.RequiredAuth,
    middleware.Logger,
    middleware.ErrorHandler,
))
```

### 错误处理中间件

```go
// middleware/error.go（参考 Linky）

func ErrorHandler(ctx *fiber.Ctx) error {
    err := ctx.Next()

    if err == nil {
        return nil
    }

    // 统一错误响应
    log.Errorf("err:%v", err)

    return ctx.JSON(fiber.Map{
        "code": -1,
        "message": err.Error(),
    })
}
```

## Service/Impl 层设计

### 业务逻辑函数

```go
// impl/user.go（参考 Linky）

// ✅ Service 层函数，直接访问全局 State
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    // ✅ 直接使用全局 User State（不通过接口）
    user, err := User.NewScoop().
        Where("username", req.Username).
        First()

    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return &LoginRsp{User: user}, nil
}

// ✅ 验证登录密码
func ValidatePassword(user *User, password string) error {
    // 业务逻辑（与数据访问无关）
    if user == nil {
        err := errors.New("user is nil")
        log.Errorf("err:%v", err)
        return err
    }

    // 密码验证逻辑
    return nil
}
```

### 链式业务逻辑

```go
// impl/friend.go

// ✅ 使用全局 State 的链式查询
func GetFriendList(ctx context.Context, uid int64) ([]*Friend, error) {
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

    return friends, nil
}
```

### 事务处理

```go
// impl/transaction.go

// ✅ 使用全局 state 执行事务（参考 Linky）
func UpdateUserWithFriends(ctx context.Context, userID int64, friendIDs []int64) error {
    return state.Tx(func(tx *Scoop) error {
        // 更新用户
        user, err := User.NewScoop(tx).
            Where("id", userID).
            First()

        if err != nil {
            log.Errorf("err:%v", err)
            return err
        }

        user.UpdatedAt = time.Now()
        if err := User.NewScoop(tx).Update(user); err != nil {
            log.Errorf("err:%v", err)
            return err
        }

        // 创建友谊关系
        for _, friendID := range friendIDs {
            friend := &Friend{
                UID:       userID,
                FriendUID: friendID,
                Status:    StatusActive,
            }
            if err := Friend.NewScoop(tx).Create(friend); err != nil {
                log.Errorf("err:%v", err)
                return err
            }
        }

        return nil
    })
}
```

## State 层设计

### 全局状态初始化

```go
// state/table.go（参考 Linky Server）

// ✅ 全局数据访问对象
var (
    User    *db.Model[User]
    Friend  *db.Model[Friend]
    Message *db.Model[Message]
)

// 初始化全局状态（参考 Linky state.Load()）
func Init(database *gorm.DB) error {
    User = &db.Model[User]{DB: database}
    Friend = &db.Model[Friend]{DB: database}
    Message = &db.Model[Message]{DB: database}

    log.Infof("state initialized")
    return nil
}
```

### db.Model 泛型数据访问

```go
// db/model.go（模拟 GORM 的泛型模型）

// ✅ 泛型数据访问接口（参考 Linky）
type Model[T any] struct {
    DB *gorm.DB
}

// 链式查询构建器
func (m *Model[T]) NewScoop(tx ...*Scoop) *Scoop {
    // 支持事务和非事务查询
    db := m.DB
    if len(tx) > 0 && tx[0].DB != nil {
        db = tx[0].DB
    }
    return &Scoop{DB: db, Model: new(T)}
}

// Where 条件查询
func (m *Model[T]) Where(column string, value interface{}) *Scoop {
    return m.NewScoop().Where(column, value)
}

// 获取单条记录
func (m *Model[T]) First(ctx context.Context) (*T, error) {
    var result T
    if err := m.DB.WithContext(ctx).First(&result).Error; err != nil {
        return nil, err
    }
    return &result, nil
}

// 创建记录
func (m *Model[T]) Create(ctx context.Context, data *T) error {
    return m.DB.WithContext(ctx).Create(data).Error
}

// 更新记录
func (m *Model[T]) Update(ctx context.Context, data *T) error {
    return m.DB.WithContext(ctx).Save(data).Error
}

// 删除记录
func (m *Model[T]) Delete(ctx context.Context, id int64) error {
    return m.DB.WithContext(ctx).Delete(new(T), id).Error
}
```

## 启动流程设计

### 三阶段启动（参考 Linky）

```go
// main.go

func main() {
    // 阶段 1：初始化全局 State（数据库连接）
    if err := state.Init(database); err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("failed to load state")
    }
    log.Infof("phase 1: state initialized")

    // 阶段 2：准备 Service（业务逻辑初始化）
    // - 可选的缓存初始化
    // - 可选的任务调度初始化
    // - 可选的 WebSocket Hub 初始化
    log.Infof("phase 2: service prepared")

    // 阶段 3：启动 API（HTTP 服务）
    app := fiber.New()
    api.SetupRoutes(app)

    if err := app.Listen(":8080"); err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("failed to start server")
    }
    log.Infof("phase 3: api running")
}
```

## 为什么使用全局状态模式？

### 对比分析

| 方面 | 全局状态模式（✅） | 显式 Interface（❌） |
|------|-------------------|---------------------|
| **复杂性** | 低 | 高 |
| **接口数** | 1-2 个 | 5-10+ 个 |
| **构造函数** | 无参 | 多个参数 |
| **测试** | 简单（替换全局） | 复杂（Mock 接口） |
| **性能** | 优秀 | 有接口调用开销 |
| **可读性** | 清晰直接 | 层级分散 |
| **适用范围** | 生产应用 | 通用库 |

### 示例对比

#### ❌ 显式 Interface（不推荐）

```go
// 定义 interface
type UserRepository interface {
    GetByID(ctx context.Context, id int64) (*User, error)
    GetByUsername(ctx context.Context, username string) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id int64) error
}

// Service 依赖注入
type UserService struct {
    userRepo UserRepository
    friendRepo FriendRepository
    settingRepo SettingRepository
}

// 复杂的构造函数
func NewUserService(
    userRepo UserRepository,
    friendRepo FriendRepository,
    settingRepo SettingRepository,
) *UserService {
    return &UserService{
        userRepo: userRepo,
        friendRepo: friendRepo,
        settingRepo: settingRepo,
    }
}

// 测试时需要复杂 Mock
type MockUserRepository struct {}
impl := NewUserService(
    &MockUserRepository{},
    &MockFriendRepository{},
    &MockSettingRepository{},
)
```

#### ✅ 全局状态模式（推荐）

```go
// 直接使用全局 state
var (
    User *db.Model[User]
    Friend *db.Model[Friend]
    Setting *db.Model[Setting]
)

// 业务逻辑函数，无需注入
func UserLogin(ctx context.Context, username string) (*User, error) {
    user, err := User.Where("username", username).First()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    return user, nil
}

// 测试时直接替换全局 state
func TestUserLogin(t *testing.T) {
    // 替换全局 User
    User = &MockUserModel{}

    user, err := UserLogin(context.Background(), "test")
    // 验证...
}
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
Service Functions (impl/*.go)  ← 业务逻辑
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

### 包依赖检查

```go
// ❌ 禁止 - API 层直接访问数据库
func GetUser(ctx *fiber.Ctx) error {
    db := ctx.Locals("db").(*gorm.DB)  // 不推荐
    user := &User{}
    db.First(user)
    return ctx.JSON(user)
}

// ✅ 推荐 - 通过 Service 层
func GetUser(ctx *fiber.Ctx) error {
    user, err := impl.GetUserByID(ctx.Context(), 1)
    if err != nil {
        return err
    }
    return ctx.JSON(user)
}
```

## 最佳实践

### 1. 业务逻辑单一职责

```go
// ❌ 混合 HTTP 和业务逻辑
func GetUserHandler(ctx *fiber.Ctx) error {
    id := ctx.Params("id")
    user, err := User.Where("id", id).First()
    if err != nil {
        return ctx.JSON(fiber.Map{"error": err.Error()})
    }
    return ctx.JSON(user)
}

// ✅ 分离关注点
func GetUserByID(ctx context.Context, id int64) (*User, error) {
    user, err := User.Where("id", id).First()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    return user, nil
}

func GetUserHandler(ctx *fiber.Ctx) error {
    id := ctx.ParamsInt("id")
    user, err := impl.GetUserByID(ctx.Context(), int64(id))
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }
    return ctx.JSON(user)
}
```

### 2. 无状态服务函数

```go
// ✅ 无状态设计（参考 Linky）
func ProcessOrder(ctx context.Context, orderID int64) error {
    order, err := Order.Where("id", orderID).First()
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // 处理订单
    order.Status = "processing"

    if err := Order.Update(ctx, order); err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    return nil
}

// 可以直接被多个 handler 或 goroutine 调用
```

### 3. Context 传递

```go
// ✅ 总是传递 context
func CreateUser(ctx context.Context, email string) (*User, error) {
    user := &User{Email: email}

    // context 支持超时、取消、日志跟踪
    if err := User.Create(ctx, user); err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return user, nil
}

// Handler 中传递
func CreateUserHandler(ctx *fiber.Ctx) error {
    // 使用 fiber context 而非 context.Context
    // 通过 context.WithValue 或 ctx.Locals 传递
    return impl.CreateUser(ctx.Context(), email)
}
```

## 参考

- **[Linky Server state/table.go](file:///Users/luoxin/persons/lyxamour/linky/server/internal/state/table.go)** - 全局状态定义
- **[Linky Server impl/*.go](file:///Users/luoxin/persons/lyxamour/linky/server/internal/impl/)** - Service 层实现
- **[Linky Server api/router.go](file:///Users/luoxin/persons/lyxamour/linky/server/internal/api/router.go)** - 路由和中间件

## 总结

全局状态模式是 Linky Server 的核心设计，它：
- 简化了项目结构（无复杂依赖注入）
- 提高了代码可读性（直接访问全局状态）
- 改善了测试效率（简单 Mock 全局对象）
- 保证了性能优势（无接口调用开销）

**在写业务逻辑时，直接使用全局 State，不要创建额外的 interface 和 Service 类。**
