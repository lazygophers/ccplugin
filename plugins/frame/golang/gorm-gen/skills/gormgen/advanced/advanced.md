# 高级功能

## 子查询

### Where 子查询

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

// EXISTS 子查询
users, err := q.User.Where(
    field.Exists(subQuery),
).Find()
```

### From 子查询

```go
// 子查询
subQuery := q.User.Select(
    q.User.ID,
    q.User.Name,
).Where(
    q.User.Age.Gte(18),
)

// 作为表查询
result, err := q.Table(subQuery.As("u")).Find()
```

### Select 子查询

```go
// 聚合子查询
subQuery := q.Order.Select(
    q.Order.UserID,
    q.Order.Amount.Sum().As("total"),
).Group(q.Order.UserID)

users, err := q.User.Select(
    q.User.ID,
    q.User.Name,
    subQuery,
).Find()
```

## 聚合查询

### Group By

```go
// 单字段分组
result, err := q.User.Select(
    q.User.Age,
    q.User.ID.Count().As("count"),
).Group(
    q.User.Age,
).Find()

// 多字段分组
result, err := q.User.Select(
    q.User.City,
    q.User.Age,
    q.User.ID.Count().As("count"),
).Group(
    q.User.City,
    q.User.Age,
).Find()
```

### Having

```go
result, err := q.User.Select(
    q.User.Age,
    q.User.ID.Count().As("count"),
).Group(
    q.User.Age,
).Having(
    q.User.ID.Count().Gte(10),
).Find()
```

## 关联查询

### 预加载

```go
// 基础预加载
users, err := q.User.Destination(
    &users,
).Relation(
    q.User.Posts,
).Find()

// 条件预加载
users, err := q.User.Destination(
    &users,
).Relation(
    q.User.Posts.Where(
        q.Post.Published.Is(true),
    ),
).Find()

// 嵌套预加载
users, err := q.User.Destination(
    &users,
).Relation(
    q.User.Posts.Posts.Comments,
).Find()
```

### Join 查询

```go
// Inner Join
users, err := q.User.InnerJoin(
    q.Post,
    q.User.ID.EqCol(q.Post.UserID),
).Find()

// Left Join
users, err := q.User.LeftJoin(
    q.Post,
    q.User.ID.EqCol(q.Post.UserID),
).Find()
```

## 事务

### 事务查询

```go
err := q.Transaction(func(tx *query.Query) error {
    // 事务内操作
    user, err := tx.User.Where(
        tx.User.ID.Eq(1),
    ).First()
    if err != nil {
        return err
    }

    tx.User.Where(tx.User.ID.Eq(1)).Update(
        tx.User.Balance,
        tx.User.Balance.Add(100),
    )

    return nil
})
```

### 嵌套事务

```go
err := q.Transaction(func(tx *query.Query) error {
    // 外层事务
    tx.User.Create(&User{Name: "John"})

    // 内层事务
    tx.Transaction(func(tx2 *query.Query) error {
        tx2.Post.Create(&Post{Title: "Hello"})
        return nil
    })

    return nil
})
```

## SavePoint

```go
tx := q.Begin()

// 设置保存点
tx.SavePoint("sp1")

tx.User.Create(&User{Name: "John"})

// 回滚到保存点
tx.RollbackTo("sp1")

tx.User.Create(&User{Name: "Jane"})

tx.Commit()
```

## 动态查询

### 条件构建

```go
// 基础条件
conditions := []field.Expr{}

if name != "" {
    conditions = append(conditions, q.User.Name.Eq(name))
}

if minAge > 0 {
    conditions = append(conditions, q.User.Age.Gte(minAge))
}

users, err := q.User.Where(conditions...).Find()
```

### 动态字段

```go
// 动态选择字段
fields := []field.Expr{
    q.User.ID,
    q.User.Name,
}

if includeAge {
    fields = append(fields, q.User.Age)
}

q.User.Select(fields...).Find()
```

## 表达式

### 算术表达式

```go
// 加法
q.User.Balance.Add(100)

// 减法
q.User.Balance.Sub(50)

// 乘法
q.User.Price.Mul(1.1)

// 除法
q.User.Price.Div(2)
```

### 字符串表达式

```go
// 拼接
q.User.Name.Concat(" ", q.User.LastName)

// 长度
q.User.Name.Length()

// 子串
q.User.Name.Substr(1, 10)
```

### 时间表达式

```go
// 日期差
q.User.CreatedAt.DateDiff(time.Now())

// 日期加
q.User.CreatedAt.AddDate(0, 1, 0)

// 时间格式化
q.User.CreatedAt.DateFormat("2006-01-02")
```

## SQL 函数

### 聚合函数

```go
// Count
q.User.ID.Count()

// Sum
q.Order.Amount.Sum()

// Avg
q.Order.Amount.Avg()

// Max/Min
q.User.Age.Max()
q.User.Age.Min()
```

### 字符串函数

```go
// Upper/Lower
q.User.Name.Upper()
q.User.Name.Lower()

// Trim
q.User.Name.Trim()

// Substring
q.User.Name.Substr(1, 10)
```

### 时间函数

```go
// Now
field.Now()

// CurrentDate
field.CurrentDate()

// CurrentTime
field.CurrentTime()
```

## 窗口函数

### Rank

```go
result, err := q.User.Select(
    q.User.ID,
    q.User.Name,
    q.User.Age,
    field.Rank().Over(
        q.User.Age.Desc(),
    ).As("rank"),
).Find()
```

### RowNumber

```go
result, err := q.User.Select(
    q.User.ID,
    q.User.Name,
    field.RowNumber().Over(
        q.User.Age.Desc(),
    ).As("row_num"),
).Find()
```

## CTE (Common Table Expression)

### WITH 子句

```go
// 定义 CTE
cte := q.User.Select(
    q.User.ID,
    q.User.Name,
).Where(
    q.User.Age.Gte(18),
).As("adults")

// 使用 CTE
result, err := q.With(cte).Select(
    field.NewString("", "*"),
).From("adults").Find()
```

## 原生 SQL

### Raw 查询

```go
// 执行原生 SQL
result, err := q.User.UnderlyingDB().
    Raw("SELECT * FROM users WHERE age > ?", 18).
    Find()
```

### SQL 表达式

```go
// 使用原生 SQL 表达式
q.User.Where(
    q.User.Age.Gte(
        field.NewInt("", "18"),
    ),
).Find()

// 复杂表达式
q.User.Where(
    field.Raw("JSON_EXTRACT(data, '$.age') > ?", 18),
).Find()
```

## 批量操作

### 批量插入

```go
// 批量创建
users := []User{
    {Name: "John", Age: 25},
    {Name: "Jane", Age: 30},
}

err := q.User.Create(&users...)
```

### 批量更新

```go
// 批量更新
err := q.User.Where(
    q.User.Status.Eq("active"),
).Update(
    q.User.UpdatedAt,
    time.Now(),
)
```

### 批量删除

```go
// 批量删除
err := q.User.Where(
    q.User.DeletedAt.IsNotNull(),
).Delete()
```
