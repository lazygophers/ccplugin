---
name: naming
description: Go 命名强制规范：Id/Uid 字段、IsActive 布尔前缀、CreatedAt 时间字段。命名时必须加载。
---

# Go 命名规范

## 核心原则

### 必须遵守

1. **导出变量/函数 PascalCase** - User, UserLogin, GetUserById（不是 GetUserByID）
2. **私有变量/函数 camelCase** - user, getUserById
3. **常量 UPPER_CASE** - DefaultTimeout, MaxRetries
4. **包名全小写单词** - user, order, payment（无下划线）
5. **文件名全小写** - user.go, user_test.go（不是 User.go）
6. **接收者必须为`p`** - (p *User), (p *Order)
7. **循环变量短名** - for i, for idx, for item
8. **字段名有意义** - 不用 x, y, z

### 禁止行为

- 混合大小写规则（UUID 但 userId）
- 无意义的短名（x, y, tmp）
- 下划线后缀（user*, data*）
- 过长的变量名（currentUserObject 应该是 user）
- 缩写不清楚（cfg 可以，但 c 不行）

## 字段命名规范

### ID 字段

```go
type User struct {
    Id        uint64
    Uid       uint64
    FriendUid uint64
    UUID      string
}
```

### 时间字段

```go
type Model struct {
    Id        uint64
    CreatedAt int64
    UpdatedAt int64
}
```

### 状态字段

```go
type Friend struct {
    Id     uint64
    State  int32
}

const (
    FriendStatusPending = 0
    FriendStatusActive  = 1
    FriendStatusBlocked = 2
)
```

### 布尔字段

```go
type User struct {
    Id       uint64
    Email    string
    IsActive bool
    HasMFA   bool
    IsAdmin  bool
}
```

## 函数命名规范

### Service 层函数

```go
func UserLogin(req *UserLoginReq) (*UserLoginRsp, error)
func UserRegister(req *UserRegisterReq) (*UserRegisterRsp, error)
func GetUserById(req *GetUserByIdReq) (*GetUserByIdRsp, error)
func GetUserByEmail(req *GetUserByEmailReq) (*GetUserByEmailRsp, error)
func AddUser(req *AddUserReq) error
func UpdateUser(req *UpdateUserReq) error
func DelUser(req *DelUserReq) error
func ListUser(req *ListUserReq) (*ListUserRsp, error)
func CountUser(req *CountUserReq) (*CountUserRsp, error)
```

### Get 前缀规则

```go
func GetUserById(id uint64) (*User, error)
func ListUser(limit int) ([]*User, error)
func CountUser(ctx context.Context) (int64, error)
func CheckUserExists(id uint64) (bool, error)
func IsUserAdmin(uid uint64) (bool, error)
func HasUserMFA(uid uint64) (bool, error)
```

## 接收者命名

```go
func (p *User) Login(password string) error
func (p *Order) Calculate() int64
func (p *Friend) IsActive() bool
func (p *Message) Send(ctx context.Context) error
```

## 常量命名

```go
const (
    DefaultPageSize    = 10
    MaxPageSize        = 100
    DefaultTimeout     = 30 * time.Second
    MaxRetries         = 3
    RequestIDHeader    = "X-Request-ID"
)

const (
    FriendStatusPending = 0
    FriendStatusActive  = 1
    FriendStatusBlocked = 2
)
```

## 类型命名

```go
type User struct { }
type UserLogin struct { }
type CreateUserReq struct { }
type CreateUserRsp struct { }
```

## 包命名

```go
package state
package impl
package api
package model
package config
package log
```

## 文件命名

```
user.go
user_test.go
user_query.go
error_handler.go
init.go
table.go
router.go
```

## 检查清单

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
