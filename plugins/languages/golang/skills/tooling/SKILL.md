---
name: golang-tooling
description: Go 工具链规范——gofmt/goimports 格式化、go mod 依赖管理 + tool 指令（Go 1.24+）、toolchain 指令、golangci-lint v2 + govulncheck 安全扫描、delve 调试、go test -fuzz 模糊测试、pprof + trace 性能分析、go fix 现代化（Go 1.26 重写）、交叉编译。装环境、跑命令、配置 Makefile/CI、做基线检查时触发。
---

# Go 工具链规范

## 格式化

```bash
gofmt -w .
goimports -w .
```

编辑器配置：

```json
{
  "go.formatTool": "goimports",
  "go.lintTool": "golangci-lint",
  "go.lintOnSave": "file",
  "go.formatOnSave": true
}
```

## 依赖管理

```bash
go mod init github.com/username/project
go mod tidy
go get github.com/lazygophers/utils@latest
go list -m all
go mod graph
```

### Toolchain 管理（Go 1.21+）

`go.mod` 显式声明：

```
go 1.26.0
toolchain go1.26.0
```

升级：

```bash
go get go@1.26.0
go get toolchain@go1.26.0
```

### tool 指令（Go 1.24+，替代 tools.go）

```
// go.mod
tool golang.org/x/tools/cmd/stringer
tool github.com/golang/mock/mockgen
```

```bash
go tool stringer -type=Status
```

不再需要 `tools.go` + `//go:build tools` 黑魔法。

## 依赖原则

- 最小化依赖
- 优先标准库 / lazygophers 生态
- 固定具体版本号，不用 `latest` 提交
- 每次发布前 `govulncheck ./...`

## 安全扫描 — govulncheck

```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
govulncheck -mode=binary ./bin/app
```

## 静态检查 — golangci-lint v2

详见 `golang-lint`。

```bash
curl -sSfL https://golangci-lint.run/install.sh | sh -s -- -b ./bin v2.12.2
./bin/golangci-lint run ./...
```

## 调试 — Delve

```bash
go install github.com/go-delve/delve/cmd/dlv@latest
dlv debug ./cmd/main.go
dlv test ./internal/impl/
dlv attach <pid>
```

```
(dlv) b main.main
(dlv) c
(dlv) goroutines
(dlv) bt
(dlv) print user
```

## 测试与基准

```bash
# 完整测试 + race
go test -v -race -cover ./...

# 模糊测试
go test -fuzz=FuzzParseInput -fuzztime=30s ./parser/

# 基准
go test -bench=. -benchmem -count=5 ./...
benchstat old.txt new.txt

# 覆盖率
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
go tool cover -func=coverage.out | grep total
```

## 性能分析 — pprof + trace

```bash
# CPU/内存
go test -cpuprofile=cpu.prof -memprofile=mem.prof ./...
go tool pprof -http=:8080 cpu.prof

# 线上 endpoint
go tool pprof http://localhost:6060/debug/pprof/heap
go tool pprof http://localhost:6060/debug/pprof/goroutine

# trace
go test -trace=trace.out ./...
go tool trace trace.out
```

### Go 1.26 实验

```bash
# Goroutine 泄漏剖析（1.26 实验，1.27 拟默认）
GOEXPERIMENT=goroutineleakprofile go build .
# 访问 /debug/pprof/goroutineleak
```

## 代码现代化 — go fix（Go 1.26 重写）

```bash
go fix ./...
```

Go 1.26 重写后基于 go vet 分析框架，提供数十个 modernizer 自动应用现代语法：

- `for i := 0; i < n; i++` → `for i := range n`
- `interface{}` → `any`
- `errors.New(fmt.Sprintf(...))` → `fmt.Errorf(...)`
- 自定义 `//go:fix inline` 做 API 迁移

强烈建议升级 1.26 后跑一次 `go fix ./...`。

## 代码生成

```go
//go:generate protoc --go_out=. ./proto.proto
//go:generate stringer -type=Status
```

```bash
go generate ./...
```

## 构建与交叉编译

```bash
go build ./...
go build -o bin/app ./cmd/main.go

# 交叉编译
GOOS=linux GOARCH=amd64 go build -o bin/app-linux ./cmd/main.go
GOOS=darwin GOARCH=arm64 go build -o bin/app-mac-arm64 ./cmd/main.go

# 体积优化
go build -ldflags="-s -w" -trimpath -o bin/app ./cmd/main.go
```

## 一键检查脚本（Makefile 示例）

```makefile
.PHONY: check
check:
	gofmt -w .
	goimports -w .
	go vet ./...
	./bin/golangci-lint run ./...
	govulncheck ./...
	go test -race -cover ./...
```

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "gofmt 够了" | 跑 goimports？ |
| "go vet 严格" | 跑 golangci-lint v2？ |
| "依赖没漏洞" | 跑 govulncheck？ |
| "print 调试" | 用 delve 断点？ |
| "手管 Go 版本" | go.mod toolchain 指令？ |
| "tools.go 还在" | 迁到 1.24 tool 指令？ |
| "没跑 go fix" | 1.26 跑一次现代化？ |

## 检查清单

- [ ] `gofmt` + `goimports` 已跑
- [ ] `go vet ./...` 无告警
- [ ] `golangci-lint run` 通过（v2）
- [ ] `govulncheck ./...` 无 HIGH
- [ ] `go mod tidy` 已跑
- [ ] `go.mod` 有 `toolchain` 指令
- [ ] 工具依赖用 `tool` 指令（非 tools.go）
- [ ] `go test -race -cover ./...` 通过
- [ ] 升级 Go 后跑过 `go fix ./...`
