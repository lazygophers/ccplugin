---
name: golang-api
description: Go HTTP API 规范——响应始终 200 + body code 字段、路由 /api/* 全 POST 单段 <Action><Model>、中间件逐路由注册禁 Group(prefix,mw...)、handler 仅返回 (rsp,error)、认证走 header。设计 HTTP API、写路由/handler/中间件时触发。
---

# Go HTTP API 规范

## 五条铁律

1. **响应始终 HTTP 200**，业务错误走 body `code` 字段。
2. **路由全 POST**，单段命名 `<Action><Model>`。
3. **中间件逐路由注册**，禁 `app.Group(prefix, mw...)`。
4. **handler 仅返回 `(rsp, error)`**，响应构造在统一 wrap 层。
5. **认证走 header**（如 `X-Token`），禁 URL 参数传 token。

## 统一响应结构

```go
type Response struct {
    Code int32       `json:"code"`
    Msg  string      `json:"msg,omitempty"`
    Data interface{} `json:"data,omitempty"`
    Hint string      `json:"hint,omitempty"`
}
```

```json
{"code": 0, "data": {"id": 1, "name": "test"}}
{"code": 40001, "msg": "用户名已存在"}
```

HTTP status 始终 200。**禁用 HTTP status code 表达业务错误**（404/403/409 等）。

## 路由命名

```
POST /api/LoginUser       → impl.LoginUser
POST /api/GetUserProfile  → impl.GetUserProfile
POST /api/ListOrders      → impl.ListOrders
POST /api/UpdateUserName  → impl.UpdateUserName
POST /api/DelFriend       → impl.DelFriend
```

规则：
- `/api/*` 前缀
- 全 POST 方法
- 单段命名：`<动词><名词>`
- 禁 `/api/user/login`、`/api/v1/users/:id` 等 RESTful 路径

## 中间件注册

```go
// ✅ 逐路由注册
pub := app.Group("/api")
pub.Post("/LoginUser", middleware.OptionalAuth, middleware.Logger, impl.ToHandler(impl.LoginUser))
pub.Post("/GetUserProfile", middleware.Auth, middleware.Logger, impl.ToHandler(impl.GetUserProfile))

// ❌ Group 级中间件（同前缀多 Group 互相污染）
api := app.Group("/api", middleware.Auth, middleware.Logger)
```

逐路由注册避免同前缀路由的中间件意外作用范围。

## Handler 模式

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

- 函数签名固定 `func XxxYyy(req *XxxYyyReq) (*XxxYyyRsp, error)`
- `var rsp XxxRsp` 函数顶声明，逐字段赋值，末尾 `return &rsp`
- 禁字面量构造 `return &XxxRsp{Field: val}`
- 禁 `c.JSON()` / `c.SendStatus()` 直接操作 response

## 认证

```go
token := c.Get("X-Token")

// ❌ /api/GetUser?token=xxx
```

## 请求/响应命名

| 操作 | Request | Response |
| --- | --- | --- |
| 登录 | `UserLoginReq` | `UserLoginRsp` |
| 查询单条 | `GetUserByIdReq` | `GetUserByIdRsp` |
| 列表 | `ListUserReq` | `ListUserRsp` |
| 创建 | `AddUserReq` | `AddUserRsp` |
| 更新 | `UpdateUserReq` | `UpdateUserRsp` |
| 删除 | `DelUserReq` | `DelUserRsp` |

## 参数校验

```go
type AddUserReq struct {
    Username string `json:"username" validate:"required"`
    Email    string `json:"email" validate:"required,email"`
    Age      uint8  `json:"age" validate:"required,gte=0"`
}
```

- 用 `validate` tag 统一校验，禁手写 `if req.X == ""`
- 校验器在中间件层统一拦截
- Update 场景全字段 unconditional 赋值，禁零值跳过逻辑

## 禁止项

| 模式 | 替代 |
| --- | --- |
| HTTP 404/403/409 表达业务错 | 始终 200 + body code |
| RESTful 路径 `/users/:id` | POST `/api/GetUserById` |
| `app.Group(prefix, mw...)` | 逐路由注册中间件 |
| handler 内 `c.JSON()` | 统一 wrap 层 |
| URL 参数传 token | Header 传 token |
| 手写 `if req.X == ""` 校验 | `validate` tag |
| `return &Rsp{Field: val}` 字面量 | `var rsp; rsp.Field = val; return &rsp` |
| Update 零值跳过 | 全字段 unconditional |

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "RESTful 更标准" | 项目全 POST 单段？ |
| "404 更语义化" | 始终 200 + code？ |
| "Group 中间件方便" | 逐路由注册？ |
| "handler 直接 c.JSON 简单" | 统一 wrap 层？ |
| "零值跳过更灵活" | Update 全字段 unconditional？ |
| "手写校验更精确" | validate tag 统一拦截？ |

## 检查清单

- [ ] 所有 API 响应 HTTP 200
- [ ] 业务错误走 body code 字段
- [ ] 路由全 POST 单段 <Action><Model>
- [ ] 中间件逐路由注册
- [ ] handler 返回 (rsp, error)
- [ ] var rsp 函数顶声明
- [ ] 参数校验用 validate tag
- [ ] 认证走 header
