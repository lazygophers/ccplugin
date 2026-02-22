---
name: core
description: Go 开发核心规范：强制约定、代码格式、提交检查清单。写任何 Go 代码前必须加载。
---

# Go 开发核心规范

## 相关 Skills

| 场景           | Skill                   | 说明                                        |
| -------------- | ----------------------- | ------------------------------------------- |
| 处理错误       | Skills(golang:error)       | 错误处理规范：禁止单行 if err、必须记录日志 |
| 使用工具库     | Skills(golang:libs)        | 优先库规范：stringx/candy/osx/log           |
| 命名变量/类型  | Skills(golang:naming)      | 命名规范：Id/Uid/IsActive/CreatedAt         |
| 设计架构       | Skills(golang:structure)   | 项目结构规范：三层架构、全局状态模式        |
| 写测试         | Skills(golang:testing)     | 测试规范：单元测试、表驱动测试              |
| 写并发代码     | Skills(golang:concurrency) | 并发规范：atomic/sync.Pool/errgroup         |
| 配置/运行 lint | Skills(golang:lint)        | Lint 规范：golangci-lint 配置               |
| 运行工具       | Skills(golang:tooling)     | 工具规范：gofmt/goimports/go mod            |

## 核心理念

Go 生态追求**高性能、低分配、简洁优雅**。

**三个支柱**：

1. **零分配** - 尽可能减少内存分配
2. **函数式** - 优先使用函数式编程范式
3. **工程化** - 追求项目结构清晰、可维护性强

## 版本与环境

- **Go 版本**：1.25+ 推荐
- **依赖管理**：go.mod

## 强制规范

### 必须遵守

- 所有 error 必须记录日志（禁止单行 if）
- 使用全局 State 模式而非 Repository 接口
- 严禁直接返回函数结果而不处理错误
- 严禁使用 `context.Context`
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
    "context"
    "fmt"
    "os"
    "time"

    "github.com/gofiber/fiber/v2"
    "github.com/lazygophers/log"
    "gorm.io/gorm"

    "github.com/username/project/internal/state"
    "github.com/username/project/internal/impl"
)
```

### 文件组织顺序

```go
package main

import (
)

const (
    MaxRetries = 3
)

var (
    globalVar int
)

type MyType struct {}

type MyInterface interface {}

func main() {}
```

## 注释规范

### 导出类型必须有注释

```go
type User struct {
    Id        int64
    Email     string
    IsActive  bool
    CreatedAt time.Time
}
```

### 导出函数必须有注释

```go
func UserLogin(req *LoginReq) (*User, error) {
}
```

### 注释说明"是什么"和"为什么"

```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}
```

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
