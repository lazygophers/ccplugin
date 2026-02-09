---
name: lazygophers-utils-cache-skills
description: lazygophers/utils cache 模块完整指南 - 高性能缓存算法集合，包含11种缓存实现（LRU、LFU、MRU、SLRU、TinyLFU、Window-TinyLFU、Adaptive LFU、LRU-K、FBR、ARC、Optimal），提供统一接口、线程安全、泛型支持和完整测试覆盖
---

# lazygophers/utils cache 模块完整指南

## 模块概述

`lazygophers/utils/cache` 是一个高性能、类型安全的 Go 缓存算法集合，提供 11 种缓存实现，每种都经过精心优化，具有统一的 API 接口、线程安全和完整的测试覆盖。

### 核心特性

- **类型安全**：完整的 Go 泛型支持，编译时类型检查
- **线程安全**：所有实现都是 goroutine 安全的，使用优化的锁机制
- **高性能**：微秒级操作，零内存分配（LRU）
- **统一接口**：所有缓存实现一致的 API
- **内存高效**：精心的内存管理和资源清理
- **淘汰回调**：可选的淘汰项回调函数
- **完整测试**：95%+ 测试覆盖率

### 可用算法

#### 核心算法

1. **LRU** (`cache/lru`) - 最近最少使用 (99.3% 覆盖率)
   - 最通用、最简单的缓存算法
   - O(1) 时间复杂度
   - 零内存分配
   - 87M+ ops/sec 性能

2. **LFU** (`cache/lfu`) - 最少使用频率 (98.5% 覆盖率)
   - 精确的访问频率跟踪
   - O(log n) 时间复杂度
   - 适合频率敏感的工作负载
   - 15M+ ops/sec 性能

3. **MRU** (`cache/mru`) - 最近最多使用 (97.7% 覆盖率)
   - 与 LRU 相反的淘汰策略
   - 适用于顺序扫描场景
   - O(1) 时间复杂度

4. **SLRU** (`cache/slru`) - 分段 LRU (97.8% 覆盖率)
   - 双段架构：试用段 + 保护段
   - 抗顺序扫描的缓存污染
   - 第二次访问自动升级到保护段
   - O(1) 时间复杂度

#### 高级算法

5. **TinyLFU** (`cache/tinylfu`) - 内存高效的 LFU (97.5% 覆盖率)
   - 使用 Count-Min Sketch 进行频率估计
   - O(1) 操作，概率性频率计数
   - 适合内存受限的大型缓存
   - 三段架构：Window + Probation + Protected

6. **Window-TinyLFU** (`cache/wtinylfu`) - 窗口 TinyLFU (82.7% 覆盖率)
   - LRU 窗口 + TinyLFU 主缓存
   - 最佳整体命中率
   - 适合混合工作负载
   - O(1) 时间复杂度

7. **Adaptive LFU** (`cache/alfu`) - 自适应 LFU (96.0% 覆盖率)
   - 带时间衰减的 LFU
   - 适应动态变化的访问模式
   - 平衡历史和近期频率
   - O(log n) 时间复杂度

8. **LRU-K** (`cache/lruk`) - LRU-K 算法 (97.6% 覆盖率)
   - 跟踪 K 个最近访问时间（通常 K=2）
   - 比标准 LRU 有更好的未来访问相关性
   - 适合数据库缓冲池
   - O(K) 时间复杂度

#### 专用算法

9. **FBR** (`cache/fbr`) - 基于频率的替换 (99.2% 覆盖率)
   - 按频率分组项目，组内使用 LRU
   - 结合频率和近期性信息
   - 平衡性能和准确性
   - O(1) 时间复杂度

10. **ARC** (`cache/arc`) - 自适应替换缓存
    - 自动适应工作负载变化
    - 在 LRU 和 LFU 之间动态调整
    - 无需手动调优
    - O(1) 时间复杂度

11. **Optimal** (`cache/optimal`) - Belady 最优算法 (94.8% 覆盖率)
    - 理论最优替换策略
    - 需要未来知识（仅用于基准测试）
    - 用于性能分析和算法比较
    - O(1) 时间复杂度

## 统一缓存接口

所有缓存实现都遵循以下统一接口：

```go
type Cache[K comparable, V any] interface {
    // 基本操作
    Get(key K) (value V, ok bool)
    Put(key K, value V) (evicted bool)
    Remove(key K) (value V, ok bool)

    // 查询操作
    Contains(key K) bool
    Peek(key K) (value V, ok bool)

    // 批量操作
    Keys() []K
    Values() []V
    Items() map[K]V

    // 状态管理
    Len() int
    Cap() int
    Clear()
    Resize(capacity int)

    // 统计信息（可选）
    Stats() Stats
}
```

### 接口方法说明

| 方法 | 描述 | 时间复杂度 |
|------|------|------------|
| `Get(key)` | 获取值并更新缓存状态 | O(1) 或 O(log n) |
| `Put(key, value)` | 添加或更新值，返回是否淘汰 | O(1) 或 O(log n) |
| `Remove(key)` | 删除指定键 | O(1) |
| `Contains(key)` | 检查键是否存在（不影响状态） | O(1) |
| `Peek(key)` | 查看值（不影响缓存状态） | O(1) |
| `Keys()` | 获取所有键（有序） | O(n) |
| `Values()` | 获取所有值（有序） | O(n) |
| `Items()` | 获取所有键值对 | O(n) |
| `Len()` | 获取当前大小 | O(1) |
| `Cap()` | 获取容量 | O(1) |
| `Clear()` | 清空缓存 | O(n) |
| `Resize(capacity)` | 调整容量 | O(n) 在最坏情况下 |

## 核心算法详解

### 1. LRU (Least Recently Used)

#### 算法原理
LRU 淘汰最近最少使用的项目。使用双向链表 + 哈希表实现：
- 哈希表：O(1) 查找
- 双向链表：维护访问顺序，最近访问的在头部

#### 数据结构
```go
type Cache[K comparable, V any] struct {
    capacity  int
    items     map[K]*list.Element      // key -> 链表节点
    evictList *list.List                // 双向链表（最近使用在前）
    mu        sync.RWMutex              // 读写锁
    onEvict   func(K, V)                // 淘汰回调
}

type entry[K comparable, V any] struct {
    key   K
    value V
}
```

#### 使用示例
```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/cache/lru"
)

func main() {
    // 创建容量为 1000 的 LRU 缓存
    cache, err := lru.New[string, int](1000)
    if err != nil {
        panic(err)
    }

    // 基本操作
    cache.Put("key1", 42)
    value, ok := cache.Get("key1")
    fmt.Printf("key1 = %d, exists: %v\n", value, ok)

    // 检查键是否存在（不影响 LRU 顺序）
    exists := cache.Contains("key1")
    fmt.Printf("key1 exists: %v\n", exists)

    // 查看值（不影响 LRU 顺序）
    value, ok = cache.Peek("key1")
    fmt.Printf("key1 = %d (peek)\n", value)

    // 删除键
    value, ok = cache.Remove("key1")
    fmt.Printf("removed key1 = %d\n", value)

    // 批量操作
    cache.Put("a", 1)
    cache.Put("b", 2)
    cache.Put("c", 3)

    keys := cache.Keys()
    fmt.Printf("keys: %v\n", keys)

    values := cache.Values()
    fmt.Printf("values: %v\n", values)

    items := cache.Items()
    fmt.Printf("items: %v\n", items)

    // 调整容量
    cache.Resize(2000)

    // 获取统计信息
    stats := cache.Stats()
    fmt.Printf("stats: %+v\n", stats)
}
```

#### 带淘汰回调的 LRU
```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/cache/lru"
)

type Resource struct {
    data []byte
}

func (r *Resource) Close() {
    fmt.Println("Resource closed")
}

func main() {
    cache, _ := lru.NewWithEvict[string, *Resource](100, func(key string, resource *Resource) {
        fmt.Printf("Evicting: %s\n", key)
        resource.Close()
    })

    cache.Put("res1", &Resource{data: []byte("data1")})
    cache.Put("res2", &Resource{data: []byte("data2")})

    // 当缓存满时，自动淘汰并调用回调
}
```

#### 性能特征
- **时间复杂度**：O(1) 所有操作
- **空间复杂度**：O(capacity)
- **内存分配**：0 B/op (零分配)
- **性能**：87M+ Put ops/sec, 85M+ Get ops/sec

### 2. LFU (Least Frequently Used)

#### 算法原理
LFU 淘汰使用频率最低的项目。使用频率分层 + 哈希表实现：
- 频率映射：frequency -> item list
- 最小频率跟踪：快速淘汰

#### 数据结构
```go
type Cache[K comparable, V any] struct {
    capacity  int
    items     map[K]*entry[K, V]           // key -> entry
    freqLists map[int]*list.List            // frequency -> list
    minFreq   int                           // 最小频率
    mu        sync.RWMutex
    onEvict   func(K, V)
}

type entry[K comparable, V any] struct {
    key     K
    value   V
    freq    int
    element *list.Element
}
```

#### 使用示例
```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/cache/lfu"
)

func main() {
    cache, _ := lfu.New[string, int](1000)

    // 多次访问会增加频率
    cache.Put("hot", 1)
    for i := 0; i < 10; i++ {
        cache.Get("hot")
    }

    cache.Put("cold", 2)
    cache.Get("cold")  // 只访问一次

    // 获取频率信息
    freq := cache.GetFreq("hot")
    fmt.Printf("'hot' frequency: %d\n", freq)  // 11

    stats := cache.Stats()
    fmt.Printf("Frequency distribution: %v\n", stats.FreqDistribution)
}
```

#### 性能特征
- **时间复杂度**：O(log n) 由于频率排序
- **空间复杂度**：O(capacity) + O(frequency_levels)
- **内存分配**：48 B/op
- **性能**：15M+ Put ops/sec, 20M+ Get ops/sec

### 3. SLRU (Segmented LRU)

#### 算法原理
SLRU 将缓存分为两个段：
- **试用段 (Probationary)**：20% 容量，新项目先进入这里
- **保护段 (Protected)**：80% 容量，第二次访问升级到这里

这种设计抗顺序扫描污染。

#### 使用示例
```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/cache/slru"
)

func main() {
    // 默认 20% 试用段，80% 保护段
    cache, _ := slru.New[string, int](1000)

    // 自定义分段比例
    cache, _ = slru.NewWithRatio[string, int](1000, 0.3)  // 30% 试用段

    cache.Put("key1", 1)
    cache.Get("key1")  // 第一次访问：key1 在试用段
    cache.Get("key1")  // 第二次访问：key1 升级到保护段

    stats := cache.Stats()
    fmt.Printf("Probationary: %d/%d\n", stats.ProbationarySize, stats.ProbationaryCapacity)
    fmt.Printf("Protected: %d/%d\n", stats.ProtectedSize, stats.ProtectedCapacity)
}
```

### 4. TinyLFU

#### 算法原理
TinyLFU 使用 Count-Min Sketch 进行频率估计：
- **Window LRU** (1%)：新项目窗口
- **Probation LRU**：试用段
- **Protected LRU**：保护段
- **Frequency Sketch**：概率性频率跟踪

#### 使用示例
```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/cache/tinylfu"
)

func main() {
    cache, _ := tinylfu.New[string, int](1000)

    cache.Put("item1", 1)
    cache.Put("item2", 2)

    // 多次访问增加频率计数
    for i := 0; i < 5; i++ {
        cache.Get("item1")
    }

    // 新项目竞争时，频率高的更可能被保留
    for i := 0; i < 1000; i++ {
        cache.Put(fmt.Sprintf("new%d", i), i)
    }

    // item1 可能仍在缓存中（因为高频）
    value, ok := cache.Get("item1")
    fmt.Printf("item1 still cached: %v, value: %d\n", ok, value)
}
```

## 算法选择策略

### 快速决策树

```
是否需要最高性能？
├─ 是 → LRU (5x faster, 零分配)
└─ 否 → 是否有明确的频率模式？
    ├─ 是 → LFU / TinyLFU / Adaptive LFU
    └─ 否 → 是否有顺序扫描？
        ├─ 是 → SLRU / MRU
        └─ 否 → Window-TinyLFU (最佳命中率)
```

### 按场景选择

| 场景 | 首选算法 | 备选算法 | 原因 |
|------|---------|---------|------|
| Web 应用缓存 | Window-TinyLFU | LRU | 混合访问模式，需要高命中率 |
| 数据库缓冲池 | LRU-K (K=2) | SLRU | 更好的未来访问相关性，抗扫描 |
| CDN 边缘缓存 | TinyLFU | Window-TinyLFU | 大规模，基于频率的访问 |
| 内存受限环境 | LRU | TinyLFU | 低内存开销，零分配 |
| 实时系统 | LRU | MRU | 可预测的 O(1) 性能 |
| 分析/OLAP 工作负载 | SLRU | MRU | 抗顺序扫描 |
| 机器学习模型缓存 | Adaptive LFU | Window-TinyLFU | 动态变化的模式 |

### 性能对比

| 算法 | 时间复杂度 | 空间开销 | 内存效率 | 抗扫描性 | 复杂度 |
|------|-----------|---------|---------|---------|--------|
| LRU | O(1) | 低 | 高 | 低 | 低 |
| LFU | O(log n) | 中 | 中 | 高 | 中 |
| MRU | O(1) | 低 | 高 | 低 | 低 |
| SLRU | O(1) | 低 | 高 | 高 | 中 |
| TinyLFU | O(1) | 低 | 高 | 高 | 中 |
| Window-TinyLFU | O(1) | 中 | 中 | 高 | 高 |
| LRU-K | O(K) | 中 | 中 | 中 | 中 |
| Adaptive LFU | O(log n) | 中 | 中 | 高 | 高 |
| FBR | O(1) | 中 | 中 | 高 | 中 |
| ARC | O(1) | 中 | 中 | 中 | 高 |
| Optimal | O(1)* | 低 | 高 | 高 | N/A |

*Optimal 需要未来知识，实际实现不可行

## 与 in-memory-cache 的区别

`lazygophers/utils` 项目中还有一个独立的 `in-memory-cache` 模块，它与 `cache` 模块的区别如下：

### cache 模块
- **位置**：`lazygophers/utils/cache`
- **用途**：纯算法实现，专注缓存策略
- **特点**：
  - 提供多种缓存算法（LRU、LFU、SLRU 等）
  - 无过期时间支持
  - 无统计指标
  - 轻量级、高性能
  - 适合作为其他缓存系统的基础组件

### in-memory-cache 模块
- **位置**：`lazygophers/utils/in-memory-cache`（如果存在）
- **用途**：功能完整的内存缓存
- **特点**：
  - 通常基于单一算法（通常是 LRU）
  - 支持过期时间（TTL）
  - 提供统计指标（命中率、淘汰数等）
  - 更适合直接用于应用层缓存

### 选择建议

**选择 cache 模块当**：
- 需要特定的缓存算法
- 构建自己的缓存系统
- 需要算法级别的控制
- 不需要过期时间

**选择 in-memory-cache 模块当**：
- 需要开箱即用的缓存
- 需要 TTL 支持
- 需要监控指标
- 快速集成到应用

## 高级用法

### 1. 自定义类型作为键

所有缓存都支持任何 `comparable` 类型作为键：

```go
// 使用结构体作为键
type Key struct {
    UserID   int
    SessionID string
}

cache, _ := lru.New[Key, []byte](1000)

key := Key{UserID: 123, SessionID: "abc"}
cache.Put(key, []byte("data"))
```

### 2. 缓存嵌套结构

```go
type User struct {
    ID       int
    Name     string
    Metadata map[string]interface{}
}

cache, _ := lru.New[int, *User](1000)

cache.Put(1, &User{
    ID:   1,
    Name: "Alice",
    Metadata: map[string]interface{}{
        "role": "admin",
    },
})

user, ok := cache.Get(1)
fmt.Println(user.Name)  // Alice
```

### 3. 并发安全使用

所有缓存都是线程安全的，可以安全地在多个 goroutine 中使用：

```go
cache, _ := lru.New[string, int](1000)

// 多个 goroutine 并发访问
var wg sync.WaitGroup
for i := 0; i < 10; i++ {
    wg.Add(1)
    go func(n int) {
        defer wg.Done()
        for j := 0; j < 1000; j++ {
            key := fmt.Sprintf("key-%d-%d", n, j)
            cache.Put(key, j)
            cache.Get(key)
        }
    }(i)
}
wg.Wait()
```

### 4. 资源清理模式

使用淘汰回调确保资源正确清理：

```go
type Connection struct {
    conn net.Conn
}

func (c *Connection) Close() {
    c.conn.Close()
}

cache, _ := lru.NewWithEvict[string, *Connection](100, func(key string, conn *Connection) {
    conn.Close()
})

// 当连接被淘汰时自动关闭
```

### 5. 动态调整缓存大小

```go
cache, _ := lru.New[string, int](1000)

// 根据内存压力动态调整
if memoryPressureHigh() {
    cache.Resize(500)   // 减小容量
} else if memoryPressureLow() {
    cache.Resize(2000)  // 增加容量
}
```

## 性能优化建议

### 1. 选择合适的容量

```go
// 根据工作集大小选择
workingSetSize := estimateWorkingSet()
cache, _ := lru.New[string, int](workingSetSize * 2)  // 2倍工作集大小
```

### 2. 避免频繁的 Resize

```go
// ❌ 不好：频繁调整
for i := 0; i < 1000; i++ {
    cache.Resize(i)
}

// ✅ 好：批量调整后稳定
cache.Resize(finalCapacity)
```

### 3. 合理使用 Peek

```go
// Peek 不影响缓存状态，适合监控场景
if cache.Peek("key") {
    // 键存在，但不影响 LRU 顺序
    log.Debug("Key exists in cache")
}
```

### 4. 批量操作优化

```go
// ❌ 不好：多次单独操作
for _, item := range items {
    cache.Put(item.Key, item.Value)
}

// ✅ 好：批量预加载
for _, item := range items {
    cache.Put(item.Key, item.Value)
}
// 注意：当前实现没有真正的批量 API，但可以预热缓存
```

## 监控和调试

### 获取统计信息

```go
stats := cache.Stats()

// LRU 统计
fmt.Printf("Size: %d/%d\n", stats.Size, stats.Capacity)

// LFU 统计
fmt.Printf("MinFreq: %d\n", stats.MinFreq)
fmt.Printf("FreqDistribution: %v\n", stats.FreqDistribution)

// SLRU 统计
fmt.Printf("Probationary: %d/%d\n", stats.ProbationarySize, stats.ProbationaryCapacity)
fmt.Printf("Protected: %d/%d\n", stats.ProtectedSize, stats.ProtectedCapacity)
```

### 监控命中率

```go
type MonitoredCache struct {
    cache *lru.Cache[string, []byte]
    hits  atomic.Int64
    misses atomic.Int64
}

func (m *MonitoredCache) Get(key string) ([]byte, bool) {
    value, ok := m.cache.Get(key)
    if ok {
        m.hits.Add(1)
    } else {
        m.misses.Add(1)
    }
    return value, ok
}

func (m *MonitoredCache) HitRate() float64 {
    total := m.hits.Load() + m.misses.Load()
    if total == 0 {
        return 0
    }
    return float64(m.hits.Load()) / float64(total)
}
```

## 常见问题

### Q1: 如何选择缓存容量？

**A**:
1. 估算工作集大小
2. 考虑内存限制
3. 测试不同容量的命中率
4. 选择 80-90% 命中率的最小容量

```go
// 经验公式
capacity := min(
    availableMemory / avgItemSize * 0.8,  // 80% 可用内存
    estimatedWorkingSet * 2,               // 2倍工作集
)
```

### Q2: LRU vs LFU 如何选择？

**A**:
- **LRU**：性能优先、内存受限、访问模式基于时间局部性
- **LFU**：命中率优先、有明确的"热点"数据、内存充足

### Q3: 如何处理并发写入？

**A**: 所有缓存都是线程安全的，但高并发下可能需要分片：

```go
type ShardedCache struct {
    shards []*lru.Cache[string, int]
    shardCount int
}

func NewShardedCache(shardCount, capacityPerShard int) *ShardedCache {
    shards := make([]*lru.Cache[string, int], shardCount)
    for i := 0; i < shardCount; i++ {
        shards[i], _ = lru.New[string, int](capacityPerShard)
    }
    return &ShardedCache{shards: shards, shardCount: shardCount}
}

func (s *ShardedCache) getShard(key string) *lru.Cache[string, int] {
    hash := fnv.New32a()
    hash.Write([]byte(key))
    return s.shards[int(hash.Sum32())%s.shardCount]
}

func (s *ShardedCache) Get(key string) (int, bool) {
    return s.getShard(key).Get(key)
}

func (s *ShardedCache) Put(key string, value int) bool {
    return s.getShard(key).Put(key, value)
}
```

### Q4: 缓存预热策略？

**A**:
```go
func warmupCache(cache *lru.Cache[string, []byte], dataset []string) {
    // 批量预加载热点数据
    for _, key := range dataset {
        if value, err := loadFromDB(key); err == nil {
            cache.Put(key, value)
        }
    }
}
```

### Q5: 如何避免缓存雪崩？

**A**:
```go
type JitterCache struct {
    cache *lru.Cache[string, int]
    rng   *rand.Rand
}

func (j *JitterCache) Get(key string) (int, bool) {
    value, ok := j.cache.Get(key)
    if !ok {
        // 加载时添加随机延迟
        time.Sleep(time.Duration(j.rng.Intn(100)) * time.Millisecond)
        value, ok = loadFromSource(key)
        if ok {
            j.cache.Put(key, value)
        }
    }
    return value, ok
}
```

## 性能基准测试

### LRU 缓存性能

```
Operation     Ops/sec      ns/op     B/op     allocs/op
Put           87,501,276   17.58     0        0
Get           85,716,580   13.75     0        0
PutGet        46,113,571   25.88     0        0
```

**关键指标**：
- 零内存分配
- 亚纳秒级延迟
- 85M+ ops/sec

### LFU 缓存性能

```
Operation     Ops/sec      ns/op     B/op     allocs/op
Put           15,828,471   67.84     48       1
Get           20,723,672   67.12     48       1
PutGet        8,832,374    147.7     96       2
```

**关键指标**：
- 每次操作 1 次内存分配
- ~67ns 延迟
- 15M+ ops/sec

### 性能对比

| 指标 | LRU | LFU | LRU 优势 |
|------|-----|-----|----------|
| Put (ns/op) | 17.58 | 67.84 | 3.9x faster |
| Get (ns/op) | 13.75 | 67.12 | 4.9x faster |
| PutGet (ns/op) | 25.88 | 147.7 | 5.7x faster |
| 内存分配 | 0 B | 48 B | 零分配 |

## 集成示例

### HTTP 缓存中间件

```go
package main

import (
    "net/http"
    "github.com/lazygophers/utils/cache/lru"
)

func CacheMiddleware(next http.Handler) http.Handler {
    cache, _ := lru.New[string, []byte](1000)

    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        key := r.URL.String()

        // 检查缓存
        if data, ok := cache.Get(key); ok {
            w.Header().Set("X-Cache", "HIT")
            w.Write(data)
            return
        }

        // 记录响应
        recorder := httptest.NewRecorder()
        next.ServeHTTP(recorder, r)

        // 缓存响应
        if recorder.Code == http.StatusOK {
            cache.Put(key, recorder.Body.Bytes())
        }

        w.Header().Set("X-Cache", "MISS")
        recorder.Result().Write(w)
    })
}
```

### 数据库查询缓存

```go
type QueryCache struct {
    cache *lru.Cache[string, Record]
    db    *sql.DB
}

type Record struct {
    ID   int
    Data []byte
}

func NewQueryCache(db *sql.DB, capacity int) *QueryCache {
    cache, _ := lru.New[string, Record](capacity)
    return &QueryCache{cache: cache, db: db}
}

func (qc *QueryCache) Query(query string) (Record, error) {
    // 检查缓存
    if record, ok := qc.cache.Get(query); ok {
        return record, nil
    }

    // 从数据库加载
    var record Record
    err := qc.db.QueryRow(query).Scan(&record.ID, &record.Data)
    if err != nil {
        return Record{}, err
    }

    // 缓存结果
    qc.cache.Put(query, record)
    return record, nil
}
```

### 多级缓存

```go
type MultiLevelCache struct {
    l1 *lru.Cache[string, []byte]  // 小而快
    l2 *tinylfu.Cache[string, []byte]  // 大而智能
}

func NewMultiLevelCache(l1Size, l2Size int) *MultiLevelCache {
    l1, _ := lru.New[string, []byte](l1Size)
    l2, _ := tinylfu.New[string, []byte](l2Size)
    return &MultiLevelCache{l1: l1, l2: l2}
}

func (mlc *MultiLevelCache) Get(key string) ([]byte, bool) {
    // L1 缓存
    if data, ok := mlc.l1.Get(key); ok {
        return data, true
    }

    // L2 缓存
    data, ok := mlc.l2.Get(key)
    if ok {
        // 提升到 L1
        mlc.l1.Put(key, data)
    }
    return data, ok
}

func (mlc *MultiLevelCache) Put(key string, data []byte) {
    mlc.l1.Put(key, data)
    mlc.l2.Put(key, data)
}
```

## 测试覆盖率

所有缓存实现都有完整的测试覆盖：

- **LRU**: 100% 测试覆盖
- **LFU**: 96.9% 测试覆盖
- **SLRU**: 97.8% 测试覆盖
- **TinyLFU**: 97.5% 测试覆盖
- **其他**: 95%+ 平均覆盖率

测试包括：
- 基本操作测试
- 并发安全测试
- 边界条件测试
- 淘汰策略测试
- 性能基准测试

## 最佳实践

### 1. 初始化检查

```go
cache, err := lru.New[string, int](capacity)
if err != nil {
    log.Fatalf("Failed to create cache: %v", err)
}
```

### 2. 优雅关闭

```go
cache.Clear()
// 等待所有操作完成
time.Sleep(100 * time.Millisecond)
```

### 3. 监控指标

```go
type CacheMetrics struct {
    hits      atomic.Int64
    misses    atomic.Int64
    evictions atomic.Int64
}

func (m *CacheMetrics) RecordHit() { m.hits.Add(1) }
func (m *CacheMetrics) RecordMiss() { m.misses.Add(1) }
func (m *CacheMetrics) RecordEviction() { m.evictions.Add(1) }

func (m *CacheMetrics) HitRate() float64 {
    total := m.hits.Load() + m.misses.Load()
    if total == 0 {
        return 0
    }
    return float64(m.hits.Load()) / float64(total)
}
```

### 4. 错误处理

```go
func safeGet(cache *lru.Cache[string, int], key string) (int, error) {
    value, ok := cache.Get(key)
    if !ok {
        return 0, fmt.Errorf("key not found: %s", key)
    }
    return value, nil
}
```

### 5. 性能测试

```go
func BenchmarkCacheAlgorithm(b *testing.B) {
    cache, _ := lru.New[string, int](1000)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        key := fmt.Sprintf("key-%d", i%1000)
        cache.Put(key, i)
        cache.Get(key)
    }
}
```

## 参考资源

- **GitHub**: https://github.com/lazygophers/utils/tree/master/cache
- **选择策略**: [SELECTION_STRATEGY.md](https://github.com/lazygophers/utils/blob/master/cache/SELECTION_STRATEGY.md)
- **性能报告**: [PERFORMANCE_REPORT.md](https://github.com/lazygophers/utils/blob/master/cache/PERFORMANCE_REPORT.md)
- **Go 缓存最佳实践**: https://github.com/golang/go/wiki/LockFile
- **缓存算法研究**: https://arxiv.org/abs/1502.06754 (TinyLFU 论文)

## 总结

`lazygophers/utils/cache` 提供了企业级的缓存解决方案：

### 核心优势
- 11 种缓存算法，覆盖各种使用场景
- 统一的 API，易于切换算法
- 类型安全，编译时检查
- 线程安全，并发性能优秀
- 高性能，零内存分配（LRU）
- 完整测试，95%+ 覆盖率

### 推荐选择
- **默认选择**: LRU - 简单、快速、可靠
- **最佳命中率**: Window-TinyLFU - 适应混合工作负载
- **频率敏感**: LFU / TinyLFU - 保留热点数据
- **抗扫描**: SLRU - 数据库、分析场景
- **自适应**: ARC - 动态工作负载

记住：最好的算法是在你的特定访问模式和约束下表现良好的算法。从简单开始，测量性能，只在有明显改进时才切换到更复杂的算法。
