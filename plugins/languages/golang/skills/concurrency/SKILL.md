---
name: golang-concurrency
description: Go 并发规范——go.uber.org/atomic 原子操作（非 sync/atomic）、errgroup 并发编排（SetLimit 限流）、context 超时取消传播、sync.Pool 对象复用、WaitGroup.Go（Go 1.25+）、Go 1.23 iter 迭代器、Green Tea GC（Go 1.26 默认）。写 goroutine、设计并发流程、调查竞态/泄漏、性能调优时触发。
---

# Go 并发规范

## 五条铁律

1. **原子用 `go.uber.org/atomic`**，禁直接 `sync/atomic`。
2. **goroutine 必须有 context** 控制生命周期，禁裸 `go func()`。
3. **goroutine 组用 `errgroup`**，必须 `SetLimit` 限制并发。
4. **高频临时对象用 `sync.Pool`** 复用。
5. **简单计数器/标志位用 atomic**，禁 mutex。

## atomic（go.uber.org/atomic）

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

类型安全 + API 友好，比标准库 `sync/atomic` 少 50% 出错。

## sync.Pool 复用

```go
var bufferPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}

func processData(data []byte) string {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer bufferPool.Put(buf)
    buf.Reset()
    buf.Write(data)
    return buf.String()
}
```

适用：每秒上千次创建-销毁的临时对象（buffer、struct）。低频对象不要 Pool，反而增加复杂度。

## errgroup 并发编排

```go
import "golang.org/x/sync/errgroup"

eg, ctx := errgroup.WithContext(ctx)
eg.SetLimit(10) // 必设并发上限

for _, item := range items {
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

注：Go 1.22+ 循环变量自动每轮新建，**无需** `item := item`。

## WaitGroup.Go（Go 1.25+）

简单场景，不需要错误传播：

```go
var wg sync.WaitGroup
for _, item := range items {
    wg.Go(func() { // 自动 Add(1) + defer Done()
        process(item)
    })
}
wg.Wait()
```

需错误传播 → 用 errgroup。仅扇出无错误 → WaitGroup.Go。

## context 最佳实践

```go
// 超时
ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
defer cancel()

// 取消
ctx, cancel := context.WithCancel(ctx)
defer cancel()

// 传播 + 协作取消
func processItem(ctx context.Context, item *Item) error {
    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }
    // 长操作中循环检查
    for chunk := range item.Chunks() {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
            handle(chunk)
        }
    }
    return nil
}
```

每个 goroutine 入口函数第一个参数必须是 `ctx context.Context`，整链路传到底。

## Go 1.23 iter 迭代器

```go
import (
    "iter"
    "maps"
    "slices"
)

for k, v := range maps.All(m) { fmt.Println(k, v) }
for i, v := range slices.All(s) { fmt.Println(i, v) }

func FilterIter[T any](seq iter.Seq[T], fn func(T) bool) iter.Seq[T] {
    return func(yield func(T) bool) {
        for v := range seq {
            if fn(v) && !yield(v) { return }
        }
    }
}
```

适合流式/惰性场景；急切批处理仍用 `candy`。

## 内存优化

### 预分配容量

```go
result := make([]string, 0, len(items))
for _, item := range items {
    result = append(result, item.String())
}
```

### 日志缓冲

```go
import "github.com/lazygophers/log"

buf := log.GetBuffer()
defer log.PutBuffer(buf)
```

## Green Tea GC（Go 1.26 默认）

- GC 暂停时间 ↓10-40%，无需任何代码改动。
- 关闭：`GOEXPERIMENT=nogreenteagc` 编译。
- cgo 调用开销 ↓~30%、小对象分配 ↓~30%（自动收益）。

## Goroutine 泄漏剖析（Go 1.26 实验）

```bash
GOEXPERIMENT=goroutineleakprofile go build .
# 运行后访问 /debug/pprof/goroutineleak
```

零开销，1.27 拟默认开启。

## 并发测试（详见 `golang-testing`）

`testing/synctest`（Go 1.25 GA）+ `-race` 是标配：

```bash
go test -race ./...
```

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "sync/atomic 是标准库" | 用 go.uber.org/atomic？ |
| "mutex 更简单" | 简单计数用 atomic？ |
| "goroutine 很轻量" | 有 errgroup + context 控制？ |
| "context 到处传麻烦" | 入口函数都接 ctx？ |
| "不需要 SetLimit" | errgroup 设上限？ |
| "iter 太新" | 适用场景用了？ |

## 检查清单

- [ ] 原子用 `go.uber.org/atomic`
- [ ] 高频临时对象 `sync.Pool`
- [ ] goroutine 组用 `errgroup` + `SetLimit`
- [ ] 所有 goroutine 接 context
- [ ] 简单计数用 atomic 非 mutex
- [ ] slice 预分配容量
- [ ] 并发代码跑 `-race`
- [ ] 阻塞操作有超时
- [ ] 并发/时间测试用 `testing/synctest`
