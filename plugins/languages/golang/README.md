# Golang 插件

> Golang 开发插件 - 提供 Golang 开发规范、最佳实践和 LSP 支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin golang@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install golang@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **Golang 开发专家代理** - 提供专业的 Golang 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 并发编程支持

- **开发规范指导** - 完整的 Golang 开发规范
  - **通用 Golang 标准** - 遵循官方 Effective Go 规范
  - **Lazygophers 风格** - 基于 lazygophers 生态的最佳实践

- **代码智能支持** - 通过 gopls LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议
  - 类型检查和错误报告

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `golang-dev` | Golang 开发专家 |
| Agent | `golang-test` | 测试专家 |
| Agent | `golang-debug` | 调试专家 |
| Agent | `golang-perf` | 性能优化专家 |
| Skill | `golang-core` | Golang 核心规范 |
| Skill | `golang-error` | 错误处理规范 |
| Skill | `golang-libs` | 常用库规范 |
| Skill | `golang-naming` | 命名规范 |
| Skill | `golang-structure` | 项目结构规范 |
| Skill | `golang-testing` | 测试策略 |
| Skill | `golang-concurrency` | 并发编程规范 |
| Skill | `golang-lint` | Lint 规范 |
| Skill | `golang-tooling` | 工具链规范 |

## 前置条件

### gopls 安装

```bash
# macOS/Linux
go install golang.org/x/tools/gopls@latest

# 验证安装
which gopls
gopls version
```

## 使用指南

### 1. 开发专家代理（golang-dev）

用于 Golang 代码开发和架构设计。

**示例**：
```
实现一个 HTTP API 服务，支持用户 CRUD 操作
```

### 2. 测试专家代理（golang-test）

用于编写和优化 Golang 测试用例。

**示例**：
```
为用户服务编写表驱动测试
```

### 3. 调试专家代理（golang-debug）

用于诊断和解决 Golang 代码问题。

**示例**：
```
排查 goroutine 泄漏问题
```

### 4. 性能优化专家代理（golang-perf）

用于 Golang 代码的性能分析和优化。

**示例**：
```
优化 JSON 序列化性能
```

## 开发规范

### 核心原则

- 遵循 [Effective Go](https://golang.org/doc/effective_go)
- 使用 `gofmt` 自动格式化
- 所有 error 必须显式处理
- 接口应该小而专一

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 包名 | 小写单词 | `package http` |
| 导出 | 大驼峰 | `MyFunction` |
| 私有 | 小驼峰 | `myFunction` |
| 常量 | 大驼峰或小驼峰 | `MaxSize` / `maxSize` |

### 错误处理

```go
// ✅ 好的错误处理
if err != nil {
    log.Error("failed to process",
        "error", err,
        "context", context,
    )
    return fmt.Errorf("process failed: %w", err)
}

// ❌ 不好的错误处理
if err != nil { return err }
```

### 并发编程

- 使用 context 进行超时和取消控制
- 使用 errgroup 管理多个 goroutine
- 使用 sync.Pool 复用对象
- 避免全局变量

## 项目结构

```
my-project/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── handler/
│   ├── service/
│   └── repository/
├── pkg/
│   └── utils/
├── api/
│   └── openapi.yaml
├── go.mod
├── go.sum
└── Makefile
```

## 快速开始

### 初始化新项目

```bash
# 创建项目
mkdir myproject && cd myproject
go mod init github.com/username/myproject

# 创建目录结构
mkdir -p cmd/server internal/{handler,service,repository} pkg/utils

# 创建主文件
cat > cmd/server/main.go << 'EOF'
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
EOF

# 运行项目
go run cmd/server/main.go
```

### 编写测试

```go
// internal/service/user_test.go
package service

import "testing"

func TestUserService_Create(t *testing.T) {
    tests := []struct {
        name    string
        input   UserInput
        want    *User
        wantErr bool
    }{
        {
            name:  "valid user",
            input: UserInput{Name: "test"},
            want:  &User{Name: "test"},
        },
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // test implementation
        })
    }
}
```

## 最佳实践

### 代码审查清单

提交前检查：

- [ ] 遵循命名规范（导出大驼峰，私有小驼峰）
- [ ] 所有 error 都有日志记录
- [ ] 没有单行 if err 语句
- [ ] 单元测试覆盖 >80%
- [ ] 通过 go vet 和 golangci-lint
- [ ] 代码通过 gofmt 格式化

## 参考资源

### 官方文档

- [Effective Go](https://golang.org/doc/effective_go)
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- [gopls](https://github.com/golang/tools/tree/master/gopls)

## 许可证

AGPL-3.0-or-later
