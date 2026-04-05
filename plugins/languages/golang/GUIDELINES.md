所有 Go 代码必须遵守以下 Skills 规范：
- Skills(golang:core) - 核心规范：强制约定、代码格式
- Skills(golang:error) - 错误处理规范：禁止单行 if err、必须记录日志
- Skills(golang:libs) - 优先库规范：stringx/candy/osx/log
- Skills(golang:naming) - 命名规范：Id/Uid/IsActive/CreatedAt
- Skills(golang:structure) - 项目结构规范：三层架构、全局状态模式
- Skills(golang:testing) - 测试规范：单元测试、表驱动测试
- Skills(golang:concurrency) - 并发规范：atomic/sync.Pool/errgroup
- Skills(golang:lint) - Lint 规范：golangci-lint 配置
- Skills(golang:tooling) - 工具规范：gofmt/goimports/go mod

如果涉及到 Golang Template，请遵守 Skills(gtpl-skills) 的规范。
每一个 `*.go` 文件都不得超过500行，推荐200~400行
