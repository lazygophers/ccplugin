---
description: Go 错误处理强制规范：禁止单行 if err、必须记录日志（lazygophers/log 或 slog）、禁止包装错误、errors.Join 聚合、sentinel errors 模式。处理错误时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 错误处理规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）
- **debug** - 调试专家

## 相关 Skills

| 场景     | Skill                    | 说明                         |
| -------- | ------------------------ | ---------------------------- |
| 核心规范 | Skills(golang:core)      | 核心规范：强制约定、代码格式 |
| 工具库   | Skills(golang:libs)      | 优先库规范：lazygophers/log  |
| 并发错误 | Skills(golang:concurrency) | errgroup 错误处理          |

## 核心原则

### 必须遵守

1. **多行处理** - 所有 error 必须多行处理，记录日志
2. **统一日志** - 使用 `log.Errorf("err:%v", err)` 统一格式
3. **不包装** - 禁止使用 `fmt.Errorf`/`errors.Wrap`/`errors.Wrapf` 包装，直接返回原始错误
4. **初始化** - 初始化中使用 `log.Fatalf` 而非 `panic`

### 禁止行为

- 单行 if 处理：`if err != nil { return err }`
- if 条件中声明变量：`if err := eg.Wait(); err != nil { return err }`
- 忽略错误：`_, _ := ...`
- 包装 error：`fmt.Errorf("...: %w", err)`
- 无日志错误处理
- 使用 panic/recover 处理业务错误

## 标准错误处理模式

### 基本模式（强制）

```go
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
```

### 错误接收与判断分离（强制）

```go
err = eg.Wait()
if err != nil {
    log.Errorf("err:%v", err)
    return err
}
```

### errors.Join 聚合多个错误（Go 1.20+）

当需要收集多个错误时使用 errors.Join：

```go
var errs []error
for _, item := range items {
    err := processItem(item)
    if err != nil {
        log.Errorf("err:%v", err)
        errs = append(errs, err)
    }
}
if len(errs) > 0 {
    return errors.Join(errs...)
}
```

### Sentinel Errors 定义

```go
var (
    ErrNotFound   = errors.New("not found")
    ErrForbidden  = errors.New("forbidden")
    ErrBadRequest = errors.New("bad request")
)
```

### 错误判断方式

```go
// 直接比较
if err == ErrNotFound {
    return nil, err
}

// 项目自定义错误码
if xerror.CheckCode(err, CodeNotFound) {
    return nil, err
}

// 类型检查函数
if IsNotFoundErr(err) {
    return nil, err
}
```

### Defer 和错误处理

```go
file, err := os.Open(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
defer file.Close()
```

## 日志规范

### 使用 lazygophers/log（已有项目）

```go
import "github.com/lazygophers/log"

log.Infof("user registered: %s", username)
log.Warnf("cache miss for key: %s", key)
log.Errorf("err:%v", err)
log.Fatalf("failed to load config: %v", err)
```

### 使用 slog（Go 1.21+ 新项目推荐）

```go
import "log/slog"

slog.Info("user registered", "username", name, "email", email)
slog.Warn("cache miss", "key", key)
slog.Error("operation failed", "err", err, "user_id", uid)
```

## 初始化中的错误处理

```go
func init() {
    config, err := loadConfig()
    if err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("failed to load config")
    }
}
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "单行 if err 更简洁" | 是否所有 error 多行处理？ | 高 |
| "fmt.Errorf 加上下文更好" | 是否禁止包装，直接返回原始错误？ | 高 |
| "errors.Is/As 更现代" | 是否使用项目规定的错误判断方式？ | 中 |
| "panic 快速失败更好" | 是否使用 log.Fatalf 而非 panic？ | 高 |
| "err 日志太多了" | 是否每个错误点都有日志？ | 高 |
| "logrus/zap 更强大" | 是否使用 lazygophers/log 或 slog？ | 中 |

## 检查清单

- [ ] 所有 error 多行处理
- [ ] 所有 error 记录日志
- [ ] 使用 `log.Errorf("err:%v", err)` 统一格式
- [ ] 没有 fmt.Errorf 包装错误
- [ ] 没有 errors.Wrap 包装错误
- [ ] 没有单行 if err 语句
- [ ] 没有 if 条件中声明变量
- [ ] 没有 panic/recover 处理业务错误
- [ ] 多错误聚合使用 errors.Join
- [ ] sentinel errors 使用 errors.New 定义
