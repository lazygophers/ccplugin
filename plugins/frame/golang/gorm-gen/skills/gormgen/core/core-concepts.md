# 核心概念

## 架构设计

```
┌─────────────────────────────────────────┐
│         应用层代码                       │
│  使用生成的 query 包进行类型安全查询      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         生成代码层                       │
│  query 包：Field API、DAO 对象           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         GORM 层                         │
│  标准 GORM 操作                         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         数据库驱动                       │
│  MySQL/PostgreSQL/SQLite                │
└─────────────────────────────────────────┘
```

## Field API

### 字段类型

```go
// 生成后的字段定义
type user struct {
    ID        field.Int64
    Name      field.String
    Email     field.String
    Age       field.Int
    Active    field.Bool
    CreatedAt field.Time
    UpdatedAt field.Time
}
```

### 字段方法

```go
// 比较方法
field.Int.Eq(1)           // =
field.Int.Neq(1)          // !=
field.Int.Gt(1)           // >
field.Int.Gte(1)          // >=
field.Int.Lt(1)           // <
field.Int.Lte(1)          // <=

// 字符串方法
field.String.Eq("John")   // =
field.String.Neq("John")  // !=
field.String.Like("%Jo%") // LIKE
field.String.In([]string{"John", "Jane"})

// 数值方法
field.Int.Between(18, 65)
field.Int.NotBetween(18, 65)

// 时间方法
field.Time.Gte(time.Now())
field.Time.Between(start, end)

// 空值检查
field.String.IsNull()
field.String.IsNotNull()
```

### 条件组合

```go
// AND（默认）
q.User.Where(
    q.User.Name.Eq("John"),
    q.User.Age.Gte(18),
)

// Or
q.User.Where(
    q.User.Name.Eq("John"),
).Or(
    q.User.Name.Eq("Jane"),
)

// Not
q.User.Not(q.User.Age.Lt(18))

// 组合条件
q.User.Where(
    q.User.Name.Eq("John").And(q.User.Age.Gte(18)),
).Or(
    q.User.Name.Eq("Jane").And(q.User.Age.Gte(20)),
)
```

## DAO 模式

### Query 对象

```go
// 初始化
q := query.Use(db)

// 表查询
userQuery := q.User
productQuery := q.Product
orderQuery := q.Order
```

### 链式调用

```go
// 链式查询
user, err := q.User.
    Where(q.User.Name.Eq("John")).
    Where(q.User.Age.Gte(18)).
    Order(q.User.ID.Desc()).
    Limit(1).
    First()
```

## 生成代码结构

```go
// query/users.gen.go
package query

type user struct {
    gen.DO

    ID        field.Int64
    Name      field.String
    Email     field.String
    Age       field.Int
    CreatedAt field.Time
    UpdatedAt field.Time
}

func User(ctx ...context.Context) userDo {
    return userDo{user{gen.DO{ctx: ctx...}}}
}

// query/gen.go
var Q = struct {
    User userDo
}{
    User: User(),
}
```

## 类型安全

### 编译时检查

```go
// ✅ 编译通过
q.User.Where(q.User.Name.Eq("John"))

// ❌ 编译错误：类型不匹配
q.User.Where(q.User.Name.Eq(123)) // string vs int

// ❌ 编译错误：字段不存在
q.User.Where(q.User.NotExistField.Eq("John"))
```

### IDE 支持

```go
// 自动补全
q.User.Where(q.User.<TAB>)
// 显示：ID, Name, Email, Age, CreatedAt, UpdatedAt

// 类型提示
q.User.Name.Eq(<string>)
```

## 上下文支持

### WithContext 模式

```go
// 启用上下文
g := gen.NewGenerator(gen.Config{
    OutPath: "./query",
    Mode:    gen.WithContext,
})

// 使用
ctx := context.Background()
user, err := q.User.WithContext(ctx).Where(
    q.User.ID.Eq(1),
).First()
```

### 超时控制

```go
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

user, err := q.User.WithContext(ctx).Where(
    q.User.ID.Eq(1),
).First()
```

## 生成模式

### 模式选项

```go
// 无上下文
Mode: gen.WithoutContext

// 默认查询
Mode: gen.WithDefaultQuery

// 上下文
Mode: gen.WithContext

// 组合
Mode: gen.WithoutContext | gen.WithDefaultQuery
```

### 生成的 API

```go
// 生成的方法
func (u userDo) Where(...field.Expr) userDo
func (u userDo) Order(...field.Expr) userDo
func (u userDo) Limit(int) userDo
func (u userDo) Offset(int) userDo
func (u userDo) First() (*User, error)
func (u userDo) Find() ([]User, error)
func (u userDo) Count() (int64, error)
func (u userDo) Update(...field.Expr) error
func (u userDo) Delete() error
```

## 命名约定

### 表名到结构体

```go
// users → User
// user_profiles → UserProfile
// JSON 响应 → JSONResponse
```

### 字段名转换

```go
// id → ID
// user_name → UserName
// created_at → CreatedAt
```

### 自定义命名

```go
g.GenerateModel("users",
    gen.FieldStructName("User"), // 结构体名
    gen.FieldTable("users"),     // 表名
)
```

## 性能优势

### 零反射

```go
// raw GORM：运行时反射
db.Where(&User{Name: "John"}).First(&user)

// gorm-gen：编译时确定
q.User.Where(q.User.Name.Eq("John")).First()
```

### 预编译语句

```go
// 生成代码使用预编译语句
stmt := &gorm.Statement{...}
stmt.SQL.String = "SELECT * FROM users WHERE name = ?"
stmt.Vars = []interface{}{"John"}
```

## 混用模式

### 与 raw GORM 混用

```go
// gorm-gen 查询
user, err := q.User.Where(q.User.ID.Eq(1)).First()

// raw GORM 操作
db.Model(&user).Association("Posts").Find(&user.Posts)
```

### 动态查询

```go
// 使用 raw GORM 处理动态条件
query := db.Model(&User{})
if name != "" {
    query = query.Where("name = ?", name)
}
if age > 0 {
    query = query.Where("age > ?", age)
}
query.Find(&users)
```
