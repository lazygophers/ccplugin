---
name: lazygophers-wait-skills
description: lazygophers/utils wait 模块完整指南 - 并发控制、协程池、信号量管理和任务编排的最佳实践
---

# lazygophers-wait: 并发控制与任务编排完整指南

## 概述

`wait` 模块是 `lazygophers/utils` 库中专门用于**并发控制**和**任务编排**的核心模块。它提供了基于通道的信号量池、增强的 WaitGroup、异步操作管理和带唯一性校验的协程池等高级并发原语。

### 核心特性

- **命名信号量池**: 基于 key 的全局信号量池，支持并发控制
- **协程池管理**: Worker 模式的工作池，支持任务队列和并发控制
- **异步任务编排**: Async 系列函数，支持批量任务并发执行
- **唯一性任务**: 基于唯一键的任务去重机制
- **对象池优化**: 使用 sync.Pool 复用 WaitGroup，减少内存分配
- **Panic 恢复**: 内置 panic 捕获和恢复机制
- **线程安全**: 所有操作都是 goroutine 安全的

---

## 模块架构

```
wait/
├── async.go      # 异步任务处理（Async、AsyncUnique、AsyncAlwaysWithChan）
├── group.go      # Worker 工作池（NewWorker、Add、Wait）
├── sync.go       # 信号量池（Pool、Lock、Unlock、Sync）
└── tests/        # 完整的单元测试和基准测试
```

### 设计模式

1. **对象池模式**: 使用 `sync.Pool` 复用 WaitGroup 对象
2. **生产者-消费者模式**: 通道用于任务传递和协调
3. **信号量模式**: 基于缓冲通道的并发控制
4. **Worker 池模式**: 固定数量的 goroutine 处理任务队列

---

## 核心组件详解

### 1. 信号量池 (sync.go)

#### Pool 类型

```go
type Pool struct {
    c chan struct{}  // 缓冲通道用作信号量
}
```

**工作原理**:
- 使用缓冲通道的容量作为最大并发数
- 通道中的元素数量表示当前正在使用的资源数
- 发送操作 (`<- struct{}{}`) 用于获取信号量
- 接收操作 (`<- c`) 用于释放信号量

#### 全局 Pool 管理

```go
var (
    poolLock sync.RWMutex  // 保护 poolMap 的读写锁
    poolMap  = make(map[string]*Pool)  // 全局 Pool 映射
)
```

**线程安全保证**:
- 使用读写锁保护 `poolMap` 的并发访问
- 双重检查锁定模式创建 Pool
- Pool 创建后不可修改（immutable）

#### 核心 API

##### 1.1 Ready - 初始化 Pool

```go
func Ready(key string, max int)
```

**功能**: 为指定的 key 创建或获取 Pool，设置最大并发数

**参数**:
- `key`: Pool 的唯一标识符
- `max`: 最大并发数（信号量容量）

**特性**:
- 幂等操作：多次调用相同的 key 不会重复创建
- 线程安全：支持并发创建
- 延迟初始化：首次使用时才创建

**示例**:
```go
// 初始化 API 请求限流池，最大 10 个并发
wait.Ready("api_requests", 10)

// 初始化数据库连接池，最大 5 个连接
wait.Ready("db_connections", 5)
```

##### 1.2 Lock/Unlock - 信号量操作

```go
func Lock(key string)
func Unlock(key string)
func Depth(key string) int
```

**功能**:
- `Lock`: 获取信号量，如果池满则阻塞
- `Unlock`: 释放信号量
- `Depth`: 返回当前已获取的信号量数量

**阻塞行为**:
```go
wait.Ready("resource", 2)

// 第一个获取
wait.Lock("resource")  // depth = 1
// 第二个获取
wait.Lock("resource")  // depth = 2

// 第三个获取会阻塞，直到有信号量释放
go func() {
    wait.Lock("resource")  // 阻塞等待
    defer wait.Unlock("resource")
    // ...
}()

wait.Unlock("resource")  // 释放一个，depth = 1
// 现在 goroutine 可以获取信号量了
```

**实际应用 - API 限流**:
```go
func FetchURL(url string) error {
    wait.Lock("api_requests", 10)  // 最多 10 个并发请求
    defer wait.Unlock("api_requests")

    resp, err := http.Get(url)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    // 处理响应...
    return nil
}

// 并发请求
urls := []string{"https://api.example.com/1", "https://api.example.com/2", ...}
for _, url := range urls {
    go FetchURL(url)
}
```

##### 1.3 Sync - 同步执行

```go
func Sync(key string, logic func() error) error
```

**功能**: 在信号量保护下同步执行逻辑函数

**特性**:
- 自动获取和释放信号量
- 记录日志（debug 和 info 级别）
- 传播逻辑函数的错误

**示例**:
```go
err := wait.Sync("critical_section", func() error {
    // 受保护的代码段
    return updateDatabase()
})
if err != nil {
    log.Errorf("操作失败: %v", err)
}
```

#### Pool 实例方法

```go
func (p *Pool) Lock()       // 获取信号量
func (p *Pool) Unlock()     // 释放信号量
func (p *Pool) Depth() int  // 当前深度
```

**直接使用 Pool 实例**:
```go
// 注意：通常通过全局函数使用，不需要直接操作 Pool 实例
// 这些方法主要用于内部实现
```

---

### 2. Worker 工作池 (group.go)

#### Worker 类型

```go
type Worker struct {
    w *sync.WaitGroup  // 等待组
    c chan func()      // 任务队列
}
```

**工作流程**:
1. 创建固定数量的 worker goroutine
2. 通过通道接收任务函数
3. 并发执行任务
4. 等待所有任务完成

#### 核心 API

##### 2.1 NewWorker - 创建 Worker

```go
func NewWorker(max int) *Worker
```

**参数**:
- `max`: worker goroutine 数量

**特殊处理**:
- `max = 0`: 使用缓冲大小为 1 的通道（任务不会执行）
- `max > 0`: 创建 `max` 个 worker goroutine

**内存优化**:
- 从全局对象池 `Wgp` 获取 WaitGroup
- 在 `Wait()` 后放回对象池

##### 2.2 Add - 提交任务

```go
func (p *Worker) Add(fn func())
```

**行为**:
- 将任务函数发送到任务队列
- 如果队列满，阻塞等待
- 任务在独立的 goroutine 中执行

##### 2.3 Wait - 等待完成

```go
func (p *Worker) Wait()
```

**操作**:
1. 关闭任务通道（停止接收新任务）
2. 等待所有 worker 完成
3. 将 WaitGroup 放回对象池

**重要**: 调用 `Wait()` 后不可再调用 `Add()`

#### 完整示例

```go
// 创建 3 个 worker 的池
worker := wait.NewWorker(3)

var (
    results []int
    mu      sync.Mutex
)

// 提交 10 个任务
for i := 0; i < 10; i++ {
    i := i  // 捕获循环变量
    worker.Add(func() {
        // 模拟耗时操作
        time.Sleep(100 * time.Millisecond)

        mu.Lock()
        results = append(results, i)
        mu.Unlock()
    })
}

// 等待所有任务完成
worker.Wait()

fmt.Printf("完成了 %d 个任务\n", len(results))
```

#### Panic 恢复机制

```go
func NewWorker(max int) *Worker {
    // ...
    for i := 0; i < max; i++ {
        routine.GoWithRecover(func() error {
            defer w.Done()

            for fn := range c {
                func() {
                    // 捕获 panic 并记录日志
                    defer runtime.CachePanic()
                    fn()
                }()
            }
            return nil
        })
    }
}
```

**特性**:
- 每个任务在独立闭包中执行
- Panic 不会影响其他任务
- 使用 `runtime.CachePanic()` 记录 panic 信息

---

### 3. 异步任务处理 (async.go)

#### 3.1 Async - 批量异步任务

```go
func Async[M any](process int, push func(chan M), logic func(M))
```

**泛型参数**:
- `M`: 任务类型

**参数**:
- `process`: 并发处理的协程数量
- `push`: 任务推送函数
- `logic`: 任务处理逻辑

**工作流程**:
1. 创建缓冲通道（容量 = process * 2）
2. 从对象池获取 WaitGroup
3. 启动 `process` 个工作协程
4. 调用 `push` 函数推送任务
5. 关闭通道并等待所有任务完成
6. 将 WaitGroup 放回对象池

**示例 - 并发处理数据**:
```go
type Task struct {
    ID    int
    Data  string
}

var (
    results []string
    mu      sync.Mutex
)

// 任务处理逻辑
logic := func(task Task) {
    // 处理任务
    result := processTask(task.Data)

    mu.Lock()
    results = append(results, result)
    mu.Unlock()
}

// 任务推送
push := func(ch chan Task) {
    for i := 0; i < 100; i++ {
        ch <- Task{ID: i, Data: fmt.Sprintf("data-%d", i)}
    }
}

// 启动 5 个协程并发处理
wait.Async(5, push, logic)

fmt.Printf("处理完成，结果数: %d\n", len(results))
```

#### 3.2 AsyncAlwaysWithChan - 持续处理

```go
func AsyncAlwaysWithChan[M any](process int, c chan M, logic func(M))
```

**特性**:
- 持续监听通道中的任务
- 调用者负责关闭通道以停止协程
- 适用于长生命周期的工作池

**示例 - 消息队列消费者**:
```go
type Message struct {
    ID      string
    Content []byte
}

messageCh := make(chan Message, 100)

// 启动 10 个消费者协程
wait.AsyncAlwaysWithChan(10, messageCh, func(msg Message) {
    // 处理消息
    handleMessage(msg)
})

// 生产者持续发送消息
for {
    msg := receiveMessage()
    messageCh <- msg
}

// 优雅关闭
close(messageCh)
time.Sleep(time.Second)  // 等待处理完成
```

#### 3.3 AsyncUnique - 唯一性任务

```go
type UniqueTask interface {
    UniqueKey() string
}

func AsyncUnique[M UniqueTask](process int, push func(chan M), logic func(M))
```

**特性**:
- 使用 `sync.Map` 存储任务唯一键
- 相同 `UniqueKey()` 的任务不会并发执行
- 任务完成后从 map 中删除

**示例 - 防止重复处理**:
```go
type UserTask struct {
    UserID int
    Action string
}

func (t UserTask) UniqueKey() string {
    return fmt.Sprintf("user-%d", t.UserID)
}

logic := func(task UserTask) {
    // 同一用户的任务不会并发执行
    updateUser(task.UserID, task.Action)
}

push := func(ch chan UserTask) {
    // 即使推送重复用户ID的任务，也会被过滤
    ch <- UserTask{UserID: 1, Action: "update"}
    ch <- UserTask{UserID: 2, Action: "update"}
    ch <- UserTask{UserID: 1, Action: "delete"}  // 会等待前一个完成
}

wait.AsyncUnique(5, push, logic)
```

#### 3.4 AsyncAlwaysUnique - 持续唯一性处理

```go
func AsyncAlwaysUnique[M UniqueTask](process int, logic func(M)) chan M
func AsyncAlwaysUniqueWithChan[M UniqueTask](c chan M, process int, logic func(M))
```

**特性**:
- 结合了持续处理和唯一性校验
- 返回通道用于推送任务
- 适用于需要去重的长生命周期场景

**示例 - API 请求去重**:
```go
type APIRequest struct {
    Endpoint string
    Params   map[string]string
}

func (r APIRequest) UniqueKey() string {
    return fmt.Sprintf("%s:%v", r.Endpoint, r.Params)
}

// 创建持续去重处理器
requestCh := wait.AsyncAlwaysUnique(5, func(req APIRequest) {
    // 相同 endpoint + params 的请求不会并发执行
    response := callAPI(req.Endpoint, req.Params)
    processResponse(response)
})

// 推送请求（会自动去重）
requestCh <- APIRequest{Endpoint: "/users/1", Params: nil}
requestCh <- APIRequest{Endpoint: "/users/1", Params: nil}  // 等待前一个完成
requestCh <- APIRequest{Endpoint: "/users/2", Params: nil}
```

---

## 全局对象池

### Wgp - WaitGroup 对象池

```go
var Wgp = sync.Pool{
    New: func() interface{} {
        return &sync.WaitGroup{}
    },
}
```

**使用位置**:
- `Async` 系列函数
- `Worker.NewWorker`

**优势**:
- 减少 GC 压力
- 复用 WaitGroup 对象
- 提升性能（在高频调用场景下）

**模式**:
```go
w := Wgp.Get().(*sync.WaitGroup)
defer Wgp.Put(w)
```

---

## 并发安全与错误处理

### 并发安全保证

1. **Pool 创建**: 双重检查锁定 + 读写锁保护
2. **Pool 操作**: 通道本身是并发安全的
3. **Worker**: 通道 + WaitGroup 保证安全
4. **Async**: 通道 + WaitGroup + sync.Map（Unique）

### Panic 恢复策略

#### Worker 模式

```go
func NewWorker(max int) *Worker {
    // ...
    routine.GoWithRecover(func() error {
        defer w.Done()
        for fn := range c {
            func() {
                defer runtime.CachePanic()  // 捕获 panic
                fn()
            }()
        }
        return nil
    })
}
```

**特性**:
- 每个任务在独立闭包中执行
- Panic 不会影响 worker 继续运行
- Panic 信息会被记录到日志

#### Async 模式

```go
routine.GoWithRecover(func() error {
    defer w.Done()
    for x := range c {
        logic(x)  // 如果 panic，会被 GoWithRecover 捕获
    }
    return nil
})
```

### 错误处理最佳实践

```go
// 1. 使用 defer 确保资源释放
wait.Lock("resource")
defer wait.Unlock("resource")

// 2. 错误传播
err := wait.Sync("key", func() error {
    return doSomething()
})

// 3. Panic 隔离（Worker 自动处理）
worker.Add(func() {
    // 即使 panic 也不会影响其他任务
})

// 4. 超时控制（需要自己实现 context）
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

go func() {
    wait.Lock("resource")
    defer wait.Unlock("resource")

    select {
    case <-ctx.Done():
        return
    default:
        // 执行操作
    }
}()
```

---

## 性能优化

### 1. 缓冲区大小

```go
// Async 使用 process * 2 作为缓冲区
c := make(chan M, process*2)

// Worker 使用 max 作为缓冲区
c := make(chan func(), bufferSize)
```

**设计考虑**:
- 避免通道阻塞
- 平衡内存使用和性能
- 根据任务特性调整

### 2. 对象池

```go
// 复用 WaitGroup，减少内存分配
w := Wgp.Get().(*sync.WaitGroup)
defer Wgp.Put(w)
```

**性能提升**:
- 减少内存分配
- 降低 GC 压力
- 高频调用场景下显著

### 3. sync.Map 用于唯一性校验

```go
var uniqueMap sync.Map

uniqueMap.LoadOrStore(key, struct{}{})  // O(1) 操作
uniqueMap.Delete(key)
```

**优势**:
- 无锁读取（fast path）
- 适合读多写少场景
- 内置并发安全

### 基准测试结果

根据测试代码的基准测试：

```go
// Worker 基准测试
func BenchmarkWorker(b *testing.B) {
    b.Run("worker_creation", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            worker := wait.NewWorker(10)
            worker.Wait()
        }
    })

    b.Run("task_execution", func(b *testing.B) {
        worker := wait.NewWorker(10)
        for i := 0; i < b.N; i++ {
            worker.Add(func() {
                time.Sleep(time.Microsecond)
            })
        }
        worker.Wait()
    })
}

// Sync 基准测试
func BenchmarkSync(b *testing.B) {
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            wait.Sync(key, func() error {
                time.Sleep(time.Microsecond)
                return nil
            })
        }
    })
}
```

**性能特点**:
- O(1) 信号量获取/释放
- 最小内存开销
- 支持数千并发操作
- 读密集型负载下的无锁操作

---

## 使用场景

### 1. API 限流

```go
func MakeAPIRequest(endpoint string) error {
    wait.Lock("api_requests", 10)
    defer wait.Unlock("api_requests")

    resp, err := http.Get(endpoint)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    return processResponse(resp)
}

// 并发请求
for _, url := range urls {
    go MakeAPIRequest(url)
}
```

### 2. 数据库连接池

```go
func QueryDatabase(sql string) (*Result, error) {
    wait.Lock("db_connections", 5)
    defer wait.Unlock("db_connections")

    return db.Query(sql)
}
```

### 3. 批量数据处理

```go
type BatchTask struct {
    ID   int
    Data []byte
}

var results []Result
var mu sync.Mutex

// Worker 模式
worker := wait.NewWorker(10)
for _, item := range items {
    item := item
    worker.Add(func() {
        result := processData(item.Data)

        mu.Lock()
        results = append(results, result)
        mu.Unlock()
    })
}
worker.Wait()
```

### 4. 消息队列消费者

```go
messageCh := make(chan Message, 1000)

// 启动消费者池
wait.AsyncAlwaysWithChan(20, messageCh, func(msg Message) {
    // 处理消息
    handleMessage(msg)
})

// 消费者持续运行...
```

### 5. 唯一性任务去重

```go
type CacheUpdate struct {
    CacheKey string
    Data     []byte
}

func (c CacheUpdate) UniqueKey() string {
    return c.CacheKey
}

// 确保同一 cache key 不会并发更新
updateCh := wait.AsyncAlwaysUnique(5, func(task CacheUpdate) {
    updateCache(task.CacheKey, task.Data)
})

updateCh <- CacheUpdate{CacheKey: "user:123", Data: data1}
updateCh <- CacheUpdate{CacheKey: "user:123", Data: data2}  // 等待前一个完成
```

### 6. 资源清理

```go
// 使用 Sync 确保资源安全释放
err := wait.Sync("file_cleanup", func() error {
    file, err := os.Open(path)
    if err != nil {
        return err
    }
    defer file.Close()

    return processData(file)
})
```

### 7. 并发控制的服务保护

```go
func ProcessRequest(req Request) error {
    // 限制每个用户的并发请求数
    key := fmt.Sprintf("user:%s", req.UserID)
    wait.Lock(key, 3)
    defer wait.Unlock(key)

    return handleRequest(req)
}
```

---

## 最佳实践

### 1. Key 命名规范

```go
// ✅ 好的命名
wait.Ready("api:github:requests", 10)
wait.Ready("db:mysql:connections", 5)
wait.Ready("cache:redis:updates", 20)

// ❌ 不好的命名
wait.Ready("pool1", 10)
wait.Ready("a", 5)
```

**建议**:
- 使用冒号分隔层级：`domain:resource:action`
- 包含具体资源类型
- 便于监控和调试

### 2. 资源释放

```go
// ✅ 使用 defer 确保释放
func DoSomething() {
    wait.Lock("resource")
    defer wait.Unlock("resource")

    // 即使 panic 也会释放
    doWork()
}

// ❌ 手动释放容易遗漏
func DoSomething() {
    wait.Lock("resource")
    doWork()
    wait.Unlock("resource")  // 如果 doWork() panic，不会执行
}
```

### 3. 并发数选择

```go
// CPU 密集型任务
worker := wait.NewWorker(runtime.NumCPU())

// I/O 密集型任务
worker := wait.NewWorker(runtime.NumCPU() * 2)

// 轻量级任务
worker := wait.NewWorker(100)
```

### 4. 避免死锁

```go
// ✅ 正确 - 顺序获取
wait.Lock("resource1")
defer wait.Unlock("resource1")

wait.Lock("resource2")
defer wait.Unlock("resource2")

// ❌ 错误 - 可能死锁
go func() {
    wait.Lock("resource1")
    wait.Lock("resource2")
}()

go func() {
    wait.Lock("resource2")
    wait.Lock("resource1")  // 死锁
}()
```

### 5. 监控和调试

```go
// 定期检查 Pool 深度
go func() {
    ticker := time.NewTicker(10 * time.Second)
    for range ticker.C {
        depth := wait.Depth("api_requests")
        log.Infof("当前并发数: %d", depth)
    }
}()
```

### 6. 优雅关闭

```go
// Worker 优雅关闭
func (s *Service) Stop() {
    // 停止接收新任务
    close(s.taskCh)

    // 等待所有任务完成
    s.worker.Wait()

    log.Info("Service stopped gracefully")
}

// Async 优雅关闭
func (c *Consumer) Stop() {
    close(c.messageCh)
    time.Sleep(time.Second)  // 等待处理完成
}
```

---

## 注意事项与陷阱

### 1. Pool 不存在会 panic

```go
// ❌ 错误 - Pool 未初始化
wait.Lock("uninitialized_pool")  // panic

// ✅ 正确 - 先初始化
wait.Ready("my_pool", 10)
wait.Lock("my_pool")
defer wait.Unlock("my_pool")
```

### 2. Worker 零值特殊处理

```go
// max = 0 时的特殊行为
worker := wait.NewWorker(0)
worker.Add(func() {
    // 这个任务不会执行
})
worker.Wait()
```

### 3. Wait 后不可 Add

```go
worker := wait.NewWorker(3)

// ... 添加任务
worker.Wait()

// ❌ 错误 - Wait 后不可再 Add
worker.Add(func() {})  // 通道已关闭
```

### 4. 通道容量考虑

```go
// Async 内部使用 process * 2
// 如果任务生产速度 > 消费速度，可能需要调整
```

### 5. UniqueTask 的时机

```go
// AsyncUnique 在任务开始时检查
// 如果任务执行时间长，可能导致误判

// 解决：在任务完成时删除
logic := func(task Task) {
    // ... 处理任务
    uniqueMap.Delete(task.UniqueKey())  // 完成后删除
}
```

---

## 与标准库对比

### vs sync.WaitGroup

```go
// 标准库
var wg sync.WaitGroup
wg.Add(1)
go func() {
    defer wg.Done()
    // ...
}()
wg.Wait()

// wait 模块（Worker）
worker := wait.NewWorker(1)
worker.Add(func() {
    // ...
})
worker.Wait()
```

**优势**:
- 自动 panic 恢复
- 内置任务队列
- 对象池优化
- 更简洁的 API

### vs channel

```go
// 标准 channel
ch := make(chan int, 10)
// ... 手动管理 goroutine

// wait.Async
wait.Async(10, push, logic)  // 自动管理
```

**优势**:
- 自动并发控制
- 内置错误处理
- 唯一性支持
- 更高层抽象

---

## 测试策略

### 单元测试示例

```go
func TestAsync(t *testing.T) {
    var results []int
    var mu sync.Mutex

    logic := func(x int) {
        mu.Lock()
        defer mu.Unlock()
        results = append(results, x*2)
    }

    push := func(ch chan int) {
        for i := 1; i <= 5; i++ {
            ch <- i
        }
    }

    wait.Async(3, push, logic)

    assert.Len(t, results, 5)
    assert.ElementsMatch(t, []int{2, 4, 6, 8, 10}, results)
}
```

### 并发测试

```go
func TestConcurrentLock(t *testing.T) {
    wait.Ready("test", 5)

    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            wait.Lock("test")
            time.Sleep(10 * time.Millisecond)
            wait.Unlock("test")
        }()
    }

    wg.Wait()
    assert.Equal(t, 0, wait.Depth("test"))
}
```

---

## 参考资料

- **GitHub**: https://github.com/lazygophers/utils/tree/master/wait
- **依赖模块**:
  - `github.com/lazygophers/log`: 日志记录
  - `github.com/lazygophers/utils/routine`: 协程管理
  - `github.com/lazygophers/utils/runtime`: Panic 捕获

---

## 总结

`wait` 模块提供了完整的并发控制工具集：

| 功能 | 适用场景 | 核心类型 |
|------|---------|---------|
| **信号量池** | 限流、资源控制 | Pool |
| **Worker 池** | 批量任务处理 | Worker |
| **Async** | 并发任务编排 | 泛型函数 |
| **AsyncUnique** | 任务去重 | UniqueTask 接口 |

**关键优势**:
1. 简洁的 API，易于使用
2. 内置 panic 恢复，健壮性强
3. 对象池优化，性能优秀
4. 线程安全，无需额外同步

**使用建议**:
- API 限流 → Pool + Lock/Unlock
- 批量处理 → Worker
- 任务编排 → Async
- 消息队列 → AsyncAlwaysWithChan
- 去重处理 → AsyncUnique
