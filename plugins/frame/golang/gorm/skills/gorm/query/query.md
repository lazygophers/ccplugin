# 查询构建

## Where 条件

### 基础条件

```go
// 字符串条件
db.Where("name = ?", "John").First(&user)
db.Where("name = ? AND age >= ?", "John", 18).Find(&users)

// Struct 条件
db.Where(&User{Name: "John", Age: 18}).First(&user)

// Map 条件
db.Where(map[string]interface{}{"name": "John", "age": 18}).First(&user)

// Slice 条件
db.Where([]int64{1, 2, 3}).First(&user)
```

### 运算符

```go
// IN
db.Where("id IN ?", []int{1, 2, 3}).Find(&users)

// NOT
db.Not("name = ?", "John").Find(&users)
db.Not(map[string]interface{}{"name": []string{"John", "Jane"}}).Find(&users)

// OR
db.Where("role = ?", "admin").Or("role = ?", "super_admin").Find(&users)

// AND
db.Where("name = ?", "John").Where("age > ?", 18).Find(&users)

// Like
db.Where("name LIKE ?", "%John%").Find(&users)
db.Where("name LIKE ?", "John%").First(&user)

// Between
db.Where("age BETWEEN ? AND ?", 18, 65).Find(&users)

// 比较运算
db.Where("age > ?", 18).Find(&users)
db.Where("age >= ?", 18).Find(&users)
db.Where("age < ?", 65).Find(&users)
db.Where("age <= ?", 65).Find(&users)
db.Where("age <> ?", 30).Find(&users)
```

## 链式查询

```go
// 基础链式
query := db.Where("age > ?", 18)
query = query.Where("active = ?", true)
query.Find(&users)

// 条件式查询
query := db.Model(&User{})
if name != "" {
    query = query.Where("name LIKE ?", "%"+name+"%")
}
if minAge > 0 {
    query = query.Where("age >= ?", minAge)
}
query.Find(&users)
```

## 排序和分页

### 排序

```go
// 升序
db.Order("age").Find(&users)

// 降序
db.Order("age DESC").Find(&users)

// 多字段排序
db.Order("age DESC, name ASC").Find(&users)

// Reorder（覆盖已有排序）
db.Order("age DESC").Reorder("name ASC").Find(&users)
```

### 分页

```go
// Limit
db.Limit(10).Find(&users)

// Offset
db.Offset(20).Limit(10).Find(&users)

// 分页函数
func Paginate(page, pageSize int) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        if page == 0 {
            page = 1
        }
        switch {
        case pageSize > 100:
            pageSize = 100
        case pageSize <= 0:
            pageSize = 10
        }
        offset := (page - 1) * pageSize
        return db.Offset(offset).Limit(pageSize)
    }
}

db.Scopes(Paginate(2, 20)).Find(&users)
```

## 选择字段

```go
// Select 指定字段
db.Select("name", "email").Find(&users)

// Omit 排除字段
db.Omit("password").Find(&users)

// Distinct 去重
db.Distinct("name").Find(&users)

// 聚合查询
db.Select("name, COUNT(*) as count").Group("name").Find(&results)
```

## 子查询

```go
// Where 子查询
subQuery := db.Select("AVG(age)").From("users")
db.Where("age > (?)", subQuery).Find(&users)

// From 子查询
subQuery := db.Model(&User{}).Select("name").Where("age > ?", 18)
db.Table("(?) as u", subQuery).Find(&users)

// Having 子查询
db.Select("name, COUNT(*) as count").Group("name").Having("COUNT(*) > ?", 5).Find(&results)
```

## 原生 SQL

### 执行原生 SQL

```go
// Raw
db.Raw("SELECT * FROM users WHERE age > ?", 18).Scan(&users)

// Exec（无返回行）
db.Exec("UPDATE users SET active = ? WHERE id = ?", true, 1)

// Scan 映射
type Result struct {
    Name string
    Age  int
}
db.Raw("SELECT name, age FROM users").Scan(&results)
```

### 命名参数

```go
db.Raw("SELECT * FROM users WHERE name = @name OR email = @email",
    sql.Named("name", "John"),
    sql.Named("email", "john@example.com"),
).Find(&users)
```

## 聚合查询

```go
// Count
var count int64
db.Model(&User{}).Where("age > ?", 18).Count(&count)

// Min/Max
var age int
db.Model(&User{}).Select("MIN(age)").Scan(&age)
db.Model(&User{}).Select("MAX(age)").Scan(&age)

// Sum/Avg
var total float64
db.Model(&Order{}).Select("SUM(amount)").Scan(&total)

// Group By
db.Model(&User{}).Select("role, COUNT(*) as count").Group("role").Scan(&results)

// Having
db.Model(&User{}).Select("role, COUNT(*) as count").Group("role").Having("COUNT(*) > ?", 10).Scan(&results)
```

## Pluck

```go
// 查询单列
var names []string
db.Model(&User{}).Pluck("name", &names)

var ages []int
db.Model(&User{}).Pluck("age", &ages)

// 结合 In
var ids []int
db.Model(&User{}).Pluck("id", &ids)
db.Where("id IN ?", ids).Find(&users)
```

## Scopes

```go
// 定义 Scope
func AgeGreaterThan(age int) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        return db.Where("age > ?", age)
    }
}

func ActiveUsers(db *gorm.DB) *gorm.DB {
    return db.Where("active = ?", true)
}

// 使用 Scope
db.Scopes(AgeGreaterThan(18)).Find(&users)
db.Scopes(AgeGreaterThan(18), ActiveUsers).Find(&users)
```

## FirstOrInit / FirstOrCreate

```go
// FirstOrInit（不创建）
var user User
db.Where("email = ?", "john@example.com").FirstOrInit(&user)
// user: {Email: "john@example.com"}

// FirstOrCreate（创建）
db.Where("email = ?", "john@example.com").FirstOrCreate(&user)
// 如果不存在则创建

// 带更多属性
db.Where("email = ?", "john@example.com").
    Attrs("name", "John").
    FirstOrCreate(&user)
```

## Locking

```go
// FOR UPDATE
db.Clauses(clause.Locking{Strength: "UPDATE"}).Find(&users)

// FOR UPDATE NOWAIT
db.Clauses(clause.Locking{
    Strength: "UPDATE",
    Options:  "NOWAIT",
}).Find(&users)

// FOR SHARE
db.Clauses(clause.Locking{Strength: "SHARE"}).Find(&users)
```
