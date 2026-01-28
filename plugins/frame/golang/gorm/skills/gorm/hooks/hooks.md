# 钩子函数

## 对象生命周期

```
BeforeSave → BeforeCreate/Update → AfterCreate/Update → AfterSave
BeforeDelete → AfterDelete
BeforeFind → AfterFind
```

## 创建钩子

```go
func (u *User) BeforeCreate(tx *gorm.DB) error {
    // 验证
    if u.Name == "" {
        return errors.New("name cannot be empty")
    }
    // 默认值
    if u.Age == 0 {
        u.Age = 18
    }
    return nil
}

func (u *User) AfterCreate(tx *gorm.DB) error {
    // 后续操作
    tx.Model(u).Update("verified", false)
    return nil
}
```

## 更新钩子

```go
func (u *User) BeforeUpdate(tx *gorm.DB) error {
    // 检查变更
    if tx.Statement.Changed("email") {
        // 发送验证邮件
    }
    return nil
}

func (u *User) AfterUpdate(tx *gorm.DB) error {
    // 更新后操作
    return nil
}
```

## 保存钩子

```go
func (u *User) BeforeSave(tx *gorm.DB) error {
    // 创建和更新前都会调用
    if u.Password != "" {
        u.Password = hashPassword(u.Password)
    }
    return nil
}

func (u *User) AfterSave(tx *gorm.DB) error {
    // 保存后操作
    return nil
}
```

## 删除钩子

```go
func (u *User) BeforeDelete(tx *gorm.DB) error {
    // 删除前清理关联
    tx.Model(u).Association("Posts").Clear()
    return nil
}

func (u *User) AfterDelete(tx *gorm.DB) error {
    // 删除后操作
    return nil
}
```

## 查询钩子

```go
func (u *User) AfterFind(tx *gorm.DB) error {
    // 查询后处理
    if u.Age < 18 {
        u.IsMinor = true
    }
    return nil
}
```

## 钩子使用场景

### 1. 数据验证

```go
func (u *User) BeforeCreate(tx *gorm.DB) error {
    if u.Email == "" {
        return errors.New("email is required")
    }
    if !isValidEmail(u.Email) {
        return errors.New("invalid email format")
    }
    return nil
}
```

### 2. 默认值

```go
func (u *User) BeforeCreate(tx *gorm.DB) error {
    if u.Status == "" {
        u.Status = "active"
    }
    if u.CreatedAt.IsZero() {
        u.CreatedAt = time.Now()
    }
    return nil
}
```

### 3. 数据加密

```go
func (u *User) BeforeSave(tx *gorm.DB) error {
    if u.Password != "" {
        u.Password = encrypt(u.Password)
    }
    return nil
}

func (u *User) AfterFind(tx *gorm.DB) error {
    if u.Password != "" {
        u.Password = decrypt(u.Password)
    }
    return nil
}
```

### 4. 时间戳

```go
func (u *User) BeforeUpdate(tx *gorm.DB) error {
    u.UpdatedAt = time.Now()
    return nil
}

func (u *User) BeforeCreate(tx *gorm.DB) error {
    u.CreatedAt = time.Now()
    u.UpdatedAt = time.Now()
    return nil
}
```

### 5. 软删除处理

```go
func (u *User) BeforeDelete(tx *gorm.DB) error {
    if u.DeletedAt.Time.IsZero() {
        u.DeletedAt.Time = time.Now()
        return tx.Save(u).Error
    }
    return nil
}
```

### 6. 变更追踪

```go
func (u *User) BeforeUpdate(tx *gorm.DB) error {
    if tx.Statement.Changed("status") {
        oldStatus := tx.Statement.DirtyFields["status"]
        log.Printf("Status changed from %v to %v", oldStatus, u.Status)
    }
    return nil
}
```

## 钩子最佳实践

### 1. 保持简单

```go
// ✅ 好的做法：钩子只做一件事
func (u *User) BeforeCreate(tx *gorm.DB) error {
    return u.validate()
}

// ❌ 不好的做法：钩子做太多事情
func (u *User) BeforeCreate(tx *gorm.DB) error {
    if err := u.validate(); err != nil {
        return err
    }
    if err := u.sendEmail(); err != nil {
        return err
    }
    if err := u.updateCache(); err != nil {
        return err
    }
    return nil
}
```

### 2. 避免副作用

```go
// ✅ 好的做法：不影响其他操作
func (u *User) BeforeCreate(tx *gorm.DB) error {
    if u.Name == "" {
        u.Name = "Anonymous" // 修改自身
    }
    return nil
}

// ❌ 不好的做法：查询数据库
func (u *User) BeforeCreate(tx *gorm.DB) error {
    var count int64
    tx.Model(&User{}).Where("email = ?", u.Email).Count(&count)
    if count > 0 {
        return errors.New("email exists")
    }
    return nil
}
```

### 3. 错误处理

```go
func (u *User) BeforeCreate(tx *gorm.DB) error {
    if err := u.validate(); err != nil {
        // 返回错误会中断操作
        return err
    }
    return nil
}
```

## 钩子陷阱

### 1. 死循环

```go
// ❌ 死循环
func (u *User) AfterFind(tx *gorm.DB) error {
    tx.First(u) // 再次查询，触发 AfterFind
    return nil
}

// ✅ 正确做法
func (u *User) AfterFind(tx *gorm.DB) error {
    // 不要在钩子中再次查询同一模型
    return nil
}
```

### 2. 跳过钩子

```go
// 跳过钩子
db.Create(&user)                    // 会触发钩子
db.Session(&gorm.Session{SkipHooks: true}).Create(&user) // 不触发钩子
```

### 3. 修改查询

```go
// ❌ 钩子中修改查询结果可能导致问题
func (u *User) AfterFind(tx *gorm.DB) error {
    u.Name = "Modified"
    return nil
}

// ✅ 只做必要的后处理
func (u *User) AfterFind(tx *gorm.DB) error {
    if u.Age < 18 {
        u.IsMinor = true
    }
    return nil
}
```
