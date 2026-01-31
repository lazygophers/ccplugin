---
name: gorm-gen-skills
description: gorm-gen 代码生成工具开发规范和最佳实践
---

# gorm-gen 代码生成工具开发规范

## 工具概述

gorm-gen 是 GORM 官方提供的代码生成工具，通过代码生成实现类型安全的数据库操作，避免运行时反射开销。

**核心特点：**
- 类型安全的查询 API
- 零运行时反射开销
- 编译时类型检查
- DAO 模式代码生成
- 完全兼容 GORM
- 从数据库反向生成模型

## 与 raw GORM 对比

| 特性 | raw GORM | gorm-gen |
|------|----------|----------|
| 类型安全 | 运行时检查 | 编译时检查 |
| 反射开销 | 有 | 无 |
| API 风格 | 方法链 | 字段表达式 |
| 代码生成 | 无 | 自动生成 |
| 性能 | 中等 | 更高 |
| 学习曲线 | 低 | 中等 |
| 灵活性 | 高 | 中等 |

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|----------|
| [核心概念](core/core-concepts.md) | 架构、Field API、DAO 模式 | 工具入门 |
| [代码生成](generation/generation.md) | 配置、生成、自定义 | 项目初始化 |
| [查询 API](query/query.md) | 类型安全查询、条件构建 | 数据查询 |
| [高级功能](advanced/advanced.md) | 子查询、聚合、关联 | 复杂查询 |
| [性能对比](comparison/comparison.md) | 性能测试、基准 | 性能分析 |
| [最佳实践](best-practices/best-practices.md) | 项目结构、工作流 | 架构设计 |
| [参考资源](references.md) | 官方文档、教程 | 深入学习 |

## 快速开始

### 安装

```bash
go install gorm.io/gen/tools/gentool@latest
```

### 代码生成器

```go
// gen.go
package main

import (
    "gorm.io/driver/mysql"
    "gorm.io/gen"
)

func main() {
    g := gen.NewGenerator(gen.Config{
        OutPath: "./query",
        Mode:    gen.WithoutContext | gen.WithDefaultQuery,
    })

    gormDB, _ := gorm.Open(mysql.Open("user:pass@tcp(127.0.0.1:3306)/db"))
    g.UseDB(gormDB)

    // 生成模型
    g.ApplyBasic(
        g.GenerateModel("users"),
        g.GenerateModel("products"),
    )

    g.Execute()
}
```

### 运行生成

```bash
go run gen.go
```

### 使用生成的代码

```go
package main

import "query"

func main() {
    // 初始化
    q := query.Use(db)

    // 类型安全查询
    user, err := q.User.Where(
        q.User.Name.Eq("John"),
        q.User.Age.Gte(18),
    ).First()

    // 更新
    q.User.Where(q.User.ID.Eq(1)).Update(q.User.Name, "Jane")
}
```

## 核心概念

### Field API

gorm-gen 使用 Field API 实现类型安全查询：

```go
// 生成后的代码
type user struct {
    ID   field.Int32
    Name field.String
    Age  field.Int
}

// 使用
q.User.Where(q.User.Name.Eq("John")).First()
```

### DAO 模式

```go
// 每个表对应一个 query 对象
q := query.Use(db)

// user 表
user := q.User

// product 表
product := q.Product
```

### 表达式构建

```go
// Eq
q.User.Name.Eq("John")

// Neq
q.User.Age.Neq(18)

// Gte/Lte
q.User.Age.Gte(18)
q.User.Age.Lte(65)

// Like
q.User.Name.Like("%John%")

// In
q.User.ID.In(1, 2, 3)

// Between
q.User.Age.Between(18, 65)
```

## 代码生成

### 从数据库生成

```go
g.ApplyBasic(
    g.GenerateModel("users"),
    g.GenerateModel("products"),
    g.GenerateModel("orders"),
)
```

### 从结构体生成

```go
type User struct {
    ID   int64  `gorm:"column:id"`
    Name string `gorm:"column:name"`
}

g.ApplyBasic(g.GenerateModelAs(User{}, "users"))
```

### 字段映射

```go
g.GenerateModel("users",
    gen.FieldJSON("name", "userName"), // JSON 标签
    gen.FieldNewTag("age", `validate:"gte=18"`), // 新标签
)
```

## 查询示例

### 基础查询

```go
// SELECT * FROM users WHERE id = 1
user, err := q.User.Where(q.User.ID.Eq(1)).First()

// SELECT * FROM users WHERE age > 18
users, err := q.User.Where(q.User.Age.Gt(18)).Find()

// 条件组合
users, err := q.User.Where(
    q.User.Name.Eq("John"),
    q.User.Age.Gte(18),
).Find()
```

### 排序和分页

```go
// 排序
q.User.Order(q.User.Age.Desc()).Find()

// 分页
q.User.Limit(10).Offset(20).Find()
```

### 更新

```go
// 单字段更新
q.User.Where(q.User.ID.Eq(1)).Update(q.User.Name, "Jane")

// 多字段更新
q.User.Where(q.User.ID.Eq(1)).Updates(map[string]interface{}{
    "name": "Jane",
    "age":  30,
})
```

### 删除

```go
q.User.Where(q.User.ID.Eq(1)).Delete()
```

## 优势

1. **类型安全**：编译时检查字段类型
2. **性能优化**：零反射开销
3. **IDE 支持**：自动补全和重构
4. **可维护**：生成代码可读可维护
5. **渐进式**：可与 raw GORM 混用

## 注意事项

1. **代码生成**：需要运行生成器
2. **学习曲线**：需要了解 Field API
3. **灵活性**：某些高级功能不如 raw GORM
4. **维护成本**：模型变更需要重新生成

## 下一步

- 阅读 [核心概念](core/core-concepts.md) 了解 Field API
- 查看 [代码生成](generation/generation.md) 学习生成配置
- 参考 [最佳实践](best-practices/best-practices.md) 进行项目设计
- 访问 [官方文档](https://gorm.io/gen/) 获取更多信息
