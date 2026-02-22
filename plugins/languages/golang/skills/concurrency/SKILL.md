---
name: concurrency
description: Go 并发规范：使用 go.uber.org/atomic、sync.Pool、errgroup。写并发代码时必须加载。
---

# Go 并发规范

## 核心原则

### 必须遵守

1. **使用 go.uber.org/atomic** - 禁止直接使用 sync/atomic
2. **使用 sync.Pool** - 复用对象减少分配
3. **使用 errgroup** - 管理 goroutine
4. **避免 mutex** - 优先使用 atomic

### 禁止行为

- 直接使用 sync/atomic（难用，容易出错）
- 使用 mutex（性能低）
- goroutine 泄漏
- 无超时的阻塞操作

## atomic 原子操作

```go
import "go.uber.org/atomic"

counter := atomic.NewInt64(0)
counter.Inc()
counter.Add(10)
counter.Dec()
counter.Sub(5)
val := counter.Load()
counter.Store(100)
counter.Swap(200)
counter.CompareAndSwap(200, 300)

id := atomic.NewUint32(0)
id.Inc()
val := id.Load()

rate := atomic.NewFloat64(0.0)
rate.Add(0.5)
val := rate.Load()

flag := atomic.NewBool(false)
flag.Toggle()
flag.Store(true)
val := flag.Load()

name := atomic.NewString("")
name.Store("hello")
val := name.Load()

value := atomic.NewValue(nil)
value.Store(&User{Id: 1})
val := value.Load().(*User)
```

## sync.Pool 复用对象

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func processData(data []byte) string {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer bufferPool.Put(buf)
    buf.Reset()

    buf.Write(data)
    return buf.String()
}
```

## errgroup 管理 goroutine

```go
import "golang.org/x/sync/errgroup"

eg, ctx := errgroup.WithContext(context.Background())
for _, item := range items {
    item := item
    eg.Go(func() error {
        return process(ctx, item)
    })
}
err = eg.Wait()
if err != nil {
    log.Errorf("err:%v", err)
    return err
}
```

## 内存优化

### 使用 embedding 减少分配

```go
type Request struct {
    *http.Request
}
```

### 预分配容量

```go
func ProcessItems(items []*Item) []string {
    result := make([]string, 0, len(items))
    for _, item := range items {
        result = append(result, item.String())
    }
    return result
}
```

### 日志缓冲优化

```go
import "github.com/lazygophers/log"

buf := log.GetBuffer()
defer log.PutBuffer(buf)
```

## 并发测试

```go
func TestConcurrentAccess(t *testing.T) {
    counter := NewCounter()

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter.Increment()
        }()
    }

    wg.Wait()

    if counter.Value() != 100 {
        t.Errorf("counter.Value() = %d, want 100", counter.Value())
    }
}
```

## 检查清单

- [ ] 使用 go.uber.org/atomic 而非 sync/atomic
- [ ] 使用 sync.Pool 复用对象
- [ ] 使用 errgroup 管理 goroutine
- [ ] 避免使用 mutex
- [ ] 预分配 slice 容量
- [ ] 并发代码有并发测试
- [ ] 无 goroutine 泄漏
- [ ] 阻塞操作有超时
