# 开发规范

Golang 插件遵循的开发规范和最佳实践。

## 编程规范

### 必须遵守

1. **风格指南**：遵循 Effective Go
2. **格式化**：使用 `gofmt` 格式化
3. **错误处理**：所有 error 必须显式处理
4. **接口设计**：接口应该小而专一

### 推荐实践

1. **代码组织**：使用标准项目结构
2. **依赖管理**：使用 Go modules
3. **测试覆盖**：关键路径测试覆盖率 > 80%
4. **文档注释**：导出函数必须有文档注释

## 代码风格

### 格式化

```bash
# 格式化代码
go fmt ./...

# 导入排序
goimports -w .
```

### 注释规范

```go
// Package user 提供用户管理功能.
//
// 用户管理包括创建、查询、更新和删除用户.
package user

// Create 创建新用户.
//
// name 参数不能为空，email 参数必须是有效的邮箱格式.
//
// 返回创建的用户对象，如果创建失败则返回错误.
func Create(name, email string) (*User, error) {
    // ...
}
```

## 项目结构

### 标准结构

```
my-project/
├── cmd/                    # 主程序入口
│   └── server/
│       └── main.go
├── internal/               # 私有代码
│   ├── handler/           # HTTP 处理器
│   ├── service/           # 业务逻辑
│   └── repository/        # 数据访问
├── pkg/                    # 公共代码
│   └── utils/
├── api/                    # API 定义
│   └── openapi.yaml
├── configs/               # 配置文件
├── scripts/               # 脚本
├── go.mod
├── go.sum
└── Makefile
```

### go.mod

```go
module github.com/username/myproject

go 1.21

require (
    github.com/go-chi/chi/v5 v5.0.10
    github.com/jackc/pgx/v5 v5.5.0
)
```

## 错误处理

### 基本原则

```go
// ✅ 好的错误处理
if err != nil {
    return fmt.Errorf("operation failed: %w", err)
}

// ❌ 不好的错误处理
if err != nil {
    panic(err)
}
```

### 错误包装

```go
import "errors"

var ErrNotFound = errors.New("not found")

func Find(id int) (*User, error) {
    user, err := db.Find(id)
    if err != nil {
        return nil, fmt.Errorf("find user %d: %w", id, err)
    }
    if user == nil {
        return nil, ErrNotFound
    }
    return user, nil
}
```

## 并发编程

### Goroutine 规范

```go
// ✅ 使用 context 控制
func Process(ctx context.Context, items []Item) error {
    for _, item := range items {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
            processItem(item)
        }
    }
    return nil
}
```

### Channel 规范

```go
// ✅ 带缓冲的 channel
results := make(chan Result, 10)

// ✅ 正确关闭
go func() {
    defer close(results)
    for _, item := range items {
        results <- process(item)
    }
}()
```

## 测试规范

### 测试命名

```go
// 测试文件：module_test.go
// 测试函数：TestFunctionName
// 基准测试：BenchmarkFunctionName
// 示例测试：ExampleFunctionName
```

### 表驱动测试

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 1, 2, 3},
        {"negative", -1, -2, -3},
        {"zero", 0, 0, 0},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Add(tt.a, tt.b)
            if result != tt.expected {
                t.Errorf("Add(%d, %d) = %d, want %d",
                    tt.a, tt.b, result, tt.expected)
            }
        })
    }
}
```

## 性能优化

### 性能分析

```bash
# CPU 分析
go test -cpuprofile=cpu.out ./...
go tool pprof cpu.out

# 内存分析
go test -memprofile=mem.out ./...
go tool pprof mem.out
```

### 常见优化

1. **减少分配**：复用对象
2. **使用 sync.Pool**：对象池
3. **避免不必要的转换**：[]byte 和 string
4. **使用合适的数据结构**：map vs slice

## 代码审查清单

提交前检查：

- [ ] 遵循命名规范（导出大驼峰，私有小驼峰）
- [ ] 所有 error 都有日志记录
- [ ] 没有单行 if err 语句
- [ ] 单元测试覆盖 >80%
- [ ] 通过 go vet 和 golangci-lint
- [ ] 代码通过 gofmt 格式化
