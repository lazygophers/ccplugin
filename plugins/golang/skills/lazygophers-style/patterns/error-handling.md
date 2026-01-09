# Lazygophers 错误处理规范

## 核心原则

### ✅ 必须遵守

1. **多行处理** - 所有 error 必须多行处理，记录日志
2. **统一日志** - 使用 `log.Errorf("err:%v", err)` 统一格式
3. **不包装** - 禁止使用 `fmt.Errorf` 包装，直接返回原始错误
4. **错误判断** - 使用 `errors.Is/As` 判断错误类型（Go 1.13+）
5. **初始化** - 初始化中使用 `log.Fatalf` 而非 `panic`

### ❌ 禁止行为

- 单行 if 处理：`if err != nil { return err }`
- 忽略错误：`_, _ := ...`
- 包装 error：`fmt.Errorf("...: %w", err)`
- 无日志错误处理
- 使用 panic/recover 处理业务错误
- 包装错误多次

## 标准错误处理模式

### 基本模式（强制）

```go
// ✅ 必须 - 多行处理 + 日志
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}

// ✅ 返回原始错误（不包装）
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ❌ 禁止 - 单行
if err != nil { return nil, err }

// ❌ 禁止 - 无日志
if err != nil { return nil, err }

// ❌ 禁止 - 包装
if err != nil {
    return nil, fmt.Errorf("read file: %w", err)  // 不要包装
}
```

### 错误类型判断

```go
// ✅ 使用 errors.Is（推荐，Go 1.13+）
import "errors"

if errors.Is(err, os.ErrNotExist) {
    // 处理文件不存在
    log.Warnf("file not found: %s", path)
    return nil, err
}

// ✅ 使用 errors.As 获取错误详情
var exitErr *exec.ExitError
if errors.As(err, &exitErr) {
    // 处理 ExitError
    log.Errorf("command failed with exit code %d", exitErr.ExitCode())
    return exitErr
}
```

### Defer 和错误处理

```go
// ✅ 简单关闭不检查
file, err := os.Open(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
defer file.Close()

// ✅ 复杂操作在 defer 中检查
if err := conn.Close(); err != nil {
    log.Errorf("err:%v", err)
}
```

## 自定义错误类型

### 定义（参考 Linky xerror 模式）

```go
// ✅ 导出的错误类型
type ValidationError struct {
    Field   string
    Message string
    Code    int32  // 错误码
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error in field %q: %s (code: %d)", e.Field, e.Message, e.Code)
}

// ✅ 实现 Unwrap 支持错误链
func (e *ValidationError) Unwrap() error {
    return nil  // 或返回嵌套的错误
}

// ✅ 错误构造函数
func NewValidationError(field, message string, code int32) *ValidationError {
    return &ValidationError{
        Field:   field,
        Message: message,
        Code:    code,
    }
}
```

### 使用自定义错误

```go
// ✅ 创建自定义错误
if email == "" {
    err := NewValidationError("email", "email cannot be empty", 400)
    log.Errorf("err:%v", err)
    return nil, err
}

// ✅ 检查自定义错误
var valErr *ValidationError
if errors.As(err, &valErr) {
    log.Warnf("validation failed: field=%s, code=%d", valErr.Field, valErr.Code)
    return err
}
```

## Linky 服务器错误处理模式

### 错误码管理（参考 Linky）

```go
// ✅ 统一的错误码定义
const (
    CodeSuccess           int32 = 0
    CodeBadRequest        int32 = 400
    CodeUnauthorized      int32 = 401
    CodeForbidden         int32 = 403
    CodeNotFound          int32 = 404
    CodeInternalError     int32 = 500
    CodeServiceUnavailable int32 = 503
)

// ✅ 错误类型包含错误码
type AppError struct {
    Code    int32
    Message string
    Err     error  // 原始错误
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}
```

### 中间件错误处理（参考 Linky 中间件链）

```go
// ✅ 错误处理中间件
type Handler func(ctx *fiber.Ctx) error

func ErrorHandler(h Handler) Handler {
    return func(ctx *fiber.Ctx) error {
        err := h(ctx)
        if err != nil {
            log.Errorf("err:%v", err)
            return handleError(ctx, err)
        }
        return nil
    }
}

// ✅ 集中错误处理
func handleError(ctx *fiber.Ctx, err error) error {
    var appErr *AppError
    if errors.As(err, &appErr) {
        return ctx.Status(int(appErr.Code)).JSON(fiber.Map{
            "code":    appErr.Code,
            "message": appErr.Message,
        })
    }

    // 未知错误
    log.Errorf("unhandled error: %v", err)
    return ctx.Status(500).JSON(fiber.Map{
        "code":    CodeInternalError,
        "message": "Internal Server Error",
    })
}
```

## 日志规范

### 日志级别和格式（Linky 风格）

```go
import "github.com/lazygophers/log"

// ✅ Info - 正常流程信息
log.Infof("user registered: %s", username)
log.Infof("loading config from %s", configPath)

// ✅ Warn - 警告（不影响功能）
log.Warnf("cache miss for key: %s", key)
log.Warnf("config file not found, using defaults")

// ✅ Error - 错误（功能异常）
log.Errorf("err:%v", err)  // 统一格式
log.Errorf("failed to save user: %v", err)

// ✅ Fatal - 致命错误（程序无法继续）
log.Fatalf("failed to load config: %v", err)
```

### 统一的错误日志格式

```go
// ✅ 简洁统一的错误格式
if err != nil {
    log.Errorf("err:%v", err)  // 所有错误使用统一格式
    return err
}

// ✅ 需要更多上下文时
if err != nil {
    log.Errorf("failed to create user (email=%s): %v", email, err)
    return err
}

// ✅ 包含操作上下文
if err != nil {
    log.Errorf("process file %q (size=%d): %v", filepath, size, err)
    return err
}
```

## 初始化中的错误处理

### Init 或 Main 中

```go
// ✅ 初始化中使用 Fatal
func init() {
    config, err := loadConfig()
    if err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("failed to load config")
    }
}

// ✅ 启动流程中（参考 Linky 三阶段启动）
func Run() error {
    // 阶段 1：加载状态
    if err := state.Load(); err != nil {
        log.Errorf("err:%v", err)
        return fmt.Errorf("load state: %v", err)  // 仅在 Run 中返回
    }

    // 阶段 2：初始化管理员
    if err := InitDefaultAdmin(); err != nil {
        log.Errorf("err:%v", err)
        return fmt.Errorf("init admin: %v", err)
    }

    // 阶段 3：启动应用
    return app.Run()
}
```

## 最佳实践

### 1. 错误即不稳定因素

```go
// ✅ 接受错误可能发生
results, err := processItems(items)
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ❌ 假设不出错
results := processItems(items)  // 假设成功
```

### 2. 清晰的错误含义

```go
// ✅ 提供足够的上下文
if len(password) < 8 {
    err := NewValidationError("password", "password must be at least 8 characters", CodeBadRequest)
    log.Errorf("err:%v", err)
    return nil, err
}

// ❌ 含义不清
if len(password) < 8 {
    return nil, errors.New("invalid")
}
```

### 3. 成对处理

```go
// ✅ 日志 + 返回成对
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)     // 日志
    return nil, err                // 返回
}

// ❌ 只返回不日志
data, err := os.ReadFile(path)
if err != nil {
    return nil, err  // 无日志
}
```

## 参考

- [Go 1.13 Error Wrapping](https://golang.org/doc/go1.13#error_wrapping)
- [errors Package](https://golang.org/pkg/errors/)
- [Linky Server 参考](../references.md)
