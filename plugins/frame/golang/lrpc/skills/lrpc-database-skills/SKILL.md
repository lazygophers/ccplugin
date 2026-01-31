---
name: lrpc-database-skills
description: lrpc database 数据库访问层规范 - 提供统一的数据库访问抽象，支持 MySQL、PostgreSQL、SQLite 等关系型数据库
---

# lrpc-database - 数据库访问层

提供统一的数据库访问抽象层，支持多种关系型数据库，简化数据库操作和管理。

## 特性

- 📦 **统一接口** - 一套 API 支持多种数据库
- 🔄 **连接池管理** - 自动管理数据库连接
- 🔍 **查询构建器** - 类型安全的查询构建
- 🏷️ **事务支持** - 嵌套事务、SavePoint
- 📊 **分页查询** - 自动处理分页逻辑
- 🛡️ **SQL 注入防护** - 参数化查询
- 🎯 **模型映射** - 自动映射结构体

## 支持的数据库

| 数据库 | 驱动 | 标识 |
|--------|------|------|
| MySQL | `mysql` | `mysql` |
| PostgreSQL | `pq` / `pgx` | `postgres` |
| SQLite | `sqlite3` | `sqlite` |
| SQL Server | `mssql` | `sqlserver` |
| TiDB | `mysql` | `tidb` |

## 基础使用

### 初始化数据库连接

```go
import (
    "github.com/lazygophers/lrpc/middleware/storage/db"
)

// MySQL 连接
db, err := database.New(database.Config{
    Type:     "mysql",
    Host:     "localhost",
    Port:     3306,
    Database: "mydb",
    Username: "user",
    Password: "pass",
    Charset:  "utf8mb4",
    ParseTime: true,
    Loc:      time.Local,
})

// PostgreSQL 连接
db, err := database.New(database.Config{
    Type:     "postgres",
    Host:     "localhost",
    Port:     5432,
    Database: "mydb",
    Username: "user",
    Password: "pass",
    SSLMode:  "disable",
})

// SQLite 连接
db, err := database.New(database.Config{
    Type: "sqlite",
    DSN:  "./data.db",
})
```

### 连接池配置

```go
db, err := database.New(database.Config{
    Type:     "mysql",
    Host:     "localhost",
    Port:     3306,
    Database: "mydb",
    Username: "user",
    Password: "pass",
    // 连接池配置
    MaxOpenConns:    100,  // 最大打开连接数
    MaxIdleConns:    10,   // 最大空闲连接数
    ConnMaxLifetime: time.Hour,  // 连接最大存活时间
    ConnMaxIdleTime: time.Minute * 10,  // 连接最大空闲时间
})
```

### 注册中间件

```go
server := lrpc.NewServer()

// 创建数据库中间件
dbMiddleware := database.NewMiddleware(db)
server.Use(dbMiddleware)

// 在 Handler 中使用数据库
func Handler(ctx *lrpc.Context, db *database.DB) error {
    var users []User
    err := db.Find(&users).Error
    if err != nil {
        return err
    }
    return ctx.JSON(users)
}
```

## 查询操作

### 简单查询

```go
// 查询单条记录
var user User
err := db.Where("id = ?", 1).First(&user).Error

// 查询多条记录
var users []User
err := db.Where("age > ?", 18).Find(&users).Error

// 查询并排序
err := db.Order("created_at DESC").Find(&users).Error

// 限制数量
err := db.Limit(10).Find(&users).Error

// 偏移量
err := db.Offset(20).Limit(10).Find(&users).Error
```

### 条件查询

```go
// AND 条件
db.Where("age > ?", 18).
   Where("status = ?", "active").
   Find(&users)

// OR 条件
db.Where("age > ?", 18).
   Or("age < ?", 10).
   Find(&users)

// IN 查询
db.Where("id IN ?", []int{1, 2, 3}).Find(&users)

// NOT 查询
db.Not("status = ?", "deleted").Find(&users)

// BETWEEN
db.Where("age BETWEEN ? AND ?", 18, 65).Find(&users)
```

### 复杂查询

```go
// 链式查询
query := db.Model(&User{}).
    Where("age > ?", 18).
    Where("status = ?", "active")

// 动态添加条件
if name != "" {
    query = query.Where("name LIKE ?", "%"+name+"%")
}

if minAge > 0 {
    query = query.Where("age >= ?", minAge)
}

// 执行查询
err := query.Find(&users).Error
```

## 插入操作

### 单条插入

```go
user := User{
    Name:  "John",
    Email: "john@example.com",
    Age:   30,
}

err := db.Create(&user).Error
// user.ID 现在包含自增 ID
```

### 批量插入

```go
users := []User{
    {Name: "John", Email: "john@example.com"},
    {Name: "Jane", Email: "jane@example.com"},
    {Name: "Bob", Email: "bob@example.com"},
}

// 批量插入（单条 SQL）
err := db.Create(&users).Error

// 分批插入（每批 100 条）
err := db.CreateInBatches(users, 100).Error
```

### 忽略字段

```go
// 使用 omitempty 忽略零值
db.Omit("").Create(&user)

// 选择字段插入
db.Select("name", "email").Create(&user)

// 排除字段
db.Omit("age", "status").Create(&user)
```

## 更新操作

### 更新单条记录

```go
// 先查询再更新
var user User
db.First(&user, 1)

user.Name = "Jane"
user.Age = 25
err := db.Save(&user).Error

// 直接更新
err := db.Model(&User{}).
    Where("id = ?", 1).
    Update("name", "Jane").
    Error
```

### 更新多条字段

```go
// 使用 map 更新
err := db.Model(&User{}).
    Where("id = ?", 1).
    Updates(map[string]interface{}{
        "name": "Jane",
        "age":  25,
    }).
    Error

// 使用结构体更新
err := db.Model(&User{}).
    Where("id = ?", 1).
    Updates(User{Name: "Jane", Age: 25}).
    Error
```

### 批量更新

```go
// 更新所有匹配的记录
err := db.Model(&User{}).
    Where("status = ?", "inactive").
    Update("status", "active").
    Error

// 更新表达式
err := db.Model(&User{}).
    Where("id = ?", 1).
    Update("age", gorm.Expr("age + ?", 1)).
    Error
```

## 删除操作

### 删除单条记录

```go
// 先查询再删除
var user User
db.First(&user, 1)
err := db.Delete(&user).Error

// 直接删除
err := db.Where("id = ?", 1).Delete(&User{}).Error
```

### 批量删除

```go
// 删除所有匹配的记录
err := db.Where("status = ?", "deleted").
    Delete(&User{}).
    Error

// 使用主键删除
err := db.Delete(&User{}, []int{1, 2, 3}).Error
```

### 软删除

```go
type User struct {
    ID        uint
    Name      string
    DeletedAt gorm.DeletedAt `gorm:"index"`
}

// 软删除（设置 deleted_at）
db.Delete(&user)

// 查询时排除已删除记录
db.Where("age > ?", 18).Find(&users)

// 包含已删除记录
db.Unscoped().Find(&users)

// 永久删除
db.Unscoped().Delete(&user)
```

## 事务处理

### 自动事务

```go
err := db.Transaction(func(tx *database.DB) error {
    // 创建用户
    if err := tx.Create(&user).Error; err != nil {
        return err  // 回滚
    }

    // 创建用户配置
    if err := tx.Create(&config).Error; err != nil {
        return err  // 回滚
    }

    return nil  // 提交
})
```

### 手动事务

```go
// 开始事务
tx := db.Begin()

// 执行操作
if err := tx.Create(&user).Error; err != nil {
    tx.Rollback()  // 回滚
    return err
}

if err := tx.Create(&config).Error; err != nil {
    tx.Rollback()  // 回滚
    return err
}

// 提交事务
tx.Commit()
```

### SavePoint

```go
err := db.Transaction(func(tx *database.DB) error {
    if err := tx.Create(&user).Error; err != nil {
        return err
    }

    // 创建 SavePoint
    tx.SavePoint("sp1")

    if err := tx.Create(&order).Error; err != nil {
        tx.RollbackTo("sp1")  // 回滚到 SavePoint
        // 可以继续操作
    }

    return nil
})
```

## 分页查询

### 基础分页

```go
type PageResult struct {
    Total int64       `json:"total"`
    Page  int         `json:"page"`
    Size  int         `json:"size"`
    Data  interface{} `json:"data"`
}

func GetUsers(db *database.DB, page, size int) (*PageResult, error) {
    var users []User
    var total int64

    // 查询总数
    if err := db.Model(&User{}).Count(&total).Error; err != nil {
        return nil, err
    }

    // 查询数据
    offset := (page - 1) * size
    if err := db.Offset(offset).Limit(size).Find(&users).Error; err != nil {
        return nil, err
    }

    return &PageResult{
        Total: total,
        Page:  page,
        Size:  size,
        Data:  users,
    }, nil
}
```

### 分页中间件

```go
// 使用分页辅助函数
func ListUsers(ctx *lrpc.Context, db *database.DB) error {
    page := ctx.QueryArgs().GetUintOrZero("page")
    size := ctx.QueryArgs().GetUintOrZero("size")

    if page == 0 {
        page = 1
    }
    if size == 0 {
        size = 10
    }
    if size > 100 {
        size = 100  // 最大每页 100 条
    }

    result, err := database.Paginate(db.Model(&User{}), page, size, &users)
    if err != nil {
        return err
    }

    return ctx.JSON(result)
}
```

## 原生 SQL

### 查询

```go
// 查询到结构体
var users []User
db.Raw("SELECT * FROM users WHERE age > ?", 18).Scan(&users)

// 查询到 map
var results []map[string]interface{}
db.Raw("SELECT name, age FROM users").Scan(&results)

// 查询单个值
var count int
db.Raw("SELECT COUNT(*) FROM users").Scan(&count)
```

### 执行

```go
// 执行 SQL
db.Exec("UPDATE users SET status = ? WHERE age < ?", "inactive", 18)

// 执行并获取结果
result := db.Exec("DELETE FROM users WHERE id = ?", 1)
rowsAffected := result.RowsAffected()
```

## 命名策略

### 自定义表名

```go
type User struct {
    ID   uint
    Name string
}

// 默认表名为 "users"
// 自定义表名
func (User) TableName() string {
    return "sys_users"
}
```

### 字段映射

```go
type User struct {
    ID        uint
    Name      string `gorm:"column:user_name"`
    Email     string `gorm:"column:email_address"`
    CreatedAt time.Time `gorm:"column:created_time"`
}
```

## 最佳实践

### 1. 使用事务

```go
// ✅ 相关操作放在事务中
err := db.Transaction(func(tx *database.DB) error {
    // 创建用户
    if err := tx.Create(&user).Error; err != nil {
        return err
    }
    // 创建配置
    if err := tx.Create(&config).Error; err != nil {
        return err
    }
    return nil
})

// ❌ 分散的操作没有事务保护
db.Create(&user)
db.Create(&config)
```

### 2. 错误处理

```go
// ✅ 检查错误
if err := db.Find(&users).Error; err != nil {
    log.Error("query failed", log.Field("error", err))
    return err
}

// ❌ 忽略错误
db.Find(&users)
```

### 3. 使用上下文

```go
// ✅ 带超时的查询
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

err := db.WithContext(ctx).Find(&users).Error

// ❌ 没有超时控制
err := db.Find(&users).Error
```

### 4. 预加载关联

```go
// ❌ N+1 查询问题
users := []User{}
db.Find(&users)
for _, user := range users {
    db.Model(&user).Association("Orders").Find(&orders)
}

// ✅ 预加载
db.Preload("Orders").Find(&users)
```

## 参考资源

- [lazygophers/lrpc database](https://github.com/lazygophers/lrpc/tree/master/middleware/storage/db)
- [Go database/sql](https://pkg.go.dev/database/sql)
- [MySQL 驱动](https://github.com/go-sql-driver/mysql)
- [PostgreSQL 驱动](https://github.com/lib/pq)
- [SQLite 驱动](https://github.com/mattn/go-sqlite3)
