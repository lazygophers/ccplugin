# 快速开始

Golang 插件快速入门指南。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin golang@ccplugin-market
```

## 前置条件

### 安装 Go

```bash
# macOS
brew install go

# Linux
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# 验证安装
go version
```

### 安装 gopls

```bash
# gopls 通常随 Go 安装
# 如果没有，手动安装
go install golang.org/x/tools/gopls@latest

# 验证安装
which gopls
gopls version
```

## 初始化新项目

### 1. 创建项目

```bash
# 创建项目目录
mkdir myproject && cd myproject

# 初始化 go.mod
go mod init github.com/username/myproject
```

### 2. 创建目录结构

```bash
mkdir -p cmd/server
mkdir -p internal/{handler,service,repository}
mkdir -p pkg/utils
mkdir -p api
```

### 3. 创建主文件

```go
// cmd/server/main.go
package main

import (
    "fmt"
    "log"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello, World!")
    })

    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

### 4. 运行项目

```bash
go run cmd/server/main.go
```

## 开发流程

### 创建模块

```go
// internal/service/user.go
package service

import "fmt"

type User struct {
    ID    int
    Name  string
    Email string
}

type UserService struct {
    users map[int]*User
}

func NewUserService() *UserService {
    return &UserService{
        users: make(map[int]*User),
    }
}

func (s *UserService) Create(name, email string) *User {
    id := len(s.users) + 1
    user := &User{ID: id, Name: name, Email: email}
    s.users[id] = user
    return user
}

func (s *UserService) Get(id int) (*User, error) {
    user, ok := s.users[id]
    if !ok {
        return nil, fmt.Errorf("user not found: %d", id)
    }
    return user, nil
}
```

### 编写测试

```go
// internal/service/user_test.go
package service

import "testing"

func TestUserService_Create(t *testing.T) {
    service := NewUserService()

    user := service.Create("test", "test@example.com")

    if user.Name != "test" {
        t.Errorf("expected name 'test', got '%s'", user.Name)
    }
    if user.Email != "test@example.com" {
        t.Errorf("expected email 'test@example.com', got '%s'", user.Email)
    }
}

func TestUserService_Get(t *testing.T) {
    service := NewUserService()
    created := service.Create("test", "test@example.com")

    user, err := service.Get(created.ID)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if user.ID != created.ID {
        t.Errorf("expected ID %d, got %d", created.ID, user.ID)
    }
}
```

### 运行测试

```bash
# 运行所有测试
go test ./...

# 运行特定测试
go test ./internal/service/...

# 运行并显示覆盖率
go test -cover ./...
```

## 使用命令

### 初始化项目

```bash
/go-init github.com/username/myproject
```

### 开发

```bash
# 运行开发服务器
/go-dev run

# 构建项目
/go-dev build
```

### 代码审查

```bash
/go-review
```

### CI/CD

```bash
# 运行完整 CI
/go-ci

# 仅运行测试
/go-ci test
```

## 常用命令

```bash
# 格式化代码
go fmt ./...

# 静态检查
go vet ./...

# 运行测试
go test ./...

# 构建项目
go build -o bin/server ./cmd/server

# 安装依赖
go mod tidy
go mod download
```

## 下一步

- 阅读 [开发规范](standards.md) 了解详细规范
- 查看 [技能系统](skills.md) 学习各种技能
- 参考 [代理系统](agents.md) 了解代理能力
- 学习 [命令系统](commands.md) 使用各种命令
