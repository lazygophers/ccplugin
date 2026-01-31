---
name: lrpc-log-skills
description: lazygophers/log 高性能日志库规范 - 基于 zap 的结构化日志，支持对象池、异步写入、自动轮转和分布式追踪
---

# lrpc-log - 高性能日志库

基于 zap 的结构化日志库，提供高性能、高可靠性的日志解决方案。

## 特性

- ⚡ **高性能** - 对象池复用 Entry，零分配
- 🔄 **异步写入** - 批量写入，减少磁盘 I/O
- 📦 **结构化** - JSON 格式，支持日志聚合
- 🔄 **自动轮转** - 按小时自动切割日志文件
- 🏷️ **TraceID** - 分布式追踪支持
- 📊 **93%+ 测试覆盖率**

## 基础使用

### 获取 Logger

```go
import "github.com/lazygophers/log"

// 获取默认 logger
logger := log.GetLogger("main")

// 或使用包级别变量
var logger = log.GetLogger("my-module")
```

### 日志级别

```go
// Debug - 调试信息
logger.Debug("processing request", log.Field("user_id", 123))

// Info - 一般信息
logger.Info("server started",
    log.Field("addr", ":8080"),
    log.Field("mode", "production"),
)

// Warn - 警告信息
logger.Warn("slow query",
    log.Field("duration", time.Second*5),
    log.Field("query", "SELECT * FROM users"),
)

// Error - 错误信息
logger.Error("database connection failed",
    log.Field("error", err),
    log.Field("host", "localhost:3306"),
)

// Fatal - 致命错误，退出程序
logger.Fatal("cannot start server",
    log.Field("error", err),
)
```

### 结构化字段

```go
// 基础类型
log.Field("name", "value")
log.Field("count", 42)
log.Field("rate", 3.14)
log.Field("enabled", true)

// 任意类型（自动 JSON 序列化）
log.Field("user", User{ID: 1, Name: "John"})
log.Field("metadata", map[string]interface{}{"key": "value"})

// 时间类型
log.Field("created_at", time.Now())

// 错误类型
log.Field("error", err)
```

## 高级功能

### 1. 对象池优化

```go
// 内部使用对象池复用 Entry
// 无需担心性能，直接使用

// 热路径也无需优化
for i := 0; i < 1000000; i++ {
    logger.Info("processing", log.Field("i", i))
}
```

### 2. 异步写入

```go
// 默认启用异步写入
// 批量写入，减少磁盘 I/O

// 自定义批量大小（可选）
log.SetBatchSize(1000)
```

### 3. 日志轮转

```go
// 默认按小时轮转
// 日志文件名格式：app.2024-01-15_14.log

// 自定义轮转配置
log.SetRotation(log.RotationConfig{
    Pattern:  "app.2006-01-02_15.log",  // 文件名格式
    MaxAge:   7 * 24 * time.Hour,       // 保留 7 天
    MaxSize:  100 * 1024 * 1024,        // 单文件最大 100MB
})
```

### 4. TraceID 支持

```go
// 自动生成和管理 TraceID
logger.Info("processing request",
    log.TraceID(),  // 自动添加 trace_id 字段
    log.Field("path", "/api/users"),
)
```

### 5. 条件日志

```go
// 条件日志（减少字符串拼接）
logger.Debugw("debug info",
    func() []log.Field {
        if someCondition {
            return []log.Field{
                log.Field("detail", "expensive computation"),
            }
        }
        return nil
    }(),
)
```

### 6. 日志采样

```go
// 对高频日志进行采样
// 只记录 10% 的 Debug 日志
logger.SetSampling(log.SamplingConfig{
    Level:      log.DebugLevel,
    Initial:    100,   // 前 100 条都记录
    Thereafter: 10,    // 之后每 10 条记录 1 条
})
```

## 配置

### 开发环境

```go
import "go.uber.org/zap/zapcore"

// 控制台输出，彩色，Debug 级别
log.SetConfig(log.Config{
    Level:      zapcore.DebugLevel,
    Encoding:   "console",
    Development: true,
})
```

### 生产环境

```go
// 文件输出，JSON 格式，Info 级别
log.SetConfig(log.Config{
    Level:      zapcore.InfoLevel,
    Encoding:   "json",
    Development: false,
    OutputPaths: []string{
        "/var/log/app/app.log",
        "/var/log/app/app-error.log",  // Error 及以上单独输出
    },
})
```

### 自定义配置

```go
// 完全自定义
log.SetLogger(zap.New(
    zapcore.NewCore(
        zapcore.NewJSONEncoder(zapcore.EncoderConfig{
            TimeKey:        "ts",
            LevelKey:       "level",
            NameKey:        "logger",
            CallerKey:      "caller",
            MessageKey:     "msg",
            StacktraceKey:  "stacktrace",
            LineEnding:     zapcore.DefaultLineEnding,
            EncodeLevel:    zapcore.LowercaseLevelEncoder,
            EncodeTime:     zapcore.ISO8601TimeEncoder,
            EncodeDuration: zapcore.SecondsDurationEncoder,
            EncodeCaller:   zapcore.ShortCallerEncoder,
        }),
        zapcore.AddSync(os.Stdout),
        zapcore.InfoLevel,
    ),
))
```

## 最佳实践

### 1. Logger 命名

```go
// ✅ 使用模块/组件名
var logger = log.GetLogger("http-server")
var logger = log.GetLogger("database")
var logger = log.GetLogger("cache-redis")

// ❌ 不要使用通用名
var logger = log.GetLogger("log")
var logger = log.GetLogger("logger")
```

### 2. 错误日志

```go
// ✅ 包含错误上下文
logger.Error("failed to create user",
    log.Field("error", err),
    log.Field("email", user.Email),
    log.Field("ip", clientIP),
)

// ❌ 只记录错误信息
logger.Error("error:", err)
```

### 3. 性能敏感场景

```go
// ✅ 使用条件日志减少开销
if logger.DebugLevel() {
    logger.Debug("expensive debug info",
        log.Field("data", heavyComputation()),
    )
}

// ✅ 使用延迟计算
logger.Debugw("lazy evaluation",
    log.Lazy(func() interface{} {
        return heavyComputation()
    }),
)
```

### 4. 结构化键名约定

```go
// 使用 snake_case 命名
log.Field("user_id", 123)        // ✅
log.Field("request_id", "abc")   // ✅
log.Field("userId", 123)         // ❌ 避免 camelCase

// 使用有意义的名称
log.Field("error", err)          // ✅
log.Field("err", err)            // ❌ 避免缩写
```

### 5. 敏感信息

```go
// ❌ 不要记录敏感信息
logger.Info("user login",
    log.Field("password", password),
    log.Field("token", token),
)

// ✅ 记录脱敏后的信息
logger.Info("user login",
    log.Field("email", maskEmail(user.Email)),
    log.Field("user_id", user.ID),
)
```

## 日志格式示例

### 开发环境（Console）

```
2024-01-15T14:30:45.123+08:00    INFO    http-server    server started
    {"addr": ":8080", "mode": "production"}
```

### 生产环境（JSON）

```json
{
  "ts": "2024-01-15T14:30:45.123+08:00",
  "level": "info",
  "logger": "http-server",
  "msg": "server started",
  "addr": ":8080",
  "mode": "production"
}
```

### 错误日志

```json
{
  "ts": "2024-01-15T14:30:45.123+08:00",
  "level": "error",
  "logger": "database",
  "msg": "query failed",
  "error": "connection refused",
  "query": "SELECT * FROM users WHERE id = 1",
  "duration_ms": 1234
}
```

## 性能基准

```
BenchmarkLogger-8     10000000    102 ns/op    0 B/op    0 allocs/op
```

- **10M+ ops/sec**: 单核每秒可处理千万级日志
- **0 分配**: 对象池复用 Entry
- **10x faster**: 比标准库快 10 倍

## 参考资源

- [lazygophers/log GitHub](https://github.com/lazygophers/log)
- [uber-go/zap 文档](https://github.com/uber-go/zap)
