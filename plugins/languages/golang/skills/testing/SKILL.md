---
name: testing
description: Go 测试规范：单元测试、表驱动测试、基准测试。写测试时必须加载。
---

# Go 测试规范

## 核心原则

### 必须遵守

1. **测试文件命名** - 测试文件以 `_test.go` 结尾
2. **测试函数命名** - 测试函数以 `Test` 开头
3. **测试覆盖** - 关键业务逻辑必须有测试
4. **测试隔离** - 测试之间相互独立，不依赖执行顺序
5. **测试可读性** - 测试代码清晰易懂，测试意图明确
6. **严禁修改生产代码** - 测试代码必须独立，不修改生产代码，不为了测试而修改生产代码

### 禁止行为

- 测试依赖执行顺序
- 测试之间共享状态
- 测试中硬编码环境依赖
- 忽略测试失败
- 测试代码过于复杂

## 单元测试

```go
func TestUserLogin(t *testing.T) {
    tests := []struct {
        name     string
        username string
        password string
        wantErr  bool
    }{
        {
            name:     "valid login",
            username: "testuser",
            password: "password123",
            wantErr:  false,
        },
        {
            name:     "invalid password",
            username: "testuser",
            password: "wrongpassword",
            wantErr:  true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            user, err := UserLogin(tt.username, tt.password)
            if (err != nil) != tt.wantErr {
                t.Errorf("UserLogin() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !tt.wantErr && user == nil {
                t.Error("UserLogin() returned nil user")
            }
        })
    }
}
```

## 表驱动测试

```go
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        email string
        valid bool
    }{
        {"test@example.com", true},
        {"invalid", false},
        {"", false},
        {"test@", false},
    }

    for _, tt := range tests {
        t.Run(tt.email, func(t *testing.T) {
            got := ValidateEmail(tt.email)
            if got != tt.valid {
                t.Errorf("ValidateEmail(%q) = %v, want %v", tt.email, got, tt.valid)
            }
        })
    }
}
```

## 集成测试

```go
func TestUserIntegration(t *testing.T) {
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)

    user := &User{
        Email:    "test@example.com",
        Password: "password123",
    }
    err := db.Create(user).Error
    if err != nil {
        t.Fatalf("failed to create test user: %v", err)
    }

    loggedIn, err := UserLogin(user.Email, "password123")
    if err != nil {
        t.Errorf("UserLogin() error = %v", err)
    }
    if loggedIn == nil {
        t.Error("UserLogin() returned nil user")
    }
}
```

## 基准测试

```go
func BenchmarkProcessData(b *testing.B) {
    data := generateTestData(1000)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ProcessData(data)
    }
}

func BenchmarkProcessDataWithAllocs(b *testing.B) {
    data := generateTestData(1000)

    b.ReportAllocs()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ProcessData(data)
    }
}
```

## 测试辅助函数

### Setup 和 Teardown

```go
func setupTestDB(t *testing.T) *gorm.DB {
    db, err := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
    if err != nil {
        t.Fatalf("failed to open test database: %v", err)
    }

    err = db.AutoMigrate(&User{}, &Friend{}, &Message{})
    if err != nil {
        t.Fatalf("failed to migrate test database: %v", err)
    }

    return db
}

func cleanupTestDB(t *testing.T, db *gorm.DB) {
    sqlDB, err := db.DB()
    if err != nil {
        t.Errorf("failed to get sql.DB: %v", err)
        return
    }
    sqlDB.Close()
}
```

### Mock 全局状态

```go
func TestUserLoginWithMock(t *testing.T) {
    originalUser := state.User
    defer func() {
        state.User = originalUser
    }()

    state.User = &MockUserModel{
        users: map[int64]*User{
            1: {Id: 1, Email: "test@example.com"},
        },
    }

    user, err := UserLogin("test@example.com", "password")
    if err != nil {
        t.Errorf("UserLogin() error = %v", err)
    }
    if user == nil || user.Email != "test@example.com" {
        t.Error("UserLogin() returned unexpected user")
    }
}
```

## 使用 testify

```go
import "github.com/stretchr/testify/assert"
import "github.com/stretchr/testify/require"

func TestCalculate(t *testing.T) {
    result := Calculate(2, 3)
    assert.Equal(t, 5, result)
    assert.NotZero(t, result)
}

func TestCalculateWithRequire(t *testing.T) {
    result := Calculate(2, 3)
    require.Equal(t, 5, result)
    require.NotZero(t, result)
}
```

## 测试覆盖率

```bash
go test -v -cover ./...

go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total
```

## 测试文件位置

```
<path>/
├── user.go
├── user_test.go
├── friend.go
└── friend_test.go
```

## 检查清单

- [ ] 测试文件以 `_test.go` 结尾
- [ ] 测试函数以 `Test` 开头
- [ ] 关键业务逻辑有测试覆盖
- [ ] 测试之间相互独立
- [ ] 测试代码清晰易懂
- [ ] 使用表驱动测试
- [ ] 测试有适当的 Setup 和 Teardown
- [ ] 测试覆盖率符合要求（≥95%）
- [ ] 并发代码有并发测试
- [ ] 错误处理有错误测试
- [ ] 测试代码符合 Go 标准库编码规范
- [ ] 测试通过率必须为 100%
