---
description: Go 并发规范：go.uber.org/atomic 替代 sync/atomic、sync.Pool 复用对象、errgroup 管理 goroutine、context 最佳实践、Go 1.23 iter 迭代器。写并发代码时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 并发规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）
- **debug** - 调试专家
- **perf** - 性能优化专家

## 相关 Skills

| 场景     | Skill                    | 说明                         |
| -------- | ------------------------ | ---------------------------- |
| 核心规范 | Skills(golang:core)      | 核心规范：强制约定           |
| 错误处理 | Skills(golang:error)     | errgroup 错误处理模式        |
| 测试     | Skills(golang:testing)   | 并发测试和 race 检测         |
| 工具     | Skills(golang:tooling)   | go test -race、pprof         |

## 核心原则

### 必须遵守

1. **使用 go.uber.org/atomic** - 禁止直接使用 sync/atomic
2. **使用 sync.Pool** - 复用对象减少分配
3. **使用 errgroup** - 管理 goroutine 组
4. **context 传播** - 所有 goroutine 通过 context 控制生命周期
5. **避免 mutex** - 优先使用 atomic

### 禁止行为

- 直接使用 sync/atomic（难用，容易出错）
- 裸 goroutine 不带 context（泄漏风险）
- 无超时的阻塞操作
- mutex 保护简单计数器（用 atomic）

## atomic 原子操作

```go
import "go.uber.org/atomic"

counter := atomic.NewInt64(0)
counter.Inc()
counter.Add(10)
val := counter.Load()

flag := atomic.NewBool(false)
flag.Toggle()
flag.Store(true)

name := atomic.NewString("")
name.Store("hello")
```

## sync.Pool 复用对象

```go
var bufferPool = sync.Pool{
    New: func() any {
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

eg, ctx := errgroup.WithContext(ctx)
for _, item := range items {
    item := item // Go 1.22 之前需要捕获
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

### 带并发限制的 errgroup

```go
eg, ctx := errgroup.WithContext(ctx)
eg.SetLimit(10) // 最多 10 个并发 goroutine
for _, url := range urls {
    url := url
    eg.Go(func() error {
        return fetch(ctx, url)
    })
}
```

## context 最佳实践

```go
// 带超时的 context
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

// 带取消的 context
ctx, cancel := context.WithCancel(ctx)
defer cancel()

// context 传播到所有下游调用
func processItem(ctx context.Context, item *Item) error {
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
        // 正常处理
    }
    return nil
}
```

## Go 1.23 iter 迭代器

```go
import (
    "iter"
    "maps"
    "slices"
)

// range-over-func 迭代 map
for k, v := range maps.All(m) {
    fmt.Println(k, v)
}

// range-over-func 迭代 slice
for i, v := range slices.All(s) {
    fmt.Println(i, v)
}

// 自定义迭代器
func FilterIter[T any](seq iter.Seq[T], fn func(T) bool) iter.Seq[T] {
    return func(yield func(T) bool) {
        for v := range seq {
            if fn(v) {
                if !yield(v) {
                    return
                }
            }
        }
    }
}
```

## 内存优化

### 预分配容量

```go
result := make([]string, 0, len(items))
for _, item := range items {
    result = append(result, item.String())
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
        t.Errorf("counter = %d, want 100", counter.Value())
    }
}
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "sync/atomic 是标准库" | 是否使用 go.uber.org/atomic？ | 高 |
| "mutex 更简单" | 简单场景是否用 atomic 替代 mutex？ | 中 |
| "goroutine 很轻量无所谓" | 是否用 errgroup 管理，无泄漏风险？ | 高 |
| "context 到处传太麻烦" | goroutine 是否通过 context 控制？ | 高 |
| "不需要并发限制" | errgroup 是否设置了 SetLimit？ | 中 |
| "iter 太新了不稳定" | 适合场景是否使用了 range-over-func？ | 低 |

## 检查清单

- [ ] 使用 go.uber.org/atomic 而非 sync/atomic
- [ ] 使用 sync.Pool 复用对象
- [ ] 使用 errgroup 管理 goroutine
- [ ] 所有 goroutine 通过 context 控制
- [ ] errgroup 设置了合理的并发限制
- [ ] 避免使用 mutex（优先 atomic）
- [ ] 预分配 slice 容量
- [ ] 并发代码有并发测试
- [ ] 无 goroutine 泄漏
- [ ] 阻塞操作有超时
