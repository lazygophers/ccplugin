# 架构设计规范

## 核心原则

### ✅ 必须遵守

1. **分层设计** - 清晰的层级划分（API → Service → Repository）
2. **接口导向** - 通过接口解耦，依赖倒转
3. **单一职责** - 每层职责明确，不混合逻辑
4. **依赖注入** - 显式注入依赖，便于测试
5. **错误处理集中** - 在 API 层统一处理错误

### ❌ 禁止行为

- 跨层直接调用（API 直接调用 Repository）
- 硬编码依赖（全局变量、硬编码创建）
- 业务逻辑泄露到 API 层
- 循环依赖
- 每层都处理 HTTP（混合关注点）

## 标准三层架构

### 概览

```
┌─────────────────────────────────────────┐
│           HTTP Router                    │
├─────────────────────────────────────────┤
│ API Handler Layer (external boundary)    │
│ - HTTP parsing                          │
│ - Parameter validation                  │
│ - Response formatting                   │
│ - Error translation to HTTP             │
├─────────────────────────────────────────┤
│ Service Layer (business logic)          │
│ - Business logic                        │
│ - Transaction management                │
│ - Cross-repository operations           │
├─────────────────────────────────────────┤
│ Repository Layer (data access)          │
│ - Database operations                   │
│ - Caching                               │
│ - External service calls                │
├─────────────────────────────────────────┤
│ Model Layer (data structure)            │
│ - Data structure definitions            │
│ - Constants and enums                   │
└─────────────────────────────────────────┘
```

### 层级职责

#### API 层（Internal）

```go
// internal/api/handler.go
package api

type Handler struct {
    service *service.UserService
    logger  Logger
}

func (h *Handler) Register(ctx *fiber.Ctx) error {
    // ✅ 职责：解析、验证、调用、响应

    // 1. 解析请求
    var req RegisterRequest
    if err := ctx.BodyParser(&req); err != nil {
        return h.error(ctx, http.StatusBadRequest, err)
    }

    // 2. 业务逻辑验证（可选，复杂验证放 service）
    if err := req.Validate(); err != nil {
        return h.error(ctx, http.StatusBadRequest, err)
    }

    // 3. 调用 service 层
    user, err := h.service.Register(ctx.Context(), req)
    if err != nil {
        log.Errorf("err:%v", err)
        return h.error(ctx, http.StatusInternalServerError, err)
    }

    // 4. 返回响应
    return ctx.JSON(http.StatusCreated, user)
}

// ❌ 禁止做的事
// - 直接访问数据库：h.db.Query(...)
// - 复杂的业务逻辑：if user.age > 18 { ... }
// - 调用 repository：h.repo.GetUser(...)
```

#### Service 层（Internal）

```go
// internal/service/user.go
package service

type UserService struct {
    repo repository.User
    cache Cache
}

func (s *UserService) Register(ctx context.Context, req *RegisterRequest) (*User, error) {
    // ✅ 职责：业务逻辑、事务管理、数据验证

    // 1. 业务验证
    exists, err := s.repo.ExistsByEmail(ctx, req.Email)
    if err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }
    if exists {
        return nil, ErrEmailExists
    }

    // 2. 数据处理
    hashedPassword := hashPassword(req.Password)
    user := &User{
        Email:    req.Email,
        Password: hashedPassword,
    }

    // 3. 存储数据（通过 repository）
    if err := s.repo.Save(ctx, user); err != nil {
        log.Errorf("err:%v", err)
        return nil, err
    }

    // 4. 更新缓存（可选）
    s.cache.Set(user.Email, user)

    return user, nil
}

// ❌ 禁止做的事
// - 直接数据库操作：rows, _ := db.Query(...)
// - 返回 HTTP 错误：return nil, errors.New("400 Bad Request")
// - HTTP 相关逻辑：w.WriteHeader(...)
```

#### Repository 层（Internal）

```go
// internal/repository/user.go
package repository

type UserRepository struct {
    db *sql.DB
}

func (r *UserRepository) ExistsByEmail(ctx context.Context, email string) (bool, error) {
    // ✅ 职责：数据访问、查询构建、错误处理

    var count int
    err := r.db.QueryRowContext(ctx,
        "SELECT COUNT(*) FROM users WHERE email = ?",
        email,
    ).Scan(&count)

    if err != nil {
        log.Errorf("err:%v", err)
        return false, err
    }

    return count > 0, nil
}

func (r *UserRepository) Save(ctx context.Context, user *User) error {
    // 数据存储
    _, err := r.db.ExecContext(ctx,
        "INSERT INTO users (email, password) VALUES (?, ?)",
        user.Email,
        user.Password,
    )
    if err != nil {
        log.Errorf("err:%v", err)
        return err
    }
    return nil
}

// ❌ 禁止做的事
// - 业务逻辑：if email exists, check age, ...
// - 返回错误码：return 400, nil
// - 多个 repository 调用（跨层）：r.role.Get(...)
```

#### Model 层（Internal/Pkg）

```go
// internal/model/user.go 或 pkg/models/user.go
package model

type User struct {
    ID       int    `db:"id"`
    Email    string `db:"email"`
    Password string `db:"password"`
    Created  time.Time `db:"created"`
}

type RegisterRequest struct {
    Email    string `json:"email"`
    Password string `json:"password"`
}

func (r *RegisterRequest) Validate() error {
    if len(r.Email) == 0 {
        return errors.New("email required")
    }
    if len(r.Password) < 8 {
        return errors.New("password too short")
    }
    return nil
}

// ✅ 职责：纯数据结构、验证方法
// ❌ 禁止：业务逻辑、数据库访问
```

## 接口设计原则

### 面向接口编程

```go
// ✅ 好的设计：service 依赖接口，不依赖具体实现
type UserService struct {
    repo UserRepository  // ← 接口
}

type UserRepository interface {
    GetByID(ctx context.Context, id int) (*User, error)
    Save(ctx context.Context, user *User) error
    ExistsByEmail(ctx context.Context, email string) (bool, error)
}

// 这样可以轻松切换实现（MySQL → PostgreSQL）
type MySQLUserRepository struct { db *sql.DB }
type PostgreSQLUserRepository struct { db *sql.DB }

// ❌ 错误的设计：service 依赖具体实现
type UserService struct {
    repo *MySQLUserRepository  // ← 硬编码
}
```

### 接口尺寸

```go
// ✅ 小接口（推荐）
type Reader interface {
    Read(ctx context.Context, id int) (*Data, error)
}

type Writer interface {
    Write(ctx context.Context, data *Data) error
}

type UserRepository interface {
    Reader
    Writer
    Exists(ctx context.Context, id int) (bool, error)
}

// ❌ 大接口（避免）
type Database interface {
    Query(...) (...)
    Exec(...) (...)
    Prepare(...) (...)
    Begin(...) (...)
    Commit(...) (...)
    Rollback(...) (...)
    Close(...) (...)
    // ... 还有更多
}
```

## 依赖注入

### 构造函数注入

```go
// ✅ 推荐：构造函数注入
type UserService struct {
    repo UserRepository
    cache Cache
    logger Logger
}

func NewUserService(
    repo UserRepository,
    cache Cache,
    logger Logger,
) *UserService {
    return &UserService{
        repo: repo,
        cache: cache,
        logger: logger,
    }
}

// ✅ 使用
userRepo := NewMySQLUserRepository(db)
cache := NewRedisCache(rdb)
logger := NewLoggerWithLevel(log.InfoLevel)
userService := NewUserService(userRepo, cache, logger)

// ❌ 避免：全局变量
var (
    globalUserService *UserService
    globalRepo UserRepository
)

func init() {
    globalRepo = NewMySQLUserRepository(nil)
    globalUserService = NewUserService(globalRepo, nil, nil)
}
```

### 工厂函数

```go
// ✅ 复杂初始化用工厂函数
func NewUserService(cfg Config) (*UserService, error) {
    // 1. 验证配置
    if err := cfg.Validate(); err != nil {
        return nil, err
    }

    // 2. 创建依赖
    db, err := sql.Open("mysql", cfg.Database)
    if err != nil {
        return nil, err
    }

    // 3. 创建 repository
    repo := NewMySQLUserRepository(db)

    // 4. 创建 service
    service := &UserService{
        repo: repo,
        cache: NewMemCache(),
    }

    return service, nil
}
```

## 启动和初始化顺序

### 标准启动流程（参考 Linky）

```go
// cmd/app/main.go
func main() {
    // 阶段 1：加载配置和初始化基础设施
    cfg := loadConfig()
    db := initDatabase(cfg.Database)
    cache := initCache(cfg.Cache)
    logger := initLogger(cfg.Log)

    // 阶段 2：初始化各层（自下而上）
    // Repository
    userRepo := repository.NewUserRepository(db)
    orderRepo := repository.NewOrderRepository(db)

    // Service
    userService := service.NewUserService(userRepo, cache)
    orderService := service.NewOrderService(orderRepo, userService)

    // API
    handler := api.NewHandler(userService, orderService)

    // 阶段 3：启动应用
    app := fiber.New()
    setupRoutes(app, handler)

    log.Infof("server starting on %s", cfg.Addr)
    if err := app.Listen(cfg.Addr); err != nil {
        log.Fatalf("server error: %v", err)
    }
}

// ✅ 自下而上初始化：
// 1. 配置和基础设施
// 2. Repository → Service → API
// 3. 启动应用
```

### 错误处理在初始化中

```go
// ✅ 初始化阶段的错误处理
func initializeApp() error {
    // 加载配置
    cfg, err := loadConfig()
    if err != nil {
        log.Errorf("err:%v", err)
        return fmt.Errorf("load config: %w", err)
    }

    // 初始化数据库
    db, err := initDatabase(cfg.Database)
    if err != nil {
        log.Errorf("err:%v", err)
        return fmt.Errorf("init database: %w", err)
    }

    // 继续其他初始化...
    return nil
}

func main() {
    if err := initializeApp(); err != nil {
        log.Errorf("err:%v", err)
        log.Fatalf("initialization failed")
    }
}
```

## 高级架构模式

### 选项模式（Options Pattern）

```go
// ✅ 灵活的初始化
type ServiceOptions struct {
    Logger Logger
    Cache  Cache
    Metrics Metrics
}

type ServiceOption func(*ServiceOptions)

func WithLogger(logger Logger) ServiceOption {
    return func(opts *ServiceOptions) {
        opts.Logger = logger
    }
}

func NewUserService(repo UserRepository, opts ...ServiceOption) *UserService {
    defaultOpts := &ServiceOptions{
        Logger: NewNullLogger(),
        Cache: NewMemCache(),
    }

    for _, opt := range opts {
        opt(defaultOpts)
    }

    return &UserService{
        repo: repo,
        logger: defaultOpts.Logger,
        cache: defaultOpts.Cache,
    }
}

// 使用
service := NewUserService(
    repo,
    WithLogger(logger),
    WithCache(cache),
)
```

### 中间件链模式

```go
// ✅ 灵活的请求处理
type Middleware func(Handler) Handler

func Logger(h Handler) Handler {
    return func(ctx *fiber.Ctx) error {
        log.Infof("request: %s %s", ctx.Method(), ctx.Path())
        return h(ctx)
    }
}

func Auth(h Handler) Handler {
    return func(ctx *fiber.Ctx) error {
        token := ctx.Get("Authorization")
        if token == "" {
            return errors.New("unauthorized")
        }
        return h(ctx)
    }
}

// 组合中间件
handler := Logger(Auth(registerHandler))
```

### 健康检查和优雅关闭

```go
// ✅ 标准的健康检查和关闭
func main() {
    app := fiber.New()

    // 健康检查
    app.Get("/health", func(ctx *fiber.Ctx) error {
        return ctx.JSON(fiber.Map{"status": "ok"})
    })

    // 优雅关闭
    go func() {
        sigint := make(chan os.Signal, 1)
        signal.Notify(sigint, os.Interrupt)
        <-sigint

        log.Infof("shutting down")
        app.Shutdown()
    }()

    if err := app.Listen(":8080"); err != nil {
        log.Fatalf("server error: %v", err)
    }
}
```

## 常见陷阱

### 1. 跨层调用

```go
// ❌ 错误：API 直接调用 Repository
func (h *Handler) GetUser(ctx *fiber.Ctx) error {
    id := ctx.Params("id")
    user, err := h.repo.GetByID(ctx.Context(), id)  // ← 直接调用
    return ctx.JSON(user)
}

// ✅ 正确：通过 Service 调用
func (h *Handler) GetUser(ctx *fiber.Ctx) error {
    id := ctx.Params("id")
    user, err := h.service.GetUser(ctx.Context(), id)  // ← 通过 Service
    return ctx.JSON(user)
}
```

### 2. 业务逻辑混合

```go
// ❌ 错误：业务逻辑在 API 层
func (h *Handler) Register(ctx *fiber.Ctx) error {
    var req RegisterRequest
    ctx.BodyParser(&req)

    // 业务逻辑不应该在这里
    exists := countUsers(req.Email) > 0
    if exists {
        return ctx.Status(400).JSON("email exists")
    }

    return ctx.JSON("ok")
}

// ✅ 正确：业务逻辑在 Service 层
func (h *Handler) Register(ctx *fiber.Ctx) error {
    var req RegisterRequest
    ctx.BodyParser(&req)

    user, err := h.service.Register(ctx.Context(), req)
    if err != nil {
        return h.error(ctx, http.StatusBadRequest, err)
    }

    return ctx.JSON(user)
}
```

### 3. 错误处理分散

```go
// ❌ 错误：多处理错误返回
func (s *Service) Process() {
    if err := step1(); err != nil {
        return fmt.Errorf("step1: %w", err)
    }
    if err := step2(); err != nil {
        return fmt.Errorf("step2: %w", err)
    }
}

// ✅ 改进：集中翻译为 HTTP 状态码
func (h *Handler) Handle(ctx *fiber.Ctx) error {
    result, err := h.service.Process(ctx.Context())
    if err != nil {
        return h.errorHandler(ctx, err)  // ← 统一处理
    }
    return ctx.JSON(result)
}

func (h *Handler) errorHandler(ctx *fiber.Ctx, err error) error {
    if errors.Is(err, ErrNotFound) {
        return ctx.Status(http.StatusNotFound).JSON("not found")
    }
    return ctx.Status(http.StatusInternalServerError).JSON("server error")
}
```

## 参考

- [Effective Go - Package Names](https://golang.org/doc/effective_go#package-names)
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- [Linky Server Architecture](../../../references/linky-server-architecture.md)
