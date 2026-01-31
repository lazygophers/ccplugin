# 最佳实践

## 项目结构

### 分层架构

```
project/
├── internal/
│   ├── model/          # 模型定义
│   │   ├── user.go
│   │   └── post.go
│   ├── repository/     # 数据访问层
│   │   ├── user_repo.go
│   │   └── post_repo.go
│   ├── service/        # 业务逻辑层
│   │   └── user_service.go
│   └── handler/        # HTTP 处理器
│       └── user_handler.go
├── pkg/
│   └── database/       # 数据库配置
│       └── database.go
└── main.go
```

### Repository 模式

```go
// repository/user_repo.go
package repository

type UserRepository interface {
    Create(user *model.User) error
    GetByID(id uint) (*model.User, error)
    Update(user *model.User) error
    Delete(id uint) error
    List(offset, limit int) ([]model.User, int64, error)
}

type gormUserRepository struct {
    db *gorm.DB
}

func NewUserRepository(db *gorm.DB) UserRepository {
    return &gormUserRepository{db: db}
}

func (r *gormUserRepository) Create(user *model.User) error {
    return r.db.Create(user).Error
}

func (r *gormUserRepository) GetByID(id uint) (*model.User, error) {
    var user model.User
    err := r.db.First(&user, id).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}

// ... 其他方法
```

### Service 层

```go
// service/user_service.go
package service

type UserService struct {
    userRepo repository.UserRepository
}

func NewUserService(userRepo repository.UserRepository) *UserService {
    return &UserService{userRepo: userRepo}
}

func (s *UserService) CreateUser(name, email string) (*model.User, error) {
    // 验证
    if name == "" || email == "" {
        return nil, errors.New("name and email are required")
    }

    // 创建
    user := &model.User{
        Name:  name,
        Email: email,
    }
    if err := s.userRepo.Create(user); err != nil {
        return nil, err
    }

    return user, nil
}
```

## 错误处理

### 错误定义

```go
// errors/errors.go
package errors

var (
    ErrUserNotFound    = &AppError{Code: 10001, Message: "用户不存在"}
    ErrUserAlreadyExist = &AppError{Code: 10002, Message: "用户已存在"}
    ErrInvalidInput    = &AppError{Code: 400, Message: "输入参数无效"}
)

type AppError struct {
    Code    int
    Message string
    Err     error
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Err)
    }
    return e.Message
}

func (e *AppError) Unwrap() error {
    return e.Err
}
```

### 错误处理

```go
// repository/user_repo.go
import "gorm.io/gorm"

func (r *gormUserRepository) GetByID(id uint) (*model.User, error) {
    var user model.User
    err := r.db.First(&user, id).Error
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, apperrors.ErrUserNotFound
        }
        return nil, err
    }
    return &user, nil
}

// service/user_service.go
func (s *UserService) GetUser(id uint) (*model.User, error) {
    user, err := s.userRepo.GetByID(id)
    if err != nil {
        if errors.Is(err, apperrors.ErrUserNotFound) {
            return nil, err
        }
        return nil, fmt.Errorf("failed to get user: %w", err)
    }
    return user, nil
}
```

## 命名约定

### 表名

```go
// 默认：User → users
type User struct{}

// 自定义表名
func (User) TableName() string {
    return "app_users"
}

// 全局配置
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    NamingStrategy: schema.NamingStrategy{
        TablePrefix:   "tbl_",
        SingularTable: true, // User → User
    },
})
```

### 列名

```go
type User struct {
    ID        uint   // id
    UserName  string // user_name
    CreatedAt time.Time // created_at
    Email     string `gorm:"column:email_address"` // email_address
}
```

### 关联外键

```go
type User struct {
    ID    uint
    Posts []Post `gorm:"foreignKey:AuthorID"` // 默认 UserID
}

type Post struct {
    ID       uint
    AuthorID uint // 外键
}
```

## 上下文使用

### 超时控制

```go
func (r *gormUserRepository) GetByID(ctx context.Context, id uint) (*model.User, error) {
    var user model.User
    err := r.db.WithContext(ctx).First(&user, id).Error
    if err != nil {
        return nil, err
    }
    return &user, nil
}

// 使用
func (s *UserService) GetUser(ctx context.Context, id uint) (*model.User, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    return s.userRepo.GetByID(ctx, id)
}
```

### 请求追踪

```go
func middleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // 添加请求 ID 到上下文
        requestID := uuid.New().String()
        ctx := context.WithValue(r.Context(), "request_id", requestID)

        // GORM 使用
        logger := logger.New(
            log.New(os.Stdout, "\r\n", log.LstdFlags),
            logger.Config{
                Context: context.Background(),
            },
        )

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

## 软删除

### 基础使用

```go
type User struct {
    ID        uint
    Name      string
    DeletedAt gorm.DeletedAt `gorm:"index"`
}

// 软删除
db.Delete(&user) // SET deleted_at = NOW()

// 包含已删除记录
db.Unscoped().Find(&users)

// 永久删除
db.Unscoped().Delete(&user)

// 只查询未删除记录（默认）
db.Find(&users)

// 只查询已删除记录
db.Unscoped().Where("deleted_at IS NOT NULL").Find(&users)
```

### 自定义软删除

```go
type User struct {
    ID        uint
    Name      string
    DeletedAt time.Time `gorm:"index"`
    IsDeleted bool      `gorm:"default:false"`
}

func (u *User) BeforeDelete(tx *gorm.DB) error {
    u.IsDeleted = true
    u.DeletedAt = time.Now()
    return tx.Save(u).Error
}
```

## 时间戳管理

### 自动时间戳

```go
type User struct {
    CreatedAt time.Time // 自动设置创建时间
    UpdatedAt time.Time // 自动更新更新时间
}

// 禁用自动更新
db.Save(&user) // 不更新 UpdatedAt

// 手动更新
db.Model(&user).Update("updated_at", time.Now())
```

### 自定义时间戳

```go
type User struct {
    ID        uint
    CreatedAt int64 `gorm:"autoCreateTime"` // Unix 时间戳
    UpdatedAt int64 `gorm:"autoUpdateTime"`
}
```

### 禁用时间戳

```go
type User struct {
    CreatedAt time.Time `gorm:"-"` // 忽略
}

// 全局禁用
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    DisableAutomaticPing: true,
})
```

## 配置管理

### 环境变量

```go
type Config struct {
    DSN          string
    MaxIdleConns int
    MaxOpenConns int
    LogMode      string
}

func LoadConfig() *Config {
    return &Config{
        DSN:          os.Getenv("DB_DSN"),
        MaxIdleConns: getIntEnv("DB_MAX_IDLE_CONNS", 10),
        MaxOpenConns: getIntEnv("DB_MAX_OPEN_CONNS", 100),
        LogMode:      getEnv("DB_LOG_MODE", "silent"),
    }
}
```

### 连接配置

```go
func InitDB(cfg *Config) (*gorm.DB, error) {
    var logLevel logger.LogLevel
    switch cfg.LogMode {
    case "silent":
        logLevel = logger.Silent
    case "error":
        logLevel = logger.Error
    case "warn":
        logLevel = logger.Warn
    case "info":
        logLevel = logger.Info
    }

    db, err := gorm.Open(mysql.Open(cfg.DSN), &gorm.Config{
        Logger: logger.Default.LogMode(logLevel),
        SkipDefaultTransaction: true,
        PrepareStmt: true,
    })
    if err != nil {
        return nil, err
    }

    sqlDB, err := db.DB()
    if err != nil {
        return nil, err
    }

    sqlDB.SetMaxIdleConns(cfg.MaxIdleConns)
    sqlDB.SetMaxOpenConns(cfg.MaxOpenConns)
    sqlDB.SetConnMaxLifetime(time.Hour)

    return db, nil
}
```

## 安全实践

### SQL 注入防护

```go
// ✅ 使用参数化查询
db.Where("name = ?", userInput).First(&user)

// ❌ 字符串拼接（危险）
db.Where(fmt.Sprintf("name = '%s'", userInput)).First(&user)
```

### 敏感数据

```go
type User struct {
    ID       uint
    Name     string
    Email    string
    Password string `gorm:"-"` // 不输出到 JSON
}

// 或使用 Omit
db.Select("id", "name", "email").Find(&users)
db.Omit("password").Find(&users)
```

### 事务安全

```go
// ✅ 使用自动事务
db.Transaction(func(tx *gorm.DB) error {
    // 操作
    return nil
})

// ✅ 手动事务
tx := db.Begin()
defer func() {
    if r := recover(); r != nil {
        tx.Rollback()
        panic(r)
    }
}()
```

## 日志记录

### 结构化日志

```go
import "gorm.io/gorm/logger"

db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    Logger: logger.New(
        log.New(os.Stdout, "\r\n", log.LstdFlags),
        logger.Config{
            SlowThreshold:             200 * time.Millisecond,
            LogLevel:                  logger.Info,
            IgnoreRecordNotFoundError: true,
            Colorful:                  true,
        },
    ),
})
```

### 自定义日志

```go
type CustomLogger struct{}

func (l CustomLogger) Printf(format string, args ...interface{}) {
    log.Printf("[SQL] "+format, args...)
}

db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    Logger: logger.New(
        CustomLogger{},
        logger.Config{
            LogLevel: logger.Info,
        },
    ),
})
```

## 常见陷阱

1. **N+1 查询**：使用 Preload 预加载
2. **忘记错误检查**：始终检查返回的 error
3. **事务过宽**：保持事务简短
4. **忽略连接池**：合理配置连接数
5. **生产环境日志**：关闭 SQL 日志
6. **时间处理**：使用 parseTime=True
7. **软删除忽略**：注意默认过滤已删除记录
8. **指针与值**：理解 nil 指针和零值的区别
