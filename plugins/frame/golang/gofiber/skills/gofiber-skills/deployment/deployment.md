# Fiber 部署指南

Fiber 应用部署到生产环境需要考虑配置、监控、日志、安全等多个方面。

## 生产配置

### 推荐配置

```go
import "github.com/gofiber/fiber/v2"

func main() {
    app := fiber.New(fiber.Config{
        // 应用配置
        AppName:               "Production App",
        DisableStartupMessage: false,
        EnablePrintRoutes:     false,

        // 网络配置
        ReadTimeout:      5 * time.Second,
        WriteTimeout:     10 * time.Second,
        IdleTimeout:      30 * time.Second,

        // 安全配置
        BodyLimit:        4 * 1024 * 1024, // 4MB
        DisableHeaderNormalizing: false,
        EnableTrustedProxyCheck: true,

        // 性能配置
        Prefork:          false, // 使用反向代理时设为 false
        Immutable:        false,
        StrictRouting:    true,
        CaseSensitive:    true,

        // 错误处理
        ErrorHandler: customErrorHandler,
    })

    setupMiddleware(app)
    setupRoutes(app)

    // 启动服务器
    addr := fmt.Sprintf(":%s", getEnv("PORT", "3000"))
    log.Fatal(app.Listen(addr))
}
```

### 环境变量配置

```go
func loadConfig() fiber.Config {
    return fiber.Config{
        AppName:     getEnv("APP_NAME", "Fiber App"),
        ReadTimeout: parseDuration(getEnv("READ_TIMEOUT", "5s")),
        WriteTimeout: parseDuration(getEnv("WRITE_TIMEOUT", "10s")),
        BodyLimit:   parseSize(getEnv("BODY_LIMIT", "4MB")),
    }
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}
```

## 优雅关闭

### 信号处理

```go
func main() {
    app := fiber.New()
    // ... 设置路由

    // 监听关闭信号
    go func() {
        sigint := make(chan os.Signal, 1)
        signal.Notify(sigint, os.Interrupt, syscall.SIGTERM)
        <-sigint

        log.Println("Shutting down...")
        if err := app.Shutdown(); err != nil {
            log.Printf("Shutdown error: %v", err)
        }
    }()

    // 启动服务器
    if err := app.Listen(":3000"); err != nil {
        log.Panic(err)
    }
}
```

### 超时控制

```go
// 优雅关闭，最多等待 30 秒
go func() {
    <-sigint

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := app.ShutdownWithContext(ctx); err != nil {
        log.Printf("Shutdown timeout: %v", err)
    }
}()
```

## 日志管理

### 结构化日志

```go
import "go.uber.org/zap"

func setupLogger() *zap.Logger {
    var logger *zap.Logger
    var err error

    if os.Getenv("ENV") == "production" {
        logger, err = zap.NewProduction()
    } else {
        logger, err = zap.NewDevelopment()
    }

    if err != nil {
        log.Panic(err)
    }

    return logger
}

func main() {
    logger := setupLogger()
    defer logger.Sync()

    // 使用 zap 记录日志
    logger.Info("Server starting",
        zap.String("port", "3000"),
        zap.String("env", os.Getenv("ENV")),
    )
}
```

### 请求日志中间件

```go
func LoggerMiddleware(logger *zap.Logger) fiber.Handler {
    return func(c *fiber.Ctx) error {
        start := time.Now()

        if err := c.Next(); err != nil {
            logger.Error("request error",
                zap.String("method", c.Method()),
                zap.String("path", c.Path()),
                zap.Int("status", c.Response().StatusCode()),
                zap.Duration("latency", time.Since(start)),
                zap.Error(err),
            )
            return err
        }

        logger.Info("request",
            zap.String("method", c.Method()),
            zap.String("path", c.Path()),
            zap.Int("status", c.Response().StatusCode()),
            zap.Duration("latency", time.Since(start)),
        )

        return nil
    }
}
```

### 日志轮转

```go
import "gopkg.in/natefinch/lumberjack.v2"

func setupLogger() *zap.Logger {
    writeSyncer := zapcore.AddSync(&lumberjack.Logger{
        Filename:   "logs/app.log",
        MaxSize:    100, // MB
        MaxBackups: 3,
        MaxAge:     28, // days
        Compress:   true,
    })

    encoderConfig := zap.NewProductionEncoderConfig()
    encoderConfig.TimeKey = "timestamp"
    encoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

    core := zapcore.NewCore(
        zapcore.NewJSONEncoder(encoderConfig),
        writeSyncer,
        zap.InfoLevel,
    )

    return zap.New(core, zap.AddCaller())
}
```

## 监控

### Prometheus 指标

```go
import "github.com/vegh1010/fiber-prometheus"

func setupMonitoring(app *fiber.App) {
    prometheus := fiberPrometheus.New("my_app")
    prometheus.RegisterAt(app, "/metrics")
    app.Use(prometheus.Middleware)
}

// 访问 /metrics 查看指标
```

### 自定义指标

```go
import "github.com/prometheus/client_golang/prometheus"

var (
    httpRequestsTotal = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "path", "status"},
    )

    httpRequestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request duration in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "path"},
    )
)

func init() {
    prometheus.MustRegister(httpRequestsTotal)
    prometheus.MustRegister(httpRequestDuration)
}

func MetricsMiddleware() fiber.Handler {
    return func(c *fiber.Ctx) error {
        start := time.Now()

        if err := c.Next(); err != nil {
            return err
        }

        duration := time.Since(start).Seconds()
        status := c.Response().StatusCode()

        httpRequestsTotal.WithLabelValues(
            c.Method(),
            c.Path(),
            fmt.Sprintf("%d", status),
        ).Inc()

        httpRequestDuration.WithLabelValues(
            c.Method(),
            c.Path(),
        ).Observe(duration)

        return nil
    }
}
```

### 健康检查

```go
func HealthCheck(db *gorm.DB) fiber.Handler {
    return func(c *fiber.Ctx) error {
        status := "ok"
        details := make(map[string]string)

        // 检查数据库连接
        sqlDB, err := db.DB()
        if err != nil {
            status = "error"
            details["database"] = "error: " + err.Error()
        } else if err := sqlDB.Ping(); err != nil {
            status = "error"
            details["database"] = "error: " + err.Error()
        } else {
            details["database"] = "ok"
        }

        // 检查 Redis
        if redisClient != nil {
            if err := redisClient.Ping(context.Background()).Err(); err != nil {
                status = "error"
                details["redis"] = "error: " + err.Error()
            } else {
                details["redis"] = "ok"
            }
        }

        statusCode := 200
        if status == "error" {
            statusCode = 503
        }

        return c.Status(statusCode).JSON(fiber.Map{
            "status":  status,
            "details": details,
        })
    }
}

app.Get("/health", HealthCheck(db))
```

## 安全配置

### HTTPS/TLS

```go
// 自动证书（Let's Encrypt）
import "github.com/caddyserver/certmagic"

func main() {
    app := fiber.New()

    certmagic.DefaultACME.Agreed = true
    certmagic.DefaultACME.Email = "admin@example.com"

    // 自动 HTTPS
    if err := certmagic.HTTPS([]string{"example.com", "www.example.com"}, app.Handler()); err != nil {
        log.Fatal(err)
    }
}
```

### 手动 TLS

```go
func main() {
    app := fiber.New()

    // TLS 配置
    certs := certmagic.Default
    certs.CacheUninstalledCerts = false

    if err := certs.CertMagic(true); err != nil {
        log.Fatal(err)
    }

    // 启动 HTTPS 服务器
    if err := app.Listen(":443"); err != nil {
        log.Fatal(err)
    }

    // HTTP 重定向到 HTTPS
    httpApp := fiber.New()
    httpApp.Get("/*", func(c *fiber.Ctx) error {
        return c.Redirect("https://"+c.Hostname()+c.Path(), 301)
    })
    go httpApp.Listen(":80")
}
```

### 安全头

```go
import "github.com/gofiber/fiber/v2/middleware/helmet"

app.Use(helmet.New(helmet.Config{
    XSSProtection:      "1; mode=block",
    ContentTypeNosniff: "nosniff",
    XFrameOptions:      "SAMEORIGIN",
    HSTSMaxAge:         31536000,
    ReferrerPolicy:     "no-referrer",
}))
```

## 反向代理

### Nginx 配置

```nginx
upstream fiber_backend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://fiber_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Caddy 配置

```caddyfile
example.com {
    reverse_proxy 127.0.0.1:3000

    # 日志
    log {
        output file /var/log/caddy/access.log
    }

    # TLS
    tls {
        dns cloudflare
    }
}
```

## Docker 部署

### Dockerfile

```dockerfile
# 构建阶段
FROM golang:1.21-alpine AS builder

WORKDIR /app

# 安装依赖
COPY go.mod go.sum ./
RUN go mod download

# 复制源码
COPY . .

# 构建
RUN CGO_ENABLED=0 go build -o main .

# 运行阶段
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# 复制二进制文件
COPY --from=builder /app/main .

# 暴露端口
EXPOSE 3000

# 运行
CMD ["./main"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - ENV=production
      - DB_HOST=postgres
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  postgres_data:
```

## Prefork 模式

```go
// Prefork 模式（多进程）
// ⚠️ 注意：Prefork 与某些功能不兼容，谨慎使用

app := fiber.New(fiber.Config{
    Prefork: true,  // 启用 Prefork
})

// 使用环境变量控制
app := fiber.New(fiber.Config{
    Prefork: os.Getenv("PREFORK") == "true",
})
```

## 生产清单

- [ ] 启用 HTTPS/TLS
- [ ] 配置反向代理
- [ ] 实现优雅关闭
- [ ] 配置日志记录
- [ ] 设置监控和告警
- [ ] 实现健康检查
- [ ] 配置 CORS（如需要）
- [ ] 设置速率限制
- [ ] 实现请求验证
- [ ] 配置环境变量
- [ ] 使用 Docker 容器化
- [ ] 设置自动重启策略
- [ ] 配置备份策略
- [ ] 实现日志轮转
- [ ] 测试负载均衡
- [ ] 设置错误追踪（Sentry）
