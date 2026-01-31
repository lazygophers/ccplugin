---
name: gozero-skills
description: go-zero 微服务框架开发规范和最佳实践
---

# go-zero 微服务框架开发规范

## 框架概述

go-zero 是一个云原生 Go 微服务框架，集成了 Web 框架、RPC 客户端、服务治理、工具链等完整微服务开发能力。

**核心特点：**
- 工具驱动（goctl 代码生成）
- 规范驱动（.api 和 .proto 定义）
- 内置服务治理（熔断、限流、负载均衡）
- 高性能（基于 Go 原生 HTTP/gRPC）
- 工程实践（日志、监控、链路追踪）

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|----------|
| [核心概念](core/core-concepts.md) | 架构、组件、goctl | 框架入门 |
| [API 服务](api/api.md) | API 定义、生成、配置 | API 开发 |
| [RPC 服务](rpc/rpc.md) | Proto 定义、生成、实现 | RPC 开发 |
| [服务治理](governance/governance.md) | 熔断、限流、负载均衡 | 生产部署 |
| [工具链](tooling/tooling.md) | goctl、代码生成 | 开发效率 |
| [最佳实践](best-practices/best-practices.md) | 项目结构、错误处理 | 架构设计 |
| [参考资源](references.md) | 官方文档、教程 | 深入学习 |

## 快速开始

go-zero 是云原生 Go 微服务框架：

- **工具驱动**：通过 goctl 代码生成减少样板代码
- **规范驱动**：使用 .api 和 .proto 文件定义服务
- **内置稳定性**：熔断、限流、超时控制等生产级特性
- **高性能**：基于 Go 原生 HTTP/gRPC
- **工程实践**：内置日志、监控、链路追踪

### 架构层次

```
┌─────────────────────────────────────────┐
│         API Gateway (HTTP)              │
│  路由、认证、限流、链路追踪入口            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         RPC Services (gRPC)             │
│  服务间通信、负载均衡、熔断降级            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│    Infrastructure Layer                 │
│  数据库、缓存、消息队列、服务发现          │
└─────────────────────────────────────────┘
```

### goctl 工具

**API 服务生成**：
```bash
goctl api go -api user.api -dir ./user -style goZero
```

**RPC 服务生成**：
```bash
goctl rpc protoc user.proto --go_out=./user --zrpc_out=./user
```

**Model 生成**：
```bash
goctl model mysql datasource -url="user:pass@tcp(127.0.0.1:3306)/db" -table="*" -dir="./model" -c
```

## API 服务

### API 定义

```api
syntax = "v1"

info(
    title: "用户服务"
    desc: "用户管理相关接口"
    author: "author"
    version: "v1.0"
)

type (
    // 登录请求
    LoginRequest {
        Username string `json:"username" validate:"required"`
        Password string `json:"password" validate:"required"`
    }

    // 登录响应
    LoginResponse {
        AccessToken string `json:"access_token"`
        ExpireTime  int64  `json:"expire_time"`
    }

    // 用户信息
    UserInfo {
        Id       int64  `json:"id"`
        Username string `json:"username"`
        Email    string `json:"email"`
    }
)

@server(
    prefix: /api/v1
    group: user
    jwt: Auth
)
service user-api {
    @doc "用户登录"
    @handler login
    post /user/login (LoginRequest) returns (LoginResponse)

    @doc "获取用户信息"
    @handler getUserInfo
    get /user/info returns (UserInfo)
}
```

### 配置文件

```yaml
Name: user-api
Host: 0.0.0.0
Port: 8888

Log:
  ServiceName: user-api
  Mode: console
  Level: info

Telemetry:
  Name: user-api
  Endpoint: http://jaeger:14268/api/traces
  Sampler: 1.0

Etcd:
  Hosts:
    - 127.0.0.1:2379
  Key: user.rpc

Auth:
  AccessSecret: your-secret-key
  AccessExpire: 86400

RateLimit:
  Seconds: 1
  Quota: 100

MySQL:
  DataSource: user:password@tcp(127.0.0.1:3306)/db

Redis:
  Host: 127.0.0.1:6379
  Type: node
  Pass: ""
```

### Handler 实现

```go
// internal/logic/loginlogic.go
package logic

import (
    "context"

    "github.com/zeromicro/go-zero/core/logx"
    "user/internal/svc"
    "user/internal/types"
)

type LoginLogic struct {
    ctx    context.Context
    svcCtx *svc.ServiceContext
    logx.Logger
}

func NewLoginLogic(ctx context.Context, svcCtx *svc.ServiceContext) *LoginLogic {
    return &LoginLogic{
        ctx:    ctx,
        svcCtx: svcCtx,
        Logger: logx.WithContext(ctx),
    }
}

func (l *LoginLogic) Login(req *types.LoginRequest) (resp *types.LoginResponse, err error) {
    // 验证用户
    user, err := l.svcCtx.UserModel.FindByUsername(l.ctx, req.Username)
    if err != nil {
        return nil, err
    }

    // 验证密码
    if !password.Verify(req.Password, user.Password) {
        return nil, errors.New("password error")
    }

    // 生成 Token
    token, err := l.generateToken(user.Id)
    if err != nil {
        return nil, err
    }

    return &types.LoginResponse{
        AccessToken: token,
        ExpireTime:  time.Now().Add(24 * time.Hour).Unix(),
    }, nil
}
```

## RPC 服务

### Proto 定义

```protobuf
syntax = "proto3";

package user;
option go_package = "./user";

message GetUserRequest {
    int64 id = 1;
}

message GetUserResponse {
    int64 id = 1;
    string username = 2;
    string email = 3;
    int64 created_at = 4;
}

message CreateUserRequest {
    string username = 1;
    string password = 2;
    string email = 3;
}

message CreateUserResponse {
    int64 id = 1;
}

service User {
    rpc GetUser(GetUserRequest) returns (GetUserResponse);
    rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);
}
```

### RPC 配置

```yaml
Name: user.rpc
ListenOn: 127.0.0.1:8080

Mysql:
  DataSource: user:password@tcp(127.0.0.1:3306)/db

RedisConf:
  Host: 127.0.0.1:6379
  Type: node
  Pass: ""

Etcd:
  Hosts:
    - 127.0.0.1:2379
  Key: user.rpc

Telemetry:
  Name: user.rpc
  Endpoint: http://jaeger:14268/api/traces
  Sampler: 1.0
```

### RPC 实现

```go
// internal/logic/getuserlogic.go
package logic

import (
    "context"

    "github.com/zeromicro/go-zero/core/logx"
    "user/internal/svc"
    "user/pb/user"
)

type GetUserLogic struct {
    ctx    context.Context
    svcCtx *svc.ServiceContext
    logx.Logger
}

func NewGetUserLogic(ctx context.Context, svcCtx *svc.ServiceContext) *GetUserLogic {
    return &GetUserLogic{
        ctx:    ctx,
        svcCtx: svcCtx,
        Logger: logx.WithContext(ctx),
    }
}

func (l *GetUserLogic) GetUser(in *user.GetUserRequest) (*user.GetUserResponse, error) {
    // 查询用户
    userModel, err := l.svcCtx.UserModel.FindOne(l.ctx, in.Id)
    if err != nil {
        return nil, err
    }

    return &user.GetUserResponse{
        Id:       userModel.Id,
        Username: userModel.Username,
        Email:    userModel.Email,
        CreatedAt: userModel.CreateTime.Unix(),
    }, nil
}
```

## 服务治理

### 熔断器

```go
import "github.com/zeromicro/go-zero/core/breaker"

breaker := breaker.NewBreaker()
err := breaker.DoWithFallbackAcceptable(func() error {
    return callDownstreamService()
}, func(err error) bool {
    return err == nil || isAcceptableError(err)
})
```

### 限流器

```go
import "github.com/zeromicro/go-zero/core/limit"

// 令牌桶限流
tokenLimiter := limit.NewTokenLimiter(rate, burst, redis, "ratelimit-{{.Key}}")
if !tokenLimiter.Allow() {
    return errors.New("rate limit exceeded")
}
```

### 超时控制

```go
import "github.com/zeromicro/go-zero/zrpc"

client := zrpc.MustNewClient(zrpc.RpcClientConf{
    Target: dnsServiceEndpoint,
    Timeout: time.Second * 3,
})
```

### 自适应熔断

go-zero 的自适应熔断器特点：
- 根据实时响应时间动态调整阈值
- 平滑状态转换
- 快速失败机制

## 项目结构

### 推荐结构

```
project/
├── services/
│   ├── user-api/              # API Gateway
│   │   ├── internal/
│   │   │   ├── config/
│   │   │   ├── handler/
│   │   │   ├── logic/
│   │   │   ├── svc/
│   │   │   ├── types/
│   │   │   └── middleware/
│   │   ├── user.api
│   │   └── etc/user-api.yaml
│   │
│   ├── user-rpc/              # RPC Service
│   │   ├── internal/
│   │   │   ├── config/
│   │   │   ├── logic/
│   │   │   ├── server/
│   │   │   ├── svc/
│   │   │   └── pb/
│   │   ├── user.proto
│   │   └── etc/user-rpc.yaml
│   │
│   └── common/                # 共享代码
│       ├── model/
│       ├── middleware/
│       └── utils/
│
├── api/                       # API 定义
├── rpc/                       # RPC 定义
├── db/                        # 数据库脚本
└── go.mod
```

## 最佳实践

### 错误处理

```go
// 统一错误码
const (
    Success         = 0
    BadRequest      = 400
    Unauthorized    = 401
    NotFound        = 404
    InternalError   = 500
    UserNotFound    = 10001
    UserAlreadyExist = 10002
)

// 错误处理
func (l *LoginLogic) Login(req *types.LoginRequest) (*types.LoginResponse, error) {
    user, err := l.svcCtx.UserModel.FindByUsername(l.ctx, req.Username)
    if err == model.ErrNotFound {
        return nil, common.NewCodeError(UserNotFound, "用户不存在")
    }
    if err != nil {
        return nil, common.NewDefaultError("数据库错误")
    }
    // ...
}
```

### 日志记录

```go
import "github.com/zeromicro/go-zero/core/logx"

func (l *LoginLogic) Login(req *types.LoginRequest) (*types.LoginResponse, error) {
    l.Info("Login request", logx.Field("username", req.Username))

    if err != nil {
        l.Errorf("Login failed: %v", err)
        return nil, err
    }

    return resp, nil
}
```

### 数据库操作

```go
// Model 使用（带缓存）
func (m *UserModel) FindOne(ctx context.Context, id int64) (*User, error) {
    query := fmt.Sprintf("SELECT %s FROM %s WHERE `id` = ? LIMIT 1", userRows, userTable)
    var resp User
    err := m.QueryRowNoCacheCtx(ctx, &resp, query, id)
    switch err {
    case nil:
        return &resp, nil
    case sqlc.ErrNotFound:
        return nil, ErrNotFound
    default:
        return nil, err
    }
}
```

### 配置管理

```go
// internal/config/config.go
package config

import "github.com/zeromicro/go-zero/zrpc"

type Config struct {
    RestConf
    Mysql    MysqlConf
    Redis    RedisConf
    Auth     AuthConf
    UserRpc  zrpc.RpcClientConf
}

type MysqlConf struct {
    DataSource string
}

type RedisConf struct {
    Host string
    Type string
    Pass string
}

type AuthConf struct {
    AccessSecret string
    AccessExpire int64
}
```

### 环境变量

```yaml
Name: user-api
Host: ${HOST:0.0.0.0}
Port: ${PORT:8888}

Mysql:
  DataSource: ${MYSQL_USER}:${MYSQL_PASS}@tcp(${MYSQL_HOST:127.0.0.1}:3306)/db

Redis:
  Host: ${REDIS_HOST:127.0.0.1}:6379
```

## 生态集成

### 数据库集成

```go
import "gorm.io/gorm"

db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
db.AutoMigrate(&User{})
```

### 缓存集成

```go
import "github.com/zeromicro/go-zero/core/stores/redis"

redisClient := redis.MustNewRedis(redis.RedisConf{
    Host: "127.0.0.1:6379",
    Type: redis.NodeType,
})
```

### 链路追踪

```yaml
Telemetry:
  Name: user-api
  Endpoint: http://jaeger:14268/api/traces
  Sampler: 1.0
```

### 监控

```go
// Prometheus 指标
http://localhost:6470/metrics
```

### 服务发现

```yaml
# etcd
Etcd:
  Hosts:
    - 127.0.0.1:2379
  Key: user.rpc

# Consul
# 使用社区支持
```

## 注意事项

1. API 和 RPC 分离
2. 使用 goctl 生成代码
3. 配置文件使用 YAML
4. 服务发现使用 etcd
5. 日志使用 logx
6. 错误处理统一格式
7. 实现熔断和限流
8. 配置监控和链路追踪

## 参考资源

- [go-zero GitHub](https://github.com/zeromicro/go-zero)
- [go-zero 文档](https://go-zero.dev/)
- [go-zero 教程](https://go-zero.dev/docs/tutorials)
