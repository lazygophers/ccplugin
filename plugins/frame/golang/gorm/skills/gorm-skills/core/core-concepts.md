# 核心概念

## 模型定义

### 基础模型

GORM 模型是标准的 Go struct，用于表示数据库表。

```go
package models

import "gorm.io/gorm"

type User struct {
    ID        uint   `gorm:"primaryKey"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt gorm.DeletedAt `gorm:"index"`
    Name      string         `gorm:"size:255;not null"`
    Email     string         `gorm:"size:255;uniqueIndex"`
}
```

### 字段标签

**结构体标签**：`gorm:"标签内容"`

| 标签 | 说明 | 示例 |
|------|------|------|
| `column` | 列名 | `gorm:"column:user_name"` |
| `type` | 列类型 | `gorm:"type:varchar(100)"` |
| `size` | 列大小 | `gorm:"size:255"` |
| `primaryKey` | 主键 | `gorm:"primaryKey"` |
| `autoIncrement` | 自增 | `gorm:"autoIncrement"` |
| `not null` | 非空 | `gorm:"not null"` |
| `unique` | 唯一 | `gorm:"unique"` |
| `index` | 索引 | `gorm:"index"` |
| `uniqueIndex` | 唯一索引 | `gorm:"uniqueIndex"` |
| `default` | 默认值 | `gorm:"default:0"` |
| `comment` | 注释 | `gorm:"comment:用户名"` |
| `check` | 约束 | `gorm:"check:age >= 18"` |
| `-` | 忽略字段 | `gorm:"-"` |

### 嵌入结构

```go
type BaseModel struct {
    ID        uint           `gorm:"primaryKey"`
    CreatedAt time.Time
    UpdatedAt time.Time
    DeletedAt gorm.DeletedAt `gorm:"index"`
}

type User struct {
    BaseModel
    Name  string
    Email string
}

type Product struct {
    BaseModel
    Name  string
    Price float64
}
```

## 连接数据库

### MySQL

```go
import (
    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

dsn := "user:pass@tcp(127.0.0.1:3306)/dbname?charset=utf8mb4&parseTime=True&loc=Local"
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
```

### PostgreSQL

```go
import (
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
)

dsn := "host=localhost user=gorm password=gorm dbname=gorm port=9920 sslmode=disable TimeZone=Asia/Shanghai"
db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
```

### SQLite

```go
import (
    "gorm.io/driver/sqlite"
    "gorm.io/gorm"
)

db, err := gorm.Open(sqlite.Open("test.db"), &gorm.Config{})
```

### 连接池配置

```go
sqlDB, err := db.DB()
sqlDB.SetMaxIdleConns(10)
sqlDB.SetMaxOpenConns(100)
sqlDB.SetConnMaxLifetime(time.Hour)
```

## CRUD 操作

### 创建

```go
// 单条创建
user := User{Name: "John", Email: "john@example.com"}
db.Create(&user)

// 批量创建
users := []User{
    {Name: "John", Email: "john@example.com"},
    {Name: "Jane", Email: "jane@example.com"},
}
db.Create(&users)

// CreateInBatches
db.CreateInBatches(users, 100)
```

### 查询

```go
// 查询单条
var user User
db.First(&user, 1)              // SELECT * FROM users WHERE id = 1
db.First(&user, "name = ?", "John")

// 查询多条
var users []User
db.Find(&users)                 // SELECT * FROM users
db.Where("age > ?", 18).Find(&users)

// 条件查询
db.Where("name = ?", "John").First(&user)
db.Where(&User{Name: "John"}).First(&user)

// 获取第一条记录（不考虑顺序）
db.Take(&user)

// 获取最后一条记录
db.Last(&user)
```

### 更新

```go
// 更新单个字段
db.Model(&user).Update("name", "Jane")

// 更新多个字段
db.Model(&user).Updates(User{Name: "Jane", Age: 30})
db.Model(&user).Updates(map[string]interface{}{"name": "Jane", "age": 30})

// 更新所有记录
db.Model(&User{}).Update("active", true)

// 更新选定字段
db.Model(&user).Select("name").Updates(User{Name: "Jane", Age: 30})
db.Model(&user).Omit("name").Updates(User{Name: "Jane", Age: 30})
```

### 删除

```go
// 删除记录
db.Delete(&user)              // 软删除（设置 deleted_at）
db.Unscoped().Delete(&user)   // 硬删除

// 批量删除
db.Where("age < ?", 18).Delete(&User{})

// 根据主键删除
db.Delete(&User{}, 1)
db.Delete(&User{}, []int{1, 2, 3})
```

## 命名策略

```go
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    NamingStrategy: schema.NamingStrategy{
        TablePrefix:   "tbl_",     // 表前缀
        SingularTable: true,        // 单数表名
        NoLowerCase:   false,       // 不转小写
    },
})
```

## 时间戳

```go
type User struct {
    CreatedAt time.Time      // 创建时间
    UpdatedAt time.Time      // 更新时间
    DeletedAt gorm.DeletedAt // 软删除时间
}

// 禁用跟踪
db.AutoMigrate(&User{})
db.Model(&User{}).Where("id = ?", 1).Update("updated_at", time.Now())
```
