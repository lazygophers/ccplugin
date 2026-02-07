# Golang 错误处理规范

## 核心原则

### ✅ 必须遵守

1. **多行处理** - 所有 error 必须多行处理，记录日志
2. **统一日志** - 使用 `log.Errorf("err:%v", err)` 统一格式
3. **不包装** - 禁止使用 `fmt.Errorf`/`errors.Wrap`/`errors.Wrapf` 包装，直接返回原始错误
4. **错误判断** - 使用 `errors.Is/As` 判断错误类型（Go 1.13+）
5. **初始化** - 初始化中使用 `log.Fatalf` 而非 `panic`

### ❌ 禁止行为

- 单行 if 处理：`if err != nil { return err }`
- if 条件中声明变量：`if err := eg.Wait(); err != nil { return err }`
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
    return nil, fmt.Errorf("read file: %w", err)
}
```

### 错误接收与判断分离（强制）

```go
// ✅ 必须 - 错误接收与判断分开
err = eg.Wait()
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ✅ 必须 - 错误接收与判断分开
err = conn.Close()
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ❌ 禁止 - if 条件中声明变量
if err := eg.Wait(); err != nil {
    log.Errorf("err:%s", err)
    return err
}

// ❌ 禁止 - if 条件中声明变量
if err := conn.Close(); err != nil {
    log.Errorf("err:%v", err)
    return err
}
```

### 错误变量作用域说明

```go
// ✅ 正确 - 错误变量在外部声明
var err error
data, err := fetchData()
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}

// ✅ 正确 - 使用短变量声明
data, err := fetchData()
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}

// ❌ 错误 - if 条件中声明变量导致作用域受限
if data, err := fetchData(); err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
// data 在这里无法访问
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
err := conn.Close()
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
```

## 服务器错误处理模式

### 错误码管理

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
```

### 中间件错误处理

```go
// ✅ 错误处理中间件
type Handler func(ctx *fiber.Ctx) error

func ErrorHandler(ctx *fiber.Ctx) error {
    err := ctx.Next(ctx)
    if err != nil {
        log.Errorf("err:%v", err)
        return handleError(ctx, err)
    }
    return nil
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

### 日志级别和格式

```go
import "github.com/lazygophers/log"

// ✅ Info - 正常流程信息
log.Infof("user registered: %s", username)
log.Infof("loading config from %s", configPath)

// ✅ Warn - 警告（不影响功能）
log.Warnf("cache miss for key: %s", key)
log.Warnf("config file not found, using defaults")

// ✅ Error - 错误（功能异常）
log.Errorf("err:%v", err)
log.Errorf("failed to save user: %v", err)

// ✅ Fatal - 致命错误（程序无法继续）
log.Fatalf("failed to load config: %v", err)
```

### 统一的错误日志格式

```go
// ✅ 简洁统一的错误格式
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ❌ 禁止 - 需要更多上下文时
if err != nil {
    log.Errorf("failed to create user (email=%s): %v", email, err)
    return err
}

// ❌ 禁止 - 包含操作上下文
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

// ✅ 启动流程中
func Run() error {
    // 阶段 1：加载状态
    err := state.Load()
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // 阶段 2：初始化管理员
    err = InitDefaultAdmin()
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    // 阶段 3：启动应用
    err = app.Run()
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }

    return nil
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
results := processItems(items)
```

### 2. 清晰的错误含义

```go
// ✅ 提供足够的上下文
if len(password) < 8 {
    log.Errorf("password must be at least 8 characters")
    return nil, NewValidationError("password must be at least 8 characters")
}

// ❌ 含义不清
if len(password) < 8 {
    return nil, errors.New("invalid")
}

// ❌ 为了日志定义错误
if len(password) < 8 {
    err := NewValidationError("password", "password must be at least 8 characters", CodeBadRequest)
    log.Errorf("err:%v", err)
    return nil, err
}
```

### 3. 成对处理

```go
// ✅ 日志 + 返回成对
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}

// ❌ 只返回不日志
data, err := os.ReadFile(path)
if err != nil {
    return nil, err
}
```
