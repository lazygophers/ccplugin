---
name: golang-structure
description: Go 项目结构规范——三层架构（API → Impl → State）、全局状态模式、internal/ 私有包、cmd/ 仅 main.go、go.work 多模块、禁止 Repository 接口和 DI 容器、struct 公共字段开头全 omitempty、handler var rsp 顶声明、禁 legacy migration。设计项目骨架、新建目录、组织包、做架构评审时触发。
---

# Go 项目结构规范

## 三条铁律

1. **三层架构**：API（HTTP/RPC 适配） → Impl（业务逻辑） → State（全局数据访问）。
2. **全局状态模式**：state 包用全局变量持有 DB/Cache/Model 引用，**禁 Repository 接口**。
3. **单向依赖**：上层 → 下层，无循环依赖。`api` 不能被 `impl` 引用、`impl` 不能被 `state` 引用。

## 禁止行为

- 创建 `service/`、`repository/`、`model/`、`config/`、`test/` 目录
- `cmd/` 下放子包（仅 `main.go`）
- 用依赖注入框架（fx/wire/dig）
- 接口在提供方定义（应在消费方）
- 写 legacy migration / 兼容代码（`preMigrateLegacy` 等）
- 自动迁移改主键（PK 变更需手动 DDL）

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
│   │   ├── table.go        # 全局数据模型 var User/Friend/...
│   │   ├── config.go       # var Config *AppConfig
│   │   ├── database.go     # var DB *gorm.DB
│   │   ├── cache.go        # var Cache *Cache
│   │   └── init.go         # 统一初始化入口
│   ├── impl/
│   │   ├── user.go
│   │   ├── user_test.go
│   │   ├── friend.go
│   │   └── friend_test.go
│   ├── api/
│   │   └── router.go
│   └── middleware/
│       ├── auth.go
│       ├── logger.go
│       └── error.go
└── cmd/
    └── main.go
```

## 三层职责

### state — 唯一有状态保管所

```go
package state

var (
    DB      *gorm.DB
    Cache   *Cache
    Config  *AppConfig

    User    *db.Model[User]
    Friend  *db.Model[Friend]
    Message *db.Model[Message]
)
```

- 任何「有状态」的东西放这里：连接、配置、模型、客户端。
- `state/init.go` 统一初始化，main 只调一次 `state.Init()`。

### impl — 业务逻辑

```go
package impl

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

- 直接调 `state.Xxx`，无 mocks 注入。测试时 `state.User = mock` 临时替换。
- 函数签名固定 `func XxxYyy(ctx, *Req) (*Rsp, error)`。

### api — HTTP/RPC 适配

```go
package api

func SetupRoutes(app *fiber.App) {
    pub := app.Group("/api", middleware.OptionalAuth, middleware.Logger)
    pub.Post("/Login", impl.ToHandler(impl.UserLogin))

    priv := app.Group("/api", middleware.Auth, middleware.Logger)
    priv.Post("/GetUserProfile", impl.ToHandler(impl.GetUserProfile))
}
```

- api 不写业务逻辑，仅做路由 + 中间件挂载。

## go.work 多模块（Go 1.22+）

```
go 1.26

use (
    ./server
    ./shared
    ./tools
)
```

仅在多个独立可发布模块共仓时用。单模块项目不需要。

## 框架选型（2026 现状）

| 场景 | 选择 |
| --- | --- |
| 简单 API、追求最小依赖 | 标准库 `net/http` + Go 1.22+ 增强路由 |
| 团队主流、生态最大 | Gin |
| 内置完整、清晰 API | Echo |
| 极致 QPS、可接受 fasthttp 锁定 | Fiber |
| 标准库可组合中间件 | Chi |

参考：JetBrains 2026 调查 Gin 48% / Gorilla 17% / Echo 16% / Fiber 11%。本项目 lazygophers 生态默认 Fiber。

## Struct 字段布局

```go
type UserLoginReq struct {
    // 1. 标识字段
    Id       uint64 `json:"id,omitempty"`
    Username string `json:"username,omitempty"`

    // 2. 业务字段
    Password string `json:"password,omitempty"`
    Email    string `json:"email,omitempty"`

    // 3. 状态/枚举
    State uint8 `json:"state"`

    // 4. 时间戳
    CreatedAt int64 `json:"created_at"`
    UpdatedAt int64 `json:"updated_at"`
}
```

- 公共字段（Id/时间戳）开头
- 全字段 `json` tag + `omitempty`（状态/时间除外，零值有意义）
- 禁指针字段区分零值和缺失，零值=不传

## Handler 实现模式

```go
func UserLogin(req *UserLoginReq) (*UserLoginRsp, error) {
    var rsp UserLoginRsp

    user, err := state.User.NewScoop().
        Where("username", req.Username).
        First()
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    rsp.Token = generateToken(user.Id)
    rsp.User = user
    return &rsp, nil
}
```

- `var rsp XxxRsp` 函数顶声明
- 逐字段赋值
- 末尾 `return &rsp`
- 禁字面量构造 `return &XxxRsp{Field: val}`

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "Repository 接口好测试" | 用全局 state？ |
| "service/ 目录清晰" | service 在 impl/ 中？ |
| "config/ 单独管理" | 配置在 state/？ |
| "model/ 分离数据" | 模型在 state/？ |
| "cmd/ 多子命令" | cmd 仅 main.go？ |
| "DI 框架灵活" | 全局变量而非 DI？ |
| "指针区分零值和缺失" | omitempty + 零值=不传？ |
| "字面量构造更简洁" | var rsp 顶声明？ |
| "兼容迁移更安全" | 禁 legacy migration？ |

## 检查清单

- [ ] 目录遵循推荐布局
- [ ] 有状态资源在 `internal/state/`
- [ ] 业务在 `internal/impl/`
- [ ] 路由在 `internal/api/`
- [ ] 中间件在 `internal/middleware/`
- [ ] 测试与实现同包
- [ ] `cmd/` 仅 main.go
- [ ] 包名全小写单数
- [ ] 依赖单向无循环
- [ ] 无 Repository 接口、无 DI 容器
- [ ] Struct 公共字段开头 + omitempty
- [ ] Handler var rsp 顶声明
- [ ] 无 legacy migration 代码
