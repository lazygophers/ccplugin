---
name: init
description: 项目初始化工作流：创建目录结构、配置文件、.golangci.yml
---

# Go 项目初始化工作流

创建新的 Go 项目结构。

## 初始化步骤

### 1. 创建目录结构

```bash
mkdir -p internal/state
mkdir -p internal/impl
mkdir -p internal/api
mkdir -p internal/middleware
mkdir -p cmd
```

### 2. 初始化 go.mod

```bash
go mod init github.com/username/project
```

### 3. 创建基础文件

#### internal/state/init.go

```go
package state

import "github.com/lazygophers/log"

func Init(configPath string) error {
    log.Infof("state initialized")
    return nil
}
```

#### internal/state/table.go

```go
package state

var (
    User    *db.Model[User]
    Friend  *db.Model[Friend]
    Message *db.Model[Message]
)
```

#### internal/impl/user.go

```go
package impl

import "github.com/lazygophers/log"

func UserLogin(req *LoginReq) (*LoginRsp, error) {
    log.Infof("UserLogin called")
    return &LoginRsp{}, nil
}
```

#### internal/api/router.go

```go
package api

import (
    "github.com/gofiber/fiber/v2"
    "github.com/username/project/internal/impl"
    "github.com/username/project/internal/middleware"
)

func SetupRoutes(app *fiber.App) {
    public := app.Group("/api", middleware.OptionalAuth, middleware.Logger)
    public.Post("/Login", impl.ToHandler(impl.UserLogin))
}
```

#### cmd/main.go

```go
package main

import (
    "github.com/gofiber/fiber/v2"
    "github.com/username/project/internal/api"
    "github.com/username/project/internal/state"
)

func main() {
    err := state.Init("config.yaml")
    if err != nil {
        log.Fatalf("failed to init state")
    }

    app := fiber.New()
    api.SetupRoutes(app)
    app.Listen(":8080")
}
```

### 4. 创建 .golangci.yml

```yaml
version: "2"

linters:
  default: standard
  enable:
    - errcheck
    - govet
    - staticcheck
    - ineffassign
    - unused
    - gosec
    - goconst
    - gocritic
    - revive
  disable:
    - wrapcheck

run:
  timeout: 5m

output:
  formats:
    - format: colored-line-number

issues:
  max-issues-per-linter: 0
  max-same-issues: 0
```

### 5. 创建 README.md

```markdown
# Project Name

项目描述

## 快速开始

```bash
go mod download
go run cmd/main.go
```

## 项目结构

- internal/state - 全局状态
- internal/impl - 业务逻辑
- internal/api - HTTP 路由
- internal/middleware - 中间件
```

## 检查清单

- [ ] 目录结构创建完成
- [ ] go.mod 初始化完成
- [ ] 基础文件创建完成
- [ ] .golangci.yml 创建完成
- [ ] README.md 创建完成
