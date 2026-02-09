---
name: lazygophers-hystrix-skills
description: lazygophers/utils hystrix 模块完整指南 - 高性能熔断器实现，包含熔断状态机、环形缓冲区优化、无锁并发设计、批量处理和快速路径
---

# Hystrix 熔断器完整指南

## 概述

`lazygophers/utils/hystrix` 是一个高性能的 Go 熔断器实现，提供三种优化级别的熔断器：

- **CircuitBreaker** - 功能完整的优化版本（环形缓冲区、无锁设计、内存对齐）
- **FastCircuitBreaker** - 超轻量级版本（仅基础功能，极致性能）
- **BatchCircuitBreaker** - 批量处理版本（适合高吞吐场景）

### 核心特性

- **无锁并发设计**：使用 CAS 原子操作，避免 mutex 竞争
- **环形缓冲区优化**：紧凑存储时间戳和结果标志
- **内存对齐优化**：缓存行填充避免伪共享（false sharing）
- **零分配状态查询**：`GetState()`, `IsOpen()`, `IsClosed()` 零 GC 压力
- **自动过期清理**：基于时间窗口的滑动窗口统计

---

## 熔断状态机

### 状态定义

```go
type State string

const (
    Closed   State = "closed"    // 熔断关闭（服务可用）
    Open     State = "open"      // 熔断开启（服务不可用）
    HalfOpen State = "half-open" // 半开状态（尝试探测）
)
```

### 状态转换规则

```
                    失败率超过阈值
    Closed ──────────────────────> Open
        ^                           │
        │                           │ 时间窗口内失败率下降
        │                           v
    HalfOpen <──────────────────────┘
         │
         │ 探测成功           探测失败
         v                     |
    Closed ─────────────────> Open
```

**Closed → Open**：当 `ReadyToTrip(successes, failures)` 返回 `true`

**Open → HalfOpen**：当 `ReadyToTrip(successes, failures)` 返回 `false`

**HalfOpen → Closed**：当有最近的成功请求

**HalfOpen → Open**：当有最近的失败请求

---

## CircuitBreaker 优化版熔断器

### 核心结构

```go
type CircuitBreaker struct {
    // 配置参数（只读，无需同步）
    timeWindow    int64         // 统计时间窗口（纳秒）
    onStateChange StateChange   // 状态变化回调
    readyToTrip   ReadyToTrip   // 熔断条件判断
    probe         Probe         // 半开状态探测函数
    bufferSize    int           // 环形缓冲区大小

    // 状态管理（原子操作优化）
    state atomic.Uint32 // 0=Closed, 1=Open, 2=HalfOpen

    // 统计计数器（内存对齐优化，避免伪共享）
    stats struct {
        successes       atomic.Uint64
        _               [56]byte // 缓存行填充
        failures        atomic.Uint64
        _               [56]byte
        lastCleanupTime atomic.Int64
        _               [56]byte
        changed         atomic.Uint32
        _               [60]byte
    }

    // 环形缓冲区优化
    ringBuffer *optimizedRingBuffer
}
```

### 配置选项

```go
type CircuitBreakerConfig struct {
    TimeWindow    time.Duration // 统计成功率的时间窗口
    OnStateChange StateChange   // 状态变化回调函数
    ReadyToTrip   ReadyToTrip   // 熔断条件判断函数
    Probe         Probe         // 半开状态探测函数
    BufferSize    int           // 请求结果缓存大小，默认1000
}
```

### 创建熔断器

```go
import "github.com/lazygophers/utils/hystrix"

// 基础配置
cb := hystrix.NewCircuitBreaker(hystrix.CircuitBreakerConfig{
    TimeWindow: time.Second * 10,
    ReadyToTrip: func(successes, failures uint64) bool {
        total := successes + failures
        return total >= 10 && failures > successes
    },
})

// 自定义探测函数（50% 概率允许探测）
cb := hystrix.NewCircuitBreaker(hystrix.CircuitBreakerConfig{
    TimeWindow: time.Second * 10,
    Probe:      hystrix.ProbeWithChance(50),
})

// 状态变化监听
cb := hystrix.NewCircuitBreaker(hystrix.CircuitBreakerConfig{
    TimeWindow: time.Second * 10,
    OnStateChange: func(oldState, newState hystrix.State) {
        log.Printf("熔断器状态变化: %s -> %s", oldState, newState)
    },
})
```

### 使用方式

#### 方式一：Before/After 模式

```go
// 请求前检查
if !cb.Before() {
    return errors.New("熔断器已开启，拒绝请求")
}

// 执行请求
err := doRequest()

// 请求后记录结果
cb.After(err == nil)
```

#### 方式二：Call 包装模式

```go
err := cb.Call(func() error {
    // 执行业务逻辑
    return doRequest()
})

if err != nil {
    if err.Error() == "circuit breaker is open" {
        // 熔断器拒绝
    }
}
```

### 环形缓冲区优化

```go
type optimizedRingBuffer struct {
    buffer []int64 // 紧凑存储：高32位存储时间戳，低32位存储状态+标志
    _      [56]byte
    head   atomic.Uint64
    _      [56]byte
    tail   atomic.Uint64
    _      [56]byte
    size   uint64
    mask   uint64 // size-1，用于快速取模
}
```

**紧凑存储格式**：
- 高 32 位：时间戳（相对或绝对）
- 低 32 位：成功标志位（`0x01` 表示成功）

**快速取模**：通过 `size` 始终为 2 的幂，使用位运算 `& mask` 代替 `%`

---

## FastCircuitBreaker 超轻量级熔断器

### 核心结构

```go
type FastCircuitBreaker struct {
    state     atomic.Uint32 // 状态
    successes atomic.Uint64 // 成功计数
    failures  atomic.Uint64 // 失败计数
    lastReset atomic.Int64  // 上次重置时间

    threshold   uint64 // 失败阈值
    windowNanos int64  // 时间窗口（纳秒）
}
```

### 创建与使用

```go
// 创建快速熔断器：10次失败触发熔断，时间窗口10秒
cb := hystrix.NewFastCircuitBreaker(10, time.Second*10)

// 方式一：AllowRequest/RecordResult
if cb.AllowRequest() {
    err := doRequest()
    cb.RecordResult(err == nil)
}

// 方式二：CallFast 包装
err := cb.CallFast(func() error {
    return doRequest()
})
```

### 特点

- **无环形缓冲区**：仅使用计数器，内存占用极小
- **自动重置**：时间窗口到期自动重置计数器
- **极致性能**：最少原子操作，适合高频调用

---

## BatchCircuitBreaker 批量处理熔断器

### 核心结构

```go
type BatchCircuitBreaker struct {
    *CircuitBreaker
    batchSize    int
    batchBuffer  []bool
    batchIndex   atomic.Int32
    batchMutex   sync.Mutex
    batchTimeout time.Duration
    lastFlush    atomic.Int64
}
```

### 创建与使用

```go
// 创建批量熔断器：批量大小100，超时50ms
cb := hystrix.NewBatchCircuitBreaker(
    hystrix.CircuitBreakerConfig{
        TimeWindow: time.Second * 10,
    },
    100,              // 批量大小
    time.Millisecond*50, // 批量超时
)

// 记录结果（自动批量刷新）
cb.AfterBatch(err == nil)

// 或使用底层 CircuitBreaker 方法
err := cb.Call(func() error {
    return doRequest()
})
```

### 批量刷新触发条件

1. 批量缓冲区满（达到 `batchSize`）
2. 超过 `batchTimeout` 时间

---

## 工具函数

### ProbeWithChance

创建概率探测函数，用于半开状态的采样探测：

```go
import "github.com/lazygophers/utils/hystrix"

// 50% 概率允许探测
probe := hystrix.ProbeWithChance(50)

// 总是允许探测
probeAlways := hystrix.ProbeWithChance(100)

// 禁止探测
probeNever := hystrix.ProbeWithChance(0)
```

---

## 监控指标

### 状态查询

```go
// 获取当前状态（返回枚举类型）
state := cb.State() // hystrix.State

// 零分配状态查询（返回 uint32）
stateUint := cb.GetState() // 0=Closed, 1=Open, 2=HalfOpen

// 快速状态检查
isOpen := cb.IsOpen()      // bool
isClosed := cb.IsClosed()  // bool
```

### 统计数据

```go
// 获取成功和失败计数
successes, failures := cb.Stat()

// 获取总请求数
total := cb.Total()
```

---

## 完整使用示例

### 示例一：HTTP 客户端熔断

```go
package main

import (
    "errors"
    "fmt"
    "log"
    "net/http"
    "time"

    "github.com/lazygophers/utils/hystrix"
)

type APIClient struct {
    client *http.Client
    breaker *hystrix.CircuitBreaker
}

func NewAPIClient() *APIClient {
    return &APIClient{
        client: &http.Client{Timeout: time.Second * 5},
        breaker: hystrix.NewCircuitBreaker(hystrix.CircuitBreakerConfig{
            TimeWindow: time.Minute,
            ReadyToTrip: func(successes, failures uint64) bool {
                // 至少10个请求，且失败率超过50%
                total := successes + failures
                return total >= 10 && failures*2 > total
            },
            Probe: hystrix.ProbeWithChance(30), // 半开状态30%探测
            OnStateChange: func(oldState, newState hystrix.State) {
                log.Printf("熔断器状态: %s -> %s", oldState, newState)
            },
        }),
    }
}

func (c *APIClient) CallAPI(url string) (*http.Response, error) {
    // 使用 Call 包装
    var resp *http.Response
    err := c.breaker.Call(func() error {
        var err error
        resp, err = c.client.Get(url)
        return err
    })

    if err != nil {
        if err.Error() == "circuit breaker is open" {
            return nil, errors.New("服务暂时不可用（熔断中）")
        }
        return nil, err
    }

    return resp, nil
}

func main() {
    client := NewAPIClient()

    for i := 0; i < 100; i++ {
        resp, err := client.CallAPI("https://api.example.com/data")
        if err != nil {
            log.Printf("请求失败: %v", err)
        } else {
            resp.Body.Close()
            log.Printf("请求成功")
        }
        time.Sleep(time.Millisecond * 100)
    }

    // 输出统计
    successes, failures := client.breaker.Stat()
    fmt.Printf("成功: %d, 失败: %d, 总计: %d\n",
        successes, failures, client.breaker.Total())
}
```

### 示例二：数据库连接池熔断

```go
package main

import (
    "database/sql"
    "errors"
    "time"

    "github.com/lazygophers/utils/hystrix"
)

type DBService struct {
    db      *sql.DB
    breaker *hystrix.FastCircuitBreaker
}

func NewDBService(db *sql.DB) *DBService {
    return &DBService{
        db: db,
        breaker: hystrix.NewFastCircuitBreaker(
            5,             // 5次失败触发熔断
            time.Minute,   // 1分钟时间窗口
        ),
    }
}

func (s *DBService) QueryUser(id int) (*User, error) {
    if !s.breaker.AllowRequest() {
        return nil, errors.New("数据库服务熔断中")
    }

    var user User
    err := s.db.QueryRow("SELECT * FROM users WHERE id = ?", id).Scan(&user)
    s.breaker.RecordResult(err == nil)

    if err != nil {
        return nil, err
    }
    return &user, nil
}
```

### 示例三：微服务间调用熔断

```go
package main

import (
    "context"
    "time"

    "github.com/lazygophers/utils/hystrix"
)

type ServiceRegistry struct {
    breakers map[string]*hystrix.CircuitBreaker
}

func NewServiceRegistry() *ServiceRegistry {
    return &ServiceRegistry{
        breakers: make(map[string]*hystrix.CircuitBreaker),
    }
}

func (r *ServiceRegistry) getBreaker(serviceName string) *hystrix.CircuitBreaker {
    if breaker, ok := r.breakers[serviceName]; ok {
        return breaker
    }

    breaker := hystrix.NewCircuitBreaker(hystrix.CircuitBreakerConfig{
        TimeWindow: time.Second * 30,
        ReadyToTrip: func(successes, failures uint64) bool {
            total := successes + failures
            // 至少5个请求，失败率超过60%
            return total >= 5 && failures*10 > total*6
        },
        OnStateChange: func(oldState, newState hystrix.State) {
            log.Printf("[%s] 熔断器: %s -> %s", serviceName, oldState, newState)
        },
    })

    r.breakers[serviceName] = breaker
    return breaker
}

func (r *ServiceRegistry) CallService(
    ctx context.Context,
    serviceName string,
    fn func() error,
) error {
    breaker := r.getBreaker(serviceName)

    // 检查上下文是否已取消
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }

    return breaker.Call(fn)
}
```

### 示例四：批量高吞吐场景

```go
package main

import (
    "time"

    "github.com/lazygophers/utils/hystrix"
)

func main() {
    // 批量处理熔断器：批量1000，超时100ms
    breaker := hystrix.NewBatchCircuitBreaker(
        hystrix.CircuitBreakerConfig{
            TimeWindow: time.Minute,
            ReadyToTrip: func(successes, failures uint64) bool {
                total := successes + failures
                return total >= 100 && failures > total/2
            },
        },
        1000,               // 批量大小
        time.Millisecond*100, // 批量超时
    )

    // 高并发场景
    for i := 0; i < 10000; i++ {
        go func(id int) {
            err := processRequest(id)
            breaker.AfterBatch(err == nil)
        }(i)
    }
}
```

---

## 性能优化要点

### 1. 无锁设计

所有状态访问使用 `atomic` 包，避免 mutex 竞争：

```go
// 状态查询（无锁）
state := cb.state.Load() // uint32

// 计数器更新（原子加）
cb.stats.successes.Add(1)

// CAS 操作（原子交换）
cb.state.CompareAndSwap(oldState, newState)
```

### 2. 内存对齐

通过缓存行填充避免伪共享：

```go
stats struct {
    successes       atomic.Uint64
    _               [56]byte // 缓存行填充（64字节 - 8字节）
    failures        atomic.Uint64
    _               [56]byte
    // ...
}
```

### 3. 零分配查询

```go
// 零分配
cb.GetState()  // 返回 uint32
cb.IsOpen()    // 返回 bool
cb.IsClosed()  // 返回 bool

// 有分配（需要类型转换）
cb.State()     // 返回 State (string)
```

### 4. 环形缓冲区

- **紧凑存储**：时间戳和标志位打包在单个 `int64`
- **快速取模**：`size` 为 2 的幂，使用 `& mask` 代替 `%`
- **无锁写入**：使用 `atomic.Add` 获取索引

---

## 最佳实践

### 1. 选择合适的熔断器类型

| 场景 | 推荐类型 | 原因 |
|------|---------|------|
| 通用场景 | CircuitBreaker | 功能完整，监控详细 |
| 高频调用 | FastCircuitBreaker | 极致性能，内存占用小 |
| 批量处理 | BatchCircuitBreaker | 减少统计开销 |

### 2. 合理配置熔断阈值

```go
ReadyToTrip: func(successes, failures uint64) bool {
    total := successes + failures

    // 最小样本数：避免误判
    if total < 10 {
        return false
    }

    // 失败率阈值：根据业务调整
    failureRate := float64(failures) / float64(total)
    return failureRate > 0.5 // 50% 失败率
}
```

### 3. 设置合适的时间窗口

```go
// 短时间窗口：快速响应故障
TimeWindow: time.Second * 10

// 长时间窗口：平滑偶然故障
TimeWindow: time.Minute
```

### 4. 半开状态探测策略

```go
// 固定概率探测
Probe: hystrix.ProbeWithChance(30), // 30% 探测

// 自适应探测（基于时间）
Probe: func() bool {
    // 逐渐增加探测概率
    elapsed := time.Since(lastFailureTime)
    if elapsed < time.Minute {
        return false
    }
    return elapsed.Minutes() < 5
}
```

### 5. 降级处理

```go
err := cb.Call(func() error {
    return callPrimaryService()
})

if err != nil && err.Error() == "circuit breaker is open" {
    // 降级到备用服务
    return callFallbackService()
}
```

---

## 注意事项

1. **并发安全**：所有熔断器方法都是并发安全的
2. **内存占用**：CircuitBreaker 的环形缓冲区会占用额外内存
3. **时间精度**：时间窗口清理依赖系统时间，避免时间跳变
4. **状态转换**：状态转换由 `Before()` 触发，确保定期调用
5. **探测函数**：半开状态的探测函数应快速返回，避免阻塞

---

## 参考资料

- **源码**：https://github.com/lazygophers/utils/tree/master/hystrix
- **测试**：hystrix_test.go（1400+ 行，包含性能基准测试）
- **依赖**：github.com/lazygophers/utils/randx（用于 ProbeWithChance）

---

## 性能基准测试结果（参考）

基于 hystrix_test.go 的基准测试：

```
BenchmarkCall_Fast          100000000    10.2 ns/op
BenchmarkCall_Optimized     50000000     25.3 ns/op
BenchmarkBefore_Fast        200000000    5.1 ns/op
BenchmarkAfter_Fast         100000000    8.7 ns/op
```

**结论**：FastCircuitBreaker 性能最优，适合高频调用场景。
