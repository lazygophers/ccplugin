# 性能优化

## N+1 查询问题

### 问题示例

```go
// ❌ N+1 查询
var users []User
db.Find(&users)
for _, user := range users {
    db.Model(&user).Association("Posts").Find(&user.Posts)
    // 1 + N 次查询
}
```

### 解决方案：预加载

```go
// ✅ 预加载
db.Preload("Posts").Find(&users)
// 只需 2 次查询

// ✅ 嵌套预加载
db.Preload("Posts.Comments").Find(&users)

// ✅ 带条件预加载
db.Preload("Posts", "published = ?", true).Find(&users)

// ✅ Joins 预加载（1 次查询）
db.Joins("Posts").Find(&users)
```

## 批量操作

### 批量创建

```go
// ❌ 逐条创建
for _, user := range users {
    db.Create(&user) // N 次插入
}

// ✅ 批量创建
db.Create(&users) // 1 次批量插入

// ✅ CreateInBatches
db.CreateInBatches(users, 100) // 每批 100 条
```

### 批量更新

```go
// ❌ 逐条更新
for _, user := range users {
    db.Model(&user).Update("status", "active")
}

// ✅ 批量更新
db.Model(&User{}).Where("id IN ?", ids).Update("status", "active")
```

### 批量删除

```go
// ❌ 逐条删除
for _, id := range ids {
    db.Delete(&User{}, id)
}

// ✅ 批量删除
db.Where("id IN ?", ids).Delete(&User{})
```

## 连接池配置

```go
sqlDB, err := db.DB()
if err != nil {
    return err
}

// 最大空闲连接数
sqlDB.SetMaxIdleConns(10)

// 最大打开连接数
sqlDB.SetMaxOpenConns(100)

// 连接最大生命周期
sqlDB.SetConnMaxLifetime(time.Hour)

// 连接最大空闲时间
sqlDB.SetConnMaxIdleTime(time.Minute * 10)
```

## 索引优化

### 创建索引

```go
type User struct {
    ID    uint
    Email string `gorm:"uniqueIndex"`
    Name  string `gorm:"index"`
    Age   int    `gorm:"index:idx_age"`
}
```

### 复合索引

```go
type User struct {
    Name     string `gorm:"index:idx_name_age,sort:asc"`
    Age      int    `gorm:"index:idx_name_age,sort:desc"`
    Email    string `gorm:"uniqueIndex:idx_email"`
}

// 查询顺序匹配索引顺序
db.Where("name = ? AND age > ?", "John", 18).Find(&users)
```

## 查询优化

### 选择字段

```go
// ❌ 查询所有字段
db.Find(&users)

// ✅ 只查询需要的字段
db.Select("id", "name").Find(&users)
db.Omit("password", "secret").Find(&users)
```

### 分页

```go
// ❌ 一次查询所有
db.Find(&users)

// ✅ 分页查询
db.Offset(0).Limit(20).Find(&users)
```

### Count 优化

```go
// ❌ 查询所有再计数
var users []User
db.Find(&users)
count := len(users)

// ✅ 使用 Count
var count int64
db.Model(&User{}).Count(&count)
```

### Pluck

```go
// ❌ 查询所有再提取
var users []User
db.Find(&users)
var names []string
for _, user := range users {
    names = append(names, user.Name)
}

// ✅ 使用 Pluck
var names []string
db.Model(&User{}).Pluck("name", &names)
```

## 预编译语句

```go
// 启用预编译
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    PrepareStmt: true,
})

// 预编译缓存
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    PrepareStmt: true,
    ConnPool:    getCustomConnPool(),
})
```

## 跳过默认事务

```go
// 跳过默认事务可以提高写入性能
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    SkipDefaultTransaction: true,
})

// 注意：跳过后需要手动管理事务
db.Transaction(func(tx *gorm.DB) error {
    return tx.Create(&user).Error
})
```

## 缓存策略

### 应用层缓存

```go
type UserCache struct {
    cache *sync.Map
}

func (uc *UserCache) Get(id uint) (*User, error) {
    // 先查缓存
    if val, ok := uc.cache.Load(id); ok {
        return val.(*User), nil
    }

    // 查数据库
    var user User
    if err := db.First(&user, id).Error; err != nil {
        return nil, err
    }

    uc.cache.Store(id, &user)
    return &user, nil
}
```

### Redis 缓存

```go
import "github.com/go-redis/redis/v8"

rdb := redis.NewClient(&redis.Options{
    Addr: "localhost:6379",
})

func GetUserWithCache(id uint) (*User, error) {
    // Redis 查询
    val, err := rdb.Get(ctx, fmt.Sprintf("user:%d", id)).Result()
    if err == nil {
        var user User
        json.Unmarshal([]byte(val), &user)
        return &user, nil
    }

    // 数据库查询
    var user User
    if err := db.First(&user, id).Error; err != nil {
        return nil, err
    }

    // 写入 Redis
    data, _ := json.Marshal(user)
    rdb.Set(ctx, fmt.Sprintf("user:%d", id), data, time.Hour)

    return &user, nil
}
```

## 性能监控

### Logger

```go
import "gorm.io/gorm/logger"

db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    Logger: logger.Default.LogMode(logger.Info),
})

// 自定义 Logger
db, err = gorm.Open(mysql.Open(dsn), &gorm.Config{
    Logger: logger.New(
        log.New(os.Stdout, "\r\n", log.LstdFlags),
        logger.Config{
            SlowThreshold:             time.Millisecond * 200,
            LogLevel:                  logger.Info,
            IgnoreRecordNotFoundError: true,
            Colorful:                  true,
        },
    ),
})
```

### 查询分析

```go
// Explain
result := db.Explain("SELECT * FROM users WHERE age > ?", 18)
fmt.Println(result)

// SQL 记录
db.Debug().Find(&users) // 打印 SQL

// RowsAffected
result := db.Where("age > ?", 18).Delete(&User{})
fmt.Printf("Deleted %d rows\n", result.RowsAffected)
```

## 性能对比

### 批量插入

```go
// 逐条插入：1000 条 ≈ 10 秒
// 批量插入：1000 条 ≈ 0.1 秒

// 测试
func BenchmarkSingleInsert(b *testing.B) {
    for i := 0; i < b.N; i++ {
        db.Create(&User{Name: "John"})
    }
}

func BenchmarkBatchInsert(b *testing.B) {
    var users []User
    for i := 0; i < b.N; i++ {
        users = append(users, User{Name: "John"})
    }
    db.CreateInBatches(users, 100)
}
```

### 预加载

```go
// N+1：100 用户，每人 10 篇文章 ≈ 1001 次查询 ≈ 5 秒
// 预加载：2 次查询 ≈ 0.05 秒
```

## 优化清单

- [ ] 使用预加载解决 N+1 问题
- [ ] 批量操作代替循环
- [ ] 合理配置连接池
- [ ] 创建必要的索引
- [ ] 只查询需要的字段
- [ ] 使用分页查询
- [ ] 启用预编译语句
- [ ] 考虑跳过默认事务
- [ ] 实施缓存策略
- [ ] 监控慢查询
