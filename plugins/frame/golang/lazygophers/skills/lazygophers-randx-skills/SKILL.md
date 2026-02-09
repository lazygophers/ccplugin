---
name: lazygophers-randx-skills
description: lazygophers/utils randx 模块深度解析 - 高性能随机数生成、字符串生成、随机选择、时间随机化和批量操作的完整指南
---

# lazygophers-randx: 高性能随机数生成工具

## 概述

`randx` 是 lazygophers/utils 提供的高性能随机数生成模块，相比标准库 `math/rand` 提供了显著的性能优化（约5-10倍）和更丰富的功能集合。

### 核心特性

- **高性能**: 使用全局优化的随机数生成器，性能提升5-10倍
- **类型安全**: 泛型支持，编译时类型检查
- **批量操作**: 支持批量生成，减少锁竞争
- **边界处理**: 完善的边界条件处理
- **测试覆盖**: 99.3% 的测试覆盖率

### 架构设计

```go
// 全局随机数生成器（使用单一互斥锁）
var (
    globalRand = rand.New(rand.NewSource(time.Now().UnixNano()))
    globalMu   sync.Mutex
)
```

## 安装

```bash
go get github.com/lazygophers/utils/randx
```

## API 参考

### 1. 数字随机数生成

#### 基础整数

```go
// 生成 [0, n) 范围内的随机整数
randx.Intn(100)        // 0-99
randx.Intn(10)         // 0-9

// 生成随机非负整数
randx.Int()            // 任意非负整数

// 生成 [min, max] 范围内的随机整数（包含边界）
randx.IntnRange(1, 10)      // 1-10
randx.IntnRange(-5, 5)      // -5 到 5
randx.IntnRange(100, 200)   // 100-200
```

#### 64位整数

```go
// 生成 [0, n) 范围内的随机 int64
randx.Int64n(1000)     // 0-999

// 生成随机 int63
randx.Int64()          // 任意非负 int64

// 生成 [min, max] 范围内的随机 int64
randx.Int64nRange(1, 100)   // 1-100
randx.Int64nRange(-100, 100) // -100 到 100
```

#### 浮点数

```go
// 生成 [0.0, 1.0) 范围内的随机浮点数
randx.Float64()        // 0.0 <= x < 1.0
randx.Float32()        // 0.0 <= x < 1.0

// 生成 [min, max] 范围内的随机浮点数
randx.Float64Range(0.0, 100.0)      // 0.0-100.0
randx.Float64Range(-5.5, 5.5)        // -5.5 到 5.5
randx.Float32Range(1.0, 10.0)        // 1.0-10.0
```

#### 无符号整数

```go
// 生成随机 uint32
randx.Uint32()                   // 任意 uint32
randx.Uint32Range(10, 100)       // 10-100

// 生成随机 uint64
randx.Uint64()                   // 任意 uint64
randx.Uint64Range(1000, 10000)   // 1000-10000
```

### 2. 批量数字生成

```go
// 批量生成整数
randx.BatchIntn(10, 100)         // 生成100个 [0,10) 范围的整数
randx.BatchInt64n(100, 50)       // 生成50个 [0,100) 范围的 int64

// 批量生成浮点数
randx.BatchFloat64(100)          // 生成100个 [0.0, 1.0) 范围的浮点数
```

**性能提示**: 批量操作比单次调用更高效，减少锁竞争。

### 3. 布尔随机数

```go
// 生成随机布尔值（50/50 概率）
randx.Bool()         // true 或 false

// 生成概率布尔值（n% 概率返回 true）
randx.Booln(50)      // 50% 概率 true
randx.Booln(80)      // 80% 概率 true
randx.Booln(0)       // 总是 false
randx.Booln(100)     // 总是 true

// 加权布尔值（weight 为 true 的权重，0.0-1.0）
randx.WeightedBool(0.7)    // 70% 概率 true
randx.WeightedBool(0.3)    // 30% 概率 true
```

#### 批量布尔生成

```go
// 批量生成布尔值
randx.BatchBool(10)              // 生成10个随机布尔值
randx.BatchBooln(70, 100)        // 生成100个 70% 概率为 true 的布尔值
```

### 4. 随机选择与洗牌

#### 从切片中随机选择

```go
// 从切片中随机选择一个元素
items := []string{"apple", "banana", "orange", "grape"}
selected := randx.Choose(items)  // 随机返回一个水果

// 从切片中选择 N 个不重复的元素
selected := randx.ChooseN(items, 2)  // 随机选择2个不重复的水果
```

#### 加权选择

```go
// 根据权重数组进行加权选择
items := []string{"A", "B", "C"}
weights := []float64{0.1, 0.3, 0.6}  // C 的权重最高
selected := randx.WeightedChoose(items, weights)
// 60% 概率选 "C"，30% 选 "B"，10% 选 "A"
```

#### 随机打乱

```go
// 原地打乱切片（Fisher-Yates 洗牌算法）
cards := []string{"A", "K", "Q", "J", "10"}
randx.Shuffle(cards)  // 原地打乱 cards 切片
```

#### 批量选择

```go
// 批量从切片中选择（可能重复）
items := []int{1, 2, 3, 4, 5}
selected := randx.BatchChoose(items, 10)
// 返回10个随机选择的元素，可能重复
```

### 5. 时间随机化

#### 随机时间间隔

```go
// 生成随机时间间隔 [min, max]
randx.RandomDuration(time.Second, time.Minute)  // 1秒到1分钟
randx.RandomDuration(0, 5*time.Second)          // 0-5秒

// 生成适合睡眠的随机时间（默认1-3秒）
randx.TimeDuration4Sleep()                       // 1-3秒
randx.TimeDuration4Sleep(100*time.Millisecond, 500*time.Millisecond)  // 100-500ms
```

#### 随机时间点

```go
now := time.Now()

// 在指定时间范围内生成随机时间点
start := time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC)
end := time.Date(2024, 12, 31, 23, 59, 59, 0, time.UTC)
randomTime := randx.RandomTime(start, end)

// 在指定日期的一天内生成随机时间点
randomTime := randx.RandomTimeInDay(now)  // 当天的随机时间

// 在指定小时内生成随机时间点
randomTime := randx.RandomTimeInHour(now, 14)  // 下午2点的随机分钟和秒
```

#### 时间抖动

```go
// 为时间间隔添加抖动（±jitterPercent% 的随机变化）
original := 10 * time.Second
jittered := randx.Jitter(original, 10)  // 9-11秒之间（±10%）

// 用于重试退避等场景
backoff := randx.Jitter(5*time.Second, 20)  // 4-6秒之间
```

#### 随机睡眠

```go
// 随机睡眠指定范围的时间
randx.SleepRandom(1*time.Second, 3*time.Second)  // 睡眠1-3秒

// 随机睡眠指定毫秒数范围
randx.SleepRandomMilliseconds(100, 500)  // 睡眠100-500ms
```

#### 批量时间间隔

```go
// 批量生成随机时间间隔
durations := randx.BatchRandomDuration(
    100*time.Millisecond,
    5*time.Second,
    10,
)  // 生成10个 100ms-5s 范围的时间间隔
```

## 使用场景

### 1. 模拟与测试

```go
// 生成随机用户数据
user := User{
    Age:    randx.IntnRange(18, 80),
    Active: randx.Booln(70),  // 70% 活跃用户
    Score:  randx.Float64Range(0.0, 100.0),
}

// 生成随机订单数量
orderCount := randx.IntnRange(1, 10)
for i := 0; i < orderCount; i++ {
    // 创建订单
}
```

### 2. 负载测试与并发

```go
// 批量生成请求数据
requests := randx.BatchIntn(1000, 10000)  // 10000个随机请求ID

// 随机延迟
for _, req := range requests {
    go func(id int) {
        randx.SleepRandomMilliseconds(10, 100)  // 10-100ms 随机延迟
        processRequest(id)
    }(req)
}
```

### 3. 游戏与抽奖

```go
// 权重抽奖系统
prizes := []string{"一等奖", "二等奖", "三等奖", "谢谢参与"}
weights := []float64{0.01, 0.05, 0.14, 0.80}  // 1%, 5%, 14%, 80%
winner := randx.WeightedChoose(prizes, weights)

// 随机发牌
deck := []string{"A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"}
randx.Shuffle(deck)
hand := randx.ChooseN(deck, 5)  // 发5张牌
```

### 4. 重试与退避

```go
// 指数退避 + 抖动
for attempt := 0; attempt < maxRetries; attempt++ {
    err := tryOperation()
    if err == nil {
        break
    }

    // 计算退避时间（指数退避 + 20% 抖动）
    backoff := time.Duration(1<<uint(attempt)) * time.Second
    jitteredBackoff := randx.Jitter(backoff, 20)

    time.Sleep(jitteredBackoff)
}
```

### 5. 随机采样

```go
// 从大数据集中随机采样
data := []string{"item1", "item2", /* ... 10000 items ... */}

// 随机选择100个样本
sample := randx.ChooseN(data, 100)

// 等价于使用 BatchChoose（允许重复）
sampleWithReplacement := randx.BatchChoose(data, 100)
```

## 性能基准

根据项目提供的基准测试结果（2024年数据）：

```
原始实现 (math/rand)    优化实现 (randx)    性能提升
-------------------     ----------------     --------
Intn(100):             ~80ns/op             ~5ns/op           16x
Int64():               ~75ns/op             ~5ns/op           15x
Float64():             ~85ns/op             ~5ns/op           17x
```

**关键优化点**:
- 全局随机数生成器复用，避免重复创建
- 单一互斥锁保护，减少锁竞争
- 批量操作减少锁获取/释放次数
- 优化的种子生成器，避免频繁系统调用

## 最佳实践

### 1. 选择合适的函数

```go
// ✅ 推荐：使用泛型 Choose
item := randx.Choose(items)

// ❌ 不推荐：手动实现
idx := randx.Intn(len(items))
item := items[idx]
```

### 2. 批量操作优先

```go
// ✅ 推荐：批量生成
numbers := randx.BatchIntn(100, 1000)

// ❌ 不推荐：循环单次生成
for i := 0; i < 1000; i++ {
    numbers[i] = randx.Intn(100)
}
```

### 3. 边界条件处理

```go
// 所有函数都处理了边界条件
randx.IntnRange(10, 5)   // 返回 0（min > max）
randx.IntnRange(5, 5)    // 返回 5（min == max）
randx.Intn(0)            // 返回 0
randx.Booln(0)           // 返回 false
randx.Booln(100)         // 返回 true
```

### 4. 并发安全

```go
// randx 的所有函数都是并发安全的
var wg sync.WaitGroup
for i := 0; i < 100; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        // 安全地在多个 goroutine 中使用
        num := randx.Intn(100)
        process(num)
    }()
}
wg.Wait()
```

### 5. 测试中的应用

```go
func TestProcessOrder(t *testing.T) {
    // 生成随机测试数据
    for i := 0; i < 1000; i++ {
        order := Order{
            ID:       randx.Int64(),
            Quantity: randx.IntnRange(1, 100),
            Price:    randx.Float64Range(10.0, 1000.0),
            Priority: randx.Booln(30),  // 30% 高优先级
        }
        testProcessOrder(t, order)
    }
}
```

## 注意事项

### 1. 非加密安全

`randx` 使用 `math/rand` 实现，**不适用于加密场景**。如需加密安全的随机数，请使用 `crypto/rand`：

```go
// 加密安全的随机数（用于密钥、token等）
import "crypto/rand"

func secureRandomBytes(n int) []byte {
    b := make([]byte, n)
    _, err := crypto/rand.Read(b)
    if err != nil {
        panic(err)
    }
    return b
}
```

### 2. 随机性质量

`randx` 使用伪随机数生成器（PRNG），对于大多数应用场景足够，但不适用于：

- 密码学应用（使用 `crypto/rand`）
- 科学模拟（需要更高质量的随机源）
- 真正的均匀分布测试

### 3. 性能考量

虽然 `randx` 已经高度优化，但在极端性能要求的场景下：

- **批量操作**: 使用 `Batch*` 函数减少锁竞争
- **预分配**: 对于大量随机数，预分配切片
- **避免热点**: 在紧密循环中考虑减少随机数生成频率

## 完整示例

### 示例1: 电商订单模拟

```go
package main

import (
    "fmt"
    "time"
    "github.com/lazygophers/utils/randx"
)

type Order struct {
    ID          int64
    UserID      int
    ProductID   int
    Quantity    int
    Price       float64
    CreatedAt   time.Time
    IsExpress   bool
}

func generateRandomOrder() Order {
    // 随机生成订单数据
    return Order{
        ID:        randx.Int64(),
        UserID:    randx.IntnRange(1000, 9999),
        ProductID: randx.IntnRange(1, 500),
        Quantity:  randx.IntnRange(1, 10),
        Price:     randx.Float64Range(10.0, 500.0),
        CreatedAt: randx.RandomTimeInDay(time.Now()),
        IsExpress: randx.Booln(15), // 15% 快递订单
    }
}

func main() {
    // 批量生成100个订单
    orders := make([]Order, 100)
    for i := range orders {
        orders[i] = generateRandomOrder()
    }

    fmt.Printf("Generated %d orders\n", len(orders))
}
```

### 示例2: API 重试机制

```go
package main

import (
    "fmt"
    "time"
    "github.com/lazygophers/utils/randx"
)

func callAPIWithRetry(url string, maxRetries int) error {
    var lastErr error

    for attempt := 0; attempt < maxRetries; attempt++ {
        err := doAPICall(url)
        if err == nil {
            return nil
        }
        lastErr = err

        // 指数退避 + 随机抖动（20%）
        baseDelay := time.Duration(1<<uint(attempt)) * time.Second
        actualDelay := randx.Jitter(baseDelay, 20)

        fmt.Printf("Attempt %d failed, retrying in %v\n", attempt+1, actualDelay)
        time.Sleep(actualDelay)
    }

    return fmt.Errorf("max retries exceeded: %w", lastErr)
}
```

### 示例3: 负载测试工具

```go
package main

import (
    "fmt"
    "sync"
    "time"
    "github.com/lazygophers/utils/randx"
)

func loadTest(url string, concurrentUsers, requestsPerUser int) {
    var wg sync.WaitGroup

    for user := 0; user < concurrentUsers; user++ {
        wg.Add(1)
        go func(userID int) {
            defer wg.Done()

            for req := 0; req < requestsPerUser; req++ {
                // 随机延迟模拟真实用户行为
                randx.SleepRandomMilliseconds(50, 200)

                start := time.Now()
                err := makeRequest(url)
                duration := time.Since(start)

                fmt.Printf("User %d, Request %d: %v (error: %v)\n",
                    userID, req, duration, err)
            }
        }(user)
    }

    wg.Wait()
}
```

### 示例4: 游戏抽奖系统

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/randx"
)

type Prize struct {
    Name   string
    Weight float64
    Count  int
}

func drawLottery(prizes []Prize) string {
    names := make([]string, len(prizes))
    weights := make([]float64, len(prizes))

    for i, prize := range prizes {
        names[i] = prize.Name
        weights[i] = prize.Weight
    }

    winner := randx.WeightedChoose(names, weights)
    return winner
}

func main() {
    prizes := []Prize{
        {"iPhone 15", 0.01, 1},      // 1% 概率
        {"AirPods", 0.05, 10},        // 5% 概率
        {"礼品卡", 0.14, 50},          // 14% 概率
        {"优惠券", 0.80, 1000},        // 80% 概率
    }

    // 模拟1000次抽奖
    results := make(map[string]int)
    for i := 0; i < 1000; i++ {
        winner := drawLottery(prizes)
        results[winner]++
    }

    for name, count := range results {
        fmt.Printf("%s: %d 次 (%.1f%%)\n", name, count, float64(count)/10)
    }
}
```

## 与标准库对比

### 性能对比

| 操作 | math/rand | randx | 提升 |
|------|-----------|-------|------|
| Intn(100) | ~80ns | ~5ns | 16x |
| Float64() | ~85ns | ~5ns | 17x |
| Int64() | ~75ns | ~5ns | 15x |

### 功能对比

| 功能 | math/rand | randx |
|------|-----------|-------|
| 基础随机数 | ✅ | ✅ |
| 泛型支持 | ❌ | ✅ |
| 批量操作 | ❌ | ✅ |
| 加权选择 | ❌ | ✅ |
| 时间随机化 | ❌ | ✅ |
| 时间抖动 | ❌ | ✅ |
| 高性能优化 | ❌ | ✅ |

## 迁移指南

### 从 math/rand 迁移

```go
// 旧代码
import "math/rand"

num := rand.Intn(100)
f := rand.Float64()

// 新代码
import "github.com/lazygophers/utils/randx"

num := randx.Intn(100)
f := randx.Float64()
```

### 从其他随机库迁移

```go
// 从 fastrand 迁移
// fastrand.Intn(n) -> randx.Intn(n)

// 从随机工具库迁移
// random.Choose(items) -> randx.Choose(items)
// random.Shuffle(items) -> randx.Shuffle(items)
```

## 总结

`randx` 是一个高性能、功能丰富的随机数生成工具，适合以下场景：

✅ **推荐使用**:
- 负载测试和性能测试
- 数据模拟和生成
- 游戏和抽奖系统
- 随机采样和选择
- 重试和退避机制
- 需要高性能随机数的场景

❌ **不推荐使用**:
- 密码学应用（使用 `crypto/rand`）
- 需要密码学安全的随机数
- 需要真正均匀分布的科学计算

## 参考资料

- 源码: https://github.com/lazygophers/utils/tree/master/randx
- 测试覆盖率: 99.3%
- 性能基准: ~5ns/op (2024年数据)
- GoDoc: https://pkg.go.dev/github.com/lazygophers/utils/randx
