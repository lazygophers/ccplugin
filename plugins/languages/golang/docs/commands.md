# 命令系统

Golang 插件提供四个命令，覆盖开发、审查、初始化和 CI 场景。

## 命令列表

| 命令 | 描述 | 用法 |
|------|------|------|
| `/go-init` | 初始化项目 | `/go-init [module-name]` |
| `/go-dev` | 开发命令 | `/go-dev [args]` |
| `/go-review` | 代码审查 | `/go-review` |
| `/go-ci` | CI/CD 命令 | `/go-ci [command]` |

## /go-init - 初始化项目

### 功能

- 创建标准项目结构
- 初始化 go.mod
- 生成基础代码模板

### 用法

```bash
/go-init github.com/username/myproject
```

### 生成的结构

```
myproject/
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

## /go-dev - 开发命令

### 功能

- 运行开发服务器
- 热重载支持
- 调试模式

### 用法

```bash
# 运行开发服务器
/go-dev run

# 构建项目
/go-dev build

# 运行测试
/go-dev test
```

## /go-review - 代码审查

### 功能

- 代码质量检查
- 安全漏洞扫描
- 性能问题识别
- 最佳实践建议

### 用法

```bash
/go-review
```

### 审查清单

- [ ] 命名规范检查
- [ ] 错误处理检查
- [ ] 并发安全检查
- [ ] 性能问题检查
- [ ] 安全漏洞检查

## /go-ci - CI/CD 命令

### 功能

- 运行 CI 流程
- 构建和测试
- 代码覆盖率
- 静态分析

### 用法

```bash
# 运行完整 CI
/go-ci

# 仅运行测试
/go-ci test

# 仅运行 lint
/go-ci lint

# 生成覆盖率报告
/go-ci coverage
```

### CI 流程

1. **代码检查**
   - go vet
   - golangci-lint

2. **测试**
   - go test ./...
   - 覆盖率报告

3. **构建**
   - go build
   - 多平台构建

4. **安全扫描**
   - go mod verify
   - 安全漏洞检查
