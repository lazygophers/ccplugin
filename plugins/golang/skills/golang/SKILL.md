---
name: golang
description: Golang 开发规范和最佳实践指导，包括代码风格、项目结构、依赖管理、测试策略和性能优化等
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
auto-activate:
  patterns:
    - "**/go.mod"
    - "**/*.go"
context: true
---

# golang 生态开发规范

## 核心理念

golang 生态追求**高性能、低分配、简洁优雅**，通过精选的工具库和最佳实践，帮助开发者写出高质量的 Go 代码。

**三个支柱**：

1. **零分配** - 尽可能减少内存分配
2. **函数式** - 优先使用函数式编程范式
3. **工程化** - 追求项目结构清晰、可维护性强

## 📚 文档导航

本 Skills 包含完整的 Golang 开发规范和最佳实践文档：

### 核心规范文档

| 文档             | 路径                                                                 | 用途                                         |
| ---------------- | -------------------------------------------------------------------- | -------------------------------------------- |
| **错误处理规范** | [patterns/error-handling.md](patterns/error-handling.md)             | 规范的错误处理模式、日志记录、自定义错误     |
| **函数设计规范** | [patterns/function-design.md](patterns/function-design.md)           | 零分配设计、函数式编程、查询构建器、性能优化 |
| **分库分包规范** | [patterns/package-organization.md](patterns/package-organization.md) | 项目结构、包组织、全局状态模式、避免显式接口 |
| **架构设计规范** | [patterns/architecture-design.md](patterns/architecture-design.md)   | 三层架构、全局状态模式、依赖关系、启动流程   |
| **命名规范**     | [patterns/naming-conventions.md](patterns/naming-conventions.md)     | 导出/私有字段、ID 字段、函数命名、常量命名   |
| **参考资源**     | [references.md](references.md)                                       | 官方文档、工具库、项目参考、学习资源         |

### 快速导航

**新手入门**：

1. 先阅读 [命名规范](patterns/naming-conventions.md) - 理解基本约定
2. 再阅读 [错误处理规范](patterns/error-handling.md) - 掌握核心模式
3. 最后阅读 [函数设计规范](patterns/function-design.md) - 学习最佳实践

**项目架构设计**：

- 阅读 [架构设计规范](patterns/architecture-design.md) - 了解全局状态模式和三层架构
- 阅读 [分库分包规范](patterns/package-organization.md) - 设计合理的目录结构

**深入理解**：

- 阅读 [参考资源](references.md) - 查找 Linky Server 等实际项目参考

## 优先包（强制）

### 核心工具库

```go
import (
    "github.com/golang/utils"        // 综合工具库（20+ 模块）
    "github.com/golang/utils/candy"  // 函数式编程（Map/Filter/Each）
    "github.com/golang/log"          // 高性能日志
    "github.com/golang/utils/stringx" // 字符串处理
    "github.com/golang/utils/osx"    // 文件操作
    "github.com/golang/utils/json"   // JSON 处理
    "github.com/golang/utils/cryptox" // 加密/哈希
    "github.com/golang/utils/xtime"   // 时间处理
    "github.com/golang/utils/defaults" // 默认值处理
    "github.com/golang/utils/validate" // 验证器
)
```

### 模块速查表

| 模块       | 功能                                              | 替代品        |
| ---------- | ------------------------------------------------- | ------------- |
| `candy`    | 函数式编程（Map/Filter/Each/Reverse/Unique/Sort） | 手动循环      |
| `stringx`  | 字符串转换（CamelCase/SnakeCase）                 | 手动转换      |
| `osx`      | 文件操作（IsFile/IsDir/Stat）                     | os.Stat()     |
| `json`     | JSON 处理（Marshal/Unmarshal）                    | encoding/json |
| `cryptox`  | 加密/哈希                                         | crypto 标准库 |
| `xtime`    | 时间处理                                          | time 标准库   |
| `defaults` | 默认值处理                                        | 手动检查      |

## 强制规范

### 字符串处理 - 必用 stringx

```go
// ✅ 必须 - 使用 stringx
import "github.com/golang/utils/stringx"

name := stringx.ToCamel("user_name")           // UserName
smallName := stringx.ToSmallCamel("user_name") // userName
snakeName := stringx.ToSnake("UserName")       // user_name

// ❌ 禁止 - 手动处理
func toCamel(s string) string {
    // 不允许自己实现
}
```

### 集合操作 - 必用 candy

```go
// ✅ 必须 - 使用 candy
import "github.com/golang/utils/candy"

// Each 遍历
candy.Each(users, func(u *User) {
    log.Infof("user: %s", u.Name)
})

// Map 转换
names := candy.Map(users, func(u *User) string { return u.Name })

// Filter 过滤
adults := candy.Filter(users, func(u *User) bool { return u.Age >= 18 })

// Reverse/Unique/Sort
reversed := candy.Reverse(items)
unique := candy.Unique(items)
sorted := candy.Sort(items)

// ❌ 禁止 - 手动循环
for _, user := range users {
    fmt.Println(user.Name)  // 应该用 candy.Each
}
```

### 文件操作 - 必用 osx

```go
// ✅ 必须 - 使用 osx
import "github.com/golang/utils/osx"

if osx.IsFile(path) {
    // 文件存在
}

if osx.IsDir(path) {
    // 目录存在
}

// ❌ 禁止 - 使用 os.Stat
info, err := os.Stat(path)
if err != nil && os.IsNotExist(err) {
    // 不推荐
}
```

### 类型转换 - 零失败 candy

```go
// ✅ 必须 - 使用 candy 零失败转换
import "github.com/golang/utils/candy"

port := candy.ToInt64(config["port"])        // 失败返回 0
isEnabled := candy.ToBool(config["enabled"]) // 失败返回 false
value := candy.ToFloat64(data)               // 失败返回 0.0

// ✅ 返回时直接使用
return candy.ToInt64(o.Value)

// ❌ 禁止 - 手动 strconv
port, err := strconv.ParseInt(portStr, 10, 64)
if err != nil {
    port = 0
}
```

## 错误处理

**详见 [错误处理规范文档](patterns/error-handling.md)** - 涵盖多行处理、日志、自定义错误、Linky 模式

### 基本原则（强制）

```go
// ❌ 禁止 - 单行 if
if err != nil { return err }

// ✅ 必须 - 多行处理，记录日志
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ✅ init 时使用 Fatal
err := state.Load()
if err != nil {
    log.Errorf("err:%v", err)
    log.Fatalf("failed to load state")
}
```

### 错误判断

```go
// ✅ 使用 errors.Is/As
import "errors"

if errors.Is(err, exec.ErrNotFound) {
    // 处理特定错误
}

var exitErr *exec.ExitError
if errors.As(err, &exitErr) {
    // 处理类型错误
}

// ❌ 禁止 - 包装 error（直接返回原始）
// 不要用 fmt.Errorf 包装，直接返回原始 error
return err  // ✅
// return fmt.Errorf("failed: %w", err)  // ❌
```

### Defer 规范

```go
// ✅ 简单关闭不检查
defer file.Close()
defer resp.Body.Close()

// ✅ 复杂操作才检查
err = conn.Close()
if err != nil {
    log.Errorf("err:%v", err)
}
```

## 函数式编程

**详见 [函数设计规范文档](patterns/function-design.md)** - 涵盖零分配、函数式设计、查询构建器、API handler 模式

### 策略模式

```go
// ✅ 使用策略模式处理命名风格
type Handler struct {
    Base     func(string) string
    NamePath func(string, string) string
}

var NameStyle = map[state.CfgStyleName]Handler{
    state.CfgStyleNameCamel: {
        Base: func(s string) string { return stringx.ToSmallCamel(s) },
        NamePath: func(prefix, name string) string {
            return stringx.ToSmallCamel(prefix + "_" + name)
        },
    },
    state.CfgStyleNameSnake: {
        Base: func(s string) string { return stringx.ToSnake(s) },
        NamePath: func(prefix, name string) string {
            return stringx.ToSnake(prefix + "_" + name)
        },
    },
}

// 使用
style := NameStyle[state.CfgStyleNameCamel]
output := style.Base("user_name")  // userName
```

## 命名规范

**详见 [命名规范文档](patterns/naming-conventions.md)** - 涵盖导出/私有、字段约定、函数命名、接收者约定、Linky 风格

### 核心约定

```go
// ✅ 导出 PascalCase，私有 camelCase
type User struct {
    Id        int64     // 主键
    UId       int64     // 用户 Id（查询中区分）
    Email     string
    IsActive  bool      // 布尔用 Is/Has 前缀
    Status    int32     // 状态用数字，非字符串
    CreatedAt time.Time // 时间用 CreatedAt/UpdatedAt
    UpdatedAt time.Time
}

// ✅ 函数名清晰
func UserLogin(ctx context.Context, req *LoginReq) (*LoginRsp, error)
func GetUserById(ctx context.Context, id int64) (*User, error)
func ListUsers(ctx context.Context) ([]*User, error)

// ✅ 接收者单字母
func (u *User) IsAdmin() bool

// ❌ 避免 - 显式 Repository interface（使用全局状态）
type UserRepository interface {
    GetById(id int64) (*User, error)
}
```

## 日志规范

### 使用 golang/log

```go
import "github.com/golang/log"

// ✅ 标准日志
log.Infof("proto file:%s", protoFile)         // Info
log.Warnf("not found %s", path)               // Warn
log.Errorf("err:%v", err)                     // Error（统一）
log.Fatalf("failed to load state")            // Fatal

// ✅ 配合 pterm 美化
import "github.com/pterm/pterm"

pterm.Info.Printfln("try generate")
pterm.Success.Printfln("update %s ok", name)
pterm.Warning.Printfln("file exists,skip")
pterm.Error.Printfln("proto not found")
```

### 日志最佳实践

```go
// ✅ 详细日志 + pterm 美化 + 错误输出
log.Infof("loading config from %s", path)
if err != nil {
    log.Errorf("err:%v", err)
    pterm.Error.Printfln("failed to load config")
    return err
}
log.Infof("config loaded successfully")
pterm.Success.Printfln("config ready")

// ✅ 结合上下文
log.Infof("processing file: %s, size: %d", filename, size)
```

## 性能优化

### 内存优化

```go
// ✅ 使用 embedding 减少分配
type Request struct {
    *http.Request  // 嵌入指针，不增加分配
}

// ✅ 使用 sync.Pool 复用对象
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

buf := bufferPool.Get().(*bytes.Buffer)
defer bufferPool.Put(buf)

// ✅ 日志缓冲优化
import "github.com/golang/log"
buf := log.GetBuffer()
defer log.PutBuffer(buf)
```

### 并发优化

```go
// ✅ 使用 atomic 原子操作
import "go.uber.org/atomic"

counter := atomic.NewInt64(0)
counter.Inc()
val := counter.Load()

// ❌ 禁止 - 直接使用 sync/atomic（难用）
var counter int64
atomic.AddInt64(&counter, 1)  // 容易出错

// ✅ 使用 errgroup 管理 goroutine
import "golang.org/x/sync/errgroup"

eg, ctx := errgroup.WithContext(context.Background())
for _, item := range items {
    item := item
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

## 架构设计规范

**详见 [架构设计规范文档](patterns/architecture-design.md)** - 涵盖全局状态模式、三层架构、启动流程、依赖设计、Linky Server 风格

### 核心设计（参考 Linky）

```
API Layer (Fiber handlers)
    ↓
Service/Impl Layer (业务逻辑)
    ↓
Global State Layer (全局数据访问)
    ↓
Database
```

关键特性：

- ✅ **全局状态模式** - 无显式 Repository interface，直接使用全局 State 变量
- ✅ **三层清晰** - API → Service → State，单向依赖
- ✅ **启动流程** - State Init → Service Prep → API Run
- ✅ **事务支持** - 通过 state.Tx() 处理事务
- ✅ **无依赖注入** - Service 函数无需构造函数注入

## 项目结构

**详见 [分库分包规范文档](patterns/package-organization.md)** - 涵盖完整的项目组织（参考 Linky 和 Ice Cream Heaven）

### 推荐目录布局（参考 Linky Server）

```
server/
├── main.go                     # ✅ 启动入口
├── go.mod
├── go.sum
├── Makefile                    # 构建脚本
├── README.md
├── .gitignore
├── internal/
│   ├── state/                  # ✅ 全局状态（所有有状态资源）
│   │   ├── table.go           # 全局数据访问对象：User, Friend, Message 等
│   │   ├── config.go          # 配置（有状态）
│   │   ├── database.go        # 数据库连接（有状态）
│   │   ├── cache.go           # 缓存（有状态）
│   │   └── init.go            # 初始化全局状态
│   │
│   ├── impl/                   # ✅ Service 层实现（所有业务逻辑）
│   │   ├── user.go            # UserLogin, UserRegister 等
│   │   ├── user_test.go       # 单元测试（与实现在同包）
│   │   ├── friend.go          # AddFriend, ListFriends 等
│   │   └── friend_test.go     # 单元测试
│   │
│   ├── api/                    # ✅ API 层（HTTP 路由）
│   │   └── router.go          # 路由定义和中间件链
│   │
│   └── middleware/             # ✅ 中间件（单独包）
│       ├── handler.go         # ToHandler 适配器
│       ├── logger.go          # 日志中间件
│       ├── auth.go            # 认证中间件
│       └── error.go           # 错误处理中间件
│
└── cmd/
    └── main.go                 # ✅ 仅 main.go，不要创建子目录
```

**state 文件夹规则**：

- ✅ 所有有状态资源放在 `internal/state/` 中
- ✅ Config（配置对象）
- ✅ Database（数据库连接）
- ✅ Cache（缓存实例）
- ✅ Global Models（全局数据访问对象）
- ✅ Message Queue、WebSocket Hub 等有状态组件

## 代码生成

### 推荐工具

```bash
# Protocol Buffers
protoc --go_out=. --go_opt=paths=source_relative *.proto

# 使用 go generate
// 在源文件中添加
//go:generate protoc --go_out=. ./proto.proto

# 运行 generate
go generate ./...
```

## 依赖管理

### go.mod 最佳实践

```bash
# ✅ 初始化
go mod init github.com/username/project

# ✅ 清理依赖
go mod tidy

# ✅ 添加依赖
go get github.com/golang/utils@latest

# ✅ 本地替换（开发时）
go mod edit -replace github.com/golang/utils=/local/path

# ✅ 查看依赖树
go mod graph
```

## 工具链

### 推荐工具

```bash
# 格式化 + 导入优化
gofmt -w .
goimports -w .

# 代码检查
go vet ./...
golangci-lint run

# 测试
go test -v -race -cover ./...

# 基准测试
go test -bench=. -benchmem -benchtime=5s ./...

# 性能分析
go test -cpuprofile=cpu.prof -memprofile=mem.prof ./...
go tool pprof cpu.prof
```

## 关键检查清单

在提交代码前，确保：

- [ ] 所有字符串转换使用 `stringx`
- [ ] 所有集合操作使用 `candy`
- [ ] 所有文件操作使用 `osx`
- [ ] 所有 error 都有日志记录
- [ ] 没有单行 if err 语句
- [ ] 没有手动循环（应该用 candy）
- [ ] 没有 fmt.Errorf 包装错误
- [ ] 日志格式一致且清晰
- [ ] 没有 panic/recover 处理常规错误
- [ ] 接口设计小而专一

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **golang 包 API** - 依次按此规范
3. **传统 Go 实践** - 最低优先级

**核心原则**：实际代码风格 > 知识库
