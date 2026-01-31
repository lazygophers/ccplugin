# Fiber 测试

Fiber 提供了完善的测试支持，包括单元测试、集成测试和性能测试。

## 测试设置

### 测试依赖

```go
// go.mod
require (
    github.com/gofiber/fiber/v2 v2.x.x
    github.com/stretchr/testify v1.x.x
)
```

### 测试文件结构

```
project/
├── handler/
│   └── user.go
├── handler/
│   └── user_test.go
```

## 单元测试

### Handler 测试

```go
// handler/user.go
package handler

func GetUser(c *fiber.Ctx) error {
    id := c.Params("id")
    if id == "" {
        return c.Status(fiber.StatusBadRequest).JSON(
            fiber.Map{"error": "id is required"},
        )
    }
    return c.JSON(fiber.Map{"id": id, "name": "John"})
}
```

```go
// handler/user_test.go
package handler

import (
    "io"
    "net/http/httptest"
    "testing"

    "github.com/gofiber/fiber/v2"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestGetUser(t *testing.T) {
    // 创建应用
    app := fiber.New()
    app.Get("/user/:id", GetUser)

    tests := []struct {
    name       string
    path       string
    statusCode int
    body       string
    }{
        {
            name:       "valid user",
            path:       "/user/123",
            statusCode: 200,
            body:       `{"id":"123","name":"John"}`,
        },
        {
            name:       "missing id",
            path:       "/user/",
            statusCode: 404,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // 创建请求
            req := httptest.NewRequest("GET", tt.path, nil)

            // 执行请求
            resp, err := app.Test(req)
            require.NoError(t, err)

            // 验证状态码
            assert.Equal(t, tt.statusCode, resp.StatusCode)

            // 验证响应体
            if tt.body != "" {
                body, _ := io.ReadAll(resp.Body)
                assert.JSONEq(t, tt.body, string(body))
            }
        })
    }
}
```

### 中间件测试

```go
func TestAuthMiddleware(t *testing.T) {
    app := fiber.New()
    app.Use(AuthMiddleware())
    app.Get("/protected", func(c *fiber.Ctx) error {
        return c.SendString("protected")
    })

    t.Run("with valid token", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/protected", nil)
        req.Header.Set("Authorization", "Bearer valid-token")
        resp, err := app.Test(req)
        require.NoError(t, err)
        assert.Equal(t, 200, resp.StatusCode)
    })

    t.Run("without token", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/protected", nil)
        resp, err := app.Test(req)
        require.NoError(t, err)
        assert.Equal(t, 401, resp.StatusCode)
    })
}
```

## 集成测试

### 完整应用测试

```go
func TestUserAPI(t *testing.T) {
    // 设置应用
    app := SetupApp()

    // 创建用户
    t.Run("create user", func(t *testing.T) {
        body := `{"name":"John","email":"john@example.com"}`
        req := httptest.NewRequest("POST", "/users", strings.NewReader(body))
        req.Header.Set("Content-Type", "application/json")

        resp, err := app.Test(req)
        require.NoError(t, err)
        assert.Equal(t, 201, resp.StatusCode)
    })

    // 获取用户列表
    t.Run("list users", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/users", nil)
        resp, err := app.Test(req)
        require.NoError(t, err)
        assert.Equal(t, 200, resp.StatusCode)
    })
}
```

### 数据库集成测试

```go
func TestUserAPIWithDB(t *testing.T) {
    // 设置测试数据库
    db := setupTestDB(t)
    defer cleanupTestDB(t, db)

    app := SetupApp(db)

    // 测试创建用户
    body := `{"name":"John","email":"john@example.com"}`
    req := httptest.NewRequest("POST", "/users", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")

    resp, err := app.Test(req)
    require.NoError(t, err)
    assert.Equal(t, 201, resp.StatusCode)

    // 验证数据库中的数据
    var user User
    db.First(&user, "email = ?", "john@example.com")
    assert.Equal(t, "John", user.Name)
}
```

## HTTP 方法测试

### GET 请求

```go
func TestGetRequest(t *testing.T) {
    app := fiber.New()
    app.Get("/", func(c *fiber.Ctx) error {
        return c.SendString("Hello, World!")
    })

    req := httptest.NewRequest("GET", "/", nil)
    resp, err := app.Test(req)

    require.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode)

    body, _ := io.ReadAll(resp.Body)
    assert.Equal(t, "Hello, World!", string(body))
}
```

### POST 请求

```go
func TestPostRequest(t *testing.T) {
    app := fiber.New()
    app.Post("/users", func(c *fiber.Ctx) error {
        return c.SendString("User created")
    })

    body := strings.NewReader(`{"name":"John"}`)
    req := httptest.NewRequest("POST", "/users", body)
    req.Header.Set("Content-Type", "application/json")

    resp, err := app.Test(req)
    require.NoError(t, err)
    assert.Equal(t, 200, resp.StatusCode)
}
```

### PUT/PATCH 请求

```go
func TestPutRequest(t *testing.T) {
    app := fiber.New()
    app.Put("/users/:id", func(c *fiber.Ctx) error {
        id := c.Params("id")
        return c.SendString("User " + id + " updated")
    })

    body := strings.NewReader(`{"name":"Jane"}`)
    req := httptest.NewRequest("PUT", "/users/123", body)
    req.Header.Set("Content-Type", "application/json")

    resp, err := app.Test(req)
    require.NoError(t, err)

    respBody, _ := io.ReadAll(resp.Body)
    assert.Equal(t, "User 123 updated", string(respBody))
}
```

### DELETE 请求

```go
func TestDeleteRequest(t *testing.T) {
    app := fiber.New()
    app.Delete("/users/:id", func(c *fiber.Ctx) error {
        return c.SendStatus(204)
    })

    req := httptest.NewRequest("DELETE", "/users/123", nil)
    resp, err := app.Test(req)

    require.NoError(t, err)
    assert.Equal(t, 204, resp.StatusCode)
}
```

## JSON 测试

### 解析 JSON 响应

```go
func TestJSONResponse(t *testing.T) {
    app := fiber.New()
    app.Get("/user", func(c *fiber.Ctx) error {
        return c.JSON(fiber.Map{
            "id":   123,
            "name": "John",
        })
    })

    req := httptest.NewRequest("GET", "/user", nil)
    resp, err := app.Test(req)
    require.NoError(t, err)

    var result map[string]interface{}
    body, _ := io.ReadAll(resp.Body)
    json.Unmarshal(body, &result)

    assert.Equal(t, float64(123), result["id"])
    assert.Equal(t, "John", result["name"])
}
```

### JSON 请求

```go
func TestJSONRequest(t *testing.T) {
    app := fiber.New()
    app.Post("/users", func(c *fiber.Ctx) error {
        var user User
        if err := c.BodyParser(&user); err != nil {
            return err
        }
        return c.JSON(user)
    })

    body := strings.NewReader(`{"name":"John","email":"john@example.com"}`)
    req := httptest.NewRequest("POST", "/users", body)
    req.Header.Set("Content-Type", "application/json")

    resp, err := app.Test(req)
    require.NoError(t, err)

    var result User
    respBody, _ := io.ReadAll(resp.Body)
    json.Unmarshal(respBody, &result)

    assert.Equal(t, "John", result.Name)
}
```

## 表单测试

```go
func TestFormRequest(t *testing.T) {
    app := fiber.New()
    app.Post("/form", func(c *fiber.Ctx) error {
        name := c.FormValue("name")
        email := c.FormValue("email")
        return c.JSON(fiber.Map{"name": name, "email": email})
    })

    form := strings.NewReader("name=John&email=john@example.com")
    req := httptest.NewRequest("POST", "/form", form)
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")

    resp, err := app.Test(req)
    require.NoError(t, err)

    var result map[string]string
    body, _ := io.ReadAll(resp.Body)
    json.Unmarshal(body, &result)

    assert.Equal(t, "John", result["name"])
    assert.Equal(t, "john@example.com", result["email"])
}
```

## 查询参数测试

```go
func TestQueryParams(t *testing.T) {
    app := fiber.New()
    app.Get("/search", func(c *fiber.Ctx) error {
        query := c.Query("q")
        return c.SendString("Search: " + query)
    })

    req := httptest.NewRequest("GET", "/search?q=golang", nil)
    resp, err := app.Test(req)
    require.NoError(t, err)

    body, _ := io.ReadAll(resp.Body)
    assert.Equal(t, "Search: golang", string(body))
}
```

## Header 测试

```go
func TestHeaders(t *testing.T) {
    app := fiber.New()
    app.Get("/", func(c *fiber.Ctx) error {
        auth := c.Get("Authorization")
        if auth == "" {
            return c.Status(401).SendString("Unauthorized")
        }
        return c.SendString("Authorized")
    })

    t.Run("with auth header", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/", nil)
        req.Header.Set("Authorization", "Bearer token")
        resp, _ := app.Test(req)
        body, _ := io.ReadAll(resp.Body)
        assert.Equal(t, "Authorized", string(body))
    })

    t.Run("without auth header", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/", nil)
        resp, _ := app.Test(req)
        assert.Equal(t, 401, resp.StatusCode)
    })
}
```

## Cookie 测试

```go
func TestCookies(t *testing.T) {
    app := fiber.New()
    app.Get("/set", func(c *fiber.Ctx) error {
        c.Cookie(&fiber.Cookie{
            Name:  "session",
            Value: "abc123",
        })
        return c.SendString("Cookie set")
    })

    app.Get("/get", func(c *fiber.Ctx) error {
        session := c.Cookies("session")
        return c.SendString("Session: " + session)
    })

    t.Run("set cookie", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/set", nil)
        resp, _ := app.Test(req)

        cookies := resp.Cookies()
        assert.Len(t, cookies, 1)
        assert.Equal(t, "session", cookies[0].Name)
        assert.Equal(t, "abc123", cookies[0].Value)
    })

    t.Run("get cookie", func(t *testing.T) {
        req := httptest.NewRequest("GET", "/get", nil)
        req.AddCookie(&http.Cookie{Name: "session", Value: "abc123"})
        resp, _ := app.Test(req)

        body, _ := io.ReadAll(resp.Body)
        assert.Equal(t, "Session: abc123", string(body))
    })
}
```

## 性能测试

### 基准测试

```go
func BenchmarkHandler(b *testing.B) {
    app := fiber.New()
    app.Get("/", func(c *fiber.Ctx) error {
        return c.SendString("Hello, World!")
    })

    b.ResetTimer()
    b.ReportAllocs()

    for i := 0; i < b.N; i++ {
        req := httptest.NewRequest("GET", "/", nil)
        resp, err := app.Test(req)
        if err != nil || resp.StatusCode != 200 {
            b.Fatal(err)
        }
    }
}
```

### 并发测试

```go
func TestConcurrentRequests(t *testing.T) {
    app := fiber.New()
    app.Get("/", func(c *fiber.Ctx) error {
        time.Sleep(10 * time.Millisecond)
        return c.SendString("OK")
    })

    concurrent := 100
    done := make(chan bool)

    for i := 0; i < concurrent; i++ {
        go func() {
            req := httptest.NewRequest("GET", "/", nil)
            resp, err := app.Test(req)
            require.NoError(t, err)
            assert.Equal(t, 200, resp.StatusCode)
            done <- true
        }()
    }

    for i := 0; i < concurrent; i++ {
        <-done
    }
}
```

## 测试最佳实践

### 1. 使用表驱动测试

```go
func TestValidation(t *testing.T) {
    tests := []struct {
    name    string
    input   string
    wantErr bool
    }{
        {"valid email", "test@example.com", false},
        {"invalid email", "invalid", true},
        {"empty email", "", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateEmail(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateEmail() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

### 2. 使用测试助手

```go
// 测试助手
func setupTestApp() *fiber.App {
    app := fiber.New(fiber.Config{
        DisableStartupMessage: true,
    })
    SetupRoutes(app)
    return app
}

func makeRequest(app *fiber.App, method, path string, body io.Reader) *http.Response {
    req := httptest.NewRequest(method, path, body)
    req.Header.Set("Content-Type", "application/json")
    resp, _ := app.Test(req)
    return resp
}

// 使用
func TestAPI(t *testing.T) {
    app := setupTestApp()
    resp := makeRequest(app, "GET", "/users", nil)
    assert.Equal(t, 200, resp.StatusCode)
}
```

### 3. 使用测试断言

```go
import "github.com/stretchr/testify/assert"

func TestAssertions(t *testing.T) {
    app := fiber.New()
    app.Get("/", func(c *fiber.Ctx) error {
        return c.JSON(fiber.Map{"id": 123})
    })

    req := httptest.NewRequest("GET", "/", nil)
    resp, _ := app.Test(req)

    assert.Equal(t, 200, resp.StatusCode)
    assert.Contains(t, resp.Header.Get("Content-Type"), "application/json")
}
```
