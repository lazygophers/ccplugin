# Golang 文档规范

## 核心原则

### ✅ 必须遵守

1. **README 完整** - 项目必须有 README.md
2. **API 文档** - 公开 API 必须有文档
3. **代码注释** - 导出类型和函数必须有注释
4. **文档更新** - 代码变更时同步更新文档
5. **文档清晰** - 文档简洁明了，易于理解

### ❌ 禁止行为

- 缺少 README.md
- 公开 API 无文档
- 注释与代码不一致
- 文档包含过时信息
- 文档过于冗长

## README 规范

### README 结构

```markdown
# 项目名称

简短描述项目的主要功能和用途。

## 功能特性

- 功能 1：描述
- 功能 2：描述
- 功能 3：描述

## 快速开始

### 安装

```bash
go get github.com/username/project
```

### 使用

```go
package main

import "github.com/username/project"

func main() {
    // 使用示例
}
```

## 项目结构

```
project/
├── internal/
│   ├── state/
│   ├── impl/
│   └── api/
└── cmd/
    └── main.go
```

## 开发指南

### 环境要求

- Go 1.21+
- MySQL 8.0+

### 运行项目

```bash
# 克隆项目
git clone https://github.com/username/project.git
cd project

# 安装依赖
go mod download

# 运行项目
go run cmd/main.go
```

### 运行测试

```bash
go test -v ./...
```

## API 文档

详见 [API 文档](docs/api.md)

## 贡献指南

详见 [贡献指南](CONTRIBUTING.md)

## 许可证

MIT License
```

### README 最佳实践

```markdown
# ✅ 正确 - 清晰的 README
# MyProject

一个高性能的 Go Web 框架，提供简洁的 API 和强大的功能。

## 功能特性

- 高性能：基于 Fiber 框架，性能优异
- 简洁 API：易于使用和集成
- 全局状态模式：简化代码结构
- 完整测试：单元测试和集成测试覆盖

## 快速开始

### 安装

```bash
go get github.com/username/myproject
```

### 使用

```go
package main

import "github.com/username/myproject"

func main() {
    app := myproject.New()
    app.Run(":8080")
}
```

# ❌ 错误 - 不完整的 README
# MyProject

Go 项目。
```

## API 文档

### API 文档结构

```markdown
# API 文档

## 用户 API

### 用户登录

**请求**

```
POST /api/user/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**错误码**

| 错误码 | 说明 |
| ------- | ---- |
| 1001    | 用户名不存在 |
| 1002    | 密码错误 |

### 用户注册

**请求**

```
POST /api/user/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password123"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**错误码**

| 错误码 | 说明 |
| ------- | ---- |
| 2001    | 用户名已存在 |
| 2002    | 邮箱已存在 |
```

### API 文档最佳实践

```markdown
# ✅ 正确 - 完整的 API 文档
# API 文档

## 用户 API

### 用户登录

**描述**

用户登录接口，验证用户名和密码，返回用户信息和访问令牌。

**请求**

- 方法：POST
- 路径：/api/user/login
- Content-Type：application/json

**请求参数**

| 参数名   | 类型   | 必填 | 说明     |
| ------- | ------ | ---- | -------- |
| username | string | 是   | 用户名   |
| password | string | 是   | 密码     |

**请求示例**

```json
{
  "username": "testuser",
  "password": "password123"
}
```

**响应**

| 字段名   | 类型   | 说明     |
| ------- | ------ | -------- |
| code    | int32  | 响应码   |
| message | string | 响应消息 |
| data    | object | 用户数据 |

**响应示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**错误码**

| 错误码 | 说明           |
| ------- | -------------- |
| 1001    | 用户名不存在   |
| 1002    | 密码错误       |

# ❌ 错误 - 不完整的 API 文档
# API 文档

## 用户登录

POST /api/user/login

{
  "username": "testuser",
  "password": "password123"
}
```

## 代码注释

### 导出类型注释

```go
// ✅ 正确 - 导出类型必须有注释
// User 表示系统用户，包含用户的基本信息和状态
type User struct {
    Id        int64
    Email     string
    IsActive  bool
    CreatedAt time.Time
}

// ❌ 错误 - 缺少注释
type User struct {
    Id   int64
    Name string
}
```

### 导出函数注释

```go
// ✅ 正确 - 导出函数必须有注释
// UserLogin 处理用户登录
// 参数 req 包含登录请求信息（用户名和密码）
// 返回登录成功的用户信息或错误
func UserLogin(req *LoginReq) (*User, error) {
    // 实现
}

// ❌ 错误 - 缺少注释
func UserLogin(req *LoginReq) (*User, error) {
    // 实现
}
```

## 文档最佳实践

### 文档更新

```go
// ✅ 正确 - 代码变更时同步更新注释
// Deprecated: 使用 NewUser 替代
// 将在 v2.0 版本中移除
func CreateUser(name string) *User {
    return &User{Name: name}
}

// NewUser 创建新用户
// 参数 name 是用户名
// 返回新创建的用户
func NewUser(name string) *User {
    return &User{Name: name}
}

// ❌ 错误 - 代码变更但注释未更新
// CreateUser 创建新用户
func CreateUser(name string) *User {
    return &User{Name: name}
}
```

### 文档清晰

```markdown
# ✅ 正确 - 清晰的文档
# 安装

使用以下命令安装项目：

```bash
go get github.com/username/project
```

# ❌ 错误 - 不清晰的文档
# 安装

你可以通过运行命令来安装这个项目，命令是 go get github.com/username/project，然后你就可以使用了。
```

## 检查清单

提交代码前，确保：

- [ ] 项目有 README.md
- [ ] README.md 包含项目描述、功能特性、快速开始
- [ ] 公开 API 有文档
- [ ] API 文档包含请求、响应、错误码
- [ ] 导出类型有注释
- [ ] 导出函数有注释
- [ ] 注释与代码一致
- [ ] 文档清晰易懂
- [ ] 文档无过时信息
- [ ] 代码变更时同步更新文档
