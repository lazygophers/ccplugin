# 代码生成

## 基础配置

### 生成器初始化

```go
package main

import (
    "gorm.io/driver/mysql"
    "gorm.io/gen"
    "gorm.io/gorm"
)

func main() {
    // 初始化生成器
    g := gen.NewGenerator(gen.Config{
        OutPath:       "./query",        // 输出目录
        Mode:          gen.WithoutContext, // 模式
        FieldNullable: true,              // 允许 NULL
        FieldSignable: false,             // 无符号
    })

    // 连接数据库
    gormDB, err := gorm.Open(mysql.Open("user:pass@tcp(127.0.0.1:3306)/db"))
    if err != nil {
        panic(err)
    }

    // 使用数据库
    g.UseDB(gormDB)

    // 生成模型
    g.ApplyBasic(
        g.GenerateModel("users"),
        g.GenerateModel("products"),
    )

    // 执行生成
    g.Execute()
}
```

## 配置选项

### 输出配置

```go
g := gen.NewGenerator(gen.Config{
    OutPath:           "./query",       // 输出路径
    OutFile:           "gen.go",        // 输出文件名
    ModelPkgPath:      "./model",       // 模型包路径
    WithUnitTest:      true,            // 生成单元测试
    FieldNullable:     true,            // 可空字段
    FieldCoverable:    false,           // 是否覆盖
    FieldSignable:     false,           // 是否有符号
    FieldWithIndexTag: false,           // 索引标签
    FieldWithTypeTag:  true,            // 类型标签
})
```

### 模式配置

```go
// 模式选项
const (
    WithoutContext   = 1 << iota // 无上下文
    WithDefaultQuery             // 默认查询
    WithContext                  // 带上下文
)

// 单一模式
Mode: gen.WithoutContext

// 组合模式
Mode: gen.WithContext | gen.WithDefaultQuery
```

## 模型生成

### 从数据库生成

```go
// 基础生成
g.ApplyBasic(
    g.GenerateModel("users"),
    g.GenerateModel("products"),
    g.GenerateModel("orders"),
)

// 生成所有表
g.ApplyBasic(g.GenerateAllTable()...)
```

### 字段配置

```go
// 自定义字段
g.ApplyBasic(
    g.GenerateModel("users",
        // JSON 标签
        gen.FieldJSON("name", "userName"),

        // 新标签
        gen.FieldNewTag("age", `validate:"gte=18,lte=120"`),

        // 忽略字段
        gen.FieldIgnore("password"),

        // 字段类型
        gen.FieldType("balance", "decimal(10,2)"),

        // 字段默认值
        gen.FieldDefault("status", "'active'"),

        // 字段注释
        gen.FieldComment("id", "用户ID"),
    ),
)
```

### 表配置

```go
g.ApplyBasic(
    g.GenerateModel("users",
        // 表名
        gen.FieldTable("users"),

        // 结构体名
        gen.FieldStructName("User"),

        // 命名策略
        gen.FieldNamingStrategy(
            schema.NamingStrategy{
                SingularTable: true,
            },
        ),
    ),
)
```

### 关联生成

```go
// 关联外键
g.GenerateModel("orders",
    gen.FieldRelate(
        model.Relate{
            Type:        gen.ManyToOne,
            RelateTable: "users",
            RelateField: "orders",
            Field:       "User",
            Relates:     []*gen.RelateConfig{
                {Field: &field{Field: field.String{}, Name: "UserID"}},
            },
        },
    ),
)
```

## 高级生成

### 过滤表

```go
// 只生成特定表
g.ApplyBasic(
    g.GenerateModel("users"),
    g.GenerateModel("products"),
)

// 排除表
tables, _ := gormDB.Migrator().GetTables()
for _, table := range tables {
    if table != "migrations" && table != "temp_tables" {
        g.ApplyBasic(g.GenerateModel(table))
    }
}
```

### 自定义模板

```go
g := gen.NewGenerator(gen.Config{
    OutPath:  "./query",
    Template: "./templates/custom.tmpl", // 自定义模板
})
```

### 钩子函数

```go
// 生成前钩子
g.WithHook(
    gen.Hook{
        BeforeCreate: func(info *model.Info) error {
            // 修改模型信息
            return nil
        },
    },
)
```

## 运行生成

### 命令行

```bash
# 直接运行
go run gen.go

# 或使用 gentool
gentool -dsn "user:pass@tcp(127.0.0.1:3306)/db" -tables "users,products"
```

### go generate

```go
//go:generate go run gen.go
package main

// 运行
go generate
```

### Makefile

```makefile
.PHONY: gen

gen:
    go run gen.go

clean-gen:
    rm -rf query/*.go
```

## 生成的文件

### 目录结构

```
query/
├── gen.go              # 主文件
├── users.gen.go        # 用户表生成代码
├── products.gen.go     # 产品表生成代码
├── gen_test.go         # 单元测试
└── users.gen_test.go   # 用户表测试
```

### gen.go

```go
package query

var (
    User  userDo
    Product productDo
)

type Query struct {
    db  *gorm.DB
    User  userDo
    Product productDo
}

func Use(db *gorm.DB) *Query {
    return &Query{
        db:     db,
        User:   *User.WithContext(db),
        Product: *Product.WithContext(db),
    }
}
```

### users.gen.go

```go
package query

type user struct {
    gen.DO

    ID        field.Int64
    Name      field.String
    Email     field.String
    Age       field.Int
    CreatedAt field.Time
}

func User() userDo {
    return userDo{user{gen.DO{}}}
}

func (u user) TableName() string {
    return "users"
}
```

## 最佳实践

### 1. 分离生成代码

```
project/
├── gen/              # 生成器代码
│   └── gen.go
├── query/            # 生成查询代码（不要手动修改）
│   └── *.gen.go
├── model/            # 模型定义
│   └── user.go
└── repository/       # 数据访问层
    └── user_repo.go
```

### 2. 版本控制

```gitignore
# .gitignore
query/*.gen.go       # 忽略生成的文件
!gen.go             # 不忽略生成器
```

### 3. 自动化

```yaml
# .github/workflows/gen.yml
name: Generate Code

on:
  push:
    paths:
      - 'gen/**'
      - 'schema/**'

jobs:
  gen:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-go@v2
      - run: go run gen.go
      - run: go test ./...
```

## 常见问题

### Q: 如何重新生成？

```bash
rm -rf query/*.go
go run gen.go
```

### Q: 如何添加自定义方法？

```go
// query/users_custom.go（不会被覆盖）
package query

func (u userDo) FindActive() ([]User, error) {
    return u.Where(u.Active.Is(true)).Find()
}
```

### Q: 如何处理模型变更？

```bash
# 1. 修改数据库
# 2. 重新生成
go run gen.go
# 3. 运行测试
go test ./...
```
