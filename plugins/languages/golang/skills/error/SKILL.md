---
name: error
description: Go 错误处理强制规范：禁止单行 if err、必须记录日志、禁止包装错误。处理错误时必须加载。
---

# Go 错误处理规范

## 相关 Skills

| 场景     | Skill        | 说明                         |
| -------- | ------------ | ---------------------------- |
| 核心规范 | Skills(core) | 核心规范：强制约定、代码格式 |
| 工具库   | Skills(libs) | 优先库规范：lazygophers/log  |

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
- 使用 `errors.Is/As` 判断错误类型

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

### 错误判断方式（三种）

```go
if err == ErrNotFound {
    return nil, err
}

if xerror.CheckCode(err, CodeNotFound) {
    return nil, err
}

if IsNotFoundErr(err) {
    return nil, err
}
```

### Defer 和错误处理

w

```go
file, err := os.Open(path)
if err != nil {
    log.Errorf("err:%v", err)
    return nil, err
}
defer file.Close()
```

## 日志规范

### 日志级别和格式

```go
import "github.com/lazygophers/log"

log.Infof("user registered: %s", username)
log.Warnf("cache miss for key: %s", key)
log.Errorf("err:%v", err)
log.Fatalf("failed to load config: %v", err)
```

### 统一的错误日志格式

```go
if err != nil {
    log.Errorf("err:%v", err)
    return err
}
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

## 检查清单

- [ ] 所有 error 多行处理
- [ ] 所有 error 记录日志
- [ ] 使用 `log.Errorf("err:%v", err)` 统一格式
- [ ] 没有 fmt.Errorf 包装错误
- [ ] 没有 errors.Wrap 包装错误
- [ ] 没有单行 if err 语句
- [ ] 没有 if 条件中声明变量
- [ ] 没有 panic/recover 处理业务错误
- [ ] 没有 errors.Is/As 判断错误
