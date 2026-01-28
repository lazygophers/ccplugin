# 事务处理

## 自动事务

```go
// 基础事务
db.Transaction(func(tx *gorm.DB) error {
    if err := tx.Create(&User{Name: "John"}).Error; err != nil {
        return err // 回滚
    }
    if err := tx.Create(&Order{UserID: 1}).Error; err != nil {
        return err // 回滚
    }
    return nil // 提交
})
```

## 手动事务

```go
// 开始事务
tx := db.Begin()

// 执行操作
if err := tx.Create(&User{Name: "John"}).Error; err != nil {
    tx.Rollback()
    return err
}

if err := tx.Create(&Order{UserID: 1}).Error; err != nil {
    tx.Rollback()
    return err
}

// 提交事务
tx.Commit()
```

## 嵌套事务

```go
db.Transaction(func(tx *gorm.DB) error {
    tx.Create(&User{Name: "John"})

    tx.Transaction(func(tx2 *gorm.DB) error {
        tx2.Create(&Post{Title: "Hello"})
        return nil
    })

    return nil
})
```

## SavePoint 和 RollbackTo

```go
tx := db.Begin()
tx.Create(&User{Name: "John"})

tx.SavePoint("sp1")
tx.Create(&Post{Title: "Post 1"})

tx.RollbackTo("sp1") // 回滚到 sp1
tx.Create(&Post{Title: "Post 2"}) // 只有 Post 2 被创建

tx.Commit()
```

## 事务最佳实践

### 1. 保持简短

```go
// ✅ 好的做法
db.Transaction(func(tx *gorm.DB) error {
    if err := validateInput(input); err != nil {
        return err
    }
    if err := processData(input); err != nil {
        return err
    }
    return tx.Create(&User{...}).Error
})

// ❌ 不好的做法
db.Transaction(func(tx *gorm.DB) error {
    // 大量业务逻辑
    time.Sleep(10 * time.Second)
    return nil
})
```

### 2. 错误处理

```go
db.Transaction(func(tx *gorm.DB) error {
    // 检查错误
    if err := tx.Create(&user).Error; err != nil {
        return err // 自动回滚
    }

    // 检查受影响行数
    result := tx.Where("id = ?", 1).Delete(&User{})
    if result.RowsAffected == 0 {
        return errors.New("record not found")
    }

    return nil
})
```

### 3. 隔离级别

```go
// 设置隔离级别
tx := db.Begin()
tx.Exec("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")

// MySQL
tx.Begin(&sql.TxOptions{
    Isolation: sql.LevelReadCommitted,
    ReadOnly:  false,
})
```

## 事务与并发

### 1. 悲观锁

```go
db.Transaction(func(tx *gorm.DB) error {
    var user User
    // FOR UPDATE 锁定记录
    tx.Clauses(clause.Locking{Strength: "UPDATE"}).
        First(&user, 1)

    // 更新
    user.Balance += 100
    return tx.Save(&user).Error
})
```

### 2. 乐观锁

```go
type User struct {
    ID      int
    Version int `gorm:"column:version;default:0"`
    Balance int
}

// 更新时检查版本
result := db.Model(&user).
    Where("version = ?", user.Version).
    Update("version", user.Version+1)

if result.RowsAffected == 0 {
    return errors.New("concurrent modification")
}
```

## 事务陷阱

### 1. 忘略错误

```go
// ❌ 错误
tx := db.Begin()
tx.Create(&user)
// 忘略错误检查
tx.Commit()

// ✅ 正确
tx := db.Begin()
if err := tx.Create(&user).Error; err != nil {
    tx.Rollback()
    return err
}
if err := tx.Commit().Error; err != nil {
    return err
}
```

### 2. 跨 goroutine

```go
// ❌ 错误：事务不能跨 goroutine
tx := db.Begin()
go func() {
    tx.Create(&user) // 可能不工作
}()
tx.Commit()

// ✅ 正确：在同一 goroutine 中完成事务
tx := db.Begin()
tx.Create(&user)
tx.Commit()
```

### 3. 嵌套过深

```go
// ❌ 错误：过深的嵌套
tx.Begin()
tx.Begin()
tx.Begin()

// ✅ 正确：使用 SavePoint
tx.Begin()
tx.SavePoint("sp1")
```
