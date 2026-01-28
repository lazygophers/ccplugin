---
name: gin
description: Gin Web 框架开发规范和最佳实践
---

# Gin Web 框架开发规范

## 框架概述

Gin 是一个高性能的 Go Web 框架，基于 httprouter 实现 Radix Tree 路由，提供快速的 HTTP 服务和简洁的 API 设计。

**核心特点：**
- 基于 Radix Tree 的高性能路由
- 中间件支持（如日志、认证）
- JSON 验证和渲染
- 路由分组组织
- 错误管理
- 内置渲染

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|----------|
| [核心概念](core/core-concepts.md) | Engine, RouterGroup, Context | 框架入门 |
| [路由系统](routing/routing.md) | 路由定义、参数、分组 | API 设计 |
| [中间件](middleware/middleware.md) | 中间件开发、内置中间件 | 功能扩展 |
| [数据绑定](binding/binding.md) | 绑定、验证 | 数据处理 |
| [性能优化](performance/performance.md) | 路由性能、连接池 | 性能调优 |
| [测试](testing/testing.md) | 单元测试、基准测试 | 质量保证 |
| [生态集成](ecosystem/ecosystem.md) | GORM、JWT、Swagger | 功能扩展 |
| [最佳实践](best-practices/best-practices.md) | 项目结构、错误处理 | 架构设计 |
| [参考资源](references.md) | 官方文档、教程 | 深入学习 |

## 快速开始

### Engine（引擎）

```go
import "github.com/gin-gonic/gin"

func main() {
    // 创建默认引擎（包含 Logger 和 Recovery）
    router := gin.Default()

    // 或创建空引擎
    router := gin.New()

    // 运行服务器
    router.Run(":8080")
}
```

### RouterGroup（路由组）

```go
// 创建路由组
v1 := router.Group("/api/v1")
v1.Use(AuthMiddleware())
{
    v1.GET("/users", listUsers)
    v1.POST("/users", createUser)
    v1.GET("/users/:id", getUser)

    // 嵌套分组
    posts := v1.Group("/users/:userId/posts")
    posts.GET("", listUserPosts)
}
```

### Context（上下文）

```go
func handler(c *gin.Context) {
    // 请求参数
    id := c.Param("id")
    query := c.Query("q")
    page := c.DefaultQuery("page", "1")

    // 请求体
    data, _ := c.GetRawData()

    // 响应
    c.JSON(200, gin.H{"message": "ok"})
    c.XML(200, gin.H{"message": "ok"})
    c.HTML(200, "index.html", gin.H{"title": "Home"})

    // 设置数据
    c.Set("user", user)
    user, exists := c.Get("user")

    // 中断请求
    c.AbortWithStatus(401)
}
```

## 路由系统

### 基础路由

```go
router := gin.Default()

// 简单路由
router.GET("/", func(c *gin.Context) {
    c.String(200, "Hello World")
})

// 所有 HTTP 方法
router.POST("/users", createUser)
router.PUT("/users/:id", updateUser)
router.DELETE("/users/:id", deleteUser)
router.PATCH("/users/:id", patchUser)
```

### 路径参数

```go
// 单个参数
router.GET("/users/:id", func(c *gin.Context) {
    id := c.Param("id")
    c.String(200, "User ID: %s", id)
})

// 多个参数
router.GET("/users/:id/posts/:post_id", func(c *gin.Context) {
    userID := c.Param("id")
    postID := c.Param("post_id")
    c.JSON(200, gin.H{"user": userID, "post": postID})
})

// 通配符
router.GET("/files/*filepath", func(c *gin.Context) {
    filepath := c.Param("filepath")
    c.String(200, "File: %s", filepath)
})
```

### 查询参数

```go
router.GET("/search", func(c *gin.Context) {
    // 获取参数
    query := c.Query("q")
    page := c.DefaultQuery("page", "1")

    // 获取数组
    tags := c.QueryArray("tags")

    // 获取 Map
    values := c.QueryMap("values")

    c.JSON(200, gin.H{
        "query": query,
        "page":  page,
        "tags":  tags,
    })
})
```

## 中间件

### 中间件基础

```go
func Logger() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        c.Next()
        latency := time.Since(start)
        log.Printf("%s %s | %v", c.Request.Method, c.Request.URL.Path, latency)
    }
}

func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(401, gin.H{"error": "Unauthorized"})
            return
        }
        c.Next()
    }
}
```

### 中间件使用

```go
router := gin.New()

// 全局中间件
router.Use(Logger())
router.Use(gin.Recovery())

// 路由组中间件
api := router.Group("/api")
api.Use(AuthMiddleware())
{
    api.GET("/users", listUsers)
}

// 单个路由中间件
router.GET("/admin", AdminMiddleware(), adminHandler)
```

### 内置中间件

```go
import "github.com/gin-gonic/gin"

// Logger
router.Use(gin.Logger())

// 自定义 Logger
router.Use(gin.LoggerWithFormatter(func(param gin.LogFormatterParams) string {
    return fmt.Sprintf("[%s] %s %s | %d | %v\n",
        param.TimeStamp.Format(time.RFC3339),
        param.Method,
        param.Path,
        param.StatusCode,
        param.Latency,
    )
}))

// Recovery
router.Use(gin.Recovery())

// 自定义 Recovery
router.Use(gin.CustomRecovery(func(c *gin.Context, recovered interface{}) {
    c.JSON(500, gin.H{"error": fmt.Sprintf("%v", recovered)})
}))
```

## 数据绑定

### 模型绑定

```go
type User struct {
    Name     string `json:"name" binding:"required,min=3,max=50"`
    Email    string `json:"email" binding:"required,email"`
    Password string `json:"password" binding:"required,min=8"`
    Age      int    `json:"age" binding:"gte=0,lte=130"`
}

router.POST("/users", func(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    c.JSON(201, user)
})
```

### 绑定类型

```go
// JSON 绑定
c.ShouldBindJSON(&obj)

// Query 绑定
type QueryParams struct {
    Page  int    `form:"page" binding:"gte=1"`
    Limit int    `form:"limit" binding:"gte=1,lte=100"`
}
c.ShouldBindQuery(&params)

// URI 绑定
type URIParams struct {
    ID int `uri:"id" binding:"required,gte=1"`
}
c.ShouldBindUri(&params)
```

### 自定义验证器

```go
import "github.com/go-playground/validator/v10"

func customValidator(fl validator.FieldLevel) bool {
    value := fl.Field().String()
    return len(value) > 0 && value[0] == '@'
}

func main() {
    router := gin.Default()

    if v, ok := binding.Validator.Engine().(*validator.Validate); ok {
        v.RegisterValidation("startswithat", customValidator)
    }

    type Tweet struct {
        Content string `binding:"required,startswithat"`
    }
}
```

## 错误处理

### 全局错误处理

```go
type AppError struct {
    Code    int    `json:"code"`
    Message string `json:"message"`
}

func ErrorHandler() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()
        if len(c.Errors) > 0 {
            err := c.Errors.Last()
            if appErr, ok := err.Err.(*AppError); ok {
                c.JSON(appErr.Code, appErr)
                return
            }
            c.JSON(500, gin.H{"error": "Internal Server Error"})
        }
    }
}

router.Use(ErrorHandler())
```

## 最佳实践

### 项目结构

```
project/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── controller/
│   ├── service/
│   ├── repository/
│   ├── model/
│   ├── middleware/
│   └── router/
├── pkg/
├── configs/
└── go.mod
```

### 配置管理

```go
type Config struct {
    Server   ServerConfig
    Database DatabaseConfig
    JWT      JWTConfig
}

func LoadConfig(path string) (*Config, error) {
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath(path)
    viper.AutomaticEnv()
    viper.ReadInConfig()

    var config Config
    viper.Unmarshal(&config)
    return &config, nil
}
```

### 日志记录

```go
import "go.uber.org/zap"

logger, _ := zap.NewProduction()
defer logger.Sync()

func LoggerMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        c.Next()
        logger.Info("Request",
            zap.String("method", c.Request.Method),
            zap.String("path", c.Request.URL.Path),
            zap.Int("status", c.Writer.Status()),
            zap.Duration("latency", time.Since(start)),
        )
    }
}
```

## 生态集成

### GORM 集成

```go
import "gorm.io/gorm"

type User struct {
    ID        uint           `gorm:"primarykey"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt gorm.DeletedAt `gorm:"index"`
    Name      string         `gorm:"size:100;not null"`
    Email     string         `gorm:"size:100;uniqueIndex;not null"`
}

func CreateUser(c *gin.Context) {
    user := new(User)
    if err := c.ShouldBindJSON(user); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }
    if err := db.Create(user).Error; err != nil {
        c.JSON(500, gin.H{"error": err.Error()})
        return
    }
    c.JSON(201, user)
}
```

### JWT 认证

```go
import "github.com/golang-jwt/jwt/v5"

func GenerateToken(userID uint) (string, error) {
    claims := jwt.MapClaims{
        "user_id": userID,
        "exp":     time.Now().Add(24 * time.Hour).Unix(),
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte("secret"))
}

func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(401, gin.H{"error": "Unauthorized"})
            return
        }

        token = strings.TrimPrefix(token, "Bearer ")
        claims, err := validateToken(token)
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "Invalid token"})
            return
        }

        c.Set("userID", claims["user_id"])
        c.Next()
    }
}
```

### Swagger

```go
import _ "docs" // swag 生成的文档
import swaggerFiles "github.com/swaggo/files"
import ginSwagger "github.com/swaggo/gin-swagger"

// @title Gin API
// @version 1.0
// @description This is a sample API.
// @host localhost:8080
// @BasePath /api/v1

func main() {
    router := gin.Default()
    router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
    router.Run(":8080")
}

// @Summary Create user
// @Accept json
// @Produce json
// @Param user body User true "User object"
// @Success 201 {object} User
// @Router /users [post]
func CreateUser(c *gin.Context) {
    // 处理逻辑
}
```

## 注意事项

1. 路由参数名不能冲突
2. Context 不是 goroutine-safe
3. 中间件执行顺序很重要
4. 使用 ShouldBind 而非 Bind
5. 注意错误处理的完整性

## 参考资源

- [Gin 官方文档](https://gin-gonic.com/docs/)
- [Gin GitHub](https://github.com/gin-gonic/gin)
- [Go Tutorial - Gin](https://go.dev/doc/tutorial/web-service-gin)
