# 测试

## 单元测试

### Mock 数据库

```go
import (
    "gorm.io/driver/sqlite"
    "gorm.io/gorm"
    "testing"
)

func setupTestDB(t *testing.T) *gorm.DB {
    db, err := gorm.Open(sqlite.Open("file::memory:?cache=shared"), &gorm.Config{})
    if err != nil {
        t.Fatal(err)
    }
    db.AutoMigrate(&User{})
    return db
}

func TestUserCreate(t *testing.T) {
    db := setupTestDB(t)

    user := User{Name: "John", Email: "john@example.com"}
    if err := db.Create(&user).Error; err != nil {
        t.Errorf("Failed to create user: %v", err)
    }

    if user.ID == 0 {
        t.Error("Expected user ID to be set")
    }
}
```

### 测试 CRUD

```go
func TestUserCRUD(t *testing.T) {
    db := setupTestDB(t)

    // Create
    user := User{Name: "John", Email: "john@example.com"}
    if err := db.Create(&user).Error; err != nil {
        t.Fatalf("Failed to create user: %v", err)
    }

    // Read
    var found User
    if err := db.First(&found, user.ID).Error; err != nil {
        t.Errorf("Failed to find user: %v", err)
    }
    if found.Name != "John" {
        t.Errorf("Expected name 'John', got '%s'", found.Name)
    }

    // Update
    if err := db.Model(&user).Update("name", "Jane").Error; err != nil {
        t.Errorf("Failed to update user: %v", err)
    }

    // Delete
    if err := db.Delete(&user).Error; err != nil {
        t.Errorf("Failed to delete user: %v", err)
    }
}
```

### 测试验证

```go
func TestUserValidation(t *testing.T) {
    db := setupTestDB(t)

    tests := []struct {
        name    string
        user    User
        wantErr bool
    }{
        {"valid", User{Name: "John", Email: "john@example.com"}, false},
        {"empty name", User{Name: "", Email: "john@example.com"}, true},
        {"empty email", User{Name: "John", Email: ""}, true},
        {"invalid email", User{Name: "John", Email: "invalid"}, true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := db.Create(&tt.user).Error
            if (err != nil) != tt.wantErr {
                t.Errorf("Create() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

## 集成测试

### Docker 测试数据库

```go
func setupIntegrationDB(t *testing.T) *gorm.DB {
    dsn := os.Getenv("TEST_DSN")
    if dsn == "" {
        dsn = "user:pass@tcp(localhost:3306)/test_db?charset=utf8mb4"
    }

    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    if err != nil {
        t.Skipf("Skipping integration test: %v", err)
    }

    // 清理并迁移
    db.Migrator().DropTable(&User{})
    db.AutoMigrate(&User{})

    return db
}

func TestUserIntegration(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test in short mode")
    }

    db := setupIntegrationDB(t)
    // 测试代码...
}
```

### 测试数据

```go
func seedTestData(db *gorm.DB) {
    users := []User{
        {Name: "John", Email: "john@example.com", Age: 25},
        {Name: "Jane", Email: "jane@example.com", Age: 30},
        {Name: "Bob", Email: "bob@example.com", Age: 35},
    }
    db.Create(&users)
}

func TestUserQueries(t *testing.T) {
    db := setupTestDB(t)
    seedTestData(db)

    var users []User
    db.Where("age > ?", 28).Find(&users)

    if len(users) != 2 {
        t.Errorf("Expected 2 users, got %d", len(users))
    }
}
```

## Mock 行为

### sqlmock

```go
import "github.com/DATA-DOG/go-sqlmock"

func TestWithSQLMock(t *testing.T) {
    db, mock, err := sqlmock.New()
    if err != nil {
        t.Fatal(err)
    }
    defer db.Close()

    gormDB, err := gorm.Open(mysql.New(mysql.Config{
        Conn:                      db,
        SkipInitializeWithVersion: true,
    }), &gorm.Config{})
    if err != nil {
        t.Fatal(err)
    }

    // 设置期望
    rows := sqlmock.NewRows([]string{"id", "name"}).
        AddRow(1, "John")

    mock.ExpectQuery("^SELECT \\* FROM `users` WHERE id = \\?").
        WithArgs(1).
        WillReturnRows(rows)

    // 执行查询
    var user User
    if err := gormDB.First(&user, 1).Error; err != nil {
        t.Errorf("Error: %v", err)
    }

    // 验证期望
    if err := mock.ExpectationsWereMet(); err != nil {
        t.Errorf("Unmet expectations: %v", err)
    }
}
```

### 接口 Mock

```go
type UserRepository interface {
    GetByID(id uint) (*User, error)
    Create(user *User) error
}

type GormUserRepository struct {
    db *gorm.DB
}

func (r *GormUserRepository) GetByID(id uint) (*User, error) {
    var user User
    err := r.db.First(&user, id).Error
    return &user, err
}

type MockUserRepository struct {
    MockGetByID func(id uint) (*User, error)
    MockCreate func(user *User) error
}

func (m *MockUserRepository) GetByID(id uint) (*User, error) {
    return m.MockGetByID(id)
}

func (m *MockUserRepository) Create(user *User) error {
    return m.MockCreate(user)
}

// 测试
func TestUserService(t *testing.T) {
    mockRepo := &MockUserRepository{
        MockGetByID: func(id uint) (*User, error) {
            return &User{ID: id, Name: "John"}, nil
        },
    }

    service := NewUserService(mockRepo)
    user, err := service.GetUser(1)
    if err != nil {
        t.Errorf("Error: %v", err)
    }
    if user.Name != "John" {
        t.Errorf("Expected name 'John', got '%s'", user.Name)
    }
}
```

## 测试事务

```go
func TestTransaction(t *testing.T) {
    db := setupTestDB(t)

    err := db.Transaction(func(tx *gorm.DB) error {
        // 创建用户
        if err := tx.Create(&User{Name: "John"}).Error; err != nil {
            return err
        }

        // 模拟错误
        return errors.New("test error")
    })

    if err == nil {
        t.Error("Expected error, got nil")
    }

    // 验证回滚
    var count int64
    db.Model(&User{}).Count(&count)
    if count != 0 {
        t.Error("Expected no users due to rollback")
    }
}
```

## 测试钩子

```go
func TestBeforeCreate(t *testing.T) {
    db := setupTestDB(t)

    user := User{Name: "", Email: "john@example.com"}
    err := db.Create(&user).Error

    if err == nil {
        t.Error("Expected validation error, got nil")
    }
}
```

## 基准测试

```go
func BenchmarkCreate(b *testing.B) {
    db := setupBenchmarkDB()
    user := User{Name: "John", Email: "john@example.com"}

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        db.Create(&user)
    }
}

func BenchmarkQuery(b *testing.B) {
    db := setupBenchmarkDB()
    db.Create(&User{Name: "John"})

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        var user User
        db.First(&user, 1)
    }
}
```

## 测试最佳实践

### 1. 隔离测试

```go
func TestIsolation(t *testing.T) {
    db := setupTestDB(t)

    t.Run("test1", func(t *testing.T) {
        db.Create(&User{Name: "John"})
    })

    t.Run("test2", func(t *testing.T) {
        // test1 的数据不应该影响 test2
        var count int64
        db.Model(&User{}).Count(&count)
        if count != 0 {
            t.Error("Tests should be isolated")
        }
    })
}
```

### 2. 使用事务回滚

```go
func withTransaction(t *testing.T, fn func(tx *gorm.DB)) {
    db := setupTestDB(t)
    db.Transaction(func(tx *gorm.DB) error {
        fn(tx)
        return errors.New("rollback") // 强制回滚
    })
}

func TestWithRollback(t *testing.T) {
    withTransaction(t, func(tx *gorm.DB) {
        tx.Create(&User{Name: "John"})
    })

    // 数据已回滚
    var count int64
    setupTestDB(t).Model(&User{}).Count(&count)
    if count != 0 {
        t.Error("Expected no data after rollback")
    }
}
```

### 3. 测试辅助函数

```go
// 辅助函数
func createUser(t *testing.T, db *gorm.DB, name, email string) User {
    user := User{Name: name, Email: email}
    if err := db.Create(&user).Error; err != nil {
        t.Fatalf("Failed to create user: %v", err)
    }
    return user
}

func assertUserCount(t *testing.T, db *gorm.DB, expected int64) {
    var count int64
    db.Model(&User{}).Count(&count)
    if count != expected {
        t.Errorf("Expected %d users, got %d", expected, count)
    }
}

// 使用
func TestHelperFunctions(t *testing.T) {
    db := setupTestDB(t)

    createUser(t, db, "John", "john@example.com")
    createUser(t, db, "Jane", "jane@example.com")

    assertUserCount(t, db, 2)
}
```

## 测试工具

### testfixtures

```go
import "github.com/testfixtures/testfixtures/v3"

func loadFixtures(db *gorm.DB) error {
    fixtures, err := testfixtures.NewFolder(
        testfixtures.Database(db),
        testfixtures.DangerousSkipTestDatabaseCheck(),
        testfixtures.Location("fixtures"),
    )
    if err != nil {
        return err
    }
    return fixtures.Load()
}

// fixtures/users.yaml
- id: 1
  name: John
  email: john@example.com

- id: 2
  name: Jane
  email: jane@example.com
```

### 工厂模式

```go
type UserFactory struct{}

func (f *UserFactory) Create(overrides ...func(*User)) User {
    user := User{
        Name:  "John",
        Email: "john@example.com",
        Age:   25,
    }
    for _, override := range overrides {
        override(&user)
    }
    return user
}

// 使用
func TestFactory(t *testing.T) {
    factory := &UserFactory{}

    user := factory.Create(func(u *User) {
        u.Name = "Jane"
        u.Age = 30
    })

    if user.Name != "Jane" || user.Age != 30 {
        t.Error("Factory override failed")
    }
}
```
