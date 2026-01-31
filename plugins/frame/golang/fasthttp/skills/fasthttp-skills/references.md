# fasthttp-skills 参考资源

## 官方资源

### 核心项目
- [fasthttp-skills GitHub](https://github.com/valyala/fasthttp) - 源代码和问题跟踪
- [fasthttp-skills GoDoc](https://pkg.go.dev/github.com/valyala/fasthttp) - Go 包文档
- [fasthttp-skills Wiki](https://github.com/valyala/fasthttp/wiki) - 项目 Wiki

### 相关项目
- [fasthttp-routing](https://github.com/fasthttp/router) - 路由库
- [fasthttp/fasthttpproxy](https://github.com/valyala/fasthttp/tree/master/fasthttpproxy) - 代理支持

## 设计理念

### 零拷贝技术
- [Zero-Copy Wikipedia](https://en.wikipedia.org/wiki/Zero-copy)
- [Go Zero-Copy Examples](https://go.dev/play/)

### 对象池模式
- [sync.Pool](https://pkg.go.dev/sync#Pool) - Go 标准库对象池
- [Object Pool Pattern](https://en.wikipedia.org/wiki/Object_pool_pattern)

## 路由器

### 推荐路由器
- [fasthttp/router](https://github.com/fasthttp/router) - 官方推荐路由器
- [bmizerany/pat](https://github.com/bmizerany/pat) - 模式路由器
- [pressly/chi](https://github.com/pressly/chi) - 轻量级路由器

### 适配器
- [fasthttp/adaptor](https://github.com/valyala/fasthttp/tree/master/adaptor) - net/http 适配器
- [alice](https://github.com justinas/alice) - 中间件链

## 中间件

### 常用中间件
- [fasthttp-middlewares](https://github.com/gofiber/faster) - 中间件集合
- [cors](https://github.com/rs/cors) - CORS 支持
- [secure](https://github.com/unrolled/secure) - 安全头

### 认证
- [jwt-go](https://github.com/golang-jwt/jwt) - JWT 实现
- [oauth2](https://github.com/golang/oauth2) - OAuth2 客户端

## 性能分析

### 基准测试
- [Go Benchmark](https://pkg.go.dev/testing#hdr-Benchmarks) - Go 基准测试
- [wrk](https://github.com/wg/wrk) - HTTP 基准测试工具
- [Apache Bench (ab)](https://httpd.apache.org/docs/2.4/programs/ab.html) - Apache 基准测试

### 性能分析
- [pprof](https://pkg.go.dev/net/http/pprof) - Go 性能分析
- [go-torch](https://github.com/uber/go-torch) - 火焰图工具

## 教程和文章

### 官方教程
- [fasthttp-skills Examples](https://github.com/valyala/fasthttp/tree/master/examples) - 官方示例

### 社区文章
- [High-Performance HTTP in Go](https://blog.cloudflare.com/the-complete-guide-to-golang-net-http-timeouts/)
- [fasthttp-skills vs net/http](https://medium.com/a-journey-with-go/go-fasthttp-vs-net-http-af409e1f202c)

## 工具库

### 测试
- [testify](https://github.com/stretchr/testify) - 断言和模拟
- [go-sqlmock](https://github.com/DATA-DOG/go-sqlmock) - SQL 模拟

### 日志
- [zap](https://github.com/uber-go/zap) - 高性能日志
- [logrus](https://github.com/sirupsen/logrus) - 结构化日志

### 配置
- [viper](https://github.com/spf13/viper) - 配置管理

### 数据库
- [GORM](https://gorm.io/) - ORM 库
- [sqlx](https://github.com/jmoiron/sqlx) - SQL 扩展

### 缓存
- [go-redis](https://github.com/redis/go-redis) - Redis 客户端
- [BigCache](https://github.com/allegro/bigcache) - 高性能缓存

## 社区

### 论坛和讨论
- [fasthttp-skills Discussions](https://github.com/valyala/fasthttp/discussions) - GitHub 讨论区
- [r/golang](https://www.reddit.com/r/golang/) - Go 社区
- [Gophers Slack](https://invite.slack.golangbridge.org/) - Go Slack

### 问题跟踪
- [fasthttp-skills Issues](https://github.com/valyala/fasthttp/issues) - Bug 报告和功能请求

## 相关项目

### Web 框架
- [Fiber](https://github.com/gofiber/fiber) - 基于 fasthttp-skills 的 Web 框架
- [Gearbox](https://github.com/gogearbox/gearbox) - fasthttp-skills 框架

### 服务器
- [Caddy](https://caddyserver.com/) - 现代化 Web 服务器
- [Traefik](https://doc.traefik.io/traefik/) - 云原生边缘路由器

## 学习资源

### Go 语言
- [Effective Go](https://go.dev/doc/effective_go) - 有效的 Go 编程
- [Go by Example](https://gobyexample.com/) - Go 示例教程
- [A Tour of Go](https://go.dev/tour/) - Go 语言导览

### 性能优化
- [Go Performance Tips](https://github.com/dgryski/go-perfbook) - Go 性能优化手册
- [Go Performance Patterns](https://www.ardanlabs.com/blog/2014/03/performance-tip-for-go.html)

## 部署

### Docker
- [Docker Hub](https://hub.docker.com/r/golang/) - Go Docker 镜像

### 云平台
- [Google Cloud Run](https://cloud.google.com/run) - 无服务器平台
- [AWS Lambda](https://aws.amazon.com/lambda/) - AWS 无服务器

## 监控

### Prometheus
- [Prometheus Go Client](https://github.com/prometheus/client_golang) - Prometheus Go 客户端

### OpenTelemetry
- [OpenTelemetry Go](https://github.com/open-telemetry/opentelemetry-go) - 分布式追踪

## 书籍

- [The Go Programming Language](https://www.gopl.io/) - Go 程序设计语言
- [Go in Action](https://www.manning.com/books/go-in-action) - Go 实战
- [Concurrency in Go](https://www.oreilly.com/library/view/concurrency-in-go/9781491941194/) - Go 并发编程
