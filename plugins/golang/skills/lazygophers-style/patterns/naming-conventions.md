# Lazygophers 命名规范

基于 Linky Server 的实际项目命名约定。强调**清晰、一致、可读**。

## 核心原则

### ✅ 必须遵守

1. **导出变量/函数 PascalCase** - User, UserLogin, GetUserByID
2. **私有变量/函数 camelCase** - user, getUserByID（或下划线前缀 `_cache`）
3. **常量 UPPER_CASE** - DefaultTimeout, MaxRetries
4. **包名全小写单词** - user, order, payment（无下划线）
5. **文件名全小写** - user.go, user_test.go（不是User.go）
6. **接收者单字母** - (u *User), (o *Order)
7. **循环变量短名** - for i, for idx, for item
8. **字段名有意义** - 不用 x, y, z, val, tmp

### ❌ 禁止行为

- 混合大小写规则（U UID 但 userId）
- 无意义的短名（x, y, tmp）
- 下划线后缀（user_，data_）
- 过长的变量名（currentUserObject 应该是 user）
- 缩写不清楚（cfg 可以，但 c 不行）

## 字段命名规范

### 特殊字段约定（参考 Linky Server）

#### ID 字段（严格遵循导出/非导出规则）

```go
// ✅ 推荐 - 导出字段用大写
type User struct {
    ID        int64     // ✅ 导出：主键（首字母大写）
    UID       int64     // ✅ 导出：用户 ID（用于 where 查询中区分）
    FriendUID int64     // ✅ 导出：关联用户 ID
}

// ✅ 私有/非导出字段用小写
func (u *User) getById(id int64) (*User, error) {  // 参数 id 是小写（私有/局部）
    return db.Where("id", id).First()
}

// ❌ 避免 - 混合不同的命名
type User struct {
    UserID    int64     // ❌ 不一致
    Id        int64     // ❌ 不推荐（既不是导出也不是清晰的私有）
    user_id   int64     // ❌ 不一致（Go 不用下划线）
}

// ❌ 避免 - 函数参数用大写
func GetUserById(ctx context.Context, ID int64) (*User, error) {  // ❌ ID 应该是小写 id
    return User.Where("id", ID).First()
}

// ✅ 查询时清晰
func GetUserByUID(ctx context.Context, uid int64) (*User, error) {
    user, err := User.Where("uid", uid).First()
    // uid 在查询中清晰表示"用户 ID"
}

// ✅ 友谊关系表中
type Friend struct {
    ID        int64     // 主键
    UID       int64     // 所有者用户 ID
    FriendUID int64     // 友谊关系的用户 ID
    Status    int32     // 0=pending, 1=active（数字枚举）
    CreatedAt time.Time
    UpdatedAt time.Time
}
```

#### 时间字段

```go
// ✅ 推荐 - 使用 CreatedAt/UpdatedAt
type Model struct {
    ID        int64
    CreatedAt time.Time  // 创建时间
    UpdatedAt time.Time  // 更新时间
}

// ❌ 避免 - 其他命名
type Model struct {
    CreatedTime time.Time  // 过长
    ModifyTime  time.Time  // 不清晰
    Timestamp   time.Time  // 太通用
}
```

#### 状态字段

```go
// ✅ 推荐 - 使用 Status 或 State（数字枚举）
type Friend struct {
    ID     int64
    Status int32  // 0=pending, 1=active, 2=blocked
}

type Task struct {
    ID    int64
    State int32  // 0=pending, 1=running, 2=done, 3=failed
}

// ❌ 禁止 - 字符串枚举或不清晰的字段名
type Friend struct {
    FriendStatus string  // 不推荐使用字符串
    FStatus      int     // 缩写不清楚
}

// ✅ 定义枚举常量（参考 Linky）
const (
    FriendStatusPending = 0
    FriendStatusActive  = 1
    FriendStatusBlocked = 2
)

// ✅ 查询时清晰
friends, err := Friend.
    Where("uid", uid).
    In("status", []int{FriendStatusActive, FriendStatusPending}).
    Find()
```

#### 布尔字段

```go
// ✅ 推荐 - Is/Has 前缀表示布尔值
type User struct {
    ID       int64
    Email    string
    IsActive bool   // 是否激活
    HasMFA   bool   // 是否启用双因素认证
    IsAdmin  bool   // 是否是管理员
}

// ❌ 避免 - 不清晰的命名
type User struct {
    Active  bool   // 不清晰
    Enabled bool   // 不清晰
    Admin   bool   // 不清晰
}
```

## 函数命名规范

### Service 层函数（参考 Linky）

```go
// ✅ 动词开头，清晰的操作
func UserLogin(ctx context.Context, req *LoginReq) (*LoginRsp, error)
func UserRegister(ctx context.Context, email, password string) (*User, error)
func GetUserByID(ctx context.Context, id int64) (*User, error)
func GetUserByEmail(ctx context.Context, email string) (*User, error)
func CreateUser(ctx context.Context, user *User) error
func UpdateUser(ctx context.Context, user *User) error
func DeleteUser(ctx context.Context, id int64) error
func ListUsers(ctx context.Context, limit int) ([]*User, error)
func CountUsers(ctx context.Context) (int64, error)

// ✅ 友谊关系操作
func AddFriend(ctx context.Context, uid, friendUID int64) error
func RemoveFriend(ctx context.Context, uid, friendUID int64) error
func ListFriends(ctx context.Context, uid int64) ([]*Friend, error)

// ✅ 消息操作
func SendMessage(ctx context.Context, msg *Message) error
func GetMessages(ctx context.Context, uid int64) ([]*Message, error)
func MarkAsRead(ctx context.Context, messageID int64) error

// ❌ 避免 - 不清晰或过长的名字
func Get(ctx context.Context, id int64) (*User, error)  // 过于通用
func FetchUserData(ctx context.Context, id int64) (*User, error)  // Fetch 不必要
func DoUserLogin(ctx context.Context, req *LoginReq) (*LoginRsp, error)  // Do 多余
```

### Get 前缀规则

```go
// ✅ Get 用于获取单个对象
func GetUserByID(ctx context.Context, id int64) (*User, error)
func GetMessageByID(ctx context.Context, id int64) (*Message, error)

// ✅ List 用于获取列表
func ListUsers(ctx context.Context, limit int) ([]*User, error)
func ListMessages(ctx context.Context, uid int64) ([]*Message, error)

// ✅ Count 用于计数
func CountUsers(ctx context.Context) (int64, error)
func CountFriends(ctx context.Context, uid int64) (int64, error)

// ✅ Check 用于检查
func CheckUserExists(ctx context.Context, id int64) (bool, error)
func CheckEmailExists(ctx context.Context, email string) (bool, error)

// ✅ Is/Has 用于判断
func IsUserAdmin(ctx context.Context, uid int64) (bool, error)
func HasUserMFA(ctx context.Context, uid int64) (bool, error)
```

### Handler 函数

```go
// ✅ Handler 后缀或动词+Handler（参考 Linky）
func UserLoginHandler(ctx *fiber.Ctx) error
func UserRegisterHandler(ctx *fiber.Ctx) error
func GetUserProfileHandler(ctx *fiber.Ctx) error

// 或者直接使用服务函数名（通过 ToHandler 适配）
impl.ToHandler(impl.UserLogin)   // UserLogin 直接作为 handler
impl.ToHandler(impl.UserRegister)
```

### Init 和 New 前缀

```go
// ✅ New 用于构造函数
func NewUser(email string) *User
func NewUserQuery() *UserQuery
func NewCache(size int) *Cache

// ✅ Init 用于初始化全局状态
func initState(db *gorm.DB) error      // 私有初始化函数
func initConfig() error                 // 私有初始化函数
func Init(database *gorm.DB) error     // 公开初始化接口

// ✅ Load 用于加载配置/数据
func state.Load() error                 // 加载全局状态
func config.Load() (*Config, error)    // 加载配置
```

## 接收者命名

### 短名约定（参考 Go 官方）

```go
// ✅ 推荐 - 单字母接收者
func (u *User) Login(password string) error
func (o *Order) Calculate() int64
func (f *Friend) IsActive() bool
func (m *Message) Send(ctx context.Context) error

// ✅ 对于自定义类型
func (q *UserQuery) Where(column string, value interface{}) *UserQuery
func (b *Builder) SetName(name string) *Builder
func (c *Cache) Get(key string) (interface{}, bool)

// ✅ 缩写清晰
func (db *DB) Query(sql string) *Rows
func (cfg *Config) Load() error
func (ctx context.Context) WithValue(key, val interface{}) context.Context

// ❌ 避免 - 过长或无意义
func (user *User) Login(password string) error  // user 应该是 u
func (userObj *User) Login(password string) error  // userObj 过长
func (u *User) U() *User  // 无意义的接收者名
```

## 常量命名

### 全局常量（参考 Linky）

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
    DefaultPageSize = 10  // 应该是 DEFAULT_PAGE_SIZE
    maxPageSize = 100     // 应该是 MAX_PAGE_SIZE（或 const block 中都大写）
)
```

### 局部常量

```go
// ✅ 函数内常量也用大写
func ProcessOrder(order *Order) error {
    const (
        STATUS_PENDING   = 0
        STATUS_PROCESSING = 1
        STATUS_COMPLETED = 2
    )

    switch order.Status {
    case STATUS_PENDING:
        // ...
    }
}
```

## 类型命名

### Struct 类型

```go
// ✅ 推荐 - PascalCase，意义清晰
type User struct { }
type UserLogin struct { }
type LoginRequest struct { }
type LoginResponse struct { }
type UserService struct { }

// ✅ 请求/响应类型后缀
type CreateUserReq struct { }   // 简写 Req
type CreateUserRsp struct { }   // 简写 Rsp
// 或者
type CreateUserRequest struct { }
type CreateUserResponse struct { }

// ❌ 避免 - 不清晰或过长
type UL struct { }  // 不清晰
type UserLoginInformation struct { }  // 过长
type login_user struct { }  // 不遵循规范
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
    Handle(ctx context.Context, req interface{}) error
}

// ✅ 如果必须用 interface（不推荐过多）
type Logger interface {
    Info(msg string, args ...interface{})
    Error(msg string, args ...interface{})
    Warn(msg string, args ...interface{})
}

// ❌ 避免 - I 前缀（Go 风格不推荐）
type IUser interface { }
type IUserRepository interface { }

// ❌ 避免 - 创建 Repository interface（使用全局状态而非接口）
type UserRepository interface {
    GetByID(id int64) (*User, error)
}
```

## 包名命名

### 包目录规范（参考 Linky）

```
project/
├── internal/
│   ├── state/           # ✅ 全局状态（小写单数）
│   ├── impl/            # ✅ Service 实现（小写）
│   ├── api/             # ✅ API 路由和 handler（小写）
│   ├── config/          # ✅ 配置管理（小写）
│   ├── middleware/      # ✅ 中间件（小写）
│   └── model/           # ✅ 数据模型（小写）
├── cmd/
│   └── main.go          # ✅ 启动入口
└── pkg/                 # ✅ 公开包（可选）
    └── errors/          # 错误类型

// ❌ 不推荐 - 混合规则
├── internal/
│   ├── Service/         # 不推荐大写
│   ├── service/         # 应该用 impl/
│   ├── models/          # 应该用 model/
│   └── user_service/    # 不推荐下划线
```

### 包名简洁规范

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

## 文件名命名

### 基本规则

```
// ✅ 推荐 - 全小写，可用下划线分隔
user.go
user_test.go
user_query.go
error_handler.go

// ❌ 避免 - 大写或混合
User.go           # 不推荐大写
UserService.go    # 应该用 user.go 或 user_service.go
user_Service.go   # 混合大小写

// ✅ 使用下划线区分
user.go           # 用户相关函数
user_test.go      # 用户测试
message.go        # 消息相关函数
message_test.go   # 消息测试

// ❌ 避免 - 冗余或不清晰
user_service.go   # 在 impl/ 包中：impl/user.go 更好
userHandler.go    # 在 api/ 包中：api/user.go 更好
```

### 特殊文件命名

```
// ✅ 初始化文件
init.go           # 包初始化（如果需要）
table.go          # state 包中的表定义
router.go         # api 包中的路由定义

// ✅ 测试文件
user_test.go      # user.go 的单元测试（同包）
user_integration_test.go  # user.go 的集成测试

// ❌ 避免 - 脱离上下文的文件名
handlers.go       # 应该分成 user.go, order.go
services.go       # 应该分成 user.go, order.go
utils.go          # 应该按功能分散到各模块
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
for x := 0; x < len(users); x++ { }  // x 不清晰
for index, user := range users { }  // index 过长（用 i）
for currentUser := range users { }  // 过长，用 user

result := func()  // 过于通用
value := someFunc()  // 过于通用
data := loadData()  // data 过于通用
```

### 错误变量

```go
// ✅ 推荐 - 使用 err
user, err := User.GetByID(ctx, id)
if err != nil {
    log.Errorf("err:%v", err)  // 统一日志格式
    return err
}

// ✅ 多个错误时区分
createErr := createUser(user)
if createErr != nil {
    log.Errorf("err:%v", createErr)
    return createErr
}

saveErr := saveUser(user)
if saveErr != nil {
    log.Errorf("err:%v", saveErr)
    return saveErr
}

// ❌ 避免 - 不清晰的错误变量
e := someFunc()      // e 不清晰
error := someFunc()  // error 是保留字
```

### Context 变量

```go
// ✅ 推荐 - 使用 ctx
func Login(ctx context.Context, username string) (*User, error) {
    user, err := User.Where("username", username).FirstContext(ctx)
}

// ✅ Fiber context
func LoginHandler(ctx *fiber.Ctx) error {
    uid := ctx.Locals("uid")
}

// ❌ 避免 - 不清晰
func Login(context context.Context, username string) (*User, error)  // 过长
func Login(c context.Context, username string) (*User, error)  // c 不清晰
```

## 特殊命名约定

### 导出与非导出

```go
package user

// ✅ 推荐

// 导出的结构体
type User struct {
    ID    int64
    Email string
}

// 导出的方法（接收者为导出类型）
func (u *User) IsAdmin() bool { }

// 私有函数（包内使用）
func validateEmail(email string) error { }

// 私有变量（包内使用）
var _cache = make(map[string]*User)

// ❌ 避免
type user struct { }  // 小写，无法导出
func (u User) IsAdmin() { }  // 值接收者用于方法
func validateUserEmail() { }  // 过长
var cache = make(map[string]*User)  // 全局变量无下划线前缀不清晰
```

## 参考

- **[Linky Server naming](file:///Users/luoxin/persons/lyxamour/linky/server)** - 实际项目命名约定
- **[Effective Go - Names](https://golang.org/doc/effective_go#names)** - Go 官方命名指南
- **[Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)** - 代码审查意见

## 检查清单

提交代码前，确保：

- [ ] 所有导出类型使用 PascalCase
- [ ] 所有导出函数使用 PascalCase，私有用 camelCase
- [ ] 接收者使用单字母（u, o, m 等）
- [ ] 包名全小写单词（不用下划线）
- [ ] 文件名全小写（可用下划线分隔）
- [ ] 常量使用 UPPER_CASE
- [ ] ID 字段统一（ID, UID, XXXID）
- [ ] 时间字段使用 CreatedAt/UpdatedAt
- [ ] 状态字段使用 Status/State（数字）
- [ ] 布尔字段使用 Is/Has 前缀
- [ ] 无 Repository interface（使用全局状态）
- [ ] 函数名清晰（不用 Get/Do/Execute 前缀，除非必要）

## 总结

遵循这些命名规范：
- **一致性强** - 代码更易维护
- **可读性高** - 名字清晰表达意图
- **符合 Go 风格** - 遵循语言约定
- **类似 Linky** - 与实际项目保持一致

**简洁清晰的名字胜过冗长的注释。**
