---
name: structure
description: Go 项目结构强制规范：三层架构、全局状态模式、禁止 Repository 接口。设计架构时必须加载。
---

# Go 项目结构规范

## 相关 Skills

| 场景     | Skill          | 说明                                |
| -------- | -------------- | ----------------------------------- |
| 核心规范 | Skills(core)   | 核心规范：强制约定、代码格式        |
| 命名规范 | Skills(naming) | 命名规范：Id/Uid/IsActive/CreatedAt |
| 错误处理 | Skills(error)  | 错误处理规范：禁止单行 if err       |
| 工具库   | Skills(libs)   | 优先库规范：stringx/candy/osx       |

## 核心原则

### 必须遵守

1. **三层架构** - API (HTTP handlers) → Impl (业务逻辑) → State (全局数据访问)
2. **全局状态模式** - 使用全局变量存储数据访问对象，而非依赖注入
3. **单向依赖** - 上层依赖下层，无循环依赖
4. **包名简洁** - 全小写、单数、有意义
5. **文件组织** - 按功能模块组织文件

### 禁止行为

- 创建 `service/` 目录 - Service 层在 `impl/` 中
- 创建 `config/` 目录 - 配置在 `state/` 中
- 创建 `model/` 目录 - 数据模型定义在 `state/` 中
- 创建 `test/` 目录 - 测试文件在各包中（`*_test.go`）
- `cmd/` 下有子目录 - 仅放 main.go
- 创建 Repository 接口 - 使用全局状态

## 推荐目录布局

```
server/
├── go.mod
├── go.sum
├── Makefile
├── README.md
├── .gitignore
├── .golangci.yml
├── Dockerfile
├── dev.Dockerfile
├── prod.Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── config.yaml
├── config.example.yaml
├── config.dev.yaml
├── config.prod.yaml
├── internal/
│   ├── state/
│   │   ├── table.go
│   │   ├── config.go
│   │   ├── database.go
│   │   ├── cache.go
│   │   └── init.go
│   │
│   ├── impl/
│   │   ├── user.go
│   │   ├── user_test.go
│   │   ├── friend.go
│   │   └── friend_test.go
│   │
│   ├── api/
│   │   └── router.go
│   │
│   └── middleware/
│       ├── handler.go
│       ├── logger.go
│       ├── auth.go
│       └── error.go
│
└── cmd/
    └── main.go
```

## 三层架构

```
API Layer (Fiber handlers)
    ↓
Service/Impl Layer (业务逻辑)
    ↓
Global State Layer (全局数据访问)
    ↓
Database
```

### 关键特性

- 全局状态模式 - 无显式 Repository interface，直接使用全局 State 变量
- 三层清晰 - API → Service → State，单向依赖
- 启动流程 - State Init → Service Prep → API Run
- 事务支持 - 通过 state.Tx() 处理事务
- 无依赖注入 - Service 函数无需构造函数注入

## State 文件夹规则

```go
var (
    User    *db.Model[User]
    Friend  *db.Model[Friend]
    Message *db.Model[Message]
)

var Config *AppConfig
var DB *gorm.DB
var Cache *Cache
```

**规则**：

- 任何有状态的东西都放在 state 中
- Config、Database、Cache、Hub、Queue 等全部在 state
- state/init.go 中统一初始化这些资源
- state 包是应用唯一的"有状态保管所"

## Impl 文件夹规则

```go
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    user, err := User.NewScoop().
        Where("username", req.Username).
        First()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    return &LoginRsp{User: user}, nil
}
```

**规则**：

- 按功能模块组织（user.go, friend.go 等）
- 函数名清晰体现功能（UserLogin, GetUserById）
- 单元测试与实现在同包（user_test.go）

## API 文件夹规则

```go
func SetupRoutes(app *fiber.App) {
    public := app.Group("/api", middleware.OptionalAuth, middleware.Logger)
    public.Post("/Login", impl.ToHandler(impl.UserLogin))
    public.Post("/Register", impl.ToHandler(impl.UserRegister))

    private := app.Group("/api", middleware.Auth, middleware.Logger)
    private.Post("/GetUserProfile", impl.ToHandler(impl.GetUserProfile))
    private.Post("/AddFriend", impl.ToHandler(impl.AddFriend))
}
```

## 依赖关系设计

```
HTTP Request
    ↓
API Router (api/router.go)
    ↓
Handler (impl/handler.go)  ← ToHandler 适配器
    ↓
Impl Functions (impl/*.go)  ← 业务逻辑
    ↓
Global State (state/table.go)  ← 全局数据访问
    ↓
Database
```

**规则**：

- 上层只能调用下层
- 下层不能调用上层
- 同层可以相互调用
- 禁止循环依赖
- 禁止跨层调用

## 检查清单

- [ ] 项目结构遵循推荐布局
- [ ] 所有有状态资源在 `internal/state/` 中
- [ ] Service 层在 `internal/impl/` 中
- [ ] API 层在 `internal/api/` 中
- [ ] 中间件在 `internal/middleware/` 中
- [ ] 测试文件与实现在同包（`*_test.go`）
- [ ] `cmd/` 下只有 main.go，无子目录
- [ ] 包名全小写、单数、有意义
- [ ] 文件按功能模块组织
- [ ] 依赖关系单向，无循环依赖
- [ ] 没有 Repository 接口
