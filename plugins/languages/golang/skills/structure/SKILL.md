---
description: Go 项目结构强制规范：三层架构（API->Impl->State）、全局状态模式、go.mod workspace 支持、禁止 Repository 接口。设计架构时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 项目结构规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）

## 相关 Skills

| 场景     | Skill                    | 说明                                |
| -------- | ------------------------ | ----------------------------------- |
| 核心规范 | Skills(golang:core)      | 核心规范：强制约定、代码格式        |
| 命名规范 | Skills(golang:naming)    | 命名规范：Id/Uid/IsActive/CreatedAt |
| 错误处理 | Skills(golang:error)     | 错误处理规范：禁止单行 if err       |
| 工具库   | Skills(golang:libs)      | 优先库规范：stringx/candy/osx       |

## 核心原则

### 必须遵守

1. **三层架构** - API (HTTP handlers) -> Impl (业务逻辑) -> State (全局数据访问)
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

## go.mod Workspace（Go 1.22+）

多模块项目使用 go.work 管理：

```
# go.work
go 1.23

use (
    ./server
    ./shared
    ./tools
)
```

## 推荐目录布局

```
server/
├── go.mod
├── go.sum
├── Makefile
├── .golangci.yml
├── config.yaml
├── internal/
│   ├── state/
│   │   ├── table.go        # 全局数据模型
│   │   ├── config.go       # 配置管理
│   │   ├── database.go     # 数据库连接
│   │   ├── cache.go        # 缓存连接
│   │   └── init.go         # 统一初始化
│   │
│   ├── impl/
│   │   ├── user.go         # 用户业务逻辑
│   │   ├── user_test.go    # 用户测试
│   │   ├── friend.go       # 好友业务逻辑
│   │   └── friend_test.go  # 好友测试
│   │
│   ├── api/
│   │   └── router.go       # 路由注册
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
    |
Service/Impl Layer (业务逻辑)
    |
Global State Layer (全局数据访问)
    |
Database
```

### State 文件夹规则

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

- 任何有状态的东西都放在 state 中
- state/init.go 中统一初始化
- state 包是应用唯一的"有状态保管所"

### Impl 文件夹规则

```go
func UserLogin(ctx *fiber.Ctx, req *LoginReq) (*LoginRsp, error) {
    user, err := state.User.NewScoop().
        Where("username", req.Username).
        First()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    return &LoginRsp{User: user}, nil
}
```

### API 文件夹规则

```go
func SetupRoutes(app *fiber.App) {
    public := app.Group("/api", middleware.OptionalAuth, middleware.Logger)
    public.Post("/Login", impl.ToHandler(impl.UserLogin))

    private := app.Group("/api", middleware.Auth, middleware.Logger)
    private.Post("/GetUserProfile", impl.ToHandler(impl.GetUserProfile))
}
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "Repository 接口更好测试" | 是否使用全局 State 模式？ | 高 |
| "service/ 目录更清晰" | Service 层是否在 impl/ 中？ | 高 |
| "config/ 单独管理配置" | 配置是否在 state/ 中？ | 中 |
| "model/ 分离数据模型" | 数据模型是否定义在 state/？ | 中 |
| "cmd/ 下多个子命令" | cmd/ 是否只有 main.go？ | 中 |
| "DI 框架更灵活" | 是否使用全局变量而非依赖注入？ | 高 |

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
