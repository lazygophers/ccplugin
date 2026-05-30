所有 Go 代码必须遵守以下 Skills 规范：
- Skill(golang-core) - 核心规范：强制约定、代码格式
- Skill(golang-error) - 错误处理规范：禁单行 if err、必须记录日志、validate tag 统一校验
- Skill(golang-libs) - 优先库规范：stringx/candy/osx/log
- Skill(golang-naming) - 命名规范：Id/Uid/IsActive/CreatedAt、集合 xxx_list、Enum XxxNil、禁 Status
- Skill(golang-structure) - 项目结构规范：三层架构、全局状态模式、var rsp 顶声明
- Skill(golang-testing) - 测试规范：单元测试、表驱动测试
- Skill(golang-concurrency) - 并发规范：atomic/sync.Pool/errgroup
- Skill(golang-lint) - Lint 规范：golangci-lint 配置
- Skill(golang-tooling) - 工具规范：gofmt/goimports/go mod
- Skill(golang-db) - 数据库规范：Model 命名、索引 idx_ 前缀、禁 time.Time、枚举 uint8
- Skill(golang-api) - HTTP API 规范：始终 200、全 POST 单段、逐路由中间件

如果涉及到 Golang Template，请遵守 Skill(gtpl-skills) 的规范。
每一个 `*.go` 文件都不得超过500行，推荐200~400行
