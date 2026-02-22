---
name: tooling
description: Go 工具使用：gofmt、goimports、go mod、代码生成。运行工具时加载。
---

# Go 工具规范

## 代码格式化

### gofmt

```bash
gofmt -w .

gofmt -w main.go

gofmt -l .
```

### goimports

```bash
goimports -w .

goimports -w main.go

goimports -l .
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

go mod edit -replace github.com/lazygophers/utils=/local/path

go mod graph

go list -m all
```

### 依赖原则

- **最小化依赖** - 仅添加必要的库
- **优先官方库** - 使用 Go 标准库优先
- **固定版本** - 使用具体版本号，避免 `latest`
- **定期审计** - 定期检查和更新依赖

## 代码生成

### Protocol Buffers

```bash
protoc --go_out=. --go_opt=paths=source_relative *.proto
```

### go generate

```go
//go:generate protoc --go_out=. ./proto.proto
```

```bash
go generate ./...
```

### 最佳实践

- 将 proto 文件放在 `api/pb/` 目录
- 使用 `//go:generate` 自动化生成
- 生成后的代码纳入版本控制
- 定期更新 protoc 版本

## 代码检查

### go vet

```bash
go vet ./...
```

### golangci-lint

```bash
golangci-lint run

golangci-lint run ./...
```

## 测试

### 运行测试

```bash
go test -v ./...

go test -v -race -cover ./...

go test -bench=. -benchmem -benchtime=5s ./...
```

### 性能分析

```bash
go test -cpuprofile=cpu.prof -memprofile=mem.prof ./...
go tool pprof cpu.prof
```

## 构建和安装

```bash
go build ./...

go build -o bin/app ./cmd/main.go

go install ./...
```

## 检查清单

- [ ] 代码已通过 gofmt 格式化
- [ ] 代码已通过 goimports 优化导入
- [ ] 代码已通过 go vet 检查
- [ ] 代码已通过 golangci-lint 检查
- [ ] 依赖已通过 go mod tidy 清理
- [ ] 测试已通过
- [ ] 构建成功
