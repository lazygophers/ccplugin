# golang 架构设计规范

生产级架构设计。强调**全局状态模式**，避免复杂的依赖注入。

## 核心架构原则

### ✅ 必须遵守

1. **三层结构** - API (HTTP handlers) → Impl (业务逻辑) → State (全局数据访问)
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
│   Impl 层 (业务逻辑)                  │
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
// api/router.go

func SetupRoutes(app *fiber.App) {
    // 公开路由
    public := app.Group("/api/public", middleware.OptionalAuth, middleware.Logger)
    public.Post("/Login", impl.ToHandler(impl.UserLogin))
    public.Post("/Register", impl.ToHandler(impl.UserRegister))

    // 需要认证的路由
    user := app.Group("/api/user", middleware.Auth, middleware.Logger)
    user.Post("/GetUserProfile", impl.ToHandler(impl.GetUserProfile))
    user.Post("/AddFriend", impl.ToHandler(impl.AddFriend))
    user.Post("/SendMessage", impl.ToHandler(impl.SendMessage))
}
```

### 中间件链

```go
// middleware/middleware.go

// ✅ 中间件调用
func ChainMiddleware(ctx *fiber.Ctx) err {
    // 前置逻辑

    err = ctx.Next(
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // 后置逻辑

    return nil
}

// 使用
route.Post("/SomeHandler", ChainMiddleware, impl.ToHandler(impl.SomeHandler),)
```

### 错误处理中间件

```go
// middleware/error.go

func ErrorHandler(ctx *fiber.Ctx) error {
    err := ctx.Next()
    if err != nil {
        log.Errorf("err:%v", err)
        return ctx.JSON(fiber.Map{
            "code": -1,
            "message": err.Error(),
        })
    }

    return nil
}
```

## Impl 层设计

### 业务逻辑函数

```go
// impl/user.go

// ✅ Service 层函数，直接访问全局 State
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    var rsp LoginRsp

    // ✅ 直接使用全局 User State（不通过接口）
    user, err := User.NewScoop().
        Where("username", req.Username).
        First()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    rsp.User = user

    return &rsp, nil
}

// ✅ 验证登录密码
func ValidatePassword(user *User, password string) error {
    // 业务逻辑（与数据访问无关）
    if user == nil {
        log.Error("user is nil")
        return xerror.NewInvalidParamError("user is nil")
    }

    // 密码验证逻辑
    return nil
}
```

### 链式业务逻辑

```go
// impl/friend.go

// ✅ 使用全局 State 的链式查询
func GetFriendList(uid int64) ([]*Friend, error) {
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

// ✅ 使用全局 state 执行事务
func UpdateUserWithFriends(userId int64, updateMap map[string]interface{}, friendIds []int64) error {
    err := state.CommitOrRollback(func(tx *Scoop) error {
            err := state.User.NewScoop(tx).
                Where("id", userId).
                Update(updateMap).
                Error
            if err != nil {
                log.Errorf("err:%v", err)
                return err
            }

            // 创建友谊关系
            err = state.Friend.NewScoop(tx).
                CreateInBatches(candy.Map(friendIds, func(friendId int64) *Friend {
                    return &Friend{
                        UId:       userId,
                        FriendUId: friendId,
                        Status:    StatusActive,
                    }
                }), 100).
                Error()
            if err != nil {
                log.Errorf("err:%v", err)
                return err
            }

        return nil
    })
}
```

## State 层设计

### 全局状态初始化

```go
// state/table.go

// ✅ 全局数据访问对象
var (
    User    *db.Model[ModelUser]
    Friend  *db.Model[ModelFriend]
    Message *db.Model[ModelMessage]
)

// 初始化全局状态
// ConnectDatabase 初始化 MySQL 数据库连接
func ConnectDatabase() error {
	log.Info("初始化数据库连接")

	// 创建数据库连接
	var err error
	_db, err = db.New(State.Config.Database,
		&linky.ModelUser{},
		&linky.ModelFriend{},
		&linky.ModelMessage{},
	)
	if err != nil {
		log.Errorf("err:%v", err)
		return err
	}

	atexit.Register(func() {
		err := _db.Close()
		if err != nil {
			log.Errorf("err:%v", err)
			return
		}
	})

	User = db.NewModel[linky.ModelUser](Db()).
		SetNotFound(xerror.New(int32(linky.ErrCode_UserNotFound))).
		SetDuplicatedKeyError(xerror.New(int32(linky.ErrCode_UserAlreadyExists)))
	Friend = db.NewModel[linky.ModelFriend](Db()).
		SetNotFound(xerror.New(int32(linky.ErrCode_UserNotFound))).
		SetDuplicatedKeyError(xerror.New(int32(linky.ErrCode_AlreadyExists)))
	Message = db.NewModel[linky.ModelMessage](Db()).
		SetNotFound(xerror.New(int32(linky.ErrCode_MessageNotFound))).
		SetDuplicatedKeyError(xerror.New(int32(linky.ErrCode_AlreadyExists)))

    return nil
}
```

## 启动流程设计

### 三阶段启动

```go
// main.go

func main() {
    err := state.Load()
    if err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("failed to load state")
    }

    err = app.Load()
    if err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("failed to load app")
    }

    runtime.WaitExit()
}
```

## 为什么使用全局状态模式？

### 对比分析

| 方面         | 全局状态模式（✅） | 显式 Interface（❌） |
| ------------ | ------------------ | -------------------- |
| **复杂性**   | 低                 | 高                   |
| **接口数**   | 1-2 个             | 5-10+ 个             |
| **构造函数** | 无参               | 多个参数             |
| **测试**     | 简单（替换全局）   | 复杂（Mock 接口）    |
| **性能**     | 优秀               | 有接口调用开销       |
| **可读性**   | 清晰直接           | 层级分散             |
| **适用范围** | 生产应用           | 通用库               |

### 示例对比

#### ❌ 显式 Interface（不允许）

```go
// 定义 interface
type UserRepository interface {
    GetById(id int64) (*User, error)
    GetByUsername(username string) (*User, error)
    Create(user *User) error
    Update(user *User) error
    Delete(id int64) error
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
func UserLogin(username string) (*User, error) {
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

### 包依赖检查

```go
// ❌ 禁止 - 通过 Service 层
func GetUser(ctx *fiber.Ctx) error {
    user, err := impl.GetUserByID(ctx.Context(), 1)
    if err != nil {
        return err
    }
    return ctx.JSON(user)
}

// ✅ 推荐 - API 层直接访问数据库
func GetUser(ctx *fiber.Ctx) error {
    user, err := state.User.Where("id", ctx.ParamsInt("id")).First()
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }
    return ctx.JSON(user)
}
```

## 最佳实践

### 1. 无状态服务函数

```go
// ✅ 无状态设计
func ProcessOrder(orderId int64) error {
    order, err := Order.Where("id", orderId).First()
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // 处理订单
    order.Status = "processing"

     err := Order.Update(ctx, order)
     if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    return nil
}

// 可以直接被多个 handler 或 goroutine 调用
```

## 总结

全局状态模式是核心设计，它：

- 简化了项目结构（无复杂依赖注入）
- 提高了代码可读性（直接访问全局状态）
- 改善了测试效率（简单 Mock 全局对象）
- 保证了性能优势（无接口调用开销）

**在写业务逻辑时，直接使用全局 State，不要创建额外的 interface 和 Service 类。**
