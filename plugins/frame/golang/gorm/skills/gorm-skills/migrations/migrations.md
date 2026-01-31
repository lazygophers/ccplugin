# 迁移管理

## AutoMigrate

### 基础使用

```go
// 自动迁移
db.AutoMigrate(&User{})
db.AutoMigrate(&User{}, &Product{}, &Order{})

// 指定表名
db.Table("users").AutoMigrate(&User{})
```

### 迁移规则

- **创建表**：表不存在时创建
- **添加列**：新字段不存在时添加
- **添加索引**：新索引不存在时添加
- **不删除**：不会删除未使用的列
- **不修改**：不会修改列类型

## 列定义

### 类型映射

| Go 类型 | MySQL | PostgreSQL |
|---------|-------|------------|
| uint/uint8/uint16/uint32/uint64 | int/unsigned bigint | serial/bigserial |
| int/int8/int16/int32/int64 | int/bigint | integer/bigint |
| string | varchar(255) | varchar(255) |
| time.Time | datetime | timestamptz |
| bool | tinyint(1) | boolean |
| float64 | double | double precision |
| []byte | varbinary(255) | bytea |

### 自定义类型

```go
type User struct {
    ID      uint
    Name    string `gorm:"type:varchar(100)"`
    Balance float64 `gorm:"type:decimal(10,2)"`
    JSON    Data   `gorm:"type:json"`
}

type Data map[string]interface{}
```

## 约束

### 主键

```go
type User struct {
    ID uint `gorm:"primaryKey"`
    // 或
    ID uint `gorm:"primarykey"`
}

// 复合主键
type Product struct {
    LanguageID uint `gorm:"primaryKey"`
    CategoryID uint `gorm:"primaryKey"`
}
```

### 外键

```go
type User struct {
    ID    uint
    Posts []Post `gorm:"constraint:OnDelete:CASCADE;"`
}

type Post struct {
    ID     uint
    UserID uint
    User   User `gorm:"foreignKey:UserID"`
}

// 外键约束
// OnDelete: CASCADE, SET NULL, SET DEFAULT, RESTRICT, NO ACTION
// OnUpdate: CASCADE, SET NULL, SET DEFAULT, RESTRICT, NO ACTION
```

### 唯一约束

```go
type User struct {
    ID    uint
    Email string `gorm:"uniqueIndex"`
    Phone string `gorm:"unique"`
}

// 复合唯一索引
type User struct {
    ID   uint
    Name string
    Age  int `gorm:"uniqueIndex:idx_name_age"`
}

// 命名唯一索引
type User struct {
    ID    uint
    Email string `gorm:"uniqueIndex:idx_email"`
}
```

### 检查约束

```go
type User struct {
    ID  uint
    Age int `gorm:"check:age >= 18"`
}
```

## 索引

### 单列索引

```go
type User struct {
    ID    uint
    Email string `gorm:"index"`
    Name  string `gorm:"index:idx_name"`
    Age   int    `gorm:"index:idx_age"`
}
```

### 复合索引

```go
type User struct {
    Name string `gorm:"index:idx_name_age,sort:asc"`
    Age  int    `gorm:"index:idx_name_age,sort:desc"`
}
```

### 唯一索引

```go
type User struct {
    Email string `gorm:"uniqueIndex"`
}
```

### 索引选项

```go
// 索引排序
Name string `gorm:"index:idx_name,sort:asc"`
Age  int    `gorm:"index:idx_age,sort:desc"`

// 指定长度
Content string `gorm:"index:idx_content,length:100"`

// 索引类型
Hash string `gorm:"index:idx_hash,type:hash"`
```

## 高级迁移

### 条件迁移

```go
// 只迁移新表
if !db.Migrator().HasTable(&User{}) {
    db.Migrator().CreateTable(&User{})
}

// 只迁移新列
if !db.Migrator().HasColumn(&User{}, "email") {
    db.Migrator().AddColumn(&User{}, "email")
}
```

### 检查表/列

```go
// 检查表是否存在
db.Migrator().HasTable(&User{})
db.Migrator().HasTable("users")

// 检查列是否存在
db.Migrator().HasColumn(&User{}, "email")

// 检查索引是否存在
db.Migrator().HasIndex(&User{}, "idx_email")
```

### 重命名

```go
// 重命名表
db.Migrator().RenameTable("users", "users_old")

// 重命名列
db.Migrator().RenameColumn(&User{}, "name", "username")

// 重命名索引
db.Migrator().RenameIndex(&User{}, "idx_old", "idx_new")
```

### 删除

```go
// 删除表
db.Migrator().DropTable(&User{})
db.Migrator().DropTable("users")

// 删除列
db.Migrator().DropColumn(&User{}, "email")

// 删除索引
db.Migrator().DropIndex(&User{}, "idx_email")
```

## 迁移陷阱

### 1. 不支持修改列

```go
// ❌ AutoMigrate 不会修改列类型
type User struct {
    Name string `gorm:"type:varchar(50)"` // 原来是 varchar(100)
}

// ✅ 使用 Migrator 手动修改
db.Migrator().AlterColumn(&User{}, "name")
```

### 2. 不支持删除列

```go
// ❌ 删除字段后不会删除列
type User struct {
    ID   uint
    Name string
    // Age 被删除
}

// ✅ 手动删除列
db.Migrator().DropColumn(&User{}, "age")
```

### 3. 生产环境谨慎使用

```go
// ❌ 生产环境自动迁移
db.AutoMigrate(&User{})

// ✅ 生产环境使用迁移脚本
// migrations/001_create_users.up.sql
// migrations/001_create_users.down.sql
```

## 版本控制迁移

### 使用 golang-migrate

```bash
# 创建迁移
migrate create -ext sql -dir migrations -seq create_users
```

```sql
-- migrations/000001_create_users.up.sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- migrations/000001_create_users.down.sql
DROP TABLE users;
```

```go
// 执行迁移
m, _ := migrate.New(
    "file://migrations",
    "mysql://user:pass@tcp(localhost:3306)/db",
)
m.Up()
```
