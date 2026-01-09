# Golang 错误处理规范

## 核心原则

### ✅ 必须遵守

1. **显式处理每个错误** - 禁止忽略任何错误，即使是 `io.Closer`
2. **多行处理** - 错误处理必须占据多行，便于阅读和维护
3. **统一日志记录** - 所有错误必须通过日志记录
4. **清晰的错误链** - 使用 `%w` 包装保留原始错误信息
5. **不重复包装** - 最多包装一次，避免嵌套 `fmt.Errorf`

### ❌ 禁止行为

- 单行 if err 处理：`if err != nil { return err }`
- 忽略错误：`_, _ := ioutil.ReadFile(path)`
- 多次包装：`fmt.Errorf("level1: %w", fmt.Errorf("level2: %w", err))`
- 无日志错误处理
- Panic/recover 处理业务错误

## 标准错误处理模式

### 基本模式

```go
// ✅ 正确
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("read file failed: %v", err)
    return nil, err
}

// ❌ 错误 - 单行
if err != nil { return nil, err }

// ❌ 错误 - 无日志
if err != nil { return nil, err }
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
}
```

### 错误包装

```go
// ✅ 包装一次，保留原始错误
if err != nil {
    return nil, fmt.Errorf("parse config: %w", err)
}

// ✅ 返回原始错误（不需要额外信息时）
if err != nil {
    log.Errorf("db error: %v", err)
    return nil, err
}

// ❌ 不要多次包装
if err != nil {
    return nil, fmt.Errorf("level1: %w", fmt.Errorf("level2: %w", err))
}

// ❌ 不要丢失原始错误
if err != nil {
    return nil, fmt.Errorf("something went wrong")  // 无法追踪原因
}
```

### Defer 与错误处理

```go
// ✅ 简单关闭不检查
file, err := os.Open(path)
if err != nil {
    return nil, err
}
defer file.Close()

// ✅ 复杂操作才检查
conn, err := db.Connect()
if err != nil {
    return nil, err
}
defer func() {
    if err := conn.Close(); err != nil {
        log.Errorf("close connection failed: %v", err)
    }
}()
```

## 自定义错误类型

### 定义

```go
// ✅ 导出的错误类型
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error in field %q: %s", e.Field, e.Message)
}

// ✅ 实现 Unwrap 支持错误链
func (e *ValidationError) Unwrap() error {
    return nil  // 或返回嵌套的错误
}
```

### 使用

```go
// ✅ 创建自定义错误
if email == "" {
    return nil, &ValidationError{
        Field:   "email",
        Message: "email cannot be empty",
    }
}

// ✅ 检查自定义错误
var valErr *ValidationError
if errors.As(err, &valErr) {
    log.Warnf("validation failed for field %q: %s", valErr.Field, valErr.Message)
}
```

## 错误日志规范

### 日志级别

```go
import "log"

// Info - 正常流程信息
log.Infof("user registered: %s", username)

// Warn - 警告（不影响功能，但需要注意）
log.Warnf("cache miss for key: %s", key)

// Error - 错误（功能异常）
log.Errorf("database error: %v", err)

// Fatal - 致命错误（程序无法继续）
log.Fatalf("failed to load config: %v", err)
```

### 日志格式

```go
// ✅ 统一的错误格式
if err != nil {
    log.Errorf("err:%v", err)  // 简洁统一
}

// ✅ 需要更多信息时
if err != nil {
    log.Errorf("failed to update user (id=%d): %v", userID, err)
}

// ✅ 添加操作上下文
if err != nil {
    log.Errorf("create file %q failed: %v", filepath, err)
}
```

## 初始化中的错误处理

```go
// ✅ init 或 main 中使用 Fatal
func init() {
    config, err := loadConfig()
    if err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("failed to load config")
    }
}

// ✅ 启动流程中的错误
func Run() error {
    db, err := connectDB()
    if err != nil {
        log.Errorf("err:%v", err)
        return fmt.Errorf("connect database: %w", err)
    }
    // ...
}
```

## 最佳实践

### 1. 错误即不稳定因素

```go
// ✅ 接受错误可能发生
results, err := processItems(items)
if err != nil {
    // 记录、处理、返回或恢复
}

// ❌ 假设不出错
results := processItems(items)  // 忽略可能的错误
```

### 2. 清晰的错误含义

```go
// ✅ 提供足够的上下文
if len(password) < 8 {
    return nil, &ValidationError{
        Field:   "password",
        Message: "password must be at least 8 characters",
    }
}

// ❌ 含义不清
if len(password) < 8 {
    return nil, fmt.Errorf("invalid")
}
```

### 3. 区分临时错误和永久错误

```go
// ✅ 标记可重试的错误
type RetryableError struct {
    Err       error
    RetryableErr bool
}

func (e *RetryableError) Temporary() bool { return e.RetryableErr }

// 使用
if err != nil {
    if te, ok := err.(interface{ Temporary() bool }); ok && te.Temporary() {
        // 可以重试
    }
}
```

## 参考

- [Effective Go - Error handling](https://golang.org/doc/effective_go#errors)
- [Go 1.13+ Error Wrapping](https://golang.org/doc/effective_go#errors)
- [Linky Server 错误处理](../../../examples/error-handling-example.go)
