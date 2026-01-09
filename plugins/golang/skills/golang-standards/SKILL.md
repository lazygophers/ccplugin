---
name: golang-standards
description: Golang 开发标准规范 - 提供通用的 Golang 编码标准、最佳实践和项目结构指导。当用户进行 Go 语言开发、编写 Go 代码或需要规范指导时自动激活
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
auto-activate:
  patterns:
    - "**/*.go"
    - "**/go.mod"
    - "**/go.sum"
---

# Golang 开发规范

## 核心原则

### ✅ 必须遵循

- **代码风格**：遵循官方 [Effective Go](https://golang.org/doc/effective_go) 指南
- **格式化**：使用 `gofmt` 或 `goimports` 自动格式化所有 Go 代码
- **命名规范**：遵循 Go 命名约定（导出大驼峰，私有小驼峰）
- **错误处理**：每个 error 都必须显式处理，不允许忽略
- **接口设计**：接口应该小而专一，通常不超过 3 个方法
- **注释规范**：公开符号必须有注释，中英文均可但保持一致

### ❌ 禁止行为

- 禁止使用下划线作为空白导入标识符以外的导入方式
- 禁止在循环中延迟 defer（容易导致内存泄漏）
- 禁止忽略 error（即使是 io.Closer）
- 禁止使用 panic/recover 处理常规错误
- 禁止创建过于复杂的接口（>5 个方法应该拆分）

## 文件组织

**详见 [分库分包规范文档](patterns/package-organization.md)** - 涵盖目录结构、包组织、依赖管理

### 目录结构

```
project/
├── main.go                    # 主程序入口
├── go.mod                     # 模块定义
├── go.sum                     # 依赖锁定
├── internal/
│   ├── pkg1/                  # 内部包
│   │   ├── pkg1.go            # 主实现
│   │   └── pkg1_test.go       # 单元测试
│   └── pkg2/
│       ├── pkg2.go
│       └── pkg2_test.go
├── pkg/                       # 公开包（可选）
│   └── pubpkg/
│       └── pubpkg.go
├── cmd/                       # 子命令程序
│   ├── cmd1/
│   │   └── main.go
│   └── cmd2/
│       └── main.go
├── test/                      # 集成测试
│   └── integration_test.go
└── README.md
```

### 文件头注释

```go
// Package pkgname 提供 XXX 功能的实现。
//
// 详细说明...
package pkgname

import (
    // 标准库
    "fmt"
    "os"

    // 第三方库（按字母序）
    "github.com/pkg/errors"
)
```

## 命名规范

**详见 [命名规范文档](patterns/naming-conventions.md)** - 涵盖变量、函数、类型、接口等全面的命名规则

### 快速参考

```go
// ✅ 导出常量 - 大驼峰
const MaxBufferSize = 1024

// ✅ 私有常量 - 小驼峰
const defaultTimeout = 30 * time.Second

// ✅ 导出变量 - 大驼峰
var DefaultConfig = Config{}

// ✅ 私有变量 - 小驼峰
var loggers = make(map[string]*Logger)

// ✅ 接收者变量 - 短名（1-2 字母）
func (r *Request) Process() {}
func (f *File) Close() error {}

// ❌ 避免 - 下划线
var default_timeout = 30 * time.Second

// ❌ 避免 - 无意义缩写
var rf *File  // 应该用 f 或 file
```

### 函数和方法

**详见 [函数规范文档](patterns/function-design.md)** - 涵盖函数设计、签名、设计模式

```go
// ✅ 导出函数 - 大驼峰，动词开头
func NewServer() *Server {}
func (s *Server) Start() error {}
func (s *Server) SetTimeout(d time.Duration) {}
func ParseConfig(data []byte) (*Config, error) {}

// ✅ 私有函数 - 小驼峰
func (s *server) handleRequest(req *Request) {}
func readConfigFile(path string) ([]byte, error) {}

// ✅ 谓词函数 - Is/Has 开头
func (u *User) IsAdmin() bool {}
func (l *List) HasElements() bool {}

// ❌ 避免 - 不清晰的命名
func Process() {}      // 太模糊，应该是 ProcessData
func DoSomething() {}  // 不清晰
```

### 类型和接口

```go
// ✅ 导出类型 - 大驼峰
type User struct {
    ID   int64
    Name string
}

// ✅ 接口 - 以 er 结尾
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Handler interface {
    Handle(ctx context.Context, req *Request) error
}

// ✅ 错误类型 - Error 结尾
type ParseError struct {
    msg string
}

func (e *ParseError) Error() string {
    return e.msg
}
```

## 代码风格与架构

**详见 [架构设计规范文档](patterns/architecture-design.md)** - 涵盖分层设计、接口导向、依赖注入、初始化流程

### 导入分组

```go
import (
    // 标准库
    "fmt"
    "io"
    "os"
    "strings"

    // 第三方库（按字母序）
    "github.com/pkg/errors"
    "golang.org/x/sync/errgroup"
)
```

### 指针接收者 vs 值接收者

```go
// ✅ 使用指针接收者：方法需要修改接收者、接收者是大结构体
type User struct {
    id   int64
    name string
}

func (u *User) SetName(name string) {
    u.name = name
}

// ✅ 使用值接收者：接收者是小结构体或不需要修改
type Point struct {
    X, Y int
}

func (p Point) Distance(other Point) float64 {
    // 计算距离
}

// 注意：如果有任何方法使用指针接收者，所有方法都应该使用指针接收者
```

### 结构体标签

```go
type User struct {
    ID   int64  `json:"id" db:"id" bson:"_id"`
    Name string `json:"name" db:"name"`
    Email string `json:"email,omitempty" db:"email"`
}
```

## 错误处理

**详见 [错误处理规范文档](patterns/error-handling.md)** - 涵盖错误处理、日志、自定义错误类型

### 基本原则

```go
// ✅ 显式处理 error
data, err := ioutil.ReadFile("config.json")
if err != nil {
    return fmt.Errorf("read config: %w", err)
}

// ✅ 日志记录
if err != nil {
    log.Printf("failed to read config: %v", err)
    return err
}

// ❌ 忽略 error
data, _ := ioutil.ReadFile("config.json")

// ❌ 单行 if
if err != nil { return err }
```

### 错误包装

```go
// ✅ 使用 %w 包装
if err != nil {
    return fmt.Errorf("parse config: %w", err)
}

// ✅ 使用 errors.Is/As 判断
import "errors"

if errors.Is(err, os.ErrNotExist) {
    // 处理文件不存在
}

var parseErr ParseError
if errors.As(err, &parseErr) {
    // 处理解析错误
}
```

### 自定义错误

```go
// ✅ 定义错误类型
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error in field %s: %s", e.Field, e.Message)
}

// ✅ 使用
return &ValidationError{
    Field:   "email",
    Message: "invalid email format",
}
```

## 并发

### Goroutine 安全

```go
// ✅ 使用 sync 包进行同步
var mu sync.Mutex
var count int

func increment() {
    mu.Lock()
    defer mu.Unlock()
    count++
}

// ✅ 使用 channel 进行通信
results := make(chan Result)
go func() {
    results <- compute()
}()
value := <-results

// ✅ 使用 context 控制取消
func process(ctx context.Context) error {
    select {
    case <-ctx.Done():
        return ctx.Err()
    // ...
    }
}

// ❌ 避免 - 直接修改共享变量
var count int
go func() {
    count++ // 数据竞争！
}()
```

### 超时处理

```go
// ✅ 使用 context.WithTimeout
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

result, err := server.Handle(ctx, request)
if err == context.DeadlineExceeded {
    // 处理超时
}
```

## 测试

### 测试函数命名

```go
// ✅ 标准格式
func TestFunctionName(t *testing.T) {
    // 测试代码
}

func TestFunctionName_SubCase(t *testing.T) {
    // 子情况测试
}

func BenchmarkFunctionName(b *testing.B) {
    // 基准测试
}

// ✅ 表驱动测试
func TestParse(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    interface{}
        wantErr bool
    }{
        {
            name:  "valid input",
            input: "...",
            want:  ...,
        },
        {
            name:    "invalid input",
            input:   "...",
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Parse(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("Parse() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if got != tt.want {
                t.Errorf("Parse() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

### 测试覆盖率

```bash
# 生成覆盖率报告
go test -cover ./...

# 详细覆盖率
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# 目标：>70% 覆盖率，关键路径 >90%
```

## 常见库使用

### 日志

```go
// ✅ 标准 log 包
import "log"
log.Printf("message: %v", value)

// 或使用第三方库（如 logrus、zap）
import "github.com/sirupsen/logrus"
logrus.WithField("user_id", id).Info("user login")
```

### HTTP

```go
// ✅ 使用标准库
import "net/http"

func handler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(result)
}

http.HandleFunc("/api/users", handler)
http.ListenAndServe(":8080", nil)
```

## 性能考虑

### 避免常见陷阱

```go
// ❌ 避免 - 字符串拼接
result := ""
for _, item := range items {
    result += item.String()  // O(n²) 复杂度
}

// ✅ 优化 - 使用 strings.Builder
var buf strings.Builder
for _, item := range items {
    buf.WriteString(item.String())  // O(n)
}
result := buf.String()

// ✅ 避免 - 频繁创建 goroutine
// 应该使用 worker pool 或 errgroup
import "golang.org/x/sync/errgroup"
eg, ctx := errgroup.WithContext(context.Background())
for _, item := range items {
    item := item
    eg.Go(func() error {
        return processItem(ctx, item)
    })
}
if err := eg.Wait(); err != nil {
    return err
}
```

## 项目初始化

### go.mod 最佳实践

```bash
# ✅ 初始化模块
go mod init github.com/username/projectname

# ✅ 清理依赖
go mod tidy

# ✅ 更新依赖
go get -u ./...

# ✅ 查看依赖树
go mod graph
```

## 工具集成

### 必用工具

```bash
# 代码格式化
gofmt -w .

# 导入优化
goimports -w .

# 代码检查
go vet ./...

# 代码质量
golangci-lint run

# 单元测试
go test ./...

# 基准测试
go test -bench=. -benchmem ./...
```

## 参考资源

- [Effective Go](https://golang.org/doc/effective_go) - 官方风格指南
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments) - 代码审查意见
- [Standard Go Project Layout](https://github.com/golang-standards/project-layout) - 项目结构参考
