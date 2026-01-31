---
name: lrpc-app-skills
description: LazyGophers Utils 应用框架模块 - 应用配置、环境变量、构建信息、运行模式管理
---

# lrpc-app: LazyGophers Utils 应用框架模块

> 模块路径: `github.com/lazygophers/utils/app`

## 概述

`app` 模块是 LazyGophers Utils 的核心应用框架模块，提供了一套完整的应用生命周期管理、构建信息注入、环境变量处理和运行模式控制机制。

### 核心功能

- **构建信息注入** - 编译时注入版本、提交哈希、构建时间等元数据
- **多环境支持** - 通过构建标签支持 debug/test/alpha/beta/release 模式
- **环境变量覆盖** - 运行时通过 `APP_ENV` 环境变量动态切换运行模式
- **类型安全** - 使用 `ReleaseType` 枚举确保类型安全
- **零运行时开销** - 构建时确定，编译器优化

## 运行模式

### ReleaseType 枚举

```go
type ReleaseType uint8

const (
    Debug ReleaseType = iota  // 0 - 开发模式
    Test                       // 1 - 测试模式
    Alpha                      // 2 - Alpha 版本
    Beta                       // 3 - Beta 版本
    Release                    // 4 - 生产发布
)
```

### 模式切换方式

#### 方式 1: 构建标签（推荐）

使用 Go 构建标签在编译时确定运行模式：

```bash
# Debug 模式（默认）
go build

# Test 模式
go build -tags=test

# Alpha 版本
go build -tags=alpha

# Beta 版本
go build -tags=beta

# Release 模式
go build -tags=release
```

对应的构建约束文件：
- `debug.go` - `//go:build debug`
- `test.go` - `//go:build test`
- `alpha.go` - `//go:build alpha`
- `beta.go` - `//go:build beta`
- `release.go` - `//go:build release`
- `other.go` - `//go:build !debug && !alpha && !beta && !release && !test`（默认 debug）

#### 方式 2: 环境变量（运行时覆盖）

通过 `APP_ENV` 环境变量在运行时覆盖编译时设置：

```bash
# 开发环境
export APP_ENV=development
# 或
export APP_ENV=dev

# 测试环境
export APP_ENV=test
# 或
export APP_ENV=canary

# 生产环境
export APP_ENV=production
# 或
export APP_ENV=prod
# 或
export APP_ENV=release

# Alpha 版本
export APP_ENV=alpha

# Beta 版本
export APP_ENV=beta
```

**注意**: 环境变量映射规则（不区分大小写）：
- `dev`, `development` → `Debug`
- `test`, `canary` → `Test`
- `prod`, `production`, `release` → `Release`
- `alpha` → `Alpha`
- `beta` → `Beta`
- 其他值或未设置 → 保持编译时设置的值

## 应用元数据

### 全局变量

```go
// 组织信息
var Organization = "lazygophers"

// 应用信息（需在编译时通过 -ldflag 注入）
var Name string          // 应用名称
var Version string       // 应用版本

// Git 信息（需在编译时通过 -ldflag 注入）
var Commit      string   // 完整提交哈希
var ShortCommit string   // 短提交哈希
var Branch      string   // Git 分支
var Tag         string   // Git 标签

// 构建信息（需在编译时通过 -ldflag 注入）
var BuildDate string     // 构建时间 (RFC3339 格式)

// Go 运行时信息（自动注入）
var GoVersion string     // Go 版本
var GoOS      string     // 目标操作系统
var Goarch    string     // 目标架构
var Goarm     string     // ARM 版本（如果适用）
var Goamd64   string     // AMD64 版本（如果适用）
var Gomips    string     // MIPS 版本（如果适用）

// 应用描述
var Description string   // 应用描述信息
```

### 编译时注入

使用 `-ldflag` 在编译时注入变量值：

```bash
# 基本注入
go build -ldflags="
  -X 'github.com/lazygophers/utils/app.Name=myapp'
  -X 'github.com/lazygophers/utils/app.Version=1.0.0'
  -X 'github.com/lazygophers/utils/app.Commit=$(git rev-parse HEAD)'
  -X 'github.com/lazygophers/utils/app.ShortCommit=$(git rev-parse --short HEAD)'
  -X 'github.com/lazygophers/utils/app.BuildDate=$(date -u +%Y-%m-%dT%H:%M:%SZ)'
"

# 使用 Makefile（推荐）
include git.mk

# git.mk 内容示例
GIT_TAG    := $(shell git describe --tags --always --dirty)
GIT_COMMIT := $(shell git rev-parse HEAD)
GIT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
BUILD_DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

LDFLAGS := -ldflags "
  -X 'github.com/lazygophers/utils/app.Name=${APP_NAME}'
  -X 'github.com/lazygophers/utils/app.Version=${GIT_TAG}'
  -X 'github.com/lazygophers/utils/app.Commit=${GIT_COMMIT}'
  -X 'github.com/lazygophers/utils/app.ShortCommit=${GIT_COMMIT}'
  -X 'github.com/lazygophers/utils/app.Branch=${GIT_BRANCH}'
  -X 'github.com/lazygophers/utils/app.BuildDate=${BUILD_DATE}'
  -X 'github.com/lazygophers/utils/app.GoVersion=${GOVERSION}'
"

build:
    go build ${LDFLAGS} -tags=${RELEASE_TYPE} -o ${BIN_NAME}
```

## API 方法

### ReleaseType.String()

返回运行模式的字符串表示：

```go
func (p ReleaseType) String() string {
    switch p {
    case Release:
        return "release"
    case Beta:
        return "beta"
    case Alpha:
        return "alpha"
    case Test:
        return "test"
    case Debug:
        fallthrough
    default:
        return "debug"
    }
}
```

**示例**:
```go
fmt.Println(app.PackageType.String()) // 输出: debug, test, alpha, beta, 或 release
```

### ReleaseType.Debug()

返回调试用的模式名称（与 `String()` 方法相同）：

```go
func (p ReleaseType) Debug() string {
    return p.String()
}
```

## 使用示例

### 示例 1: 基本应用框架

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/app"
)

func main() {
    // 根据运行模式设置日志级别
    switch app.PackageType {
    case app.Debug:
        fmt.Println("Running in DEBUG mode with verbose logging")
    case app.Test:
        fmt.Println("Running in TEST mode")
    case app.Alpha:
        fmt.Printf("Running ALPHA version %s\n", app.Version)
    case app.Beta:
        fmt.Printf("Running BETA version %s\n", app.Version)
    case app.Release:
        fmt.Printf("Running production release %s\n", app.Version)
    }

    // 输出应用信息
    fmt.Printf("Application: %s/%s\n", app.Organization, app.Name)
    fmt.Printf("Version: %s\n", app.Version)
    fmt.Printf("Commit: %s\n", app.ShortCommit)
    fmt.Printf("Build Date: %s\n", app.BuildDate)
}
```

### 示例 2: 条件编译

```go
// main.go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/app"
)

func main() {
    fmt.Printf("Running in %s mode\n", app.PackageType)

    // 使用构建标签的特性
    #if app.PackageType == app.Debug {
        enableDebugFeatures()
    #}
}

func enableDebugFeatures() {
    // 仅在 debug 模式下启用的功能
    fmt.Println("Debug features enabled")
    fmt.Println("  - Profiling")
    fmt.Println("  - Detailed logging")
    fmt.Println("  - Development tools")
}
```

### 示例 3: HTTP 服务

```go
package main

import (
    "fmt"
    "net/http"
    "github.com/lazygophers/utils/app"
)

func main() {
    // 根据运行模式配置服务
    var port string
    switch app.PackageType {
    case app.Debug:
        port = "8080"
        http.HandleFunc("/debug", debugHandler)
    case app.Test:
        port = "8081"
    case app.Release:
        port = "80"
    }

    // 健康检查端点
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, `{
            "status": "ok",
            "version": "%s",
            "commit": "%s",
            "build_date": "%s",
            "mode": "%s"
        }`, app.Version, app.ShortCommit, app.BuildDate, app.PackageType)
    })

    fmt.Printf("Server starting on port %s (%s mode)\n", port, app.PackageType)
    http.ListenAndServe(":"+port, nil)
}

func debugHandler(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Debug endpoint - Version: %s, Commit: %s",
        app.Version, app.Commit)
}
```

### 示例 4: 版本命令

```go
package cmd

import (
    "fmt"
    "github.com/lazygophers/utils/app"
    "github.com/spf13/cobra"
)

var versionCmd = &cobra.Command{
    Use:   "version",
    Short: "Print version information",
    Run: func(cmd *cobra.Command, args []string) {
        fmt.Printf("%s/%s %s\n", app.Organization, app.Name, app.Version)
        fmt.Printf("  Commit:    %s\n", app.ShortCommit)
        fmt.Printf("  Branch:    %s\n", app.Branch)
        fmt.Printf("  BuildDate: %s\n", app.BuildDate)
        fmt.Printf("  GoVersion: %s\n", app.GoVersion)
        fmt.Printf("  Mode:      %s\n", app.PackageType)
        fmt.Printf("  Platform:  %s/%s\n", app.GoOS, app.Goarch)
    },
}
```

### 示例 5: 配置管理

```go
package config

import (
    "fmt"
    "os"
    "github.com/lazygophers/utils/app"
)

type Config struct {
    LogLevel string
    Database DatabaseConfig
    Server   ServerConfig
}

type DatabaseConfig struct {
    Host     string
    Port     int
    Username string
    Password string
    Database string
}

type ServerConfig struct {
    Port int
    Host string
}

func Load() (*Config, error) {
    cfg := &Config{}

    // 根据运行模式设置默认值
    switch app.PackageType {
    case app.Debug:
        cfg.LogLevel = "debug"
        cfg.Database = DatabaseConfig{
            Host:     "localhost",
            Port:     5432,
            Database: "myapp_dev",
        }
        cfg.Server = ServerConfig{
            Port: 8080,
            Host: "localhost",
        }
    case app.Test:
        cfg.LogLevel = "warn"
        cfg.Database = DatabaseConfig{
            Host:     "localhost",
            Port:     5433,
            Database: "myapp_test",
        }
        cfg.Server = ServerConfig{
            Port: 8081,
            Host: "localhost",
        }
    case app.Release:
        cfg.LogLevel = "info"
        cfg.Database = DatabaseConfig{
            Host:     getEnv("DB_HOST", "prod-db.example.com"),
            Port:     5432,
            Database: "myapp_prod",
        }
        cfg.Server = ServerConfig{
            Port: 80,
            Host: "0.0.0.0",
        }
    }

    // 从环境变量覆盖配置
    if port := os.Getenv("SERVER_PORT"); port != "" {
        fmt.Sscanf(port, "%d", &cfg.Server.Port)
    }

    return cfg, nil
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}
```

### 示例 6: Makefile 集成

```makefile
# Makefile
APP_NAME := myapp
VERSION := $(shell git describe --tags --always --dirty)
COMMIT := $(shell git rev-parse HEAD)
SHORT_COMMIT := $(shell git rev-parse --short HEAD)
BUILD_DATE := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
GOVERSION := $(shell go version | awk '{print $$3}')

# 根据目标设置构建标签
ifeq ($(ENV),prod)
    RELEASE_TYPE := release
else ifeq ($(ENV),beta)
    RELEASE_TYPE := beta
else ifeq ($(ENV),alpha)
    RELEASE_TYPE := alpha
else ifeq ($(ENV),test)
    RELEASE_TYPE := test
else
    RELEASE_TYPE := debug
endif

LDFLAGS := -ldflags " \
    -X 'github.com/lazygophers/utils/app.Name=$(APP_NAME)' \
    -X 'github.com/lazygophers/utils/app.Version=$(VERSION)' \
    -X 'github.com/lazygophers/utils/app.Commit=$(COMMIT)' \
    -X 'github.com/lazygophers/utils/app.ShortCommit=$(SHORT_COMMIT)' \
    -X 'github.com/lazygophers/utils/app.BuildDate=$(BUILD_DATE)' \
    -X 'github.com/lazygophers/utils/app.GoVersion=$(GOVERSION)' \
"

.PHONY: build build-prod build-beta build-alpha build-test

build: ## Build with current ENV (default: debug)
    go build $(LDFLAGS) -tags=$(RELEASE_TYPE) -o bin/$(APP_NAME)

build-prod: ## Build production release
    ENV=prod $(MAKE) build

build-beta: ## Build beta release
    ENV=beta $(MAKE) build

build-alpha: ## Build alpha release
    ENV=alpha $(MAKE) build

build-test: ## Build test release
    ENV=test $(MAKE) build
```

### 示例 7: Docker 集成

```dockerfile
# Dockerfile
ARG GO_VERSION=1.21
ARG APP_NAME=myapp
ARG VERSION=dev

FROM golang:${GO_VERSION} AS builder

# 设置构建参数
ARG VERSION
ARG COMMIT
ARG BUILD_DATE
ARG RELEASE_TYPE=release

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
ARG VERSION
ARG COMMIT
ARG BUILD_DATE
ARG RELEASE_TYPE

RUN LDFLAGS=" \
    -X 'github.com/lazygophers/utils/app.Name=${APP_NAME}' \
    -X 'github.com/lazygophers/utils/app.Version=${VERSION}' \
    -X 'github.com/lazygophers/utils/app.Commit=${COMMIT}' \
    -X 'github.com/lazygophers/utils/app.BuildDate=${BUILD_DATE}' \
    " && \
    go build -ldflags "$$LDFLAGS" -tags=${RELEASE_TYPE} -o /app/${APP_NAME}

# 最终镜像
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/${APP_NAME} .

# 设置环境变量覆盖（可选）
# ENV APP_ENV=production

ENTRYPOINT ["./${APP_NAME}"]
```

构建命令：
```bash
# 生产构建
docker build --build-arg VERSION=1.0.0 \
             --build-arg COMMIT=$(git rev-parse HEAD) \
             --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
             --build-arg RELEASE_TYPE=release \
             -t myapp:1.0.0 .

# 测试构建
docker build --build-arg VERSION=1.0.0-test \
             --build-arg RELEASE_TYPE=test \
             -t myapp:test .
```

## 测试

模块包含完整的单元测试覆盖：

```bash
# 运行测试
go test github.com/lazygophers/utils/app

# 运行测试并查看覆盖率
go test -cover github.com/lazygophers/utils/app

# 详细输出
go test -v github.com/lazygophers/utils/app
```

### 测试覆盖范围

测试文件 `app_test.go` 包含以下测试用例：

1. **环境变量测试** (`TestSetPackageTypeFromEnv`)
   - 测试所有环境变量值的映射
   - 验证默认值处理
   - 验证大小写敏感性

2. **ReleaseType 方法测试**
   - `TestReleaseTypeString` - 测试 String() 方法
   - `TestReleaseTypeDebug` - 测试 Debug() 方法
   - `TestStringAndDebugConsistency` - 验证两个方法一致性

3. **包变量测试**
   - `TestOrganization` - 验证组织名称
   - `TestGlobalVariables` - 验证全局变量存在性
   - `TestPackageVariables` - 验证包变量

4. **枚举测试**
   - `TestReleaseTypeConstants` - 验证枚举常量值
   - `TestReleaseTypeOrder` - 验证枚举顺序
   - `TestReleaseTypeRange` - 验证枚举范围

## 最佳实践

### 1. 始终注入构建信息

```bash
# ❌ 不好：缺少构建信息
go build -o myapp

# ✅ 好：完整的构建信息
go build -ldflags="
  -X 'github.com/lazygophers/utils/app.Name=myapp'
  -X 'github.com/lazygophers/utils/app.Version=${VERSION}'
  -X 'github.com/lazygophers/utils/app.Commit=${COMMIT}'
  -X 'github.com/lazygophers/utils/app.BuildDate=${BUILD_DATE}'
" -tags=release -o myapp
```

### 2. 使用构建标签区分环境

```bash
# ❌ 不好：所有环境使用相同二进制
go build -o myapp

# ✅ 好：为不同环境构建不同的二进制
go build -tags=debug -o myapp-debug
go build -tags=test -o myapp-test
go build -tags=release -o myapp
```

### 3. 提供版本信息端点

```go
// ✅ 好：提供 /version 端点用于部署验证
http.HandleFunc("/version", func(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]interface{}{
        "name": app.Name,
        "version": app.Version,
        "commit": app.ShortCommit,
        "build_date": app.BuildDate,
        "mode": app.PackageType.String(),
    })
})
```

### 4. 使用环境变量覆盖

```bash
# ✅ 好：通过环境变量动态调整日志级别
export APP_ENV=development
./myapp  # 自动切换到 debug 模式

export APP_ENV=production
./myapp  # 切换到 release 模式
```

### 5. 版本信息嵌入到二进制

```go
// ✅ 好：在 main 函数中输出版本信息
func main() {
    if len(os.Args) > 1 && os.Args[1] == "version" {
        fmt.Printf("%s %s (commit: %s, built: %s)\n",
            app.Name, app.Version, app.ShortCommit, app.BuildDate)
        os.Exit(0)
    }
    // ... 正常逻辑
}
```

## 注意事项

1. **构建信息必须在编译时注入** - 如果不使用 `-ldflag` 注入，变量将为空字符串
2. **环境变量覆盖有限制** - 环境变量仅在运行时生效，不会改变编译时的优化选项
3. **构建标签优先级更高** - 如果同时使用构建标签和环境变量，构建标签优先
4. **类型安全** - `ReleaseType` 是枚举类型，不要直接使用数字常量
5. **版本格式** - 建议使用语义化版本（SemVer）：`v1.2.3`
6. **时间格式** - `BuildDate` 应使用 RFC3339 格式：`2024-01-15T10:30:00Z`

## 相关模块

- **config/** - 配置文件加载模块（YAML/JSON/TOML）
- **runtime/** - 运行时信息模块
- **osx/** - 操作系统相关操作
- **atexit/** - 优雅退出处理

## 参考资料

- [Go Build Constraints](https://pkg.go.dev/cmd/go#hdr-Build_constraints)
- [Semantic Versioning](https://semver.org/)
- [LazyGophers Utils 完整文档](https://github.com/lazygophers/utils)
