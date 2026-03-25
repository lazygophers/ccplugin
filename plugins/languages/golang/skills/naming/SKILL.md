---
name: naming
description: Go 命名强制规范：Id/Uid 字段、IsActive 布尔前缀、CreatedAt 时间字段、接收者用 p、Go 1.22+ 新路由模式命名。命名时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 命名规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）
- **test** - 测试专家

## 相关 Skills

| 场景     | Skill                    | 说明                         |
| -------- | ------------------------ | ---------------------------- |
| 核心规范 | Skills(golang:core)      | 核心规范：强制约定           |
| 项目结构 | Skills(golang:structure) | 三层架构命名约定             |
| 错误处理 | Skills(golang:error)     | 错误变量命名                 |

## 核心原则

### 必须遵守

1. **导出变量/函数 PascalCase** - User, UserLogin, GetUserById（不是 GetUserByID）
2. **私有变量/函数 camelCase** - user, getUserById
3. **常量 PascalCase** - DefaultTimeout, MaxRetries
4. **包名全小写单词** - user, order, payment（无下划线）
5. **文件名全小写** - user.go, user_test.go（不是 User.go）
6. **接收者必须为 `p`** - (p *User), (p *Order)
7. **循环变量短名** - for i, for idx, for item
8. **字段名有意义** - 不用 x, y, z

### 禁止行为

- 混合大小写规则（UUID 但 userId）
- 无意义的短名（x, y, tmp）
- 下划线后缀（user_, data_）
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
    Id    uint64
    State int32
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
func GetUserById(req *GetUserByIdReq) (*GetUserByIdRsp, error)
func AddUser(req *AddUserReq) error
func UpdateUser(req *UpdateUserReq) error
func DelUser(req *DelUserReq) error
func ListUser(req *ListUserReq) (*ListUserRsp, error)
```

### Get 前缀规则

```go
func GetUserById(id uint64) (*User, error)    // 获取单个
func ListUser(limit int) ([]*User, error)      // 获取列表
func CountUser() (int64, error)                // 计数
func CheckUserExists(id uint64) (bool, error)  // 检查存在
func IsUserAdmin(uid uint64) (bool, error)     // 判断状态
```

## 接收者命名

```go
// 接收者统一使用 p
func (p *User) Login(password string) error
func (p *Order) Calculate() int64
func (p *Friend) IsActive() bool
```

## 泛型类型参数命名（Go 1.18+）

```go
// 使用描述性名称而非单字母
func Map[T any, R any](items []T, fn func(T) R) []R
func Filter[T any](items []T, fn func(T) bool) []T

// 约束接口命名
type Ordered interface {
    ~int | ~float64 | ~string
}
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "ID 全大写更规范" | 是否使用 Id 而非 ID？ | 高 |
| "self/this 更直观" | 接收者是否统一用 p？ | 高 |
| "变量名越长越清晰" | 是否避免过长变量名？ | 中 |
| "GetByID 更标准" | 是否使用 GetUserById 风格？ | 中 |
| "用 T 就够了" | 泛型参数是否有描述性？ | 低 |
| "pkg_name 更清晰" | 包名是否全小写无下划线？ | 中 |

## 检查清单

- [ ] 所有导出类型使用 PascalCase
- [ ] 所有导出函数使用 PascalCase，私有用 camelCase
- [ ] 接收者使用单字母（p）
- [ ] 包名全小写单词（不用下划线）
- [ ] 文件名全小写（可用下划线分隔）
- [ ] 常量使用 PascalCase
- [ ] ID 字段统一（Id, Uid, XXXId）
- [ ] 时间字段使用 CreatedAt/UpdatedAt
- [ ] 状态字段使用数字类型 Status/State
- [ ] 布尔字段使用 Is/Has 前缀
