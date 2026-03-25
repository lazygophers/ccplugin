---
name: tooling
description: Go 工具链规范：gofmt、goimports、go mod、golangci-lint v2、govulncheck、delve debugger、go test -fuzz。运行工具时加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 工具规范

## 适用 Agents

- **dev** - 开发专家
- **debug** - 调试专家
- **test** - 测试专家
- **perf** - 性能优化专家

## 相关 Skills

| 场景     | Skill                    | 说明                     |
| -------- | ------------------------ | ------------------------ |
| 核心规范 | Skills(golang:core)      | 核心规范：强制约定       |
| Lint     | Skills(golang:lint)      | golangci-lint v2 配置    |
| 测试     | Skills(golang:testing)   | 测试命令和策略           |

## 代码格式化

### gofmt + goimports

```bash
gofmt -w .
goimports -w .
```

### 编辑器集成

```json
{
    "go.formatTool": "goimports",
    "go.lintTool": "golangci-lint",
    "go.lintOnSave": "file",
    "go.formatOnSave": true
}
```

## 依赖管理

### go.mod 命令

```bash
go mod init github.com/username/project
go mod tidy
go get github.com/lazygophers/utils@latest
go mod graph
go list -m all
```

### Go 1.23 Toolchain 管理

```bash
# go.mod 中指定 toolchain
go 1.23.0
toolchain go1.23.4

# 更新 toolchain
go get go@1.23.4
go get toolchain@go1.23.4
```

### 依赖原则

- **最小化依赖** - 仅添加必要的库
- **优先标准库** - 使用 Go 标准库优先
- **固定版本** - 使用具体版本号
- **定期审计** - govulncheck 检查漏洞

## 安全工具

### govulncheck（推荐）

```bash
# 安装
go install golang.org/x/vuln/cmd/govulncheck@latest

# 检查项目漏洞
govulncheck ./...

# 检查二进制
govulncheck -mode=binary ./myapp
```

## 代码检查

### go vet

```bash
go vet ./...
```

### golangci-lint v2

```bash
# 安装最新版
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@latest

# 运行
golangci-lint run ./...

# 自动修复
golangci-lint run --fix
```

## 调试工具

### Delve

```bash
# 安装
go install github.com/go-delve/delve/cmd/dlv@latest

# 调试
dlv debug ./cmd/main.go
dlv test ./internal/impl/

# 附加到进程
dlv attach <pid>
```

## 测试工具

```bash
# 单元测试 + race 检测
go test -v -race -cover ./...

# 模糊测试（Go 1.18+）
go test -fuzz=FuzzXxx -fuzztime=30s ./parser/

# 基准测试
go test -bench=. -benchmem -count=5 ./...

# 性能分析
go test -cpuprofile=cpu.prof -memprofile=mem.prof ./...
go tool pprof -http=:8080 cpu.prof

# 覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
go tool cover -func=coverage.out | grep total
```

## 代码生成

### go generate

```go
//go:generate protoc --go_out=. ./proto.proto
//go:generate stringer -type=Status
```

```bash
go generate ./...
```

## 构建

```bash
go build ./...
go build -o bin/app ./cmd/main.go

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o bin/app-linux ./cmd/main.go
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "gofmt 就够了" | 是否也运行了 goimports？ | 中 |
| "go vet 够严格了" | 是否运行了 golangci-lint v2？ | 高 |
| "依赖没有漏洞" | 是否运行了 govulncheck？ | 高 |
| "print 调试够用" | 是否使用 delve 断点调试？ | 中 |
| "手动管理 Go 版本" | 是否在 go.mod 中用 toolchain 指令？ | 低 |
| "不需要 fuzz 测试" | 解析器是否添加了 fuzz 测试？ | 中 |

## 检查清单

- [ ] 代码已通过 gofmt 格式化
- [ ] 代码已通过 goimports 优化导入
- [ ] 代码已通过 go vet 检查
- [ ] 代码已通过 golangci-lint v2 检查
- [ ] 依赖已通过 go mod tidy 清理
- [ ] 依赖已通过 govulncheck 安全检查
- [ ] go.mod 中指定了 toolchain 版本
- [ ] 测试已通过（含 -race）
- [ ] 构建成功
