---
description: "Go 1.23+ 核心开发规范：强制约定、代码格式、新特性（range-over-func/slog/min/max/clear）、提交检查清单。编写Go代码时自动加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 开发核心规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）
- **debug** - 调试专家
- **test** - 测试专家
- **perf** - 性能优化专家

## 相关 Skills

| 场景           | Skill                      | 说明                                        |
| -------------- | -------------------------- | ------------------------------------------- |
| 处理错误       | Skills(golang:error)       | 错误处理规范：禁止单行 if err、必须记录日志 |
| 使用工具库     | Skills(golang:libs)        | 优先库规范：stringx/candy/osx/log           |
| 命名变量/类型  | Skills(golang:naming)      | 命名规范：Id/Uid/IsActive/CreatedAt         |
| 设计架构       | Skills(golang:structure)   | 项目结构规范：三层架构、全局状态模式        |
| 写测试         | Skills(golang:testing)     | 测试规范：表驱动测试、模糊测试              |
| 写并发代码     | Skills(golang:concurrency) | 并发规范：atomic/sync.Pool/errgroup/iter    |
| 配置/运行 lint | Skills(golang:lint)        | Lint 规范：golangci-lint v2 配置            |
| 运行工具       | Skills(golang:tooling)     | 工具规范：gofmt/goimports/govulncheck       |

## 核心理念

Go 生态追求**高性能、低分配、简洁优雅**。

**三个支柱**：

1. **零分配** - 尽可能减少内存分配
2. **函数式** - 优先使用函数式编程范式
3. **工程化** - 追求项目结构清晰、可维护性强

## 版本与环境

- **Go 版本**：1.23+ 推荐
- **依赖管理**：go.mod（支持 workspace）
- **工具链管理**：Go 1.23 内置 toolchain 指令

## Go 1.21-1.23 关键新特性

### Go 1.21（slog、内置函数）
```go
// 结构化日志（标准库）
import "log/slog"
slog.Info("user registered", "username", name, "email", email)

// 内置 min/max/clear
m := min(a, b)
M := max(a, b)
clear(mySlice) // 清空 slice
clear(myMap)   // 清空 map
```

### Go 1.22（for-range integer、增强路由）
```go
// for-range 整数
for i := range 10 {
    fmt.Println(i) // 0..9
}

// net/http 增强路由模式
mux.HandleFunc("GET /api/users/{id}", getUser)
mux.HandleFunc("POST /api/users", createUser)
```

### Go 1.23（range-over-func、iter 包）
```go
// range-over-func 迭代器
import "maps"
import "slices"

for k, v := range maps.All(m) {
    fmt.Println(k, v)
}

for i, v := range slices.All(s) {
    fmt.Println(i, v)
}

// 自定义迭代器
func (t *Tree[V]) All() iter.Seq2[string, V] {
    return func(yield func(string, V) bool) {
        // ...
    }
}
```

## 强制规范

### 必须遵守

- 所有 error 必须记录日志（禁止单行 if）
- 使用全局 State 模式而非 Repository 接口
- 严禁直接返回函数结果而不处理错误
- API Handler 仅做 HTTP 适配，逻辑委托给 Service 层

### 禁止行为

- 单行 if err 处理：`if err != nil { return err }`
- 手动 for 循环遍历集合（必须用 candy 库）
- 手动字符串转换（必须用 stringx 库）
- 使用 os.Stat 检查文件（必须用 osx 库）
- 使用 fmt.Errorf 包装错误

## 代码格式规范

### 自动格式化

```bash
gofmt -w .
goimports -w .
```

### 导入分组

```go
import (
    // 标准库
    "context"
    "fmt"
    "os"
    "time"

    // 第三方库
    "github.com/gofiber/fiber/v2"
    "github.com/lazygophers/log"
    "gorm.io/gorm"

    // 项目内部
    "github.com/username/project/internal/state"
    "github.com/username/project/internal/impl"
)
```

### 文件组织顺序

```go
package main

import ()

const ()

var ()

type MyType struct {}

type MyInterface interface {}

func main() {}
```

## 注释规范

### 导出类型必须有注释

```go
// User 表示系统用户
type User struct {
    Id        int64
    Email     string
    IsActive  bool
    CreatedAt time.Time
}
```

### 导出函数必须有注释

```go
// UserLogin 处理用户登录逻辑
func UserLogin(req *LoginReq) (*User, error) {}
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "单行 if err 更简洁" | 是否所有 error 都多行处理？ | 高 |
| "for 循环更直观" | 是否使用 candy 库操作集合？ | 高 |
| "fmt.Errorf 能加上下文" | 是否禁止包装错误，直接返回原始？ | 高 |
| "Go 1.18 泛型就够了" | 是否使用了 Go 1.23 新特性（iter、min/max）？ | 低 |
| "Repository 接口更灵活" | 是否使用全局 State 模式？ | 高 |
| "导出函数不用注释" | 是否所有导出类型/函数有注释？ | 中 |

## 提交前检查清单

- [ ] 所有 error 都有日志记录
- [ ] 没有单行 if err 语句或 if xxx = func(); xxx != nil 之类的判断
- [ ] 没有手动循环（应该用 candy）
- [ ] 没有 fmt.Errorf/errors.Wrap 包装错误
- [ ] 日志格式一致且清晰
- [ ] 没有 panic/recover 处理常规错误
- [ ] 代码已通过 gofmt 和 goimports
- [ ] 代码已通过 golangci-lint
- [ ] 所有导出类型和函数有注释
- [ ] 使用了适当的 Go 1.21+ 新特性
