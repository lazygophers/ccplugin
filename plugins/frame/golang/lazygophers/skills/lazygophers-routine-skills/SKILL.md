---
name: lazygophers-routine-skills
description: lazygophers/utils routine 模块完整指南 - 增强的协程管理、错误恢复、缓存机制
---

# lazygophers/utils routine 模块完整指南

## 概述

`routine` 模块提供了增强的 goroutine 管理工具，包括：

- **增强的 goroutine 启动函数** - 带错误处理、panic 恢复、日志集成
- **生命周期钩子** - BeforeRoutine/AfterRoutine 回调机制
- **协程本地缓存** - 线程安全的泛型缓存实现
- **日志追踪集成** - 基于 goroutine ID 的分布式追踪支持

## 核心组件

### 1. Goroutine 启动函数

#### Go - 基础错误处理

启动带错误日志记录的 goroutine：

```go
import "github.com/lazygophers/utils/routine"

routine.Go(func() error {
    // 业务逻辑
    if err := doSomething(); err != nil {
        return err  // 错误会自动记录到日志
    }
    return nil
})
```

**特性：**
- 错误自动记录到日志（使用 `github.com/lazygophers/log`）
- 触发 before/after 生命周期钩子
- 不会因为 panic 导致程序崩溃（但 panic 不会被恢复）

#### GoWithRecover - Panic 恢复

启动带 panic 恢复和完整堆栈追踪的 goroutine：

```go
routine.GoWithRecover(func() error {
    // 可能 panic 的代码
    riskyOperation()
    return nil
})
```

**特性：**
- 捕获 panic 并记录完整堆栈信息
- 错误自动记录
- 适合处理不可信的第三方代码或可能 panic 的业务逻辑

**panic 处理流程：**
```go
// 源码中的 panic 处理逻辑
defer func() {
    if err := recover(); err != nil {
        log.Errorf("err:%v", err)
        st := debug.Stack()
        if len(st) > 0 {
            log.Errorf("dump stack (%s):", err)
            lines := strings.Split(string(st), "\n")
            for _, line := range lines {
                log.Error("  ", line)
            }
        } else {
            log.Errorf("stack is empty (%s)", err)
        }
    }
}()
```

#### GoWithMustSuccess - 关键任务

启动必须成功的 goroutine，错误时退出程序：

```go
routine.GoWithMustSuccess(func() error {
    // 关键初始化逻辑
    if err := initCriticalSystem(); err != nil {
        return err  // 调用 os.Exit(1)
    }
    return nil
})
```

**特性：**
- 错误时调用 `os.Exit(1)` 终止程序
- 适用于关键初始化步骤或不能失败的操作
- 错误记录会在程序退出前完成

### 2. 生命周期钩子

#### BeforeRoutine - 前置钩子

在 goroutine 启动前执行的回调：

```go
routine.AddBeforeRoutine(func(baseGid, currentGid int64) {
    log.Infof("Goroutine %d starting from %d", currentGid, baseGid)
})
```

**内置钩子：**
```go
// 源码中的默认实现（init 函数）
func init() {
    routine.AddBeforeRoutine(func(baseGid, currentGid int64) {
        // 设置追踪 ID：父goroutine.traceID.新生成的traceID
        log.SetTraceWithGID(currentGid,
            fmt.Sprintf("%s.%s",
                log.GetTraceWithGID(baseGid),
                log.GenTraceId()))
    })
}
```

#### AfterRoutine - 后置钩子

在 goroutine 结束后执行的回调：

```go
routine.AddAfterRoutine(func(currentGid int64) {
    log.Infof("Goroutine %d completed", currentGid)
})
```

**内置钩子：**
```go
// 源码中的默认实现
func init() {
    routine.AddAfterRoutine(func(currentGid int64) {
        // 清理 goroutine 的追踪上下文
        log.DelTraceWithGID(currentGid)
    })
}
```

**钩子调用时机：**
```go
// Go/GoWithRecover/GoWithMustSuccess 内部流程
baseGid := goid.Get()  // 获取父 goroutine ID
go func() {
    currentGid := goid.Get()  // 获取当前 goroutine ID
    before(baseGid, currentGid)  // 调用所有 BeforeRoutine
    defer func() {
        after(currentGid)  // 调用所有 AfterRoutine
    }()

    // 执行用户函数
    err := f()
    if err != nil {
        log.Errorf("err:%v", err)
    }
}()
```

### 3. 协程缓存 (Cache)

#### 基础用法

线程安全的泛型缓存，支持过期时间：

```go
import "github.com/lazygophers/utils/routine"

// 创建缓存：string -> int
cache := routine.NewCache[string, int]()

// 设置值
cache.Set("key1", 42)

// 获取值
value, ok := cache.Get("key1")
if ok {
    fmt.Println(value)  // 42
}

// 获取值（带默认值）
value = cache.GetWithDef("key2", 100)  // key2 不存在，返回 100

// 删除值
cache.Delete("key1")
```

#### 过期时间

设置带过期时间的缓存项：

```go
// 设置 5 秒后过期
cache.SetEx("session", userData, 5*time.Second)

value, ok := cache.Get("session")
if !ok {
    // 已过期或不存在
}
```

**注意：** 当前实现存在过期逻辑 bug（见源码第 30 行）：
```go
// 错误的逻辑：时间未过期时删除
if !v.expire.IsZero() && time.Now().Before(v.expire) {
    p.Delete(key)
    return v.value, false
}
```

**临时解决方案：** 使用 `Set` 代替 `SetEx`，或手动管理过期时间。

#### 类型安全

泛型支持多种键值类型：

```go
// string -> string
stringCache := routine.NewCache[string, string]()
stringCache.Set("hello", "world")

// int -> bool
intCache := routine.NewCache[int, bool]()
intCache.Set(42, true)

// string -> struct
type User struct {
    Name string
    Age  int
}
userCache := routine.NewCache[string, User]()
userCache.Set("user:1", User{Name: "Alice", Age: 30})
```

#### 并发安全

```go
cache := routine.NewCache[int, string]()

// 多个 goroutine 并发写入
for i := 0; i < 10; i++ {
    go func(id int) {
        cache.Set(id, fmt.Sprintf("value_%d", id))
    }(i)
}

// 多个 goroutine 并发读取
for i := 0; i < 10; i++ {
    go func(id int) {
        value, _ := cache.Get(id)
        fmt.Println(value)
    }(i)
}
```

## 使用场景

### 1. 后台任务处理

```go
// 定时清理任务
routine.Go(func() error {
    ticker := time.NewTicker(time.Hour)
    defer ticker.Stop()

    for range ticker.C {
        if err := cleanupOldData(); err != nil {
            log.Errorf("Cleanup failed: %v", err)
            // 继续运行，不退出
        }
    }
    return nil
})
```

### 2. 并行数据处理

```go
// 并行处理多个任务
tasks := []string{"task1", "task2", "task3"}

for _, task := range tasks {
    task := task  // 闭包捕获
    routine.Go(func() error {
        return processTask(task)
    })
}
```

### 3. 危险操作的 panic 恢复

```go
// 处理可能 panic 的第三方代码
routine.GoWithRecover(func() error {
    // 调用不可信的第三方库
    return thirdPartyLibrary.RiskyFunction()
})
```

### 4. 关键初始化

```go
// 关键系统初始化
routine.GoWithMustSuccess(func() error {
    // 连接关键数据库
    if err := connectToPrimaryDB(); err != nil {
        return err  // 失败时程序退出
    }
    return nil
})
```

### 5. 分布式追踪

```go
// 添加自定义追踪钩子
routine.AddBeforeRoutine(func(baseGid, currentGid int64) {
    // 记录 goroutine 启动
    metrics.GoroutineStarted.Inc()
})

routine.AddAfterRoutine(func(currentGid int64) {
    // 记录 goroutine 结束
    metrics.GoroutineCompleted.Inc()
})

// 使用 routine.Go 自动获得追踪支持
routine.Go(func() error {
    // 此处的日志会自动包含追踪 ID
    log.Info("Processing request")
    return nil
})
```

### 6. 协程本地数据缓存

```go
// 为每个 goroutine 缓存数据
func processData(userID string) {
    cache := routine.NewCache[string, *User]()

    // 检查缓存
    if user, ok := cache.Get(userID); ok {
        return user
    }

    // 从数据库加载
    user := loadUserFromDB(userID)
    cache.Set(userID, user)
    return user
}
```

## 最佳实践

### 1. 错误处理

```go
// ✅ 正确：返回错误
routine.Go(func() error {
    if err := doWork(); err != nil {
        return err  // 错误会自动记录
    }
    return nil
})

// ❌ 错误：在 goroutine 中直接 panic
routine.Go(func() error {
    if err := doWork(); err != nil {
        panic(err)  // 不会被 Go 恢复
    }
    return nil
})

// ✅ 正确：使用 GoWithRecover 处理 panic
routine.GoWithRecover(func() error {
    if err := doWork(); err != nil {
        panic(err)  // 会被恢复并记录
    }
    return nil
})
```

### 2. 闭包变量捕获

```go
// ❌ 错误：所有 goroutine 使用相同的 i
for i := 0; i < 10; i++ {
    routine.Go(func() error {
        fmt.Println(i)  // 可能打印 10 十次
        return nil
    })
}

// ✅ 正确：使用局部变量
for i := 0; i < 10; i++ {
    i := i  // 创建新的变量
    routine.Go(func() error {
        fmt.Println(i)  // 打印 0-9
        return nil
    })
}
```

### 3. 资源清理

```go
routine.Go(func() error {
    // 使用 defer 确保资源清理
    file, err := os.Open("data.txt")
    if err != nil {
        return err
    }
    defer file.Close()

    // 处理文件
    return processData(file)
})
```

### 4. Goroutine 同步

```go
// 使用 sync.WaitGroup 等待多个 goroutine
var wg sync.WaitGroup

for i := 0; i < 10; i++ {
    wg.Add(1)
    routine.Go(func() error {
        defer wg.Done()
        return doWork(i)
    })
}

wg.Wait()  // 等待所有 goroutine 完成
```

## 性能考虑

### 基准测试结果

```go
// 来自 routine_test.go 的基准测试
func BenchmarkGo(b *testing.B) {
    var wg sync.WaitGroup
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        wg.Add(1)
        routine.Go(func() error {
            wg.Done()
            return nil
        })
    }
    wg.Wait()
}

func BenchmarkGoWithRecover(b *testing.B) {
    var wg sync.WaitGroup
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        wg.Add(1)
        routine.GoWithRecover(func() error {
            wg.Done()
            return nil
        })
    }
    wg.Wait()
}
```

**性能特性：**
- `Go`：最小开销，仅增加错误日志和生命周期钩子
- `GoWithRecover`：略高开销，添加 defer recover 和堆栈追踪
- `GoWithMustSuccess`：与 `Go` 相当，但错误时会终止程序

### 内存管理

```go
// ✅ 正确：避免在 goroutine 中捕获大对象
largeData := make([]byte, 1024*1024)  // 1MB

routine.Go(func() error {
    // 处理数据，但不捕获 largeData
    return processLargeData(largeData)
})

// ❌ 错误：闭包捕获大对象
routine.Go(func() error {
    // largeData 被闭包引用，不会被 GC
    time.Sleep(time.Hour)
    return nil
})
```

## 依赖关系

### 外部依赖

```go
import (
    "github.com/lazygophers/log"        // 日志库
    "github.com/petermattis/goid"       // Goroutine ID 获取
    "runtime/debug"                     // 堆栈追踪
)
```

### 日志集成

`routine` 模块深度集成 `github.com/lazygophers/log`：

- 错误自动记录到日志系统
- 基于 goroutine ID 的分布式追踪
- 自动生成和传播追踪 ID

**追踪 ID 生成规则：**
```
子goroutine追踪ID = 父goroutine追踪ID + "." + 新生成的UUID
```

## 测试指南

### 单元测试

```go
func TestMyRoutine(t *testing.T) {
    done := make(chan bool, 1)

    routine.Go(func() error {
        // 测试逻辑
        done <- true
        return nil
    })

    select {
    case <-done:
        // 成功
    case <-time.After(time.Second):
        t.Error("Timeout")
    }
}
```

### 并发测试

```go
func TestConcurrent(t *testing.T) {
    var wg sync.WaitGroup
    counter := int32(0)

    for i := 0; i < 100; i++ {
        wg.Add(1)
        routine.Go(func() error {
            defer wg.Done()
            atomic.AddInt32(&counter, 1)
            return nil
        })
    }

    wg.Wait()
    if atomic.LoadInt32(&counter) != 100 {
        t.Error("Counter mismatch")
    }
}
```

### Panic 测试

```go
func TestPanicRecovery(t *testing.T) {
    done := make(chan bool, 1)

    routine.GoWithRecover(func() error {
        defer func() { done <- true }()
        panic("test panic")
    })

    select {
    case <-done:
        // panic 被恢复
    case <-time.After(time.Second):
        t.Error("Timeout")
    }
}
```

## 常见问题

### Q1: 为什么使用 routine.Go 而不是原生 go？

**A:** `routine.Go` 提供：
- 自动错误日志记录
- 分布式追踪支持
- 统一的生命周期管理
- 更好的调试体验

### Q2: GoWithRecover 会捕获所有 panic 吗？

**A:** 是的，但要注意：
- 只捕获当前 goroutine 的 panic
- 不会恢复其他 goroutine 的 panic
- 恢复后程序继续运行（不会崩溃）

### Q3: 何时使用 GoWithMustSuccess？

**A:** 仅用于关键初始化：
- 程序启动时的必要步骤
- 不能失败的配置加载
- 关键连接建立（数据库、消息队列等）

**避免滥用：** 正常业务逻辑不应使用此函数。

### Q4: Cache 的过期机制可靠吗？

**A:** 当前实现存在 bug，建议：
- 暂不使用 `SetEx` 方法
- 手动实现过期逻辑
- 关注官方更新修复

### Q5: 如何追踪 goroutine 的执行？

**A:** 使用内置钩子：
```go
routine.AddBeforeRoutine(func(baseGid, currentGid int64) {
    log.Infof("[%d -> %d] Starting", baseGid, currentGid)
})

routine.AddAfterRoutine(func(currentGid int64) {
    log.Infof("[%d] Completed", currentGid)
})
```

## 完整示例

### 示例 1：Web 服务器请求处理

```go
package main

import (
    "fmt"
    "net/http"
    "time"

    "github.com/lazygophers/utils/routine"
)

func main() {
    // 添加自定义钩子
    routine.AddBeforeRoutine(func(baseGid, currentGid int64) {
        fmt.Printf("[Trace] Request starting: %d -> %d\n", baseGid, currentGid)
    })

    http.HandleFunc("/api/process", func(w http.ResponseWriter, r *http.Request) {
        // 异步处理请求
        routine.GoWithRecover(func() error {
            // 模拟处理
            time.Sleep(100 * time.Millisecond)
            fmt.Fprintf(w, "Processed")
            return nil
        })
        fmt.Fprintf(w, "Request accepted")
    })

    http.ListenAndServe(":8080", nil)
}
```

### 示例 2：批量数据处理

```go
package main

import (
    "fmt"
    "sync"

    "github.com/lazygophers/utils/routine"
)

func main() {
    items := []int{1, 2, 3, 4, 5}
    results := make(chan int, len(items))
    var wg sync.WaitGroup

    for _, item := range items {
        item := item
        wg.Add(1)

        routine.GoWithRecover(func() error {
            defer wg.Done()

            // 处理数据
            result := item * 2
            results <- result

            return nil
        })
    }

    // 等待所有处理完成
    go func() {
        wg.Wait()
        close(results)
    }()

    // 收集结果
    for result := range results {
        fmt.Printf("Result: %d\n", result)
    }
}
```

### 示例 3：带缓存的 worker pool

```go
package main

import (
    "fmt"
    "sync"

    "github.com/lazygophers/utils/routine"
)

func main() {
    cache := routine.NewCache[string, string]()
    var wg sync.WaitGroup

    // Worker 1: 生产数据
    wg.Add(1)
    routine.Go(func() error {
        defer wg.Done()
        for i := 0; i < 10; i++ {
            key := fmt.Sprintf("key%d", i)
            value := fmt.Sprintf("value%d", i)
            cache.Set(key, value)
        }
        return nil
    })

    // Worker 2: 消费数据
    wg.Add(1)
    routine.Go(func() error {
        defer wg.Done()
        for i := 0; i < 10; i++ {
            key := fmt.Sprintf("key%d", i)
            if value, ok := cache.Get(key); ok {
                fmt.Printf("Got %s: %s\n", key, value)
            }
        }
        return nil
    })

    wg.Wait()
}
```

## 参考资料

- **源码位置**: `github.com/lazygophers/utils/routine`
- **测试文件**: `routine_test.go`（1144 行，包含全面的测试用例）
- **文档文件**: `llms.txt`（模块使用说明）

**相关模块：**
- `github.com/lazygophers/log` - 日志库
- `github.com/petermattis/goid` - Goroutine ID 获取
- `runtime/debug` - 堆栈追踪

---

**最后更新**: 2026-01-28
**维护者**: lazygophers
**许可证**: 查看项目根目录 LICENSE 文件
