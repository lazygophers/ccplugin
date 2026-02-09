---
name: lazygophers-validator-skills
description: lazygophers/utils validator 模块完整指南 - 结构体验证、自定义验证规则、国际化错误处理
---

# lazygophers/utils validator 模块完整指南

## 概述

`lazygophers/utils/validator` 是一个强大且灵活的 Go 语言数据验证库，提供结构体验证、自定义验证规则、国际化错误消息支持等功能。它基于 struct tag 进行声明式验证，支持链式验证规则，并提供丰富的内置验证器。

## 核心特性

- **结构体验证**: 通过 struct tag 定义验证规则
- **内置验证器**: 提供常用验证规则（required, email, url, min, max 等）
- **自定义验证器**: 支持注册自定义验证函数
- **国际化支持**: 支持多语言错误消息（中文、英文、日文等）
- **字段名称优先级**: 支持 JSON tag 和结构体字段名
- **错误处理**: 详细的验证错误信息，支持多种输出格式

## 架构设计

### 核心组件

```
validator/
├── validator.go          # 验证器主入口
├── engine.go             # 验证引擎核心
├── types.go              # 错误类型定义
├── options.go            # 配置选项
├── custom_validators.go  # 自定义验证器实现
├── locale.go             # 国际化配置
└── locale_*.go           # 各语言包（zh, en, ja, ko 等）
```

### 核心类型

#### 1. Validator 验证器

```go
type Validator struct {
    engine   *Engine           // 验证引擎
    locale   string            // 语言地区
    useJSON  bool              // 是否使用 JSON 字段名
    mu       sync.RWMutex      // 互斥锁
    messages map[string]string // 自定义翻译
}
```

**创建验证器实例**:

```go
// 使用默认配置
v, err := validator.New()

// 使用自定义配置
v, err := validator.New(
    validator.WithLocale("zh"),      // 设置中文
    validator.WithUseJSON(true),     // 使用 JSON 字段名
    validator.WithTranslations(map[string]string{
        "zh.custom_rule": "自定义错误消息",
    }),
)

// 使用配置对象
config := validator.Config{
    Locale:  "zh",
    UseJSON: true,
    Translations: map[string]string{
        "zh.mobile": "手机号格式不正确",
    },
}
v, err := validator.New(validator.WithConfig(config))
```

#### 2. Engine 验证引擎

```go
type Engine struct {
    validators    map[string]ValidatorFunc  // 验证器函数映射
    tagName       string                    // 验证标签名称（默认 "validate"）
    fieldNameFunc func(reflect.StructField) string  // 字段名解析函数
}
```

#### 3. FieldError 字段错误

```go
type FieldError struct {
    Field       string      // 字段名称（优先 JSON tag）
    Tag         string      // 验证标签
    Value       interface{} // 字段值
    Param       string      // 验证参数
    ActualTag   string      // 实际验证标签
    Namespace   string      // 完整命名空间
    StructField string      // 结构体字段路径
    Message     string      // 错误消息
}
```

#### 4. ValidationErrors 验证错误集合

```go
type ValidationErrors []*FieldError
```

**方法**:
- `First() *FieldError` - 获取第一个错误
- `FirstError() string` - 获取第一个错误消息
- `ByField(field string) *FieldError` - 根据字段名获取错误
- `HasField(field string) bool` - 检查是否包含指定字段的错误
- `Fields() []string` - 返回所有出错的字段名
- `Messages() []string` - 返回所有错误消息
- `ToMap() map[string]string` - 转换为字段名到错误消息的映射
- `ToDetailMap() map[string]map[string]interface{}` - 转换为详细错误信息
- `JSON() map[string]interface{}` - 返回 JSON 格式的错误信息
- `Filter(fn func(*FieldError) bool) ValidationErrors` - 过滤错误
- `ForField(field string) ValidationErrors` - 获取指定字段的所有错误
- `ForTag(tag string) ValidationErrors` - 获取指定标签的所有错误
- `Format(format string) string` - 格式化错误信息

## 内置验证器

### 基础验证器

| 验证器 | 描述 | 示例 |
|--------|------|------|
| `required` | 必填字段 | `validate:"required"` |
| `email` | 邮箱格式 | `validate:"email"` |
| `url` | URL 格式 | `validate:"url"` |
| `min=n` | 最小值/长度 | `validate:"min=5"` |
| `max=n` | 最大值/长度 | `validate:"max=100"` |
| `len=n` | 固定长度 | `validate:"len=11"` |
| `numeric` | 数字字符串 | `validate:"numeric"` |
| `alpha` | 纯字母 | `validate:"alpha"` |
| `alphanum` | 字母数字 | `validate:"alphanum"` |
| `eq=n` | 等于 | `validate:"eq=10"` |
| `ne=n` | 不等于 | `validate:"ne=0"` |

### 中国本地化验证器

| 验证器 | 描述 | 格式要求 |
|--------|------|----------|
| `mobile` | 手机号 | 1[3-9]开头的11位数字 |
| `idcard` | 身份证 | 15位或18位 |
| `bankcard` | 银行卡号 | 13-19位数字，Luhn算法验证 |
| `chinese_name` | 中文姓名 | 2-4个中文字符，可包含· |
| `strong_password` | 强密码 | 至少8位，包含大写、小写、数字、特殊字符中的3种 |

### 网络和技术验证器

| 验证器 | 描述 | 示例 |
|--------|------|------|
| `ipv4` | IPv4 地址 | `192.168.1.1` |
| `mac` | MAC 地址 | `00:1A:2B:3C:4D:5E` |
| `json` | JSON 格式 | `{"key":"value"}` |
| `uuid` | UUID 格式 | `550e8400-e29b-41d4-a716-446655440000` |

## 结构体验证

### 基本用法

```go
type User struct {
    Name     string `json:"name" validate:"required,min=2"`
    Email    string `json:"email" validate:"required,email"`
    Phone    string `json:"phone" validate:"mobile"`
    Age      int    `json:"age" validate:"gte=0,lte=150"`
    Password string `json:"password" validate:"strong_password"`
}

func main() {
    v, _ := validator.New(validator.WithLocale("zh"))

    user := User{
        Name:     "张三",
        Email:    "zhangsan@example.com",
        Phone:    "13812345678",
        Age:      25,
        Password: "MyPass123!",
    }

    err := v.Struct(user)
    if err != nil {
        // 处理验证错误
        validationErrors := err.(validator.ValidationErrors)
        fmt.Println(validationErrors.ToMap())
    }
}
```

### 验证规则组合

```go
type Product struct {
    Name        string  `json:"name" validate:"required,min=3,max=50"`
    Price       float64 `json:"price" validate:"required,gt=0"`
    Description string  `json:"description" validate:"max=500"`
    SKU         string  `json:"sku" validate:"required,alphanum,len=10"`
    Stock       int     `json:"stock" validate:"gte=0"`
}
```

### 嵌套结构体验证

```go
type Address struct {
    Province string `json:"province" validate:"required"`
    City     string `json:"city" validate:"required"`
    Detail   string `json:"detail" validate:"required,max=200"`
}

type User struct {
    Name    string  `json:"name" validate:"required"`
    Address Address `json:"address" validate:"required"` // 嵌套验证
}
```

## 单变量验证

使用 `Var` 方法验证单个变量：

```go
v, _ := validator.New()

// 验证手机号
err := v.Var("13812345678", "mobile")
if err != nil {
    fmt.Println("手机号格式错误")
}

// 验证邮箱
err = v.Var("test@example.com", "email")
if err != nil {
    fmt.Println("邮箱格式错误")
}

// 组合验证
err = v.Var("password123", "required,min=8,alphanum")
if err != nil {
    fmt.Println("密码不符合要求")
}
```

## 自定义验证器

### 注册自定义验证器

```go
v, _ := validator.New()

// 注册偶数验证器
err := v.RegisterValidation("even", func(fl validator.FieldLevel) bool {
    field := fl.Field()
    if field.Kind() != reflect.Int {
        return false
    }
    return field.Int()%2 == 0
})

// 使用自定义验证器
type Config struct {
    Port int `json:"port" validate:"even,gte=0,lte=65535"`
}
```

### 使用 WithCustomValidator 选项

```go
v, _ := validator.New(
    validator.WithCustomValidator("even_number", func(value interface{}) bool {
        if num, ok := value.(int); ok {
            return num%2 == 0
        }
        return false
    }),
)
```

### 复杂自定义验证器示例

```go
// 用户名验证器：4-20位字母数字下划线，必须以字母开头
v.RegisterValidation("username", func(fl validator.FieldLevel) bool {
    username := fl.Field().String()
    if len(username) < 4 || len(username) > 20 {
        return false
    }

    matched, _ := regexp.MatchString(`^[a-zA-Z][a-zA-Z0-9_]*$`, username)
    return matched
})

// 中国车牌号验证器
v.RegisterValidation("license_plate", func(fl validator.FieldLevel) bool {
    plate := fl.Field().String()
    // 普通车牌：省份简称(1汉字) + 字母(1) + 字母数字(5-6)
    matched, _ := regexp.MatchString(`^[\u4e00-\u9fa5][A-Z][A-Z0-9]{5,6}$`, plate)
    return matched
})

// 验证码验证器：6位数字
v.RegisterValidation("captcha", func(fl validator.FieldLevel) bool {
    captcha := fl.Field().String()
    matched, _ := regexp.MatchString(`^\d{6}$`, captcha)
    return matched
})
```

## 错误处理

### 错误类型判断

```go
err := v.Struct(user)
if err != nil {
    // 类型断言为 ValidationErrors
    if validationErrors, ok := err.(validator.ValidationErrors); ok {
        // 处理验证错误
        for _, fieldErr := range validationErrors {
            fmt.Printf("字段: %s, 标签: %s, 消息: %s\n",
                fieldErr.Field, fieldErr.Tag, fieldErr.Message)
        }
    }
}
```

### 错误信息提取

```go
err := v.Struct(user)
if err != nil {
    validationErrors := err.(validator.ValidationErrors)

    // 获取第一个错误
    firstErr := validationErrors.First()
    fmt.Println(firstErr.Error())

    // 获取第一个错误消息
    fmt.Println(validationErrors.FirstError())

    // 获取所有字段名
    fields := validationErrors.Fields()
    fmt.Println("出错字段:", fields)

    // 获取所有错误消息
    messages := validationErrors.Messages()
    fmt.Println("错误消息:", messages)

    // 转换为 map
    errMap := validationErrors.ToMap()
    for field, msg := range errMap {
        fmt.Printf("%s: %s\n", field, msg)
    }

    // 转换为详细 map
    detailMap := validationErrors.ToDetailMap()
    for field, detail := range detailMap {
        fmt.Printf("%s: %+v\n", field, detail)
    }

    // JSON 格式输出
    jsonOutput := validationErrors.JSON()
    jsonData, _ := json.Marshal(jsonOutput)
    fmt.Println(string(jsonData))
}
```

### 字段级错误查询

```go
err := v.Struct(user)
if err != nil {
    validationErrors := err.(validator.ValidationErrors)

    // 检查特定字段是否有错误
    if validationErrors.HasField("email") {
        emailErr := validationErrors.ByField("email")
        fmt.Println("邮箱错误:", emailErr.Message)
    }

    // 获取特定字段的所有错误
    nameErrors := validationErrors.ForField("name")
    for _, e := range nameErrors {
        fmt.Println("name 字段错误:", e.Message)
    }

    // 获取特定标签的所有错误
    requiredErrors := validationErrors.ForTag("required")
    fmt.Printf("有 %d 个必填字段错误\n", len(requiredErrors))
}
```

### 错误过滤

```go
err := v.Struct(user)
if err != nil {
    validationErrors := err.(validator.ValidationErrors)

    // 自定义过滤
    filteredErrors := validationErrors.Filter(func(err *validator.FieldError) bool {
        // 只保留 required 错误
        return err.Tag == "required"
    })

    // 格式化输出
    formatted := validationErrors.Format("{field}: {message}")
    fmt.Println(formatted)
}
```

## 国际化支持

### 设置语言

```go
// 创建中文验证器
zhV, _ := validator.New(validator.WithLocale("zh"))

// 创建英文验证器
enV, _ := validator.New(validator.WithLocale("en"))

// 动态切换语言
v, _ := validator.New()
v.SetLocale("zh")  // 切换到中文
v.SetLocale("en")  // 切换到英文
```

### 自定义翻译

```go
v, _ := validator.New(
    validator.WithTranslations(map[string]string{
        "zh.mobile":       "手机号格式不正确",
        "zh.idcard":       "身份证号码无效",
        "zh.strong_password": "密码强度不够",
        "en.mobile":       "Invalid mobile phone number",
        "en.idcard":       "Invalid ID card number",
    }),
)

// 或者动态注册翻译
v.RegisterTranslation("zh", "custom_rule", "自定义错误消息")
```

### 可用语言列表

```go
locales := validator.GetAvailableLocales()
fmt.Println("可用语言:", locales)
// 输出: [en zh zh-CN zh-TW ja ko fr es ar ru it pt de]
```

### 语言回退机制

当指定语言不存在时，自动回退到英文：

```go
// 使用不存在的语言
v, _ := validator.New(validator.WithLocale("unknown"))
// 错误消息会回退到英文
```

### 各语言错误消息示例

| 语言 | required | email | mobile |
|------|----------|-------|--------|
| en | {field} is required | {field} must be a valid email address | {field} must be a valid mobile phone number |
| zh | {field}不能为空 | {field}必须是有效的邮箱地址 | {field}必须是有效的手机号码 |
| zh-CN | {field}不能为空 | {field}必须是有效的邮箱地址 | {field}必须是有效的手机号码 |
| ja | {field}は必須です | {field}は有効なメールアドレスである必要があります | {field}は有効な携帯電話番号である必要があります |

## 字段名控制

### 使用 JSON 字段名（默认）

```go
v, _ := validator.New(validator.WithUseJSON(true))

type User struct {
    Name string `json:"user_name" validate:"required"`
}

user := User{Name: ""}
err := v.Struct(user)
validationErrors := err.(validator.ValidationErrors)
// 错误字段名为 "user_name"
```

### 使用结构体字段名

```go
v, _ := validator.New(validator.WithUseJSON(false))

type User struct {
    Name string `json:"user_name" validate:"required"`
}

user := User{Name: ""}
err := v.Struct(user)
validationErrors := err.(validator.ValidationErrors)
// 错误字段名为 "Name"
```

### 全局设置

```go
validator.SetUseJSON(true)  // 使用 JSON 字段名
validator.SetLocale("zh")   // 设置中文
```

## 高级用法

### 条件验证

```go
type Order struct {
    HasPayment bool    `json:"has_payment"`
    PaymentID  string  `json:"payment_id" validate:"required_if=HasPayment true"`
    Status     string  `json:"status" validate:"required_unless=HasPayment false"`
}
```

### 跨字段验证

```go
type User struct {
    Password        string `json:"password" validate:"required,min=8"`
    ConfirmPassword string `json:"confirm_password" validate:"required,eqfield=Password"`
}
```

### 字段排除

```go
type Form struct {
    TempField string `json:"temp_field" validate:"excluded_if=Step 1"`
    FinalData string `json:"final_data" validate:"required_without=TempField"`
}
```

### 动态验证规则

```go
// 根据环境动态设置验证规则
func getValidatorForEnv(env string) (*validator.Validator, error) {
    if env == "production" {
        return validator.New(
            validator.WithLocale("zh"),
            validator.WithUseJSON(true),
        )
    }
    return validator.New(validator.WithLocale("en"))
}
```

## API 响应集成

### JSON API 错误响应

```go
func handleCreateUser(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(400, gin.H{"error": "无效的请求参数"})
        return
    }

    v, _ := validator.New(validator.WithLocale("zh"))
    if err := v.Struct(user); err != nil {
        validationErrors := err.(validator.ValidationErrors)

        c.JSON(400, gin.H{
            "code":    400,
            "message": "参数验证失败",
            "errors":  validationErrors.ToMap(),
            "details": validationErrors.ToDetailMap(),
        })
        return
    }

    // 处理业务逻辑
}
```

### RESTful API 错误格式

```go
type ValidationErrorResponse struct {
    Code    int                    `json:"code"`
    Message string                 `json:"message"`
    Errors  map[string]string      `json:"errors"`
    Count   int                    `json:"count"`
}

func toValidationResponse(err error) ValidationErrorResponse {
    validationErrors := err.(validator.ValidationErrors)
    return ValidationResponse{
        Code:    400,
        Message: "Validation failed",
        Errors:  validationErrors.ToMap(),
        Count:   validationErrors.Len(),
    }
}
```

## 性能优化

### 复用验证器实例

```go
var globalValidator *validator.Validator

func init() {
    globalValidator, _ = validator.New(
        validator.WithLocale("zh"),
        validator.WithUseJSON(true),
    )
}

func validateUser(user *User) error {
    return globalValidator.Struct(user)
}
```

### 避免重复创建

```go
// ❌ 不推荐：每次都创建新验证器
func validateUser(user *User) error {
    v, _ := validator.New()
    return v.Struct(user)
}

// ✅ 推荐：复用全局验证器
var v, _ = validator.New()

func validateUser(user *User) error {
    return v.Struct(user)
}
```

### 并发安全

验证器是并发安全的，可以在多个 goroutine 中共享使用：

```go
v, _ := validator.New()

var wg sync.WaitGroup
for i := 0; i < 100; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        user := getUser()
        v.Struct(user)  // 并发安全
    }()
}
wg.Wait()
```

## 最佳实践

### 1. 结构体定义

```go
// ✅ 推荐：使用 JSON tag 和 validate tag
type User struct {
    Name     string `json:"name" validate:"required,min=2,max=50"`
    Email    string `json:"email" validate:"required,email"`
    Phone    string `json:"phone" validate:"omitempty,mobile"`
}

// ❌ 不推荐：缺少 JSON tag
type User struct {
    Name     string `validate:"required"`
    Email    string `validate:"required,email"`
}
```

### 2. 可选字段

使用 `omitempty` 或去掉 `required` 来表示可选字段：

```go
type Profile struct {
    Nickname    string `json:"nickname" validate:"omitempty,min=2,max=20"`
    Avatar      string `json:"avatar" validate:"omitempty,url"`
    Description string `json:"description" validate:"omitempty,max=500"`
}
```

### 3. 密码验证

```go
type RegisterRequest struct {
    Password string `json:"password" validate:"required,strong_password"`
}

// 强密码要求：
// - 至少 8 位
// - 包含大写字母、小写字母、数字、特殊字符中的至少 3 种
// 示例：MyPass123!, Complex1@
```

### 4. 错误处理

```go
func (h *UserHandler) CreateUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": "invalid request"})
        return
    }

    if err := h.validator.Struct(&req); err != nil {
        validationErrors := err.(validator.ValidationErrors)

        // 返回友好的错误信息
        c.JSON(400, gin.H{
            "error":  "validation failed",
            "fields": validationErrors.ToMap(),
        })
        return
    }

    // 业务逻辑
}
```

### 5. 验证器配置

```go
// 初始化全局验证器
func InitValidator() (*validator.Validator, error) {
    return validator.New(
        validator.WithLocale("zh"),
        validator.WithUseJSON(true),
        validator.WithTranslations(map[string]string{
            "zh.custom": "自定义验证错误",
        }),
    )
}
```

## 完整示例

### 用户注册验证

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/validator"
)

type RegisterRequest struct {
    Username string `json:"username" validate:"required,min=4,max=20,alphanum"`
    Email    string `json:"email" validate:"required,email"`
    Phone    string `json:"phone" validate:"required,mobile"`
    Password string `json:"password" validate:"required,strong_password"`
    IDCard   string `json:"id_card" validate:"required,idcard"`
}

func main() {
    v, err := validator.New(
        validator.WithLocale("zh"),
        validator.WithUseJSON(true),
    )
    if err != nil {
        panic(err)
    }

    // 测试有效数据
    validReq := RegisterRequest{
        Username: "zhangsan123",
        Email:    "zhangsan@example.com",
        Phone:    "13812345678",
        Password: "MyPass123!",
        IDCard:   "11010119800101123X",
    }

    err = v.Struct(validReq)
    if err != nil {
        fmt.Println("验证失败:", err)
    } else {
        fmt.Println("验证成功！")
    }

    // 测试无效数据
    invalidReq := RegisterRequest{
        Username: "zs",  // 太短
        Email:    "invalid-email",  // 格式错误
        Phone:    "123",  // 格式错误
        Password: "weak",  // 强度不够
        IDCard:   "invalid",  // 格式错误
    }

    err = v.Struct(invalidReq)
    if err != nil {
        validationErrors := err.(validator.ValidationErrors)
        fmt.Println("\n验证错误:")
        for field, msg := range validationErrors.ToMap() {
            fmt.Printf("  %s: %s\n", field, msg)
        }
    }
}
```

### API 集成示例

```go
package handlers

import (
    "github.com/gin-gonic/gin"
    "github.com/lazygophers/utils/validator"
)

type UserHandler struct {
    validator *validator.Validator
}

func NewUserHandler() *UserHandler {
    v, _ := validator.New(
        validator.WithLocale("zh"),
        validator.WithUseJSON(true),
    )
    return &UserHandler{validator: v}
}

type CreateUserRequest struct {
    Name     string `json:"name" validate:"required,min=2,max=50,chinese_name"`
    Email    string `json:"email" validate:"required,email"`
    Phone    string `json:"phone" validate:"required,mobile"`
    Password string `json:"password" validate:"required,strong_password"`
}

func (h *UserHandler) CreateUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": "无效的请求参数"})
        return
    }

    // 验证
    if err := h.validator.Struct(&req); err != nil {
        validationErrors := err.(validator.ValidationErrors)

        c.JSON(400, gin.H{
            "code":    400,
            "message": "参数验证失败",
            "errors":  validationErrors.ToMap(),
            "details": validationErrors.JSON(),
        })
        return
    }

    // 创建用户
    // ...

    c.JSON(200, gin.H{"message": "用户创建成功"})
}
```

## 错误消息参考

### 中文错误消息

| 验证器 | 错误消息 |
|--------|----------|
| required | {field}不能为空 |
| email | {field}必须是有效的邮箱地址 |
| mobile | {field}必须是有效的手机号码 |
| idcard | {field}必须是有效的身份证号码 |
| bankcard | {field}必须是有效的银行卡号 |
| chinese_name | {field}必须是有效的中文姓名 |
| strong_password | {field}必须是强密码（至少8位，包含大写字母、小写字母、数字和特殊字符） |
| min | {field}最小值为{param} |
| max | {field}最大值为{param} |

### 英文错误消息

| 验证器 | 错误消息 |
|--------|----------|
| required | {field} is required |
| email | {field} must be a valid email address |
| mobile | {field} must be a valid mobile phone number |
| url | {field} must be a valid URL |
| min | {field} must be at least {param} |
| max | {field} must be at most {param} |

## 注意事项

1. **空值处理**: 大多数验证器对空值返回 true，使用 `required` 来确保字段非空
2. **字段名优先级**: 默认使用 JSON tag，可通过 `WithUseJSON(false)` 改变
3. **并发安全**: 验证器实例是并发安全的，可以共享使用
4. **性能考虑**: 避免在循环中重复创建验证器，应该复用实例
5. **错误回退**: 指定语言不存在时自动回退到英文
6. **嵌套结构**: 自动递归验证嵌套的结构体字段
7. **自定义验证器**: 自定义验证器函数必须实现 `ValidatorFunc` 类型

## 参考资源

- **GitHub**: https://github.com/lazygophers/utils/tree/master/validator
- **文档**: 查看源码中的 `*_test.go` 文件获取更多示例
- **相关模块**:
  - `lazygophers-anyx` - 类型安全的 Map 操作
  - `lazygophers-xtime` - 时间处理工具
  - `lazygophers-config` - 配置管理
