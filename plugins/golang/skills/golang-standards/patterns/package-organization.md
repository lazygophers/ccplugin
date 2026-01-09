# 分库分包规范

## 核心原则

### ✅ 必须遵守

1. **标准目录结构** - 遵循 Go 官方推荐的项目布局
2. **包名规范** - 包名简洁、有意义、全小写
3. **公开性明确** - 用 `internal/` 隐藏内部实现，`pkg/` 暴露公开接口
4. **单一职责** - 每个包职责单一，内聚度高
5. **循环依赖禁止** - 任何包都不能形成循环依赖

### ❌ 禁止行为

- 包名大写或包含下划线
- 把所有代码放在根目录
- 公开包中混合内部实现
- 依赖关系不清（横向依赖）
- 深度嵌套包（超过 3 层）

## 标准项目布局

### 完整项目结构

```
project/
├── cmd/                    # 应用入口
│   ├── app/               # 主应用
│   │   └── main.go
│   └── cli/               # CLI 工具（可选）
│       └── main.go
│
├── internal/              # 内部实现（禁止外部引用）
│   ├── api/              # API 接口处理
│   │   ├── handler.go
│   │   └── middleware.go
│   ├── service/          # 业务逻辑
│   │   ├── user.go
│   │   └── order.go
│   ├── repository/       # 数据访问
│   │   ├── user.go
│   │   └── db.go
│   ├── config/           # 配置管理
│   │   └── config.go
│   ├── model/            # 内部数据模型
│   │   └── model.go
│   └── util/             # 内部工具函数
│       └── helper.go
│
├── pkg/                   # 公开包（可被外部引用）
│   ├── models/           # 公开数据模型
│   │   └── user.go
│   ├── errors/           # 公开错误
│   │   └── error.go
│   └── client/           # 公开客户端
│       └── client.go
│
├── test/                  # 集成测试
│   ├── integration_test.go
│   └── fixtures/         # 测试数据
│
├── go.mod
├── go.sum
├── Makefile             # 构建脚本
└── README.md
```

### 最小项目结构

```
project/
├── cmd/
│   └── app/
│       └── main.go
├── internal/
│   ├── api/
│   │   └── handler.go
│   ├── service/
│   │   └── service.go
│   └── config/
│       └── config.go
├── go.mod
├── main.go              # 简单项目可直接在根目录
└── README.md
```

## 包的组织原则

### 包命名规范

```go
// ✅ 正确 - 简洁有意义
package api        // API 相关
package service    // 业务逻辑
package repository // 数据访问
package config     // 配置
package model      // 数据模型
package util       // 工具函数
package cache      // 缓存

// ✅ 子包命名
package user       // internal/service/user
package mysql      // internal/repository/mysql
package redis      // internal/cache/redis

// ❌ 避免 - 模糊、大写、下划线
package impl       // 太模糊
package Impl       // 大写
package v1_impl    # 下划线
package utils      # 复数形式
package helpers    # 复数形式
```

### 包大小控制

```go
// ✅ 合理的包大小
// - user.go ~500 行：用户相关所有函数
// - service.go ~300 行：核心业务逻辑
// - 每个文件 200-500 行

// ❌ 避免
// - service.go 2000 行：包含所有业务逻辑
// - 多个功能混在一个文件
```

### 文件组织（同一包内）

```
service/
├── service.go       # 接口定义和公开方法
├── user.go          # 用户相关实现
├── order.go         # 订单相关实现
├── internal.go      # 内部辅助函数（可选）
└── service_test.go  # 测试

// ✅ 文件顺序
1. 接口定义
2. 公开函数
3. 私有函数
4. 测试用例
```

## 内部包 vs 公开包

### Internal 包（强制隐藏）

```go
// internal/service/user.go
package service

// ❌ 禁止从外部引用 internal/*
import "myapp/internal/service"

// ✅ 只能从 internal 内部引用
import "myapp/internal/repository"

// internal 包的特点：
// 1. 实现细节（具体实现）
// 2. 不稳定 API
// 3. 项目特定逻辑
// 4. 可以随意重构
```

### Pkg 包（公开 API）

```go
// pkg/models/user.go
package models

// ✅ 可以从外部引用
// other-project/main.go
import "myapp/pkg/models"

// pkg 包的特点：
// 1. 稳定接口
// 2. 向后兼容
// 3. 通用逻辑
// 4. 需要版本管理
```

### 何时使用 Pkg

```go
// ✅ 使用 pkg 的情况：
// - 库项目（被其他项目引用）
// - 公开的数据模型（User, Order 等）
// - 通用客户端（HTTPClient, DBClient）
// - 公开的错误类型

// ❌ 不使用 pkg：
// - API handlers（私有实现）
// - 服务实现（private）
// - 配置相关（project specific）
```

## 依赖关系设计

### 依赖方向（强制）

```go
// ✅ 正确的依赖方向（自上而下）
cmd/
  └── internal/api/       ← API handlers
        └── internal/service/  ← business logic
              └── internal/repository/  ← data access
                    └── internal/model/     ← data model

// 关键规则：
// 1. cmd 可以导入任何包
// 2. api 导入 service（不导入 repository）
// 3. service 导入 repository
// 4. repository 不导入其他业务包
// 5. model 是最底层，不导入任何业务包

// ❌ 禁止
// - api 直接导入 repository（跳过 service）
// - service 导入 api（向上依赖）
// - 形成循环依赖：api → service → api
```

### 依赖注入

```go
// ✅ 构造函数注入依赖
type UserService struct {
    repo repository.User
    cache Cache
}

func NewUserService(repo repository.User, cache Cache) *UserService {
    return &UserService{repo: repo, cache: cache}
}

// ✅ 方法接收依赖
func (s *UserService) Get(ctx context.Context, id int) (*User, error) {
    // ctx 是方法级依赖
}

// ❌ 全局变量
var globalDB *sql.DB  // 避免

// ❌ 硬编码创建
func (s *UserService) Get(id int) {
    db := sql.Open(...)  // 不行
}
```

## 常见包类型

### 1. API 层

```go
// internal/api/handler.go
package api

type Handler struct {
    service *service.Service
    logger  Logger
}

func (h *Handler) Register(ctx *fiber.Ctx) error {
    // API 处理逻辑
}

// ✅ 特点：
// - 接收 HTTP 请求
// - 调用 service 层
// - 返回 HTTP 响应
```

### 2. Service 层

```go
// internal/service/user.go
package service

type UserService struct {
    repo repository.User
}

func (s *UserService) Register(ctx context.Context, req *RegisterReq) (*User, error) {
    // 业务逻辑
    // 调用 repository
}

// ✅ 特点：
// - 业务逻辑实现
// - 与 HTTP 无关
// - 易于测试
```

### 3. Repository 层

```go
// internal/repository/user.go
package repository

type UserRepository struct {
    db *sql.DB
}

func (r *UserRepository) GetByID(ctx context.Context, id int) (*User, error) {
    // 数据访问逻辑
}

// ✅ 特点：
// - 数据访问抽象
// - 数据库操作
// - 与业务逻辑无关
```

### 4. Model 层

```go
// internal/model/user.go
package model

type User struct {
    ID    int
    Name  string
    Email string
}

// ✅ 特点：
// - 数据结构定义
// - 不包含业务逻辑
// - 可以在各层共享
```

## 包间通信

### 接口定义（推荐放在上层）

```go
// internal/service/interface.go
package service

type Repository interface {
    GetUser(ctx context.Context, id int) (*User, error)
    SaveUser(ctx context.Context, user *User) error
}

// ✅ 好处：
// - service 定义需要的接口
// - repository 实现接口
// - 依赖反转
```

### 错误定义位置

```go
// pkg/errors/error.go 或 internal/error.go
package errors

var (
    ErrNotFound      = errors.New("not found")
    ErrInvalidInput  = errors.New("invalid input")
    ErrUnauthorized  = errors.New("unauthorized")
)

// ✅ 优势：
// - 统一错误管理
// - 易于测试
// - 避免硬编码错误字符串
```

## 初始化顺序

### Main 函数中的初始化

```go
// cmd/app/main.go
func main() {
    // 1. 加载配置
    cfg := config.Load()

    // 2. 初始化资源（数据库、缓存等）
    db := database.New(cfg.Database)
    cache := cache.New(cfg.Cache)

    // 3. 初始化 repository 层
    userRepo := repository.NewUserRepository(db)

    // 4. 初始化 service 层
    userService := service.NewUserService(userRepo, cache)

    // 5. 初始化 API 层
    handler := api.NewHandler(userService)

    // 6. 启动应用
    router := setupRouter(handler)
    router.Listen(cfg.Port)
}

// ✅ 自下而上初始化：
// repository → service → api → main
```

## 管理复杂项目

### 中等规模项目

```
project/
├── cmd/
│   └── app/main.go
├── internal/
│   ├── api/
│   │   ├── handler.go
│   │   └── middleware.go
│   ├── service/
│   │   ├── user.go
│   │   └── order.go
│   ├── repository/
│   │   ├── user.go
│   │   └── order.go
│   ├── model/
│   │   └── model.go
│   └── config/
│       └── config.go
├── pkg/
│   ├── models/
│   │   └── user.go
│   └── client/
│       └── client.go
└── test/
    └── integration_test.go
```

### 大规模项目

```
project/
├── cmd/
│   ├── app/
│   │   └── main.go
│   └── migration/
│       └── main.go
├── internal/
│   ├── user/          # 按领域分包
│   │   ├── api/
│   │   ├── service/
│   │   └── repository/
│   ├── order/
│   │   ├── api/
│   │   ├── service/
│   │   └── repository/
│   ├── payment/
│   │   ├── api/
│   │   ├── service/
│   │   └── repository/
│   ├── shared/        # 共享层
│   │   ├── config/
│   │   ├── model/
│   │   └── middleware/
│   └── infra/         # 基础设施
│       ├── db/
│       ├── cache/
│       └── log/
└── pkg/
    ├── models/
    └── errors/
```

## 参考

- [Go Project Layout](https://github.com/golang-standards/project-layout)
- [Effective Go - Packages](https://golang.org/doc/effective_go#package-names)
- [Linky Server 项目结构](../../../references/linky-server-structure.md)
