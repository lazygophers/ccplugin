---
name: golang-naming
description: Go 命名规范——Id/Uid 字段（非 ID）、IsActive/HasMFA 布尔前缀、CreatedAt 时间字段、接收者统一用 p、包名全小写无下划线、泛型类型参数描述性命名。定义结构体字段、函数、变量、包、接收者名、泛型时触发。
---

# Go 命名规范

## 八条铁律

1. 导出（包外可见）：`PascalCase`，如 `User`、`UserLogin`、`GetUserById`（**不是 ID**）
2. 私有：`camelCase`，如 `user`、`getUserById`
3. 常量：`PascalCase`，如 `DefaultTimeout`、`MaxRetries`
4. 包名：全小写单词，单数，无下划线，如 `user`、`order`、`payment`
5. 文件名：全小写，可下划线分隔，如 `user.go`、`user_test.go`
6. 接收者：统一 `p`，如 `(p *User)`、`(p *Order)`
7. 循环变量：短名 `i`、`idx`、`item`
8. 字段必须有意义，禁 `x`/`y`/`z`/`tmp`

## ID 字段

```go
type User struct {
    Id        uint64  // 主键
    Uid       uint64  // 用户唯一标识
    FriendUid uint64  // 关联用户 ID
    UUID      string  // 仅当确实是 UUID（大写）
}
```

不写 `ID`/`UserID`/`UID`，统一 `Id`/`Uid`/`Xxxid` → `XxxId`。

## 时间字段

```go
type Model struct {
    Id        uint64
    CreatedAt int64
    UpdatedAt int64
    DeletedAt int64 // 软删
}
```

## 状态字段

```go
type Friend struct {
    Id    uint64
    State int32
}

const (
    FriendStatusPending = 0
    FriendStatusActive  = 1
    FriendStatusBlocked = 2
)
```

数值枚举用 `State`/`Status` + 常量分组。

## 布尔字段

```go
type User struct {
    IsActive bool
    HasMFA   bool
    IsAdmin  bool
    CanEdit  bool
}
```

前缀必须是 `Is`/`Has`/`Can`/`Should`。

## 函数命名

### Service 层

```go
func UserLogin(req *UserLoginReq) (*UserLoginRsp, error)
func GetUserById(req *GetUserByIdReq) (*GetUserByIdRsp, error)
func AddUser(req *AddUserReq) error
func UpdateUser(req *UpdateUserReq) error
func DelUser(req *DelUserReq) error
func ListUser(req *ListUserReq) (*ListUserRsp, error)
```

### Get 系前缀

| 前缀 | 用途 |
| --- | --- |
| `GetXxxById` | 取单条 |
| `ListXxx` | 取列表 |
| `CountXxx` | 计数 |
| `CheckXxxExists` | 存在性 |
| `IsXxx` | 布尔判断 |

## 接收者

```go
func (p *User) Login(password string) error
func (p *Order) Calculate() int64
func (p *Friend) IsActive() bool
```

不用 `self`/`this`/`u`/`o`，统一 `p`。

## 泛型类型参数（Go 1.18+）

```go
// 描述性命名
func Map[T any, R any](items []T, fn func(T) R) []R
func Filter[T any](items []T, fn func(T) bool) []T

// 约束接口
type Ordered interface {
    ~int | ~float64 | ~string
}

// Go 1.26 自引用
type Node[T Node[T]] interface {
    Children() []T
}
```

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "ID 全大写更规范" | 用 Id 不是 ID？ |
| "self/this 更直观" | 接收者统一 p？ |
| "变量名越长越清晰" | 避免冗长？ |
| "GetByID 是 Go 官方写法" | 项目用 GetUserById 风格？ |
| "T 就够了" | 泛型参数描述性？ |
| "pkg_name 更清晰" | 包名全小写无下划线？ |

## 检查清单

- [ ] 导出 PascalCase、私有 camelCase
- [ ] 接收者统一 `p`
- [ ] 包名全小写单数
- [ ] 文件名全小写
- [ ] 常量 PascalCase
- [ ] ID 字段用 `Id`/`Uid`
- [ ] 时间用 `CreatedAt`/`UpdatedAt`
- [ ] 状态用 `Status`/`State` 数值
- [ ] 布尔用 `Is`/`Has`/`Can` 前缀
