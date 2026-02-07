# Golang 测试规范

## 核心原则

### ✅ 必须遵守

1. **测试文件命名** - 测试文件以 `_test.go` 结尾
2. **测试函数命名** - 测试函数以 `Test` 开头
3. **测试覆盖** - 关键业务逻辑必须有测试
4. **测试隔离** - 测试之间相互独立，不依赖执行顺序
5. **测试可读性** - 测试代码清晰易懂，测试意图明确

### ❌ 禁止行为

- 测试依赖执行顺序
- 测试之间共享状态
- 测试中硬编码环境依赖
- 忽略测试失败
- 测试代码过于复杂

## 测试类型

### 单元测试

```go
// ✅ 正确 - 单元测试
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

### 表驱动测试

```go
// ✅ 正确 - 表驱动测试
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

### 集成测试

```go
// ✅ 正确 - 集成测试
func TestUserIntegration(t *testing.T) {
    // 设置测试数据库
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)

    // 创建测试用户
    user := &User{
        Email:    "test@example.com",
        Password: "password123",
    }
    err := db.Create(user).Error
    if err != nil {
        t.Fatalf("failed to create test user: %v", err)
    }

    // 测试登录
    loggedIn, err := UserLogin(user.Email, "password123")
    if err != nil {
        t.Errorf("UserLogin() error = %v", err)
    }
    if loggedIn == nil {
        t.Error("UserLogin() returned nil user")
    }
}
```

### 基准测试

```go
// ✅ 正确 - 基准测试
func BenchmarkProcessData(b *testing.B) {
    data := generateTestData(1000)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ProcessData(data)
    }
}

// ✅ 正确 - 带内存分配的基准测试
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
// ✅ 正确 - Setup 和 Teardown
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
// ✅ 正确 - Mock 全局状态
func TestUserLoginWithMock(t *testing.T) {
    // 保存原始状态
    originalUser := state.User
    defer func() {
        state.User = originalUser
    }()

    // 设置 Mock
    state.User = &MockUserModel{
        users: map[int64]*User{
            1: {Id: 1, Email: "test@example.com"},
        },
    }

    // 执行测试
    user, err := UserLogin("test@example.com", "password")
    if err != nil {
        t.Errorf("UserLogin() error = %v", err)
    }
    if user == nil || user.Email != "test@example.com" {
        t.Error("UserLogin() returned unexpected user")
    }
}
```

## 测试最佳实践

### 使用 testify

```go
import "github.com/stretchr/testify/assert"
import "github.com/stretchr/testify/require"

// ✅ 正确 - 使用 assert（失败继续执行）
func TestCalculate(t *testing.T) {
    result := Calculate(2, 3)
    assert.Equal(t, 5, result)
    assert.NotZero(t, result)
}

// ✅ 正确 - 使用 require（失败立即停止）
func TestCalculateWithRequire(t *testing.T) {
    result := Calculate(2, 3)
    require.Equal(t, 5, result)
    require.NotZero(t, result)
}
```

### 测试覆盖率

```bash
# 运行测试并显示覆盖率
go test -v -cover ./...

# 生成覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# 检查覆盖率阈值
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total
```

### 并发测试

```go
// ✅ 正确 - 并发测试
func TestConcurrentAccess(t *testing.T) {
    counter := NewCounter()

    var wg sync.WaitGroup
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter.Increment()
        }()
    }

    wg.Wait()

    if counter.Value() != 100 {
        t.Errorf("counter.Value() = %d, want 100", counter.Value())
    }
}
```

### 测试错误处理

```go
// ✅ 正确 - 测试错误处理
func TestUserLoginError(t *testing.T) {
    tests := []struct {
        name     string
        username string
        password string
        wantErr  bool
        errType  error
    }{
        {
            name:     "empty username",
            username: "",
            password: "password",
            wantErr:  true,
            errType:  ErrInvalidUsername,
        },
        {
            name:     "empty password",
            username: "testuser",
            password: "",
            wantErr:  true,
            errType:  ErrInvalidPassword,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := UserLogin(tt.username, tt.password)
            if (err != nil) != tt.wantErr {
                t.Errorf("UserLogin() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if tt.wantErr && !errors.Is(err, tt.errType) {
                t.Errorf("UserLogin() error = %v, want %v", err, tt.errType)
            }
        })
    }
}
```

## 测试组织

### 测试文件位置

```
// ✅ 正确 - 测试文件与实现在同包
impl/
├── user.go
├── user_test.go
├── friend.go
└── friend_test.go

// ❌ 错误 - 测试文件在单独目录
impl/
├── user.go
└── friend.go

test/
├── user_test.go
└── friend_test.go
```

### 测试命名规范

```go
// ✅ 正确 - 清晰的测试命名
func TestUserLogin_Success(t *testing.T) {}
func TestUserLogin_InvalidPassword(t *testing.T) {}
func TestUserLogin_UserNotFound(t *testing.T) {}

// ❌ 错误 - 不清晰的测试命名
func TestUserLogin1(t *testing.T) {}
func TestUserLogin2(t *testing.T) {}
func TestUserLogin3(t *testing.T) {}
```

## 检查清单

提交代码前，确保：

- [ ] 测试文件以 `_test.go` 结尾
- [ ] 测试函数以 `Test` 开头
- [ ] 关键业务逻辑有测试覆盖
- [ ] 测试之间相互独立
- [ ] 测试代码清晰易懂
- [ ] 使用表驱动测试
- [ ] 测试有适当的 Setup 和 Teardown
- [ ] 测试覆盖率符合要求
- [ ] 并发代码有并发测试
- [ ] 错误处理有错误测试
