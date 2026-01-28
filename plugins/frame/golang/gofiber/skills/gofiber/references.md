# Fiber 参考资源

## 官方资源

### 官方网站
- [Fiber 官方文档](https://docs.gofiber.io/) - 完整的框架文档
- [Fiber GitHub](https://github.com/gofiber/fiber) - 源代码和问题跟踪
- [Fiber Recipes](https://docs.gofiber.io/recipes/) - 实用示例和教程
- [API 参考](https://pkg.go.dev/github.com/gofiber/fiber/v2) - Go 包文档

### 官方中间件
- [fiber/middleware/logger](https://docs.gofiber.io/api/middleware/logger) - 请求日志
- [fiber/middleware/cors](https://docs.gofiber.io/api/middleware/cors) - CORS 支持
- [fiber/middleware/compress](https://docs.gofiber.io/api/middleware/compress) - 响应压缩
- [fiber/middleware/recover](https://docs.gofiber.io/api/middleware/recover) - Panic 恢复
- [fiber/middleware/limiter](https://docs.gofiber.io/api/middleware/limiter) - 速率限制
- [fiber/middleware/csrf](https://docs.gofiber.io/api/middleware/csrf) - CSRF 保护
- [fiber/middleware/jwt](https://docs.gofiber.io/api/middleware/jwt) - JWT 认证
- [fiber/middleware/session](https://docs.gofiber.io/api/middleware/session) - 会话管理
- [fiber/middleware/websocket](https://docs.gofiber.io/api/middleware/websocket) - WebSocket 支持
- [fiber/middleware/redis](https://docs.gofiber.io/api/middleware/redis) - Redis 存储
- [fiber/middleware/helmet](https://docs.gofiber.io/api/middleware/helmet) - 安全头

## 社区资源

### 教程
- [Fiber 入门教程](https://docs.gofiber.io/tutorial/)
- [构建 REST API](https://docs.gofiber.io/guide/routing)
- [中间件开发](https://docs.gofiber.io/guide/middleware)
- [模板引擎集成](https://docs.gofiber.io/guide/templates)

### 示例项目
- [Fiber Recipes](https://github.com/gofiber/recipes) - 官方示例集合
- [Fiber Boilerplate](https://github.com/gofiber/boilerplate) - 项目模板
- [Fiber GraphQL](https://github.com/gofiber/graphql) - GraphQL 集成

## 第三方库集成

### 数据库
- [GORM](https://gorm.io/) - ORM 库
- [sqlx](https://jmoiron.github.io/sqlx/) - SQL 扩展库
- [pgx](https://github.com/jackc/pgx) - PostgreSQL 驱动

### 缓存
- [go-redis](https://github.com/redis/go-redis) - Redis 客户端
- [go-cache](https://github.com/patrickmn/go-cache) - 内存缓存
- [BigCache](https://github.com/allegro/bigcache) - 高性能缓存

### 验证
- [go-playground/validator](https://github.com/go-playground/validator) - 结构体验证

### 日志
- [zap](https://github.com/uber-go/zap) - 高性能日志库
- [logrus](https://github.com/sirupsen/logrus) - 结构化日志

### 配置
- [viper](https://github.com/spf13/viper) - 配置管理
- [env](https://github.com/caarlos0/env) - 环境变量解析

### 工具库
- [testify](https://github.com/stretchr/testify) - 测试工具
- [errors](https://github.com/pkg/errors) - 错误处理
- [uuid](https://github.com/google/uuid) - UUID 生成

## 监控和可观测性

### Prometheus
- [fiber-prometheus](https://github.com/vegh1010/fiber-prometheus) - Prometheus 中间件
- [prometheus/client_golang](https://github.com/prometheus/client_golang) - Prometheus Go 客户端

### 链路追踪
- [OpenTelemetry Go](https://github.com/open-telemetry/opentelemetry-go) - 分布式追踪
- [Jaeger Go](https://github.com/jaegertracing/jaeger-client-go) - Jaeger 客户端

### 日志聚合
- [ELK Stack](https://www.elastic.co/what-is/elk-stack) - 日志收集和分析
- [Loki](https://grafana.com/oss/loki/) - 日志聚合系统

## 认证和安全

### JWT
- [golang-jwt/jwt](https://github.com/golang-jwt/jwt) - JWT 实现
- [fiber-middleware/jwt](https://github.com/gofiber/jwt) - Fiber JWT 中间件

### OAuth2
- [oauth2](https://github.com/golang/oauth2) - OAuth2 客户端
- [authboss](https://github.com/volatiletech/authboss) - 认证系统

### 加密
- [crypto/bcrypt](https://pkg.go.dev/golang.org/x/crypto/bcrypt) - 密码哈希
- [crypto](https://pkg.go.dev/golang.org/x/crypto) - 加密库

## 部署

### Docker
- [Docker Hub - Fiber](https://hub.docker.com/r/gofiber/fiber)
- [Docker 部署指南](https://docs.gofiber.io/guide/deployment)

### 云平台
- [AWS 部署](https://aws.amazon.com/)
- [Google Cloud 部署](https://cloud.google.com/)
- [Azure 部署](https://azure.microsoft.com/)

### 反向代理
- [Nginx 配置](https://docs.nginx.com/)
- [Caddy 配置](https://caddyserver.com/docs/)
- [Traefik](https://doc.traefik.io/traefik/)

## 性能分析

### 基准测试
- [Go Benchmark](https://pkg.go.dev/testing#hdr-Benchmarks)
- [Fiber 性能对比](https://docs.gofiber.io/guide/performance)

### 分析工具
- [pprof](https://pkg.go.dev/net/http/pprof) - 性能分析
- [go-torch](https://github.com/uber/go-torch) - 火焰图

## 测试

### 测试框架
- [testify](https://github.com/stretchr/testify) - 断言和模拟
- [gomock](https://github.com/golang/mock) - Mock 生成器
- [httpexpect](https://github.com/gavv/httpexpect) - HTTP 测试

### 测试工具
- [Fiber Test](https://docs.gofiber.io/api/test) - 内置测试工具
- [Go Test](https://pkg.go.dev/testing) - 标准测试库

## 相关框架

### Fasthttp
- [fasthttp](https://github.com/valyala/fasthttp) - 高性能 HTTP 服务器
- [fasthttp-routing](https://github.com/fasthttp/router) - 路由器

### 其他 Go 框架
- [Gin](https://github.com/gin-gonic/gin) - 基于 httprouter 的框架
- [Echo](https://github.com/labstack/echo) - 高性能极简框架
- [Chi](https://github.com/go-chi/chi) - 轻量级 HTTP 路由器

## 学习资源

### 视频教程
- [Fiber YouTube 频道](https://www.youtube.com/results?search_query=gofiber)
- [Go Web 开发](https://www.youtube.com/results?search_query=go+web+development)

### 书籍
- [Web Development with Go](https://www.packtpub.com/product/web-development-with-go)
- [Go Programming Language](https://www.gopl.io/)

### 社区
- [Fiber Discord](https://discord.gg/9 wkW4Se) - Discord 社区
- [Fiber Slack](https://gophers.slack.com/) - Slack 频道
- [Reddit - r/golang](https://www.reddit.com/r/golang/) - Go 社区
- [Stack Overflow - Fiber](https://stackoverflow.com/questions/tagged/gofiber) - 问答

## 相关项目

### 模板引擎
- [html/template](https://pkg.go.dev/html/template) - Go 标准模板
- [quicktemplate](https://github.com/valyala/quicktemplate) - 快速模板引擎
- [plush](https://github.com/gobuffalo/plush) - Ruby 风格模板

### WebSocket
- [gorilla/websocket](https://github.com/gorilla/websocket) - WebSocket 库
- [fiber websocket](https://docs.gofiber.io/api/middleware/websocket) - 内置 WebSocket

### 静态文件
- [packr](https://github.com/gobuffalo/packr) - 静态文件嵌入
- [embed](https://pkg.go.dev/embed) - Go 1.16+ 内嵌
