# 技能系统

Golang 插件提供九个核心技能，覆盖 Golang 开发的主要领域。

## 技能列表

| 技能 | 描述 | 自动激活 |
|------|------|----------|
| `core` | Golang 核心规范 | 始终激活 |
| `error` | 错误处理规范 | 处理错误时 |
| `libs` | 常用库规范 | 使用库时 |
| `naming` | 命名规范 | 命名时 |
| `structure` | 项目结构规范 | 创建项目时 |
| `testing` | 测试策略 | 编写测试时 |
| `concurrency` | 并发编程规范 | 并发代码时 |
| `lint` | Lint 规范 | 代码检查时 |
| `tooling` | 工具链规范 | 使用工具时 |

## core - Golang 核心规范

### 编程规范

- 遵循 Effective Go
- 使用 `gofmt` 格式化
- 所有 error 必须显式处理
- 接口应该小而专一

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 包名 | 小写单词 | `package http` |
| 导出 | 大驼峰 | `MyFunction` |
| 私有 | 小驼峰 | `myFunction` |
| 常量 | 大驼峰或小驼峰 | `MaxSize` / `maxSize` |

## error - 错误处理规范

### 错误处理

```go
// ✅ 好的错误处理
if err != nil {
    log.Error("failed to process",
        "error", err,
        "context", context,
    )
    return fmt.Errorf("process failed: %w", err)
}

// ❌ 不好的错误处理
if err != nil { return err }
```

### 自定义错误

```go
type AppError struct {
    Code    int
    Message string
    Err     error
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("[%d] %s: %v", e.Code, e.Message, e.Err)
    }
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

func (e *AppError) Unwrap() error {
    return e.Err
}
```

## libs - 常用库规范

### 标准库优先

```go
import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "time"
)
```

### 常用第三方库

```go
import (
    "github.com/go-chi/chi/v5"
    "github.com/jackc/pgx/v5"
    "go.uber.org/zap"
)
```

## naming - 命名规范

### 包命名

```go
// ✅ 好的包名
package http
package json
package user

// ❌ 不好的包名
package httpUtil
package json_parser
package userService
```

### 接口命名

```go
// ✅ 单方法接口
type Reader interface {
    Read(p []byte) (n int, err error)
}

// ✅ 多方法接口
type Handler interface {
    ServeHTTP(ResponseWriter, *Request)
}
```

## structure - 项目结构规范

### 标准结构

```
my-project/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── handler/
│   ├── service/
│   └── repository/
├── pkg/
│   └── utils/
├── api/
│   └── openapi.yaml
├── go.mod
├── go.sum
└── Makefile
```

## testing - 测试策略

### 单元测试

```go
func TestUserService_Create(t *testing.T) {
    tests := []struct {
        name    string
        input   UserInput
        want    *User
        wantErr bool
    }{
        {
            name:  "valid user",
            input: UserInput{Name: "test"},
            want:  &User{Name: "test"},
        },
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // test implementation
        })
    }
}
```

## concurrency - 并发编程规范

### Goroutine

```go
// ✅ 使用 context 控制
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

go func() {
    select {
    case <-ctx.Done():
        return
    case result <- process():
    }
}()
```

### Channel

```go
// ✅ 带缓冲的 channel
ch := make(chan int, 10)

// ✅ 关闭 channel
close(ch)

// ✅ 检查 channel 关闭
v, ok := <-ch
```

## lint - Lint 规范

### golangci-lint

```yaml
# .golangci.yml
linters:
  enable:
    - gofmt
    - goimports
    - govet
    - errcheck
    - staticcheck
    - ineffassign
    - typecheck
```

## tooling - 工具链规范

### 常用命令

```bash
# 格式化
go fmt ./...

# 静态检查
go vet ./...

# 测试
go test ./...

# 构建
go build -o bin/server ./cmd/server
```
