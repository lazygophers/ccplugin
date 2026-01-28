---
name: gorm
description: GORM ORM 库开发规范和最佳实践
---

# GORM ORM 库开发规范

## 框架概述

GORM 是 Go 语言最流行的 ORM 库，提供友好的 API、完整的关联支持和丰富的扩展能力。

**核心特点：**
- 全功能 ORM
- 关联关系（一对一、一对多、多对多、多态）
- 钩子函数（Before/After Create/Save/Update/Delete/Find）
- 预加载（Eager Loading）
- 事务支持
- 多数据库支持（MySQL、PostgreSQL、SQLite、SQL Server）
- 自动迁移
- 内置日志

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|----------|
| [核心概念](core/core-concepts.md) | 模型定义、连接、CRUD | 框架入门 |
| [关联关系](associations/associations.md) | 一对一、一对多、多对多、预加载 | 关联设计 |
| [查询构建](query/query.md) | Where、链式查询、子查询、原生 SQL | 数据查询 |
| [事务处理](transactions/transactions.md) | 事务、嵌套事务、回滚 | 数据一致性 |
| [迁移管理](migrations/migrations.md) | AutoMigrate、版本控制 | 数据库演进 |
| [钩子函数](hooks/hooks.md) | Before/After 钩子 | 业务逻辑 |
| [性能优化](performance/performance.md) | N+1 问题、批量操作、索引 | 性能调优 |
| [测试](testing/testing.md) | 单元测试、集成测试 | 质量保证 |
| [最佳实践](best-practices/best-practices.md) | 项目结构、错误处理、命名 | 架构设计 |
| [参考资源](references.md) | 官方文档、教程 | 深入学习 |

## 快速开始

### 模型定义

```go
package models

import "time"

type User struct {
    ID        uint           `gorm:"primaryKey"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt gorm.DeletedAt `gorm:"index"`
    Name      string         `gorm:"size:255;not null"`
    Email     string         `gorm:"size:255;uniqueIndex;not null"`
    Age       int            `gorm:"index"`
    Active    bool           `gorm:"default:true"`
}

// 设置表名
func (User) TableName() string {
    return "users"
}
```

### 连接数据库

```go
import (
    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

dsn := "user:pass@tcp(127.0.0.1:3306)/dbname?charset=utf8mb4&parseTime=True&loc=Local"
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    Logger: logger.Default.LogMode(logger.Info),
    SkipDefaultTransaction: false,
    PrepareStmt: true,
})
```

### CRUD 操作

```go
// 创建
user := User{Name: "John", Email: "john@example.com"}
db.Create(&user)

// 查询
var user User
db.First(&user, 1)
db.Where("email = ?", "john@example.com").First(&user)

// 更新
db.Model(&user).Update("name", "Jane")
db.Model(&user).Updates(User{Name: "Jane", Age: 30})

// 删除
db.Delete(&user)
```

## 核心概念

### 模型标签

```go
type User struct {
    ID        uint   `gorm:"primaryKey"`
    Name      string `gorm:"column:name;type:varchar(100);not null"`
    Email     string `gorm:"uniqueIndex:idx_email"`
    Age       int    `gorm:"index:idx_age"`
    CreatedAt time.Time
}
```

**常用标签**：
- `primaryKey` - 主键
- `autoIncrement` - 自增
- `column:name` - 列名
- `type:varchar(100)` - 类型
- `not null` - 非空
- `unique` - 唯一
- `index` - 索引
- `uniqueIndex` - 唯一索引
- `default:value` - 默认值
- `comment:text` - 注释

### 命名约定

GORM 使用 `NamingStrategy` 转换名称：

```go
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    NamingStrategy: schema.NamingStrategy{
        TablePrefix:   "tbl_",
        SingularTable: true,
        NoLowerCase:   false,
    },
})
```

**默认规则**：
- 结构体 → 蛇形表名（User → users）
- 字段 → 蛇形列名（UserName → user_name）
- ID → id（主键）

## 关联关系

### 一对一（Has One）

```go
type User struct {
    ID    uint
    Profile Profile
}

type Profile struct {
    ID     uint
    UserID uint
    Bio    string
}
```

### 一对多（Has Many）

```go
type User struct {
    ID    uint
    Posts []Post
}

type Post struct {
    ID     uint
    UserID uint
    Title  string
}
```

### 多对多（Many To Many）

```go
type User struct {
    ID    uint
    Languages []Language `gorm:"many2many:user_languages;"`
}

type Language struct {
    ID   uint
    Name string
}
```

详见 [关联关系](associations/associations.md)。

## 查询构建

```go
// Where 条件
db.Where("name = ?", "John").Find(&users)
db.Where("age >= ? AND age <= ?", 18, 65).Find(&users)
db.Where(&User{Name: "John"}).First(&user)

// 链式查询
db.Where("age > ?", 18).Order("age DESC").Limit(10).Find(&users)

// Or 条件
db.Where("role = ?", "admin").Or("role = ?", "super_admin").Find(&users)

// Not 条件
db.Not("name = ?", "John").Find(&users)

// In 查询
db.Where("id IN ?", []int{1, 2, 3}).Find(&users)

// Like 查询
db.Where("name LIKE ?", "%John%").Find(&users)

// 子查询
subQuery := db.Select(" AVG(age)").From("users")
db.Where("age > (?)", subQuery).Find(&users)
```

详见 [查询构建](query/query.md)。

## 事务处理

```go
// 自动事务
db.Transaction(func(tx *gorm.DB) error {
    if err := tx.Create(&User{Name: "John"}).Error; err != nil {
        return err // 回滚
    }
    if err := tx.Create(&Post{Title: "Hello"}).Error; err != nil {
        return err // 回滚
    }
    return nil // 提交
})

// 手动事务
tx := db.Begin()
if err := tx.Create(&user).Error; err != nil {
    tx.Rollback()
    return
}
tx.Commit()
```

详见 [事务处理](transactions/transactions.md)。

## 钩子函数

```go
func (u *User) BeforeCreate(tx *gorm.DB) error {
    // 创建前验证
    if u.Name == "" {
        return errors.New("name cannot be empty")
    }
    return nil
}

func (u *User) AfterCreate(tx *gorm.DB) error {
    // 创建后操作
    return nil
}
```

详见 [钩子函数](hooks/hooks.md)。

## 性能优化

### 预加载（解决 N+1 问题）

```go
// ❌ N+1 查询
users := []User{}
db.Find(&users)
for _, user := range users {
    db.Model(&user).Association("Posts").Find(&user.Posts)
}

// ✅ 预加载
db.Preload("Posts").Find(&users)

// ✅ 嵌套预加载
db.Preload("Posts.Comments").Find(&users)
```

### 批量操作

```go
// 批量创建
var users []User
db.CreateInBatches(users, 100)

// 批量更新
db.Model(&User{}).Where("active = ?", true).Update("verified", true)
```

详见 [性能优化](performance/performance.md)。

## 注意事项

1. **N+1 查询问题**：使用 Preload 预加载关联
2. **软删除**：使用 DeletedAt gorm.DeletedAt
3. **事务范围**：保持事务简短
4. **连接池**：合理配置最大连接数
5. **时间处理**：使用 parseTime=True 参数
6. **日志记录**：生产环境关闭 SQL 日志

## 下一步

- 阅读 [核心概念](core/core-concepts.md) 了解模型定义
- 查看 [关联关系](associations/associations.md) 学习关系设计
- 参考 [最佳实践](best-practices/best-practices.md) 进行架构设计
- 访问 [官方文档](https://gorm.io/) 获取更多信息
