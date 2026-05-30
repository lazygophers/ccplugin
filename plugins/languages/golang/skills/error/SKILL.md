---
name: golang-error
description: Go 错误处理规范——禁止单行 if err、必须记录日志（lazygophers/log 或 slog）、禁止包装错误、errors.Join 聚合、sentinel error 模式、初始化用 log.Fatalf、参数校验用 validate tag 禁手写 if。处理 Go error、写 if err 块、设计错误类型、做参数校验时触发。
---

# Go 错误处理规范

## 四条硬约束

1. **多行处理**：每个 error 必须独立 `if err != nil {}` 块，禁单行。
2. **记录日志**：所有错误进入处理分支前 `log.Errorf("err:%v", err)`。
3. **禁止包装**：不用 `fmt.Errorf("%w", err)`、不用 `errors.Wrap`，直接返回原始 err。
4. **初始化用 `log.Fatalf`**：`init()` 或启动期失败用 Fatalf，不用 panic。

## 强制模式

### 基本（必用）

```go
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
```

### 接收与判断分离（必用）

```go
err = eg.Wait()
if err != nil {
    log.Errorf("err:%v", err)
    return err
}
```

不写 `if err := eg.Wait(); err != nil {}`，错误变量必须显式赋值后判断。

### errors.Join 聚合（Go 1.20+）

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

### Sentinel error

```go
var (
    ErrNotFound   = errors.New("not found")
    ErrForbidden  = errors.New("forbidden")
    ErrBadRequest = errors.New("bad request")
)
```

判断方式（按项目约定择一）：

```go
// 直接比较 sentinel
if err == ErrNotFound { return nil, err }

// 自定义错误码
if xerror.CheckCode(err, CodeNotFound) { return nil, err }

// 类型判定函数
if IsNotFoundErr(err) { return nil, err }
```

### defer 释放与错误处理共存

```go
file, err := os.Open(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
defer file.Close()
```

## 日志选择

## 参数校验（validate tag）

```go
type AddUserReq struct {
    Username string `json:"username" validate:"required"`
    Email    string `json:"email" validate:"required,email"`
    Age      uint8  `json:"age" validate:"gte=0"`
}
```

- 用 `validate` tag 声明约束，校验器在中间件/拦截层统一执行
- **禁手写** `if req.X == ""` / `if req.Y == 0` / `if req.Z == nil` 校验
- Update 场景全字段 unconditional 赋值，禁零值跳过逻辑
- 禁 `strings.TrimSpace` 预处理请求字段

## 日志选择（lazygophers/log 或 slog）

### lazygophers/log（已有项目）

```go
import "github.com/lazygophers/log"

log.Infof("user registered: %s", username)
log.Warnf("cache miss for key: %s", key)
log.Errorf("err:%v", err)
log.Fatalf("failed to load config: %v", err)
```

### slog（Go 1.21+ 新项目推荐）

```go
import "log/slog"

slog.Info("user registered", "username", name)
slog.Error("operation failed", "err", err, "user_id", uid)
```

slog 在 2026 已是事实标准（go-test-coverage、service observability 主流）。新仓库优先用 slog + JSON handler。

## 初始化中的错误

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

| AI 借口 | 实际应验证 |
| --- | --- |
| "单行 if err 更简洁" | 所有 error 多行？ |
| "fmt.Errorf 加上下文更好" | 禁止包装、直接 return？ |
| "errors.Is/As 更现代" | 用项目约定的判断方式？ |
| "panic 快速失败" | 业务用 return error、初始化用 Fatalf？ |
| "日志太多了" | 每个 error 分支都有日志？ |
| "logrus/zap 更强" | 用 lazygophers/log 或 slog？ |

## 检查清单

- [ ] 每处 error 多行处理
- [ ] 每处 error 有日志
- [ ] 统一 `log.Errorf("err:%v", err)` 格式
- [ ] 无 `fmt.Errorf`/`errors.Wrap` 包装
- [ ] 无单行 `if err`
- [ ] 无 `if err := f(); err != nil` 内联声明
- [ ] 业务无 panic/recover
- [ ] 多错误用 `errors.Join`
- [ ] sentinel 用 `errors.New` 定义
- [ ] 参数校验用 validate tag，禁手写 if
- [ ] Update 全字段 unconditional，禁零值跳过
