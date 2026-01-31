# Fiber 最佳实践

遵循这些最佳实践可以构建可维护、高性能和安全的 Fiber 应用。

## 项目结构

### 推荐结构（Clean Architecture）

```
project/
├── cmd/
│   └── server/
│       └── main.go              # 应用入口
├── internal/
│   ├── domain/                  # 领域层（实体）
│   │   ├── user.go
│   │   └── user_repository.go
│   ├── usecase/                 # 用例层（业务逻辑）
│   │   ├── user_usecase.go
│   │   └── auth_usecase.go
│   ├── delivery/                # 交付层
│   │   └── http/
│   │       ├── handler.go       # HTTP 处理器
│   │       ├── middleware.go    # 中间件
│   │       └── router.go        # 路由配置
│   ├── repository/              # 数据访问层
│   │   ├── user_repo.go
│   │   └── user_repo_gorm.go
│   └── infrastructure/          # 基础设施
│       ├── database/
│       ├── cache/
│       └── config/
├── pkg/                         # 公共库
│   ├── logger/
│   └── validator/
├── configs/                     # 配置文件
├── migrations/                  # 数据库迁移
├── docs/                        # 文档
└── go.mod
```

### 分层职责

```go
// domain/user.go - 领域实体
package domain

type User struct {
    ID        int64
    Name      string
    Email     string
    Password  string
    CreatedAt time.Time
    UpdatedAt time.Time
}

// domain/user_repository.go - 仓储接口
type UserRepository interface {
    FindByID(ctx context.Context, id int64) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id int64) error
}

// usecase/user_usecase.go - 用例层
type UserUseCase struct {
    repo domain.UserRepository
    log  *zap.Logger
}

func NewUserUseCase(repo domain.UserRepository, log *zap.Logger) *UserUseCase {
    return &UserUseCase{repo: repo, log: log}
}

func (uc *UserUseCase) GetUser(ctx context.Context, id int64) (*User, error) {
    return uc.repo.FindByID(ctx, id)
}

// delivery/http/handler.go - 交付层
type UserHandler struct {
    usecase *usecase.UserUseCase
}

func NewUserHandler(usecase *usecase.UserUseCase) *UserHandler {
    return &UserHandler{usecase: usecase}
}

func (h *UserHandler) GetUser(c *fiber.Ctx) error {
    id, _ := c.ParamsInt("id")
    user, err := h.usecase.GetUser(c.Context(), id)
    if err != nil {
        return c.Status(404).JSON(fiber.Map{"error": "user not found"})
    }
    return c.JSON(user)
}
```

## 错误处理

### 统一错误类型

```go
// pkg/errors/errors.go
package errors

type AppError struct {
    Code    int    `json:"code"`
    Message string `json:"message"`
    Detail  string `json:"detail,omitempty"`
}

func (e *AppError) Error() string {
    return e.Message
}

// 预定义错误
var (
    ErrBadRequest     = &AppError{400, "bad request", ""}
    ErrUnauthorized   = &AppError{401, "unauthorized", ""}
    ErrForbidden      = &AppError{403, "forbidden", ""}
    ErrNotFound       = &AppError{404, "not found", ""}
    ErrInternalServer = &AppError{500, "internal server error", ""}
)

// 创建错误
func NewError(code int, message string) *AppError {
    return &AppError{Code: code, Message: message}
}

func NewNotFound(resource string) *AppError {
    return &AppError{404, fmt.Sprintf("%s not found", resource), ""}
}
```

### 全局错误处理

```go
// delivery/http/middleware/error.go
func ErrorHandler() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // 继续处理请求
        c.Next()

        // 检查是否有错误
        if len(c.Errors()) > 0 {
            err := c.Errors().Last()
            return handleError(c, err.Err)
        }

        return nil
    }
}

func handleError(c *fiber.Ctx, err error) error {
    // 应用错误
    if appErr, ok := err.(*errors.AppError); ok {
        return c.Status(appErr.Code).JSON(appErr)
    }

    // 验证错误
    if validationErrors, ok := err.(validator.ValidationErrors); ok {
        return c.Status(400).JSON(fiber.Map{
            "error": "validation failed",
            "details": formatValidationErrors(validationErrors),
        })
    }

    // 默认错误
    log.Printf("Unhandled error: %v", err)
    return c.Status(500).JSON(errors.ErrInternalServer)
}
```

### 在 Handler 中使用

```go
func (h *UserHandler) GetUser(c *fiber.Ctx) error {
    id, err := c.ParamsInt("id")
    if err != nil {
        return errors.NewError(400, "invalid user id")
    }

    user, err := h.usecase.GetUser(c.Context(), id)
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return errors.NewNotFound("user")
        }
        return err
    }

    return c.JSON(user)
}
```

## 配置管理

### 配置结构

```go
// infrastructure/config/config.go
package config

import "time"

type Config struct {
    Server   ServerConfig
    Database DatabaseConfig
    Redis    RedisConfig
    JWT      JWTConfig
}

type ServerConfig struct {
    Host         string
    Port         string
    ReadTimeout  time.Duration
    WriteTimeout time.Duration
}

type DatabaseConfig struct {
    Host     string
    Port     string
    User     string
    Password string
    DBName   string
}

type RedisConfig struct {
    Host     string
    Password string
    DB       int
}

type JWTConfig struct {
    Secret string
    Expire time.Duration
}
```

### 加载配置

```go
// infrastructure/config/loader.go
package config

import (
    "fmt"
    "os"
    "github.com/spf13/viper"
)

func Load() (*Config, error) {
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath("./configs")
    viper.AddConfigPath(".")

    // 环境变量支持
    viper.AutomaticEnv()

    if err := viper.ReadInConfig(); err != nil {
        return nil, fmt.Errorf("failed to read config: %w", err)
    }

    var config Config
    if err := viper.Unmarshal(&config); err != nil {
        return nil, fmt.Errorf("failed to unmarshal config: %w", err)
    }

    return &config, nil
}
```

### 配置文件（config.yaml）

```yaml
server:
  host: "0.0.0.0"
  port: "3000"
  readTimeout: 5s
  writeTimeout: 10s

database:
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  user: ${DB_USER:user}
  password: ${DB_PASSWORD:password}
  dbName: ${DB_NAME:mydb}

redis:
  host: ${REDIS_HOST:localhost:6379}
  password: ${REDIS_PASSWORD:}
  db: 0

jwt:
  secret: ${JWT_SECRET:your-secret-key}
  expire: 24h
```

## 依赖注入

### 手动注入

```go
// cmd/server/main.go
package main

func main() {
    // 加载配置
    config, err := config.Load()
    if err != nil {
        log.Fatal(err)
    }

    // 初始化基础设施
    db := database.NewPostgres(config.Database)
    redis := database.NewRedis(config.Redis)
    logger := logger.New(config.Env)

    // 初始化仓储
    userRepo := repository.NewUserRepositoryGorm(db)

    // 初始化用例
    userUseCase := usecase.NewUserUseCase(userRepo, logger)

    // 初始化处理器
    userHandler := handler.NewUserHandler(userUseCase)

    // 设置路由
    app := setupRouter(userHandler)

    // 启动服务器
    app.Listen(":3000")
}
```

### 使用 Wire

```go
// cmd/server/wire.go
//go:build wireinject
// +build wireinject

package main

import "github.com/google/wire"

func InitializeApp(config *config.Config) (*fiber.App, error) {
    wire.Build(
        // Infrastructure
        database.NewPostgres,
        database.NewRedis,

        // Repository
        repository.NewUserRepositoryGorm,
        repository.NewSessionRepositoryRedis,

        // UseCase
        usecase.NewUserUseCase,
        usecase.NewAuthUseCase,

        // Handler
        handler.NewUserHandler,
        handler.NewAuthHandler,

        // Router
        NewRouter,
    )
    return &fiber.App{}, nil
}
```

## 中间件组织

### 中间件链

```go
// delivery/http/router.go
func setupRouter(app *fiber.App, handlers *HandlerContainer) {
    // 全局中间件
    app.Use(recover.New())
    app.Use(logger.New())
    app.Use(cors.New())
    app.Use(middleware.ErrorHandler())

    // API 路由组
    api := app.Group("/api")

    // 公开路由
    api.Post("/auth/login", handlers.Auth.Login)
    api.Post("/auth/register", handlers.Auth.Register)

    // 认证路由
    authenticated := api.Group("/", middleware.Auth())
    authenticated.Get("/profile", handlers.User.GetProfile)

    // 管理员路由
    admin := authenticated.Group("/admin", middleware.Role("admin"))
    admin.Get("/users", handlers.Admin.ListUsers)
}
```

## 数据验证

### DTO 验证

```go
// delivery/http/dto/user.go
package dto

type CreateUserRequest struct {
    Name     string `json:"name" validate:"required,min=3,max=50"`
    Email    string `json:"email" validate:"required,email"`
    Password string `json:"password" validate:"required,min=8"`
}

type UpdateUserRequest struct {
    Name  string `json:"name" validate:"omitempty,min=3,max=50"`
    Email string `json:"email" validate:"omitempty,email"`
}

// delivery/http/validator/validator.go
package validator

type Validator struct {
    validate *validator.Validate
}

func New() *Validator {
    v := validator.New()
    return &Validator{validate: v}
}

func (v *Validator) Validate(s interface{}) error {
    if err := v.validate.Struct(s); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }
    return nil
}

// 在 Handler 中使用
func (h *UserHandler) CreateUser(c *fiber.Ctx) error {
    var req dto.CreateUserRequest
    if err := c.BodyParser(&req); err != nil {
        return errors.ErrBadRequest
    }

    if err := h.validator.Validate(&req); err != nil {
        return c.Status(400).JSON(fiber.Map{
            "error": "validation failed",
            "details": err,
        })
    }

    // 调用用例...
}
```

## 日志记录

### 上下文日志

```go
// pkg/logger/logger.go
package logger

type Logger struct {
    zap *zap.Logger
}

func (l *Logger) WithRequest(c *fiber.Ctx) *zap.Logger {
    return l.zap.With(
        zap.String("method", c.Method()),
        zap.String("path", c.Path()),
        zap.String("ip", c.IP()),
    )
}

// 在 Handler 中使用
func (h *UserHandler) GetUser(c *fiber.Ctx) error {
    log := h.logger.WithRequest(c)

    id, _ := c.ParamsInt("id")
    log.Info("getting user", zap.Int("id", id))

    user, err := h.usecase.GetUser(c.Context(), id)
    if err != nil {
        log.Error("failed to get user", zap.Error(err))
        return err
    }

    log.Info("user retrieved", zap.Int("id", user.ID))
    return c.JSON(user)
}
```

## 安全实践

### 密码处理

```go
// pkg/password/password.go
package password

import "golang.org/x/crypto/bcrypt"

func Hash(password string) (string, error) {
    bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    return string(bytes), err
}

func Verify(password, hash string) bool {
    err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
    return err == nil
}
```

### JWT 认证

```go
// pkg/jwt/jwt.go
package jwt

import "github.com/golang-jwt/jwt/v5"

type Claims struct {
    UserID int64  `json:"user_id"`
    Email  string `json:"email"`
    jwt.RegisteredClaims
}

func GenerateToken(userID int64, email, secret string) (string, error) {
    claims := Claims{
        UserID: userID,
        Email:  email,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
        },
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte(secret))
}

func ValidateToken(tokenString, secret string) (*Claims, error) {
    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
        return []byte(secret), nil
    })

    if err != nil {
        return nil, err
    }

    if claims, ok := token.Claims.(*Claims); ok && token.Valid {
        return claims, nil
    }

    return nil, fmt.Errorf("invalid token")
}
```

## 测试策略

### 测试组织

```
internal/
├── delivery/
│   └── http/
│       ├── handler.go
│       └── handler_test.go
├── usecase/
│   ├── user_usecase.go
│   └── user_usecase_test.go
└── repository/
    ├── user_repo.go
    └── user_repo_test.go
```

### Mock 依赖

```go
// usecase/user_usecase_test.go
func TestUserUseCase_GetUser(t *testing.T) {
    // 创建 mock 仓储
    mockRepo := &MockUserRepository{
        users: map[int64]*domain.User{
            1: {ID: 1, Name: "John", Email: "john@example.com"},
        },
    }

    useCase := usecase.NewUserUseCase(mockRepo, zap.NewNop())

    // 测试
    user, err := useCase.GetUser(context.Background(), 1)
    require.NoError(t, err)
    assert.Equal(t, "John", user.Name)
}
```

## 性能最佳实践

1. **使用连接池**：数据库、Redis 连接池
2. **启用缓存**：内存缓存、Redis 缓存
3. **使用对象池**：sync.Pool 复用对象
4. **避免 N+1 查询**：使用预加载
5. **启用压缩**：Gzip 中间件
6. **限流保护**：防止过载

## 可观测性

1. **结构化日志**：使用 zap
2. **指标收集**：Prometheus
3. **链路追踪**：OpenTelemetry
4. **健康检查**：/health 端点
5. **错误追踪**：Sentry
