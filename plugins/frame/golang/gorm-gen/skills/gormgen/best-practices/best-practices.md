# 最佳实践

## 项目结构

### 推荐结构

```
project/
├── gen/              # 代码生成器
│   └── gen.go
├── query/            # 生成的查询代码（不要修改）
│   ├── gen.go
│   ├── user.gen.go
│   └── ...
├── model/            # 模型定义
│   ├── user.go
│   └── post.go
├── repository/       # 数据访问层
│   ├── user_repo.go
│   └── post_repo.go
├── service/          # 业务逻辑层
│   └── user_service.go
└── main.go
```

### 分层架构

```go
// repository/user_repo.go
package repository

type UserRepository interface {
    Create(user *model.User) error
    GetByID(id int64) (*model.User, error)
    Update(user *model.User) error
    Delete(id int64) error
}

type gormUserRepository struct {
    q *query.Query
}

func NewUserRepository(q *query.Query) UserRepository {
    return &gormUserRepository{q: q}
}

func (r *gormUserRepository) Create(user *model.User) error {
    return r.q.User.Create(user)
}

func (r *gormUserRepository) GetByID(id int64) (*model.User, error) {
    return r.q.User.Where(r.q.User.ID.Eq(id)).First()
}
```

## 代码生成

### 生成器配置

```go
// gen/gen.go
package main

import (
    "gorm.io/driver/mysql"
    "gorm.io/gen"
)

func main() {
    g := gen.NewGenerator(gen.Config{
        OutPath:       "../query",
        Mode:          gen.WithoutContext | gen.WithDefaultQuery,
        FieldNullable: true,
    })

    gormDB, _ := gorm.Open(mysql.Open("dsn"))
    g.UseDB(gormDB)

    // 生成模型
    g.ApplyBasic(
        g.GenerateModel("users"),
        g.GenerateModel("products"),
    )

    g.Execute()
}
```

### 自动化生成

```makefile
# Makefile
.PHONY: gen clean-gen

gen:
    cd gen && go run gen.go

clean-gen:
    rm -rf query/*.gen.go
```

### 版本控制

```gitignore
# .gitignore
query/*.gen.go       # 忽略生成的文件
!gen.go             # 不忽略生成器
```

## 使用模式

### Repository 模式

```go
type UserRepository struct {
    q *query.Query
}

func (r *UserRepository) GetActiveUsers() ([]model.User, error) {
    return r.q.User.Where(
        r.q.User.Active.Is(true),
    ).Find()
}
```

### Service 层

```go
type UserService struct {
    userRepo repository.UserRepository
}

func (s *UserService) CreateUser(name, email string) (*model.User, error) {
    // 验证
    if name == "" || email == "" {
        return nil, errors.New("invalid input")
    }

    // 创建
    user := &model.User{
        Name:  name,
        Email: email,
    }
    if err := s.userRepo.Create(user); err != nil {
        return nil, err
    }

    return user, nil
}
```

## 错误处理

### 错误定义

```go
var (
    ErrUserNotFound = errors.New("user not found")
    ErrInvalidInput = errors.New("invalid input")
)

func (r *UserRepository) GetByID(id int64) (*model.User, error) {
    user, err := r.q.User.Where(
        r.q.User.ID.Eq(id),
    ).First()
    if err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, ErrUserNotFound
        }
        return nil, err
    }
    return user, nil
}
```

## 性能优化

### 批量操作

```go
// 批量创建
func (r *UserRepository) BatchCreate(users []model.User) error {
    return r.q.User.CreateInBatches(users, 100)
}

// 批量更新
func (r *UserRepository) BatchUpdate(ids []int64, status string) error {
    return r.q.User.Where(
        r.q.User.ID.In(ids...),
    ).Update(
        r.q.User.Status,
        status,
    )
}
```

### 选择字段

```go
// 只查询需要的字段
func (r *UserRepository) GetUserNames() ([]string, error) {
    var names []string
    err := r.q.User.Select(
        r.q.User.Name,
    ).Scan(&names)
    return names, err
}
```

### 分页查询

```go
type Pagination struct {
    Page     int
    PageSize int
}

func (r *UserRepository) ListUsers(p Pagination) ([]model.User, int64, error) {
    var users []model.User
    var total int64

    // 计数
    total, err := r.q.User.Count()
    if err != nil {
        return nil, 0, err
    }

    // 分页查询
    err = r.q.User.
        Limit(p.PageSize).
        Offset((p.Page - 1) * p.PageSize).
        Find(&users)

    return users, total, err
}
```

## 事务处理

```go
func (s *UserService) TransferMoney(fromID, toID int64, amount float64) error {
    return s.q.Transaction(func(tx *query.Query) error {
        // 扣款
        from, err := tx.User.Where(tx.User.ID.Eq(fromID)).First()
        if err != nil {
            return err
        }

        // 加款
        to, err := tx.User.Where(tx.User.ID.Eq(toID)).First()
        if err != nil {
            return err
        }

        // 更新
        tx.User.Where(tx.User.ID.Eq(fromID)).Update(
            tx.User.Balance,
            tx.User.Balance.Sub(amount),
        )

        tx.User.Where(tx.User.ID.Eq(toID)).Update(
            tx.User.Balance,
            tx.User.Balance.Add(amount),
        )

        return nil
    })
}
```

## 测试

### 单元测试

```go
func TestUserRepository(t *testing.T) {
    // 使用内存数据库
    db, _ := gorm.Open(sqlite.Open("file::memory:"), &gorm.Config{})
    db.AutoMigrate(&model.User{})

    q := query.Use(db)
    repo := repository.NewUserRepository(q)

    // 测试创建
    user := &model.User{Name: "John"}
    err := repo.Create(user)
    if err != nil {
        t.Errorf("Create failed: %v", err)
    }

    // 测试查询
    found, err := repo.GetByID(user.ID)
    if err != nil {
        t.Errorf("GetByID failed: %v", err)
    }
    if found.Name != "John" {
        t.Errorf("Expected name 'John', got '%s'", found.Name)
    }
}
```

## 常见陷阱

### 1. 修改生成的代码

```go
// ❌ 错误：修改 query/*.gen.go
// query/user.gen.go
func (u userDo) Find() ([]User, error) {
    // 不要修改这里的代码
}

// ✅ 正确：在自定义文件中扩展方法
// query/user_custom.go
func (u userDo) FindActive() ([]User, error) {
    return u.Where(u.Active.Is(true)).Find()
}
```

### 2. 忘记重新生成

```bash
# 数据库变更后
# 1. 更新数据库
# 2. 重新生成代码
make clean-gen && make gen
# 3. 运行测试
go test ./...
```

### 3. 过度使用动态查询

```go
// ❌ 使用 raw GORM 动态查询
db.Where("name = ?", name).First(&user)

// ✅ 使用 gorm-gen-skills 类型安全查询
q.User.Where(q.User.Name.Eq(name)).First()
```

## 迁移建议

### 从 raw GORM 迁移

1. **设置代码生成器**
2. **生成基础代码**
3. **逐步替换查询**
4. **保持测试通过**
5. **完成迁移**

### 混合使用

```go
// 简单查询用 gorm-gen-skills
user, err := q.User.Where(q.User.ID.Eq(1)).First()

// 复杂查询用 raw GORM
db.Raw("SELECT * FROM users WHERE ...").Scan(&users)
```
