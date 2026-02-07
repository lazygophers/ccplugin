# Golang 注释规范

## 核心原则

### ✅ 必须遵守

1. **导出必须有注释** - 所有导出的类型、函数、常量必须有注释
2. **说明意图** - 注释说明"是什么"和"为什么"，而不是"怎么做"
3. **简洁清晰** - 注释简洁明了，避免冗余
4. **保持更新** - 代码变更时同步更新注释
5. **避免误导** - 不准确或过时的注释比没有注释更糟糕

### ❌ 禁止行为

- 注释显而易见的代码
- 注释与代码不一致
- 使用 C 风格的多行注释 `/* */`
- 注释包含作者、日期等版本控制信息
- 过度注释

## 注释类型

### 包注释

```go
// ✅ 正确 - 包注释在 package 声明之前
// Package user 提供用户管理功能，包括用户注册、登录、信息更新等
package user

// ❌ 错误 - 缺少包注释
package user
```

### 类型注释

```go
// ✅ 正确 - 导出类型必须有注释
// User 表示系统用户，包含用户的基本信息和状态
type User struct {
    Id        int64
    Email     string
    IsActive  bool
    CreatedAt time.Time
}

// ❌ 错误 - 缺少注释
type User struct {
    Id   int64
    Name string
}

// ✅ 正确 - 私有类型可选注释
// userCache 是用户缓存，用于提高查询性能
type userCache struct {
    cache map[int64]*User
}
```

### 函数注释

```go
// ✅ 正确 - 导出函数必须有注释
// UserLogin 处理用户登录
// 参数 req 包含登录请求信息（用户名和密码）
// 返回登录成功的用户信息或错误
func UserLogin(req *LoginReq) (*User, error) {
    // 实现
}

// ✅ 正确 - 复杂函数需要详细注释
// ProcessBatch 批量处理订单
// 处理流程：
// 1. 验证订单数据
// 2. 检查库存
// 3. 创建订单记录
// 4. 扣减库存
// 5. 发送通知
// 返回处理结果或错误
func ProcessBatch(orders []*Order) (*BatchResult, error) {
    // 实现
}

// ❌ 错误 - 缺少注释
func UserLogin(req *LoginReq) (*User, error) {
    // 实现
}
```

### 常量注释

```go
// ✅ 正确 - 导出常量必须有注释
// DefaultPageSize 是默认分页大小
const DefaultPageSize = 10

// ✅ 正确 - 枚举常量需要注释
// FriendStatusPending 表示好友关系待确认
const FriendStatusPending = 0

// FriendStatusActive 表示好友关系已激活
const FriendStatusActive = 1

// FriendStatusBlocked 表示好友关系已拉黑
const FriendStatusBlocked = 2

// ❌ 错误 - 缺少注释
const MaxRetries = 3
```

## 注释格式

### 单行注释

```go
// ✅ 正确 - 单行注释
// 处理用户登录
func Login() error {}

// ❌ 错误 - 使用 C 风格注释
/* 处理用户登录 */
func Login() error {}
```

### 多行注释

```go
// ✅ 正确 - 多行注释
// 处理用户登录流程：
// 1. 验证用户名和密码
// 2. 生成访问令牌
// 3. 返回用户信息
func Login() error {}

// ❌ 错误 - 使用 C 风格多行注释
/*
处理用户登录流程：
1. 验证用户名和密码
2. 生成访问令牌
3. 返回用户信息
*/
func Login() error {}
```

### 行内注释

```go
// ✅ 正确 - 行内注释用于解释复杂逻辑
result := (a + b) * c // 计算加权平均值

// ❌ 错误 - 行内注释解释显而易见的代码
result := a + b // 加法运算
```

## 注释内容

### 说明"是什么"和"为什么"

```go
// ✅ 正确 - 说明意图和原因
// 使用 sync.Pool 复用缓冲区，减少内存分配和 GC 压力
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

// ❌ 错误 - 说明"怎么做"（代码已经很清楚）
// 创建一个 sync.Pool，New 函数返回一个新的 bytes.Buffer
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}
```

### 解释复杂逻辑

```go
// ✅ 正确 - 解释复杂算法
// 使用滑动窗口算法计算最大子数组和
// 时间复杂度 O(n)，空间复杂度 O(1)
func maxSubArray(nums []int) int {
    maxSum := nums[0]
    currentSum := nums[0]

    for i := 1; i < len(nums); i++ {
        currentSum = max(nums[i], currentSum+nums[i])
        maxSum = max(maxSum, currentSum)
    }

    return maxSum
}
```

### 说明设计决策

```go
// ✅ 正确 - 说明设计决策
// 使用全局状态而非依赖注入，简化代码结构
var globalState *State
```

## 注释最佳实践

### 避免注释显而易见的代码

```go
// ❌ 错误 - 注释显而易见的代码
// 增加计数器
count++

// 获取用户
user := getUser(id)

// 检查错误
if err != nil {
    return err
}

// ✅ 正确 - 代码本身已经很清楚
count++
user := getUser(id)
if err != nil {
    return err
}
```

### 保持注释与代码同步

```go
// ❌ 错误 - 注释与代码不一致
// 返回所有活跃用户
func GetAllUsers() ([]*User, error) {
    return User.Where("status", StatusActive).Find()
}

// ✅ 正确 - 注释与代码一致
// 返回所有活跃用户
func GetActiveUsers() ([]*User, error) {
    return User.Where("status", StatusActive).Find()
}
```

### 使用 TODO 和 FIXME

```go
// ✅ 正确 - 标记待办事项
// TODO: 添加缓存层以提高性能
func GetUser(id int64) (*User, error) {
    return User.Where("id", id).First()
}

// ✅ 正确 - 标记需要修复的问题
// FIXME: 这里存在潜在的并发问题，需要加锁
var counter int
func increment() {
    counter++
}
```

### 避免版本控制信息

```go
// ❌ 错误 - 注释包含版本控制信息
// Author: John Doe
// Date: 2024-01-01
// Modified: 2024-01-15
func GetUser(id int64) (*User, error) {
    return User.Where("id", id).First()
}

// ✅ 正确 - 不包含版本控制信息
func GetUser(id int64) (*User, error) {
    return User.Where("id", id).First()
}
```

## 特殊注释

### Deprecated 注释

```go
// ✅ 正确 - 标记已弃用的代码
// Deprecated: 使用 NewUser 替代
func CreateUser(name string) *User {
    return &User{Name: name}
}

// ✅ 正确 - 说明替代方案
// Deprecated: 使用 GetUserById 替代
// 将在 v2.0 版本中移除
func GetUser(id int64) (*User, error) {
    return User.Where("id", id).First()
}
```

### Performance 注释

```go
// ✅ 正确 - 说明性能特征
// 时间复杂度 O(n)，空间复杂度 O(1)
func FindMax(nums []int) int {
    max := nums[0]
    for _, num := range nums {
        if num > max {
            max = num
        }
    }
    return max
}
```

### Security 注释

```go
// ✅ 正确 - 说明安全注意事项
// 注意：密码必须使用 bcrypt 加密存储
func SetPassword(user *User, password string) error {
    hashed, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return err
    }
    user.PasswordHash = string(hashed)
    return nil
}
```

## 检查清单

提交代码前，确保：

- [ ] 所有导出类型有注释
- [ ] 所有导出函数有注释
- [ ] 所有导出常量有注释
- [ ] 包有注释
- [ ] 注释说明"是什么"和"为什么"
- [ ] 注释与代码一致
- [ ] 没有注释显而易见的代码
- [ ] 没有版本控制信息（作者、日期）
- [ ] 使用 Go 风格注释（`//`），不使用 C 风格（`/* */`）
- [ ] TODO/FIXME 有明确的描述
