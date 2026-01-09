# 命名规范

## 核心原则

### ✅ 必须遵守

1. **导出大写，私有小写** - PascalCase for public, camelCase for private
2. **简洁有意义** - 名字应自解释，避免模糊
3. **完整词汇** - 不使用过度缩写，除非广为人知
4. **一致性** - 相同概念使用相同名字
5. **上下文清晰** - 不重复包名、类型名等显而易见的部分

### ❌ 禁止行为

- 单字母变量（除了 loop counter i, j, k）
- 无意义的前缀/后缀（Var, Type, Impl）
- 混合命名风格（camelCase 与 snake_case 混用）
- 过度缩写（usr, crt, cfg 不好，除非上下文明确）
- 大小写错误的常量或变量

## 变量和常量命名

### 导出变量和常量

```go
// ✅ 正确 - PascalCase 导出
var GlobalConfig Config        // 全局变量
const MaxRetries = 3          // 常量
const DefaultTimeout = 30 * time.Second

var Users []*User             // 切片
var UserCache map[int]*User   // 映射

// ❌ 避免
var globalConfig Config       // 不导出应该小写
var global_config Config      # 不用下划线
const maxRetries = 3          // 导出应该大写
```

### 私有变量和常量

```go
// ✅ 正确 - camelCase 私有
var userCache map[string]*User
const maxConnections = 100
var defaultLogger Logger

func doProcess() {
    var result *Result
    return result
}

// ❌ 避免
var UserCache map[string]*User  // 不应导出
const MaxConnections = 100       // 不应导出
var _config Config               // 不用前缀下划线（除非特殊）
```

### 特殊变量命名

```go
// ✅ 循环变量（单字母）
for i := 0; i < len(items); i++ {
    for j := 0; j < len(items[i]); j++ {
        // ...
    }
}

// ✅ 临时变量（简洁）
b := buf.Bytes()        // 字节
n := len(items)         // 数字/长度
ok := cache.Get(key)    // 布尔

// ✅ 下划线用于忽略
_, err := doSomething()  // 忽略第一个返回值

// ❌ 避免 - 无意义的单字母
var x, y, z interface{}  // 不清楚
```

### 缩写规范

```go
// ✅ 广为人知的缩写保留
var ctx context.Context
var cfg Config
var uid int             // user ID
var repo Repository
var msg string          // message
var buf *bytes.Buffer
var rdb *redis.Client
var pb *pb.User        // protobuf

// ❌ 避免 - 非标准缩写
var usr *User
var crt Certificate
var conn *Connection  // 应该是 conn 是接受的
var pwd string        // 应该是 password
var tmp interface{}   // 应该是 temp 或更具体的名字
```

## 函数命名

### 导出函数

```go
// ✅ 动词开头 - 导出函数
func New(cfg Config) *Server
func NewWithContext(ctx context.Context, cfg Config) *Server
func Load(path string) (*Config, error)
func Parse(data []byte) (*User, error)
func Validate(value string) error
func Save(item *Item) error
func Get(key string) interface{}
func Set(key string, value interface{})
func Delete(key string) error
func Find(id int) (*Item, error)
func FindAll() ([]*Item, error)

// ✅ 布尔函数
func Is(value string) bool
func Has(key string) bool
func Exists(id int) (bool, error)

// ✅ 初始化函数
func init(cfg Config)
func initialize()
func setup()

// ❌ 避免
func User() {}           # 名词，不是动词
func Process() {}        # 太模糊
func Do() {}            # 太模糊
func Execute() {}       # 太模糊
func GetUser_ById() {}  # 混合风格
```

### 私有函数

```go
// ✅ 正确 - camelCase
func (h *Handler) register(ctx context.Context, req *Request) error
func parseRequest(ctx *fiber.Ctx) (*Request, error)
func validateEmail(email string) error
func hashPassword(password string) string
func extractUserFromContext(ctx context.Context) (*User, error)

// ❌ 避免
func (h *Handler) Register(ctx context.Context) error  # 不应导出
func parseRequest() (*Request, error)  // 应该考虑参数
```

### 方法命名（Receiver Methods）

```go
// ✅ 导出方法 - PascalCase
type User struct {
    name string
}

func (u *User) Name() string {
    return u.name
}

func (u *User) SetName(name string) {
    u.name = name
}

// ✅ 私有方法 - camelCase
func (u *User) validate() error {
    // ...
}

// ✅ Receiver 名字简洁
func (u *User) GetAge() int { }      // u for User
func (h *Handler) Handle(ctx *fiber.Ctx) error { }  // h for Handler
func (s *Server) Listen() error { }   // s for Server

// ❌ 避免 - Receiver 太长
func (user *User) Name() string { }   // 用 u 即可
func (server *Server) Listen() error { }  // 用 s 即可
```

## 类型和结构体命名

### 结构体和接口

```go
// ✅ 导出类型 - PascalCase
type User struct {
    ID       int
    Name     string
    Email    string
    Created  time.Time
}

type UserService interface {
    GetUser(ctx context.Context, id int) (*User, error)
    SaveUser(ctx context.Context, user *User) error
}

// ✅ 接口命名习惯
type Reader interface {         // 单方法接口用 er 结尾
    Read(ctx context.Context) ([]byte, error)
}

type Writer interface {
    Write(ctx context.Context, data []byte) error
}

type Handler interface {        // 或 Handler
    Handle(ctx *fiber.Ctx) error
}

// ❌ 避免
type user struct { }            // 私有应该小写（但少用）
type UserData struct { }        # Data 是多余的
type UserImpl struct { }         # Impl 是多余的
type IUser interface { }        # I 前缀不用
```

### 私有结构体（少用）

```go
// ✅ 私有结构体 - 很少使用
type config struct {
    addr    string
    timeout time.Duration
}

// 通常导出：
type Config struct {
    Addr    string
    Timeout time.Duration
}
```

## 字段命名

### 结构体字段

```go
// ✅ 字段命名 - PascalCase
type User struct {
    ID       int       // 标识符
    Name     string    // 名字
    Email    string    // 邮箱
    Age      int       // 年龄
    Created  time.Time // 创建时间
    Updated  time.Time // 更新时间
}

// ✅ 接收者短名
type Handler struct {
    service UserService   // 不是 userService
    logger  Logger
}

// ✅ 布尔字段 - Is/Has 前缀
type User struct {
    IsActive bool
    HasAuth  bool
    Verified bool  // 或 IsVerified
}

// ❌ 避免
type User struct {
    id           int       # 应该大写
    user_name    string    # 应该用驼峰 UserName
    created_at   time.Time # 应该用驼峰 CreatedAt
    Firstname    string    # 应该是 FirstName
}
```

### Tag 中的字段名

```go
// ✅ JSON/DB Tag - 保持一致
type User struct {
    ID    int    `json:"id" db:"id"`
    Name  string `json:"name" db:"name"`
    Email string `json:"email" db:"email"`

    // ✅ 可以使用蛇形（JSON API 常见）
    CreatedAt time.Time `json:"created_at" db:"created_at"`
}

// ❌ 避免 - Tag 中混合风格
type User struct {
    ID        int    `json:"userId" db:"user_id"`  # 不一致
    FirstName string `json:"firstname" db:"first_name"`  # 混合
}
```

## 包和文件命名

### 包名规范

```go
// ✅ 包名 - 全小写，单数，简洁
package api           // API 处理
package service       // 业务逻辑
package repository    // 数据访问
package model         // 数据模型
package config        // 配置
package cache         // 缓存
package handler       // 处理器
package middleware    // 中间件
package util          // 工具函数

// ✅ 子包
package http
package mysql
package redis

// ❌ 避免
package API           # 不要大写
package user_service  # 不用下划线
package services      # 不用复数（service 更清楚）
package Utils         # 不要大写
```

### 文件名规范

```
// ✅ 文件名 - 全小写，下划线分隔
user.go              # 用户相关
user_test.go         # 用户测试
handler.go           # 处理器
middleware.go        # 中间件
service.go           # 服务
repository.go        # 仓库
config.go            # 配置

// ❌ 避免
User.go              # 不要大写
userService.go       # 不用驼峰
user_service.go      # 分部分可以，但单个概念不用
UserService.go       # 不要大写
```

## 常量命名

### 常量分类

```go
// ✅ 导出常量 - SCREAMING_SNAKE_CASE（可选）或 PascalCase（推荐）
const (
    DefaultTimeout = 30 * time.Second
    MaxRetries     = 3
    MinPasswordLen = 8
)

// ✅ 或使用 PascalCase（推荐，更 Go 风格）
const (
    DefaultTimeout = 30 * time.Second
    MaxConnections = 100
    BufferSize     = 1024
)

// ✅ 枚举常量 - 前缀 + 值
const (
    StatusPending   = "pending"
    StatusActive    = "active"
    StatusInactive  = "inactive"
)

// 或用 iota
const (
    RoleAdmin = iota
    RoleUser
    RoleGuest
)

// ✅ 私有常量 - camelCase
const (
    defaultBufferSize = 1024
    maxRetries        = 3
)

// ❌ 避免
const DefaultTimeout = 30 * time.Second  // 不应导出常量
const default_timeout = 30 * time.Second # 混合风格
```

## 特殊命名约定

### 接收者命名

```go
// ✅ 接收者 - 1-2 字母缩写，保持一致
type User struct{}
func (u *User) GetName() string

type UserService struct{}
func (s *UserService) GetUser() *User

type Handler struct{}
func (h *Handler) Handle() error

// ✅ 相同类型保持一致
type API struct{}
func (a *API) Register() error
func (a *API) Handler(ctx *fiber.Ctx) error  // 同一类型用同一接收者

// ❌ 避免 - 不一致
type User struct{}
func (u *User) GetName() string
func (user *User) GetAge() int  // 应该都用 u

type Service struct{}
func (s *Service) Process() error
func (service *Service) Handle() error  // 应该都用 s
```

### 错误命名

```go
// ✅ 错误变量
var (
    ErrNotFound       = errors.New("not found")
    ErrInvalidInput   = errors.New("invalid input")
    ErrUnauthorized   = errors.New("unauthorized")
    ErrInternal       = errors.New("internal server error")
)

// ✅ 自定义错误类型
type ValidationError struct {
    Field   string
    Message string
}

type NotFoundError struct {
    ID string
}

// ❌ 避免
const (
    NotFoundError = "Not Found"  # 应该是 var，大小写错误
)

var (
    Error_NotFound = errors.New("not found")  # 不用下划线
)
```

### 接口实现命名

```go
// ✅ 实现接口的结构体
type Reader interface {
    Read(ctx context.Context) ([]byte, error)
}

// 实现类型 - 不需要特殊前缀
type FileReader struct {
    file *os.File
}

func (f *FileReader) Read(ctx context.Context) ([]byte, error) {
    // ...
}

// ❌ 避免
type FileReaderImpl struct { }  # 不用 Impl 后缀
type IFileReader interface { } # 不用 I 前缀（Java 风格）
```

## 命名审查清单

在提交代码前，检查：

- [ ] 所有导出（公开）函数/类型/常量/变量用 PascalCase
- [ ] 所有私有（非导出）用 camelCase
- [ ] 变量名自解释，不需要注释说明
- [ ] 避免单字母变量（除了 loop counter i, j, k）
- [ ] 避免缩写（除了广为人知的）
- [ ] 接收者名字简洁（1-2 个字母）
- [ ] 错误变量用 `Err` 或 `Error` 前缀
- [ ] 布尔变量用 `Is`, `Has`, `Can` 等前缀
- [ ] 函数名以动词开头
- [ ] 接口名以 `er` 结尾（可选但推荐）
- [ ] 包名简洁、小写、单数形式
- [ ] 常量用 SCREAMING_SNAKE_CASE 或 PascalCase

## 参考

- [Effective Go - Names](https://golang.org/doc/effective_go#names)
- [Go Code Review Comments - Naming](https://github.com/golang/go/wiki/CodeReviewComments#naming)
- [Uber Go Style Guide - Naming Conventions](https://github.com/uber-go/guide/blob/master/style.md#naming)
