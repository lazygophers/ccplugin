# 查询 API

## 基础查询

### Select

```go
q := query.Use(db)

// 查询单条
user, err := q.User.Where(
    q.User.ID.Eq(1),
).First()

// 查询多条
users, err := q.User.Where(
    q.User.Age.Gte(18),
).Find()

// 查询主键
user, err := q.User.Where(
    q.User.ID.Eq(1),
).Take()
```

### 条件查询

```go
// Eq
q.User.Name.Eq("John")

// Neq
q.User.Age.Neq(18)

// Gt/Gte
q.User.Age.Gt(18)
q.User.Age.Gte(18)

// Lt/Lte
q.User.Age.Lt(65)
q.User.Age.Lte(65)

// Like
q.User.Name.Like("%John%")
q.User.Name.NotLike("%admin%")

// In
q.User.ID.In(1, 2, 3)
q.User.Name.In([]string{"John", "Jane"})

// NotIn
q.User.ID.NotIn(1, 2, 3)

// Between
q.User.Age.Between(18, 65)
q.User.CreatedAt.Between(start, end)

// Null 检查
q.User.Email.IsNull()
q.User.Email.IsNotNull()
```

## 逻辑组合

### And 条件

```go
// 默认就是 AND
q.User.Where(
    q.User.Name.Eq("John"),
    q.User.Age.Gte(18),
)

// 显式 AND
q.User.Where(
    q.User.Name.Eq("John").And(q.User.Age.Gte(18)),
)
```

### Or 条件

```go
// 单一 OR
q.User.Where(
    q.User.Name.Eq("John"),
).Or(
    q.User.Name.Eq("Jane"),
)

// 组合 OR
q.User.Where(
    q.User.Name.Eq("John").And(q.User.Age.Gte(18)),
).Or(
    q.User.Name.Eq("Jane").And(q.User.Age.Gte(20)),
)
```

### Not 条件

```go
// Not
q.User.Not(q.User.Age.Lt(18))

// Not 嵌套
q.User.Where(
    q.User.Name.NotIn("admin", "root"),
)
```

## 排序和分页

### 排序

```go
// 单字段升序
q.User.Order(q.User.ID.Asc()).Find()

// 单字段降序
q.User.Order(q.User.CreatedAt.Desc()).Find()

// 多字段排序
q.User.Order(
    q.User.Age.Desc(),
    q.User.Name.Asc(),
).Find()
```

### 分页

```go
// Limit
q.User.Limit(10).Find()

// Offset
q.User.Offset(20).Limit(10).Find()

// 分页函数
func Paginate(page, size int) func(field.RelationField) field.Expr {
    return field.NewField("", "")
}

page := 2
size := 10
q.User.Limit(size).Offset((page - 1) * size).Find()
```

## 聚合查询

### Count

```go
// 计数
count, err := q.User.Where(
    q.User.Age.Gte(18),
).Count()

// Distinct 计数
count, err := q.User.Distinct(q.User.Email).Count()
```

### 聚合函数

```go
// Max
maxAge, err := q.User.Select(
    q.User.Age.Max(),
).Scalar()

// Min
minAge, err := q.User.Select(
    q.User.Age.Min(),
).Scalar()

// Sum
total, err := q.Order.Select(
    q.Order.Amount.Sum(),
).Scalar()

// Avg
avg, err := q.Order.Select(
    q.Order.Amount.Avg(),
).Scalar()
```

## 更新

### 单字段更新

```go
// Update
q.User.Where(q.User.ID.Eq(1)).Update(
    q.User.Name,
    "Jane",
)

// 多条件更新
q.User.Where(
    q.User.ID.Eq(1),
).Update(
    q.User.Status,
    "active",
)
```

### 多字段更新

```go
// Updates（map）
q.User.Where(q.User.ID.Eq(1)).Updates(map[string]interface{}{
    "name":  "Jane",
    "age":   30,
    "email": "jane@example.com",
})

// Updates（结构体）
q.User.Where(q.User.ID.Eq(1)).Updates(User{
    Name: "Jane",
    Age:  30,
})
```

### 表达式更新

```go
// 自增
q.User.Where(q.User.ID.Eq(1)).Update(
    q.User.Age,
    q.User.Age.Add(1),
)

// 自减
q.User.Where(q.User.ID.Eq(1)).Update(
    q.User.Balance,
    q.User.Balance.Sub(100),
)
```

## 删除

### 条件删除

```go
// 单条删除
q.User.Where(q.User.ID.Eq(1)).Delete()

// 批量删除
q.User.Where(
    q.User.DeletedAt.IsNotNull(),
).Delete()

// Not 删除
q.User.Not(q.User.Age.Gte(18)).Delete()
```

### 软删除

```go
// 软删除（如果有 DeletedAt）
q.User.Where(q.User.ID.Eq(1)).Delete()

// 永久删除
q.User.Unscoped().Where(q.User.ID.Eq(1)).Delete()
```

## 选择字段

### Select

```go
// 选择特定字段
q.User.Select(
    q.User.ID,
    q.User.Name,
).Find()

// 聚合字段
q.User.Select(
    q.User.ID,
    q.User.Name,
    q.User.Age.Max().As("max_age"),
).Find()
```

### Omit

```go
// 排除字段
q.User.Omit(
    q.User.Password,
).Find()
```

## 子查询

### Where 子查询

```go
// 子查询
subQuery := q.Order.Select(
    q.Order.UserID,
).Where(
    q.Order.Amount.Gte(1000),
)

// 主查询
users, err := q.User.Where(
    q.User.ID.In(subQuery),
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

// 主查询
result, err := q.Table(subQuery.As("u")).Find()
```

## 关联查询

### 关联定义

```go
// 生成时定义关联
g.ApplyBasic(
    g.GenerateModel("users",
        gen.FieldRelate(
            model.Relate{
                Type:        gen.HasMany,
                RelateTable: "posts",
                Field:       "Posts",
            },
        ),
    ),
)
```

### 预加载

```go
// 预加载关联
users, err := q.User.Related(
    q.User.Posts,
).Find()

// 条件预加载
users, err := q.User.Related(
    q.User.Posts.Where(
        q.Post.Published.Is(true),
    ),
).Find()
```

## 事务支持

### 事务查询

```go
err := q.Transaction(func(tx *query.Query) error {
    // 事务内查询
    user, err := tx.User.Where(
        tx.User.ID.Eq(1),
    ).First()
    if err != nil {
        return err
    }

    // 事务内更新
    tx.User.Where(tx.User.ID.Eq(1)).Update(
        tx.User.Balance,
        tx.User.Balance.Add(100),
    )

    return nil
})
```

## 原生 SQL

### Raw SQL

```go
// Raw 查询
result, err := q.User.UnderlyingDB().
    Raw("SELECT * FROM users WHERE age > ?", 18).
    Find()
```

### SQL 表达式

```go
// SQL 表达式
q.User.Where(
    q.User.Age.Gte(
        field.NewInt("", "18"),
    ),
).Find()
```

## 调试

### SQL 日志

```go
// Debug 模式
user, err := q.User.Debug().Where(
    q.User.ID.Eq(1),
).First()

// 打印 SQL
user, err := q.User.Where(
    q.User.ID.Eq(1),
).First()
fmt.Printf("SQL: %s\n", user.SQL)
```

### Explain

```go
// 查询计划
result, err := q.User.Where(
    q.User.ID.Eq(1),
).Explain()
fmt.Printf("Plan: %v\n", result)
```
