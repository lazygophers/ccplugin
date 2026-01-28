# GORM - Go ORM 库插件

提供完整的 GORM ORM 开发规范、最佳实践和代码智能支持。包括模型定义、关联关系、查询构建、事务处理、迁移管理和性能优化。

## 特性

- 📊 **完整 ORM 支持** - 模型定义、关联关系、CRUD 操作
- 🔗 **关联关系** - 一对一、一对多、多对多、多态关联
- 🔍 **查询构建器** - 链式查询、子查询、原生 SQL
- 🔄 **事务处理** - 自动事务、嵌套事务、SavePoint
- 📦 **迁移管理** - AutoMigrate、版本控制
- 🪝 **钩子函数** - Before/After 钩子
- ⚡ **性能优化** - N+1 问题解决、批量操作、连接池
- 🧪 **测试支持** - 单元测试、集成测试、Mock
- 📚 **最佳实践** - 项目结构、错误处理、命名约定

## 技术栈

- **GORM** v1.25+ - Go 语言最流行的 ORM 库
- **数据库支持**: MySQL、PostgreSQL、SQLite、SQL Server

## 文档结构

```
skills/gorm/
├── SKILL.md                      # 主入口 - 快速导航
├── core/
│   └── core-concepts.md          # 核心概念 - 模型、连接、CRUD
├── associations/
│   └── associations.md           # 关联关系 - 一对一、一对多、多对多
├── query/
│   └── query.md                  # 查询构建 - Where、链式、子查询
├── transactions/
│   └── transactions.md           # 事务处理 - 自动事务、嵌套事务
├── migrations/
│   └── migrations.md             # 迁移管理 - AutoMigrate、版本控制
├── hooks/
│   └── hooks.md                  # 钩子函数 - Before/After 钩子
├── performance/
│   └── performance.md            # 性能优化 - N+1、批量、索引
├── testing/
│   └── testing.md                # 测试 - 单元测试、集成测试
├── best-practices/
│   └── best-practices.md         # 最佳实践 - 项目结构、错误处理
└── references.md                 # 参考资源 - 官方文档、教程
```

## 快速开始

### 模型定义

```go
type User struct {
    ID        uint           `gorm:"primaryKey"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt gorm.DeletedAt `gorm:"index"`
    Name      string         `gorm:"size:255;not null"`
    Email     string         `gorm:"size:255;uniqueIndex"`
    Age       int            `gorm:"index"`
}
```

### 连接数据库

```go
import (
    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

dsn := "user:pass@tcp(127.0.0.1:3306)/dbname?charset=utf8mb4&parseTime=True&loc=Local"
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
```

### CRUD 操作

```go
// 创建
user := User{Name: "John", Email: "john@example.com"}
db.Create(&user)

// 查询
var user User
db.First(&user, 1)

// 更新
db.Model(&user).Update("name", "Jane")

// 删除
db.Delete(&user)
```

## 关联关系

### 一对一（Has One）

```go
type User struct {
    ID      uint
    Profile Profile `gorm:"foreignKey:UserID"`
}
```

### 一对多（Has Many）

```go
type User struct {
    ID    uint
    Posts []Post `gorm:"foreignKey:UserID"`
}
```

### 多对多（Many To Many）

```go
type User struct {
    ID        uint
    Languages []Language `gorm:"many2many:user_languages;"`
}
```

## 查询构建

```go
// Where 条件
db.Where("name = ?", "John").First(&user)
db.Where("age >= ?", 18).Find(&users)

// 链式查询
db.Where("age > ?", 18).
    Order("age DESC").
    Limit(10).
    Find(&users)

// 预加载（解决 N+1）
db.Preload("Posts").Find(&users)
```

## 事务处理

```go
// 自动事务
db.Transaction(func(tx *gorm.DB) error {
    if err := tx.Create(&User{Name: "John"}).Error; err != nil {
        return err // 回滚
    }
    return nil // 提交
})

// 手动事务
tx := db.Begin()
tx.Create(&user)
tx.Commit()
```

## 性能优化

### 预加载

```go
// ❌ N+1 查询
users := []User{}
db.Find(&users)
for _, user := range users {
    db.Model(&user).Association("Posts").Find(&user.Posts)
}

// ✅ 预加载
db.Preload("Posts").Find(&users)
```

### 批量操作

```go
// 批量创建
db.CreateInBatches(users, 100)

// 批量更新
db.Model(&User{}).Where("active = ?", true).
    Update("verified", true)
```

## 测试

### 单元测试

```go
func TestUserCreate(t *testing.T) {
    db, _ := gorm.Open(sqlite.Open("file::memory:"), &gorm.Config{})
    db.AutoMigrate(&User{})

    user := User{Name: "John"}
    err := db.Create(&user).Error
    if err != nil {
        t.Errorf("Failed to create user: %v", err)
    }
}
```

## 目录结构

```
plugins/frame/golang/gorm/
├── .claude-plugin/
│   └── plugin.json                # 插件元数据
├── AGENT.md                       # 行为规范
├── hooks/
│   └── hooks.json                 # Hook 配置
├── scripts/
│   ├── __init__.py                # Python 包
│   ├── main.py                    # CLI 入口
│   └── hooks.py                   # Hook 处理
├── skills/gorm/                   # Skills 文档
│   ├── SKILL.md
│   ├── core/
│   ├── associations/
│   ├── query/
│   ├── transactions/
│   ├── migrations/
│   ├── hooks/
│   ├── performance/
│   ├── testing/
│   └── best-practices/
└── README.md                      # 本文件
```

## 参考资源

- [GORM 官方文档](https://gorm.io/)
- [GORM GitHub](https://github.com/go-gorm/gorm)
- [GORM 中文文档](https://gorm.io/zh_CN/docs/)

## 许可证

AGPL-3.0-or-later
