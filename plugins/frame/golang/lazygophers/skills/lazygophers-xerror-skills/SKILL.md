---
name: lazygophers-xerror-skills
description: lrpc xerror 错误处理中间件规范 - 提供统一的错误码定义、错误响应格式化和错误堆栈追踪
---

# lazygophers-xerror - 错误处理中间件

提供统一的错误处理机制，包括错误码定义、错误响应格式化和错误堆栈追踪。

## 特性

- 🎯 **统一错误码** - 标准化的错误码体系
- 📋 **错误响应格式** - 一致的错误响应结构
- 🔍 **堆栈追踪** - 详细的错误堆栈信息
- 🌐 **多语言错误消息** - 结合 i18n 支持多语言
- 📊 **错误日志** - 自动记录错误日志
- 🔄 **可扩展** - 支持自定义错误类型

## 基础使用

### 初始化中间件

```go
import (
    "github.com/lazygophers/lrpc"
    "github.com/lazygophers/lrpc/middleware/xerror"
)

// 创建 xerror 中间件
errorMiddleware := xerror.New(
    xerror.WithDebugMode(true),        // 开发模式显示堆栈
    xerror.WithDefaultCode(500),       // 默认错误码
    xerror.WithLogErrors(true),        // 记录错误日志
)

server := lrpc.NewServer()
server.Use(errorMiddleware)
```

### 标准错误响应格式

```json
{
  "error": {
    "code": 10001,
    "message": "用户不存在",
    "details": "User ID 123 not found",
    "request_id": "req-abc123",
    "stack": "..."  // 仅开发模式
  }
}
```

## 错误码定义

### 预定义错误码

```go
const (
    // 通用错误 1xxxx
    CodeSuccess           = 0     // 成功
    CodeInvalidParams     = 10001 // 参数错误
    CodeUnauthorized      = 10002 // 未授权
    CodeForbidden         = 10003 // 禁止访问
    CodeNotFound          = 10004 // 资源不存在
    CodeInternalError     = 10005 // 内部错误
    CodeServiceUnavailable = 10006 // 服务不可用

    // 用户错误 2xxxx
    CodeUserNotFound      = 20001 // 用户不存在
    CodeUserExists        = 20002 // 用户已存在
    CodeInvalidPassword   = 20003 // 密码错误
    CodeTokenExpired      = 20004 // Token 过期

    // 业务错误 3xxxx
    CodeInsufficientBalance = 30001 // 余额不足
    CodeOrderExpired         = 30002 // 订单过期
)
```

### 创建自定义错误

```go
import "github.com/lazygophers/lrpc/middleware/xerror"

// 简单错误
err := xerror.Error(CodeNotFound, "User not found")

// 带详情的错误
err := xerror.ErrorDetails(CodeInvalidParams, "Validation failed",
    "email: invalid format",
    "age: must be positive",
)

// 带上下文的错误
err := xerror.Errorf(CodeUserNotFound, "user %s not found", userID)
```

### 错误类型

```go
// 业务错误（返回给客户端）
type BusinessError struct {
    Code    int
    Message string
    Details []string
}

// 系统错误（记录日志，返回通用消息）
type SystemError struct {
    Err     error
    Message string
    Stack   string
}
```

## 在 Handler 中使用

### 返回错误

```go
func GetUser(ctx *lrpc.Context) error {
    userID := ctx.Param("id")

    user, err := db.GetUser(userID)
    if err != nil {
        if errors.Is(err, db.ErrNotFound) {
            // 返回业务错误
            return xerror.Error(CodeUserNotFound, "User not found")
        }
        // 返回系统错误
        return xerror.Wrap(err, CodeInternalError, "Database error")
    }

    return ctx.JSON(user)
}
```

### 错误处理流程

```go
func Handler(ctx *lrpc.Context) error {
    // 1. 参数验证
    if err := validateInput(ctx); err != nil {
        return xerror.Error(CodeInvalidParams, err.Error())
    }

    // 2. 业务逻辑
    result, err := doSomething()
    if err != nil {
        // 判断错误类型
        if bizErr, ok := err.(*xerror.BusinessError); ok {
            return bizErr
        }
        // 包装系统错误
        return xerror.Wrap(err, CodeInternalError, "Operation failed")
    }

    return ctx.JSON(result)
}
```

## 错误响应

### 成功响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "John"
  }
}
```

### 错误响应

```json
{
  "code": 10001,
  "message": "参数错误",
  "error": {
    "code": 10001,
    "message": "参数错误",
    "details": [
      "email: 必填字段",
      "age: 必须大于0"
    ],
    "request_id": "req-abc123"
  }
}
```

### 开发模式响应

```json
{
  "code": 10005,
  "message": "内部错误",
  "error": {
    "code": 10005,
    "message": "内部错误",
    "stack": "goroutine 17 [running]:\ngithub.com/...",
    "request_id": "req-abc123"
  }
}
```

## 高级功能

### 错误日志

```go
// 自动记录错误日志
errorMiddleware := xerror.New(
    xerror.WithLogErrors(true),
    xerror.WithLogger(logger),
)

// 自定义日志格式
errorMiddleware := xerror.New(
    xerror.WithLogFunc(func(ctx *lrpc.Context, err error) {
        logger.Error("request error",
            log.Field("path", ctx.Path()),
            log.Field("method", ctx.Method()),
            log.Field("error", err),
            log.Field("request_id", getRequestID(ctx)),
        )
    }),
)
```

### 错误监控

```go
// 集成监控系统
errorMiddleware := xerror.New(
    xerror.WithOnError(func(ctx *lrpc.Context, err error) {
        // 上报错误到监控系统
        metrics.ReportError(err)
        // 发送告警
        alerts.SendAlert(err)
    }),
)
```

### 多语言错误消息

```go
// 结合 i18n 中间件
err := xerror.ErrorT(ctx, CodeUserNotFound, "errors.user_not_found")

// 在翻译文件中定义
// locales/en.json: {"errors": {"user_not_found": "User not found"}}
// locales/zh-CN.json: {"errors": {"user_not_found": "用户不存在"}}
```

## 错误码规范

### 错误码分段

| 范围 | 类型 | 说明 |
|------|------|------|
| 0 | 成功 | 请求成功 |
| 1xxxx | 通用错误 | 参数、认证、权限等 |
| 2xxxx | 用户错误 | 用户相关错误 |
| 3xxxx | 业务错误 | 业务逻辑错误 |
| 4xxxx | 第三方错误 | 外部服务错误 |
| 5xxxx | 系统错误 | 服务器内部错误 |

### 错误码注册

```go
// 定义错误码常量
const (
    CodeOrderNotFound = 31001
    CodeOrderExpired  = 31002
    CodeOrderPaid     = 31003
)

// 注册错误码描述
var errorMessages = map[int]string{
    CodeOrderNotFound: "订单不存在",
    CodeOrderExpired:  "订单已过期",
    CodeOrderPaid:     "订单已支付",
}
```

## 最佳实践

### 1. 错误处理层级

```go
// ✅ 分层错误处理
func Service() error {
    if err := repository.DoSomething(); err != nil {
        return xerror.Wrap(err, CodeInternalError, "Service failed")
    }
    return nil
}

// ❌ 直接返回底层错误
func Service() error {
    return repository.DoSomething()
}
```

### 2. 错误上下文

```go
// ✅ 添加错误上下文
return xerror.Wrap(err, CodeInternalError,
    "Failed to create user",
    "email", user.Email,
)

// ❌ 丢失原始错误
return xerror.Error(CodeInternalError, "Failed")
```

### 3. 客户端友好

```go
// ✅ 返回客户端可理解的错误
if !user.IsActive() {
    return xerror.Error(CodeUserInactive,
        "Account is inactive. Please contact support.")
}

// ❌ 返回技术细节
return xerror.Error(CodeUserInactive,
    "user.active flag is false in database")
```

### 4. 错误恢复

```go
// 结合 recovery 中间件
server.Use(
    xerror.New(),      // 1. 先注册错误处理
    recover.New(),     // 2. 然后 panic 恢复
)
```

## 常见错误模式

### 参数验证错误

```go
func ValidateUser(user *User) error {
    if user.Email == "" {
        return xerror.Error(CodeInvalidParams, "email is required")
    }
    if user.Age < 0 {
        return xerror.Error(CodeInvalidParams, "age must be positive")
    }
    return nil
}
```

### 数据库错误

```go
func GetUser(id int) (*User, error) {
    user, err := db.QueryUser(id)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, xerror.Error(CodeUserNotFound, "user not found")
        }
        return nil, xerror.Wrap(err, CodeInternalError, "database error")
    }
    return user, nil
}
```

### 第三方服务错误

```go
func CallExternalAPI() error {
    resp, err := httpClient.Post(url, body)
    if err != nil {
        return xerror.Wrap(err, CodeExternalServiceError,
            "external service unavailable")
    }
    if resp.StatusCode != 200 {
        return xerror.Error(CodeExternalServiceError,
            fmt.Sprintf("external service returned %d", resp.StatusCode))
    }
    return nil
}
```

## 参考资源

- [lazygophers/lrpc xerror](https://github.com/lazygophers/lrpc/tree/master/middleware/xerror)
- [Go 错误处理最佳实践](https://go.dev/doc/effective_go#errors)
