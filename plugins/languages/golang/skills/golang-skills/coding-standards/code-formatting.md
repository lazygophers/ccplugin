# Golang 代码格式规范

## 核心原则

### ✅ 必须遵守

1. **自动格式化** - 使用 `gofmt` 和 `goimports` 自动格式化代码
2. **导入分组** - 标准库、第三方库、本地库分组
3. **注释规范** - 导出类型和函数必须有注释
4. **代码组织** - 按逻辑顺序组织代码
5. **行长度** - 单行不超过 120 字符

### ❌ 禁止行为

- 手动格式化代码（使用工具）
- 混乱导入顺序
- 缺少必要注释
- 过长单行
- 不一致的缩进

## 代码格式化

### 使用 gofmt

```bash
# 格式化所有 Go 文件
gofmt -w .

# 格式化特定文件
gofmt -w main.go

# 检查格式（不修改）
gofmt -l .
```

### 使用 goimports

```bash
# 格式化并优化导入
goimports -w .

# 格式化特定文件
goimports -w main.go

# 检查导入（不修改）
goimports -l .
```

### 集成到编辑器

```json
// VSCode settings.json
{
    "go.formatTool": "goimports",
    "go.lintTool": "golangci-lint",
    "go.lintOnSave": "file",
    "go.formatOnSave": true
}
```

## 导入规范

### 导入分组

```go
// ✅ 正确 - 标准库、第三方库、本地库分组
import (
    // 标准库
    "context"
    "fmt"
    "os"
    "time"

    // 第三方库
    "github.com/gofiber/fiber/v2"
    "github.com/lazygophers/log"
    "gorm.io/gorm"

    // 本地库
    "github.com/username/project/internal/state"
    "github.com/username/project/internal/impl"
)

// ❌ 错误 - 混乱导入
import (
    "github.com/gofiber/fiber/v2"
    "context"
    "github.com/username/project/internal/state"
    "fmt"
    "github.com/lazygophers/log"
)
```

### 导入别名

```go
// ✅ 正确 - 需要时使用别名
import (
    "fmt"
    "time"

    fiber "github.com/gofiber/fiber/v2"
    gorm "gorm.io/gorm"
)

// ❌ 错误 - 不必要的别名
import (
    f "fmt"
    t "time"
)

// ✅ 正确 - 避免冲突
import (
    "github.com/lazygophers/utils/stringx"
    localStringx "github.com/username/project/internal/stringx"
)
```

### 未使用导入

```bash
# 检查并移除未使用的导入
goimports -w .

# 或使用 go mod tidy
go mod tidy
```

## 注释规范

### 导出类型注释

```go
// ✅ 正确 - 导出类型必须有注释
// User 表示系统用户
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
```

### 导出函数注释

```go
// ✅ 正确 - 导出函数必须有注释
// UserLogin 处理用户登录
// 返回登录用户信息或错误
func UserLogin(req *LoginReq) (*User, error) {
    // 实现
}

// ❌ 错误 - 缺少注释
func UserLogin(req *LoginReq) (*User, error) {
    // 实现
}
```

### 注释格式

```go
// ✅ 正确 - 单行注释
// 处理用户登录
func Login() error {}

// ✅ 正确 - 多行注释
// 处理用户登录流程：
// 1. 验证用户名和密码
// 2. 生成访问令牌
// 3. 返回用户信息
func Login() error {}

// ❌ 错误 - 使用 C 风格注释
/* 处理用户登录 */
func Login() error {}
```

### 注释内容

```go
// ✅ 正确 - 说明"是什么"和"为什么"
// 使用 sync.Pool 复用缓冲区，减少内存分配
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

## 代码组织

### 文件组织顺序

```go
// ✅ 正确 - 标准顺序
package main

import (
    // 导入
)

// 常量定义
const (
    MaxRetries = 3
)

// 变量定义
var (
    globalVar int
)

// 类型定义
type MyType struct {}

// 接口定义
type MyInterface interface {}

// 函数定义
func main() {}

// ❌ 错误 - 混乱顺序
package main

import "fmt"

func main() {}

const MaxRetries = 3
```

### 结构体字段顺序

```go
// ✅ 正确 - 按逻辑分组
type User struct {
    // 主键
    Id int64

    // 基本信息
    Name  string
    Email string

    // 状态
    IsActive bool
    Status   int32

    // 时间戳
    CreatedAt time.Time
    UpdatedAt time.Time
}

// ❌ 错误 - 混乱顺序
type User struct {
    CreatedAt time.Time
    Name      string
    Id        int64
    IsActive  bool
    Email     string
    UpdatedAt time.Time
}
```

## 行长度和缩进

### 行长度

```go
// ✅ 正确 - 合理的行长度
func ProcessUser(user *User, config *Config, logger Logger) error {
    // 实现
}

// ❌ 错误 - 过长的行
func ProcessUser(user *User, config *Config, logger Logger, ctx context.Context, timeout time.Duration, retries int) error {
    // 实现
}

// ✅ 正确 - 拆分长行
func ProcessUser(
    user *User,
    config *Config,
    logger Logger,
) error {
    // 实现
}
```

### 缩进

```go
// ✅ 正确 - 使用 Tab 缩进
func main() {
    if true {
        fmt.Println("Hello")
    }
}

// ❌ 错误 - 使用空格缩进
func main() {
    if true {
        fmt.Println("Hello")
    }
}
```

## 空行使用

### 函数之间

```go
// ✅ 正确 - 函数之间有空行
func Function1() error {
    return nil
}

func Function2() error {
    return nil
}

// ❌ 错误 - 函数之间没有空行
func Function1() error {
    return nil
}
func Function2() error {
    return nil
}
```

### 逻辑块之间

```go
// ✅ 正确 - 逻辑块之间有空行
func Process() error {
    // 阶段 1
    err := step1()
    if err != nil {
        return err
    }

    // 阶段 2
    err = step2()
    if err != nil {
        return err
    }

    return nil
}
```

## 括号和空格

### 括号使用

```go
// ✅ 正确 - 适当的空格
if err != nil {
    return err
}

for i := 0; i < len(items); i++ {
    // 处理
}

// ❌ 错误 - 不必要的空格
if err != nil {
    return err
}

for i := 0; i < len(items); i++ {
    // 处理
}
```

### 运算符空格

```go
// ✅ 正确 - 运算符周围有空格
result := a + b
result = result * 2

// ❌ 错误 - 缺少空格
result := a+b
result = result*2
```

## 检查清单

提交代码前，确保：

- [ ] 代码已通过 `gofmt -w .` 格式化
- [ ] 代码已通过 `goimports -w .` 优化导入
- [ ] 所有导出类型和函数有注释
- [ ] 导入按标准库、第三方库、本地库分组
- [ ] 单行不超过 120 字符
- [ ] 使用 Tab 缩进，不使用空格
- [ ] 函数之间有空行
- [ ] 结构体字段按逻辑分组
- [ ] 没有未使用的导入
- [ ] 代码组织顺序正确（常量、变量、类型、接口、函数）
