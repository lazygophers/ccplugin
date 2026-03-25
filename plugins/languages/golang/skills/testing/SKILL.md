---
description: Go 测试规范：表驱动测试（table-driven）、模糊测试（go test -fuzz，Go 1.18+）、基准测试（benchstat）、testify 断言、覆盖率 >= 90%。写测试时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 测试规范

## 适用 Agents

- **dev** - 开发专家
- **test** - 测试专家（主要使用者）

## 相关 Skills

| 场景     | Skill                      | 说明                         |
| -------- | -------------------------- | ---------------------------- |
| 核心规范 | Skills(golang:core)        | 核心规范：强制约定           |
| 错误处理 | Skills(golang:error)       | 错误路径测试                 |
| 并发测试 | Skills(golang:concurrency) | race 检测、并发测试          |
| 工具链   | Skills(golang:tooling)     | go test 命令、pprof          |

## 核心原则

### 必须遵守

1. **测试文件命名** - 以 `_test.go` 结尾
2. **测试函数命名** - 以 `Test` 开头
3. **表驱动测试** - 默认使用表驱动模式
4. **测试隔离** - 测试之间相互独立
5. **覆盖率** - >= 90%，关键路径 100%
6. **严禁修改生产代码** - 不为测试而改生产代码

### 禁止行为

- 测试依赖执行顺序
- 测试之间共享状态
- 使用 time.Sleep 等待异步操作
- 忽略测试失败
- 测试代码过于复杂

## 表驱动测试（标准模式）

```go
func TestUserLogin(t *testing.T) {
    tests := []struct {
        name     string
        username string
        password string
        wantErr  bool
    }{
        {"valid login", "testuser", "password123", false},
        {"invalid password", "testuser", "wrong", true},
        {"empty username", "", "password123", true},
        {"empty password", "testuser", "", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
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

## 模糊测试（Go 1.18+）

```go
func FuzzParseJSON(f *testing.F) {
    // 种子语料
    f.Add(`{"name":"test"}`)
    f.Add(`{}`)
    f.Add(`[]`)
    f.Add(`""`)

    f.Fuzz(func(t *testing.T, input string) {
        result, err := ParseJSON(input)
        if err != nil {
            return // 合法的解析失败
        }
        // 验证不变量
        if result == nil {
            t.Error("ParseJSON returned nil without error")
        }
    })
}
```

运行模糊测试：

```bash
go test -fuzz=FuzzParseJSON -fuzztime=30s ./parser/
```

## 基准测试

```go
func BenchmarkProcessData(b *testing.B) {
    data := generateTestData(1000)
    b.ReportAllocs()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ProcessData(data)
    }
}
```

基准对比：

```bash
go test -bench=. -benchmem -count=5 > old.txt
# 修改代码后
go test -bench=. -benchmem -count=5 > new.txt
benchstat old.txt new.txt
```

## 使用 testify

```go
import (
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestCalculate(t *testing.T) {
    result := Calculate(2, 3)
    assert.Equal(t, 5, result)
    assert.NotZero(t, result)
}

func TestCreateUser(t *testing.T) {
    user, err := CreateUser("test@example.com")
    require.NoError(t, err)       // 失败则立即终止
    require.NotNil(t, user)
    assert.Equal(t, "test@example.com", user.Email)
}
```

## Mock 全局状态

```go
func TestUserLoginWithMock(t *testing.T) {
    originalUser := state.User
    defer func() { state.User = originalUser }()

    state.User = &MockUserModel{
        users: map[int64]*User{
            1: {Id: 1, Email: "test@example.com"},
        },
    }

    user, err := UserLogin("test@example.com", "password")
    require.NoError(t, err)
    assert.Equal(t, "test@example.com", user.Email)
}
```

## 测试覆盖率

```bash
# 运行并生成覆盖率
go test -coverprofile=coverage.out ./...

# 查看总覆盖率
go tool cover -func=coverage.out | grep total

# HTML 报告
go tool cover -html=coverage.out

# 带 race 检测
go test -v -race -cover ./...
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "80% 覆盖率就够了" | 是否 >= 90%，关键路径 100%？ | 高 |
| "不需要 fuzz 测试" | 解析器/编解码器是否有 fuzz？ | 中 |
| "time.Sleep 等等就好" | 是否用确定性同步机制？ | 高 |
| "mock 一切依赖" | 是否只 mock 外部依赖？ | 中 |
| "Test1/Test2 命名" | 表驱动测试 name 是否有描述性？ | 中 |
| "跳过错误路径" | 错误路径是否有测试？ | 高 |

## 检查清单

- [ ] 测试文件以 `_test.go` 结尾
- [ ] 测试函数以 `Test` 开头
- [ ] 使用表驱动测试模式
- [ ] 关键业务逻辑有测试覆盖
- [ ] 测试之间相互独立
- [ ] 覆盖率 >= 90%
- [ ] 解析器/编解码器有模糊测试
- [ ] 关键函数有基准测试
- [ ] 并发代码有 race 检测测试
- [ ] 错误路径有专门测试
- [ ] 测试通过率 100%
