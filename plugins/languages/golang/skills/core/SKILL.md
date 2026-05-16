---
name: golang-core
description: Go 1.26 核心开发规范——强制约定、代码格式、Go 1.21-1.26 新特性（range-over-func、slog、generic aliases、Green Tea GC、new(expr)、自引用泛型）、提交前检查清单。编写 Go 代码、设置项目骨架、做代码评审、回答 "Go 应该怎么写" 时触发。
---

# Go 开发核心规范

适用于 Go 1.26（2026-02 发布），向下兼容 1.21+。

## 关联 Skills

| 场景 | Skill |
| --- | --- |
| 错误处理 | `golang-error` |
| 工具库选型 | `golang-libs` |
| 命名 | `golang-naming` |
| 项目结构 | `golang-structure` |
| 测试 | `golang-testing` |
| 并发 | `golang-concurrency` |
| Lint 配置 | `golang-lint` |
| 工具链 | `golang-tooling` |

## 三条铁律

1. **error 多行处理 + 记录日志**，禁止单行 `if err != nil { return err }`。
2. **状态托管在 state 包**（全局变量），禁止 Repository 接口/DI 容器。
3. **集合操作必经 `candy`、字符串经 `stringx`、文件经 `osx`**，禁止手写 for 循环遍历做 Map/Filter。

## Go 1.21 → 1.26 关键新特性（按版本）

### 1.21 — `log/slog` + 内置函数

```go
import "log/slog"
slog.Info("user registered", "username", name, "email", email)

m := min(a, b)
M := max(a, b)
clear(mySlice)
clear(myMap)
```

### 1.22 — for-range 整数 + 增强路由 + 循环变量作用域

```go
for i := range 10 { /* 0..9 */ }

mux.HandleFunc("GET /api/users/{id}", getUser)
mux.HandleFunc("POST /api/users", createUser)

// 1.22+ 循环变量每轮新建，无需再 item := item
for _, item := range items {
    go func() { handle(item) }()
}
```

### 1.23 — range-over-func + `iter` 包

```go
import "iter"
import "maps"
import "slices"

for k, v := range maps.All(m) { fmt.Println(k, v) }

func (t *Tree[V]) All() iter.Seq2[string, V] {
    return func(yield func(string, V) bool) { /* ... */ }
}
```

### 1.24 — 泛型类型别名 + `tool` 指令 + `os.Root` + `testing.B.Loop`

```go
type Set[T comparable] = map[T]struct{}

// go.mod 中: tool golang.org/x/tools/cmd/stringer

root, _ := os.OpenRoot("/data")
defer root.Close()
f, _ := root.Open("config.json") // 越界拒绝

func BenchmarkFoo(b *testing.B) {
    for b.Loop() { foo() }
}
```

### 1.25 — `WaitGroup.Go` + `testing/synctest` GA

```go
var wg sync.WaitGroup
wg.Go(func() { doWork() }) // 自动 Add(1)/Done()
wg.Wait()

synctest.Test(t, func(t *testing.T) {
    // bubble 内 time 为假时钟，goroutine 全 durably blocked 后 Wait 返回
})
```

### 1.26 — `new(expr)` + 自引用泛型 + Green Tea GC 默认 + `go fix` 现代化

```go
p := new(42)         // *int = 42
q := new(Point{1,2}) // *Point

type Node[T Node[T]] interface {
    Children() []T
}
```

- Green Tea GC 默认启用，GC 开销 ↓10-40%
- cgo 调用开销 ↓~30%，小对象分配 ↓~30%
- `go fix` 重写为现代化工具，配合 `//go:fix inline` 做 API 迁移
- 实验：`GOEXPERIMENT=goroutineleakprofile`（goroutine 泄漏剖析）、`GOEXPERIMENT=simd`（向量 SIMD）

## 文件组织

```go
package mypkg

import (
    // 标准库
    "context"
    "log/slog"
    "os"

    // 第三方
    "github.com/lazygophers/log"
    "github.com/lazygophers/utils/candy"
    "gorm.io/gorm"

    // 项目内
    "github.com/your/project/internal/state"
)

const (...)

var (...)

type Foo struct {...}

type Bar interface {...}

func New() *Foo {...}
```

- 单个 `.go` 文件 ≤500 行，推荐 200-400 行。
- 导出类型/函数必须有文档注释，以名字开头：`// Foo 表示...`。

## 强制禁止清单

| 模式 | 替代 |
| --- | --- |
| `if err != nil { return err }` 单行 | 多行 + `log.Errorf("err:%v", err)` |
| `fmt.Errorf("...: %w", err)` | 直接 `return err`，禁止包装 |
| 手写 `for _, x := range xs` 做 Map/Filter | `candy.Map`/`candy.Filter` |
| `os.Stat`/手写 `os.OpenFile + close` 检查存在 | `osx.IsFile`/`osx.IsDir` |
| `sync/atomic` 直接用 | `go.uber.org/atomic` |
| 业务流程用 `panic`/`recover` | `log.Errorf` + return error；初始化用 `log.Fatalf` |
| Repository 接口 + 依赖注入 | `state` 包全局变量 |

## 提交前检查清单

- [ ] `gofmt -w .` + `goimports -w .` 已跑
- [ ] `go vet ./...` 无告警
- [ ] `golangci-lint run ./...` 通过（见 `golang-lint`）
- [ ] `govulncheck ./...` 无 HIGH
- [ ] `go test -race -cover ./...` 通过
- [ ] 所有 error 多行 + 日志
- [ ] 无 `fmt.Errorf` 包装
- [ ] 无单行 `if err`
- [ ] 集合操作走 `candy`，字符串走 `stringx`
- [ ] 导出 API 有注释
- [ ] 用了 1.21+ 适用新特性（`min/max`、`for i := range N`、`slog`、`WaitGroup.Go`）

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "单行 if err 更简洁" | 是否所有 error 多行 + 日志？ |
| "fmt.Errorf 加上下文更清晰" | 是否禁止包装、直接 return？ |
| "for 循环更直观" | 集合操作是否走 candy？ |
| "Repository 接口更好测试" | 是否用 state 全局？ |
| "Go 1.18 泛型够用了" | 是否启用 1.23 iter / 1.26 new(expr) 等？ |
| "导出函数不用注释" | 所有导出 API 是否有名字开头注释？ |

## 权威参考

- Go 1.26 Release Notes — https://go.dev/doc/go1.26
- Effective Go — https://go.dev/doc/effective_go
- Go Code Review Comments — https://github.com/golang/go/wiki/CodeReviewComments
