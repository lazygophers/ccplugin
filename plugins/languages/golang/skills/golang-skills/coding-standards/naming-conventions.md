# Golang 命名规范

强调**清晰、一致、可读**。

## 核心原则

### ✅ 必须遵守

1. **导出变量/函数 PascalCase** - User, UserLogin, GetUserById（不是 GetUserByID）
2. **私有变量/函数 camelCase** - user, getUserById（或下划线前缀 `_cache`）
3. **常量 UPPER_CASE** - DefaultTimeout, MaxRetries
4. **包名全小写单词** - user, order, payment（无下划线）
5. **文件名全小写** - user.go, user_test.go（不是 User.go）
6. **接收者单字母** - (p *User), (p *Order)
7. **循环变量短名** - for i, for idx, for item
8. **字段名有意义** - 不用 x, y, z, val, tmp

### ❌ 禁止行为

- 混合大小写规则（UUID 但 userId）
- 无意义的短名（x, y, tmp）
- 下划线后缀（user*，data*）
- 过长的变量名（currentUserObject 应该是 user）
- 缩写不清楚（cfg 可以，但 c 不行）

## 字段命名规范

### 特殊字段约定

#### ID 字段（严格遵循导出/非导出规则）

```go
// ✅ 推荐 - 导出字段用大写
type User struct {
    Id        int64
    Uid       int64
    FriendUid int64
    UUID      string
}

// ✅ 私有/非导出字段用小写
func (u *User) getById(id int64) (*User, error) {
    return db.Where("id", id).First()
}

// ❌ 避免 - 混合不同的命名
type User struct {
    UserID    int64
    user_id   int64
}

// ❌ 避免 - 函数参数用大写
func GetUserById(ID int64) (*User, error) {
    return User.Where("id", ID).First()
}
```

#### 时间字段

```go
// ✅ 推荐 - 使用 CreatedAt/UpdatedAt
type Model struct {
    Id        int64
    CreatedAt time.Time
    UpdatedAt time.Time
}

// ❌ 避免 - 其他命名
type Model struct {
    CreatedTime time.Time
    ModifyTime  time.Time
    Timestamp   time.Time
}
```

#### 状态字段

```go
// ✅ 推荐 - 使用 Status 或 State（数字枚举）
type Friend struct {
    Id     int64
    State  int32
}

type Task struct {
    Id     int64
    State  int32
}

// ❌ 禁止 - 字符串枚举或不清晰的字段名
type Friend struct {
    FriendStatus string
    FStatus      int
}

// ✅ 定义枚举常量
const (
    FriendStatusPending = 0
    FriendStatusActive  = 1
    FriendStatusBlocked = 2
)
```

#### 布尔字段

```go
// ✅ 推荐 - Is/Has 前缀表示布尔值
type User struct {
    Id       int64
    Email    string
    IsActive bool
    HasMFA   bool
    IsAdmin  bool
}

// ❌ 避免 - 不清晰的命名
type User struct {
    Active  bool
    Enabled bool
    Admin   bool
}
```

## 函数命名规范

### Service 层函数

```go
// ✅ 动词开头，清晰的操作
func UserLogin(req *UserLoginReq) (*UserLoginRsp, error)
func UserRegister(req *UserRegisterReq) (*UserRegisterRsp, error)
func GetUserById(req *GetUserByIdReq) (*GetUserByIdRsp, error)
func GetUserByEmail(req *GetUserByEmailReq) (*GetUserByEmailRsp, error)
func AddUser(req *AddUserReq) error
func UpdateUser(req *UpdateUserReq) error
func DelUser(req *DelUserReq) error
func ListUser(req *ListUserReq) (*ListUserRsp, error)
func CountUser(req *CountUserReq) (*CountUserRsp, error)

// ❌ 避免 - 不清晰或过长的名字
func Get(id int64) (*User, error)
func FetchUserData(id int64) (*User, error)
func DoUserLogin(req *LoginReq) (*LoginRsp, error)
```

### Get 前缀规则

```go
// ✅ Get 用于获取单个对象
func GetUserById(id int64) (*User, error)
func GetMessageById(id int64) (*Message, error)

// ✅ List 用于获取列表
func ListUser(limit int) ([]*User, error)
func ListMessage(uid int64) ([]*Message, error)

// ✅ Count 用于计数
func CountUser(ctx context.Context) (int64, error)
func CountFriend(uid int64) (int64, error)

// ✅ Check 用于检查
func CheckUserExists(id int64) (bool, error)
func CheckEmailExists(email string) (bool, error)

// ✅ Is/Has 用于判断
func IsUserAdmin(uid int64) (bool, error)
func HasUserMFA(uid int64) (bool, error)
```

### Handler 函数

```go
// ✅ Handler 后缀或动词+Handler
func UserLogin(ctx *fiber.Ctx) error
func UserRegister(ctx *fiber.Ctx) error
func GetUserProfile(ctx *fiber.Ctx) error

// 或者直接使用服务函数名（通过 ToHandler 适配）
impl.ToHandler(impl.UserLogin)
impl.ToHandler(impl.UserRegister)
```

### Init 和 New 前缀

```go
// ✅ New 用于构造函数
func NewUser(email string) *User
func NewUserQuery() *UserQuery
func NewCache(size int) *Cache

// ✅ Init 用于初始化全局状态
func initState(db *gorm.DB) error
func initConfig() error
func Init(database *gorm.DB) error

// ✅ Load 用于加载配置/数据
func state.Load() error
func config.Load() (*Config, error)
```

## 接收者命名

### 短名约定（参考 Go 官方）

```go
// ✅ 推荐 - 单字母接收者
func (p *User) Login(password string) error
func (p *Order) Calculate() int64
func (p *Friend) IsActive() bool
func (p *Message) Send(ctx context.Context) error

// ❌ 避免 - 过长或无意义
func (user *User) Login(password string) error
func (userObj *User) Login(password string) error
func (u *User) U() *User
```

## 常量命名

### 全局常量

```go
// ✅ 推荐 - UPPER_CASE
const (
    DefaultPageSize    = 10
    MaxPageSize        = 100
    DefaultTimeout     = 30 * time.Second
    MaxRetries         = 3
    RequestIDHeader    = "X-Request-ID"
)

// ✅ 枚举常量
const (
    FriendStatusPending = 0
    FriendStatusActive  = 1
    FriendStatusBlocked = 2
)

// ✅ 错误码常量
const (
    ErrCodeSuccess      = 0
    ErrCodeBadRequest   = 1000
    ErrCodeUnauthorized = 1001
    ErrCodeForbidden    = 1002
    ErrCodeNotFound     = 1003
)

// ❌ 避免 - 小写或混合
const (
    DefaultPageSize = 10
    maxPageSize = 100
)
```

### 局部常量

```go
// ✅ 函数内常量也用大写
func ProcessOrder(order *Order) error {
    const (
        StatusPending   = 0
        StatusProcessing = 1
        StatusCompleted = 2
    )

    switch order.State {
    case StatusPending:
    }
}
```

## 类型命名

### Struct 类型

```go
// ✅ 推荐 - PascalCase，意义清晰
type User struct { }
type UserLogin struct { }

// ✅ 请求/响应类型后缀
type CreateUserReq struct { }
type CreateUserRsp struct { }

// ❌ 避免 - 不清晰或过长
type UL struct { }
type UserLoginInformation struct { }
type login_user struct { }
```

### Interface 类型

```go
// ✅ 推荐 - 动词或 Reader/Writer 模式
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Handler interface {
    Handle(req interface{}) error
}

// ❌ 避免 - I 前缀（Go 风格不推荐）
type IUser interface { }
type IUserRepository interface { }
```

## 包名命名

### 包目录规范

```
project/
├── internal/
│   ├── state/
│   ├── impl/
│   ├── middleware/
├── cmd/
│   └── main.go
└── pkg/
    └── errors/
```

### 包名简洁规范

```go
// ✅ 推荐 - 简洁清晰
package state
package impl
package api
package model
package config
package log

// ❌ 避免 - 冗长或不清晰
package user_service
package models
package service
package repository
```

## 文件名命名

### 基本规则

```
// ✅ 推荐 - 全小写，可用下划线分隔
user.go
user_test.go
user_query.go
error_handler.go

// ❌ 避免 - 大写或混合
User.go
UserService.go
user_Service.go

// ✅ 使用下划线区分
user.go
user_test.go
message.go
message_test.go
```

### 特殊文件命名

```
// ✅ 初始化文件
init.go
table.go
router.go

// ✅ 测试文件
user_test.go
user_integration_test.go

// ❌ 避免 - 脱离上下文的文件名
handlers.go
services.go
utils.go
```

## 变量命名

### 临时/循环变量

```go
// ✅ 推荐 - 短名但清晰
for i := 0; i < len(users); i++ { }
for idx, user := range users { }
for _, user := range users { }
for item := range items { }

err := someFunc()
ok := someCondition()
n := count()

// ❌ 避免 - 无意义或过长
for x := 0; x < len(users); x++ { }
for index, user := range users { }
for currentUser := range users { }

result := func()
value := someFunc()
data := loadData()
```

### 错误变量

```go
// ✅ 推荐 - 使用 err
user, err := User.GetById(ctx, id)
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ✅ 多个错误时不要区分
err = createUser(user)
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

err = saveUser(user)
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ❌ 避免 - 不清晰的错误变量
e := someFunc()
error := someFunc()
```

### Context 变量

```go
// ✅ 推荐 - 使用 ctx
func Login(username string) (*User, error) {
    user, err := User.Where("username", username).FirstContext(ctx)
}

// ✅ Fiber context
func LoginHandler(ctx *fiber.Ctx) error {
    uid := ctx.Locals("uid")
}

// ❌ 避免 - 不清晰
func Login(context context.Context, username string) (*User, error)
func Login(c context.Context, username string) (*User, error)
```

## 检查清单

提交代码前，确保：

- [ ] 所有导出类型使用 PascalCase
- [ ] 所有导出函数使用 PascalCase，私有用 camelCase
- [ ] 接收者使用单字母（p）
- [ ] 包名全小写单词（不用下划线）
- [ ] 文件名全小写（可用下划线分隔）
- [ ] 常量使用 UPPER_CASE
- [ ] ID 字段统一（Id, Uid, XXXId）
- [ ] 时间字段使用 CreatedAt/UpdatedAt
- [ ] 状态字段使用数字类型 Status/State
- [ ] 布尔字段使用 Is/Has 前缀
- [ ] 无 Repository interface（使用全局状态）
