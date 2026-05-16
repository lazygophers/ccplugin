---
name: golang-testing
description: Go 测试规范——表驱动测试（t.Run 子测试）、testing/synctest 确定性并发测试（Go 1.25 GA）、模糊测试（go test -fuzz）、基准测试（B.Loop, Go 1.24+）、testify 断言、mock 全局 state、覆盖率 ≥90%。写单元测试/集成测试/benchmark、调查 flaky 测试、设计 mock 策略时触发。
---

# Go 测试规范

## 六条铁律

1. 文件命名 `_test.go`，函数命名 `TestXxx`/`BenchmarkXxx`/`FuzzXxx`。
2. **默认表驱动 + `t.Run` 子测试**。
3. **禁 `time.Sleep` 等待异步**，并发测试用 `testing/synctest`（Go 1.25 GA）。
4. **测试隔离**：测试间无共享状态，`t.Parallel()` 默认开。
5. **覆盖率 ≥90%**，关键路径 100%。不为达指标删测试代码。
6. **禁为测试改生产代码**（除非加 internal/testonly 钩子）。

## 表驱动测试（标准模板）

```go
func TestUserLogin(t *testing.T) {
    tests := []struct {
        name     string
        username string
        password string
        wantErr  bool
    }{
        {"valid", "user", "pass123", false},
        {"wrong password", "user", "wrong", true},
        {"empty user", "", "pass123", true},
        {"empty pass", "user", "", true},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()
            user, err := UserLogin(tt.username, tt.password)
            if (err != nil) != tt.wantErr {
                t.Errorf("UserLogin() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !tt.wantErr && user == nil {
                t.Error("UserLogin() returned nil user")
            }
        })
    }
}
```

注：Go 1.22+ 循环变量每轮新建，**无需** `tt := tt`。

## testing/synctest（Go 1.25 GA，并发/时间测试）

**杀手锏**：测试涉及 `time.After`/`context.WithTimeout`/goroutine 协作时，告别 `time.Sleep` 和 flaky 测试。

```go
import "testing/synctest"

func TestContextDeadline(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        ctx, cancel := context.WithTimeout(context.Background(), time.Second)
        defer cancel()

        synctest.Wait()              // 等所有 goroutine durably blocked
        select {
        case <-ctx.Done():
            // ctx 已超时（假时钟瞬间推进）
        default:
            t.Fatal("ctx should be done")
        }
    })
}
```

- bubble 内 `time` 用假时钟，零等待。
- `synctest.Wait()` 阻塞到 bubble 内所有 goroutine durably blocked。
- 适用：定时器、超时、ticker、context 传播测试。

## 模糊测试（Go 1.18+）

```go
func FuzzParseJSON(f *testing.F) {
    f.Add(`{"name":"test"}`)
    f.Add(`{}`)
    f.Add(`""`)
    f.Fuzz(func(t *testing.T, input string) {
        result, err := ParseJSON(input)
        if err != nil { return }
        if result == nil {
            t.Error("ParseJSON returned nil without error")
        }
    })
}
```

```bash
go test -fuzz=FuzzParseJSON -fuzztime=30s ./parser/
```

解析器、编解码器、URL 处理类强制写 fuzz。

## 基准测试（Go 1.24+ 推荐 B.Loop）

```go
func BenchmarkProcessData(b *testing.B) {
    data := generateTestData(1000)
    b.ReportAllocs()
    for b.Loop() { // Go 1.24+，自动 ResetTimer + 避免编译器消除
        ProcessData(data)
    }
}
```

对比：

```bash
go test -bench=. -benchmem -count=5 > old.txt
# 修改代码后
go test -bench=. -benchmem -count=5 > new.txt
benchstat old.txt new.txt
```

## testify 断言

```go
import (
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestCreate(t *testing.T) {
    user, err := CreateUser("test@example.com")
    require.NoError(t, err)        // 失败即停
    require.NotNil(t, user)
    assert.Equal(t, "test@example.com", user.Email)
}
```

`require` 用于必要前提，失败即停；`assert` 用于次要断言，可累积。

## Mock 全局 state

```go
func TestUserLoginWithMock(t *testing.T) {
    orig := state.User
    defer func() { state.User = orig }()

    state.User = &MockUserModel{
        users: map[int64]*User{1: {Id: 1, Email: "x@y.z"}},
    }

    user, err := UserLogin("x@y.z", "pwd")
    require.NoError(t, err)
    assert.Equal(t, "x@y.z", user.Email)
}
```

- 仅 mock 外部依赖（DB/HTTP/缓存）。
- 不 mock 自己写的业务函数。

## 覆盖率

```bash
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total
go tool cover -html=coverage.out
go test -v -race -cover ./...
```

CI 中用 `vladopajic/go-test-coverage` 配置 `.testcoverage.yml` 设阈值。

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "80% 覆盖率够了" | ≥90%，关键路径 100%？ |
| "fuzz 太慢" | 解析器/编解码器有 fuzz？ |
| "time.Sleep 等等" | 用 testing/synctest？ |
| "mock 一切" | 仅 mock 外部依赖？ |
| "Test1/Test2" | 子测试 name 描述性？ |
| "跳过错误路径" | 错误路径有用例？ |

## 检查清单

- [ ] 文件 `_test.go`、函数 `Test`/`Benchmark`/`Fuzz` 前缀
- [ ] 表驱动 + `t.Run`
- [ ] `t.Parallel()` 开启
- [ ] 测试间无共享状态
- [ ] 覆盖率 ≥90%
- [ ] 并发/时间测试用 `testing/synctest`
- [ ] 解析器有 fuzz
- [ ] 关键函数有 benchmark（B.Loop）
- [ ] 错误路径有专用 case
- [ ] CI 跑 `-race`

## 权威参考

- `testing/synctest` 官博 — https://go.dev/blog/synctest
- testing 包 — https://pkg.go.dev/testing
