# Golang 架构设计和工具链

## 架构设计规范

### 核心设计

```
API Layer (Fiber handlers)
    ↓
Service/Impl Layer (业务逻辑)
    ↓
Global State Layer (全局数据访问)
    ↓
Database
```

**关键特性**：

- ✅ **全局状态模式** - 无显式 Repository interface，直接使用全局 State 变量
- ✅ **三层清晰** - API → Service → State，单向依赖
- ✅ **启动流程** - State Init → Service Prep → API Run
- ✅ **事务支持** - 通过 state.Tx() 处理事务
- ✅ **无依赖注入** - Service 函数无需构造函数注入

### 设计原则

1. **全局状态模式**
    - 所有有状态资源（数据库、缓存、配置）作为全局变量
    - 避免使用 Repository 接口或依赖注入
    - 简化代码，减少样板代码

2. **三层架构**
    - **API 层**：HTTP 路由、请求验证、响应格式化
    - **Service 层**：业务逻辑实现、事务处理
    - **State 层**：数据访问、资源管理

3. **启动顺序**
    - 初始化全局 State（数据库、缓存）
    - 准备 Service 层（数据预加载）
    - 启动 API 服务器

## 项目结构

### 推荐目录布局

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

### 包组织规则

**state 文件夹规则**：

- ✅ 所有有状态资源放在 `internal/state/` 中
- ✅ Config（配置对象）
- ✅ Database（数据库连接）
- ✅ Cache（缓存实例）
- ✅ Global Models（全局数据访问对象）
- ✅ Message Queue、WebSocket Hub 等有状态组件

**impl 文件夹规则**：

- ✅ 按功能模块组织（user.go, friend.go 等）
- ✅ 函数名清晰体现功能（UserLogin, GetUserById）
- ✅ 单元测试与实现在同包（user_test.go）

**api 文件夹规则**：

- ✅ 路由定义和中间件链
- ✅ Handler 是简单的 HTTP 适配器
- ✅ 业务逻辑委托给 impl 层

## 代码生成

### Protocol Buffers

```bash
# 单个文件编译
protoc --go_out=. --go_opt=paths=source_relative *.proto

# 使用 go generate（推荐）
// 在源文件中添加
//go:generate protoc --go_out=. ./proto.proto

# 运行 generate
go generate ./...
```

### 代码生成最佳实践

- 将 proto 文件放在 `api/pb/` 目录
- 使用 `//go:generate` 自动化生成
- 生成后的代码纳入版本控制
- 定期更新 protoc 版本

## 依赖管理

### go.mod 最佳实践

```bash
# ✅ 初始化
go mod init github.com/username/project

# ✅ 清理依赖（移除未使用的）
go mod tidy

# ✅ 添加依赖
go get github.com/lazygophers/utils@latest

# ✅ 本地替换（开发时）
go mod edit -replace github.com/lazygophers/utils=/local/path

# ✅ 查看依赖树
go mod graph

# ✅ 检查依赖安全性
go list -m all
```

### 依赖原则

- **最小化依赖** - 仅添加必要的库
- **优先官方库** - 使用 Go 标准库优先
- **固定版本** - 使用具体版本号，避免 `latest`
- **定期审计** - 定期检查和更新依赖

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

### 开发工作流

1. **编写代码**

    ```bash
    gofmt -w .
    goimports -w .
    ```

2. **本地测试**

    ```bash
    go test -v -race -cover ./...
    ```

3. **代码检查**

    ```bash
    go vet ./...
    golangci-lint run
    ```

4. **性能基准**

    ```bash
    go test -bench=. -benchmem ./...
    ```

5. **提交前检查**
    ```bash
    go mod tidy
    go test -v ./...
    ```

## 优先级规则

当本规范与其他规范冲突时：

1. **实际项目代码** - 最高优先级（看现有实现）
2. **golang 包 API** - 依次按此规范
3. **传统 Go 实践** - 最低优先级

**核心原则**：实际代码风格 > 知识库

## 关键检查清单

提交代码前的完整检查：

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
- [ ] 项目结构遵循推荐布局
- [ ] 全局 State 变量清晰定义
- [ ] Service 层函数签名一致（ctx first）
- [ ] API Handler 简洁清晰
- [ ] 单元测试覆盖关键业务逻辑
- [ ] 代码已通过 go vet 和 golangci-lint

## 常见问题

**Q: 为什么不使用 Repository 接口？**
A: 全局状态模式更简洁，避免接口膨胀。实际项目实践证明可行。

**Q: 如何处理事务？**
A: 通过 `state.Tx()` 开启事务上下文，传递给 Service 层函数。

**Q: 如何测试 Service 层？**
A: Mock 全局 State，注入 test state，单元测试 Service 函数。

**Q: 性能会不会有问题？**
A: 全局变量在 Go 中是安全的，goroutine-safe。使用 sync.Pool 和 atomic 优化。
