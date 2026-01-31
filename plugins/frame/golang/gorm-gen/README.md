# gorm-gen-skills - GORM 代码生成工具插件

提供类型安全的 GORM 代码生成规范、最佳实践和开发指南。包括代码生成、类型安全查询 API、DAO 模式和性能优化。

## 特性

- 🔒 **类型安全** - 编译时类型检查，避免运行时错误
- ⚡ **零反射** - 无运行时反射开销，性能更优
- 🔨 **代码生成** - 从数据库自动生成模型和查询代码
- 🎯 **Field API** - 类型安全的字段表达式
- 📦 **DAO 模式** - 自动生成数据访问对象
- 🔍 **查询构建** - 链式查询、条件组合、子查询
- 📊 **性能优化** - 比原生 GORM 快 20-25%
- 🧪 **测试友好** - 支持单元测试和集成测试
- 📚 **最佳实践** - 项目结构、工作流、迁移指南

## 与 raw GORM 对比

| 特性 | raw GORM | gorm-gen-skills |
|------|----------|----------|
| 类型安全 | 运行时检查 | 编译时检查 |
| 反射开销 | 有 | 无 |
| API 风格 | 方法链 | 字段表达式 |
| 代码生成 | 无 | 自动生成 |
| 性能 | 中等 | 更高（+20-25%） |
| 学习曲线 | 低 | 中等 |

## 技术栈

- **gorm/gen** v0.5+ - GORM 官方代码生成工具
- **Go** 1.22+ - 编译器版本要求

## 文档结构

```
skills/gormgen/
├── SKILL.md                      # 主入口 - 快速导航
├── core/
│   └── core-concepts.md          # 核心概念 - Field API、DAO 模式
├── generation/
│   └── generation.md             # 代码生成 - 配置、自定义
├── query/
│   └── query.md                  # 查询 API - 类型安全查询
├── advanced/
│   └── advanced.md               # 高级功能 - 子查询、聚合、关联
├── comparison/
│   └── comparison.md             # 性能对比 - 基准测试
├── best-practices/
│   └── best-practices.md         # 最佳实践 - 项目结构、工作流
└── references.md                 # 参考资源 - 官方文档、教程
```

## 快速开始

### 安装工具

```bash
go install gorm.io/gen/tools/gentool@latest
```

### 创建生成器

```go
// gen/gen.go
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

    gormDB, _ := gorm.Open(mysql.Open("dsn"))
    g.UseDB(gormDB)

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
import "query"

q := query.Use(db)

// 类型安全查询
user, err := q.User.Where(
    q.User.Name.Eq("John"),
    q.User.Age.Gte(18),
).First()

// 更新
q.User.Where(q.User.ID.Eq(1)).
    Update(q.User.Name, "Jane")
```

## Field API

### 字段方法

```go
// 比较方法
q.User.Name.Eq("John")      // =
q.User.Age.Neq(18)          // !=
q.User.Age.Gt(18)           // >
q.User.Age.Gte(18)          // >=
q.User.Age.Lt(65)           // <
q.User.Age.Lte(65)          // <=

// 字符串方法
q.User.Name.Like("%Jo%")    // LIKE
q.User.ID.In(1, 2, 3)       // IN

// 空值检查
q.User.Email.IsNull()
q.User.Email.IsNotNull()
```

### 条件组合

```go
// AND（默认）
q.User.Where(
    q.User.Name.Eq("John"),
    q.User.Age.Gte(18),
)

// OR
q.User.Where(
    q.User.Name.Eq("John"),
).Or(
    q.User.Name.Eq("Jane"),
)

// NOT
q.User.Not(q.User.Age.Lt(18))
```

## 高级功能

### 子查询

```go
// 子查询
subQuery := q.Order.Select(
    q.Order.UserID,
).Where(
    q.Order.Amount.Gte(1000),
)

// IN 子查询
users, err := q.User.Where(
    q.User.ID.In(subQuery),
).Find()
```

### 聚合查询

```go
// Group By
result, err := q.User.Select(
    q.User.Age,
    q.User.ID.Count().As("count"),
).Group(
    q.User.Age,
).Find()

// Having
result, err := q.User.Select(
    q.User.Age,
    q.User.ID.Count().As("count"),
).Group(
    q.User.Age,
).Having(
    q.User.ID.Count().Gte(10),
).Find()
```

### 关联查询

```go
// 预加载
users, err := q.User.Destination(
    &users,
).Relation(
    q.User.Posts,
).Find()

// 条件预加载
users, err := q.User.Relation(
    q.User.Posts.Where(
        q.Post.Published.Is(true),
    ),
).Find()
```

## 性能优化

### 批量操作

```go
// 批量创建
q.User.CreateInBatches(users, 100)

// 批量更新
q.User.Where(
    q.User.ID.In(ids...),
).Update(
    q.User.Status,
    "active",
)
```

### 选择字段

```go
// 只查询需要的字段
q.User.Select(
    q.User.ID,
    q.User.Name,
).Find()
```

## 项目结构

### 推荐结构

```
project/
├── gen/              # 代码生成器
│   └── gen.go
├── query/            # 生成的查询代码（不要修改）
│   ├── gen.go
│   ├── user.gen.go
│   └── ...
├── model/            # 模型定义
│   └── user.go
├── repository/       # 数据访问层
│   └── user_repo.go
└── service/          # 业务逻辑层
    └── user_service.go
```

## 目录结构

```
plugins/frame/golang/gorm-gen/
├── .claude-plugin/
│   └── plugin.json                # 插件元数据
├── AGENT.md                       # 行为规范
├── hooks/
│   └── hooks.json                 # Hook 配置
├── scripts/
│   ├── __init__.py                # Python 包
│   ├── main.py                    # CLI 入口
│   └── hooks.py                   # Hook 处理
├── skills/gormgen/                # Skills 文档
│   ├── SKILL.md
│   ├── core/
│   ├── generation/
│   ├── query/
│   ├── advanced/
│   ├── comparison/
│   └── best-practices/
└── README.md                      # 本文件
```

## 参考资源

- [GORM Gen 官方文档](https://gorm.io/gen/)
- [GORM Gen GitHub](https://github.com/go-gorm/gen)
- [GORM 官方文档](https://gorm.io/)

## 许可证

AGPL-3.0-or-later
