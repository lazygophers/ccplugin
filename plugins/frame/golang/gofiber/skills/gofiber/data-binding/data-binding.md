# Fiber 数据绑定

Fiber 提供了强大的数据绑定功能，支持从请求体、查询参数、路径参数等多种来源解析和验证数据。

## BodyParser

### JSON 解析

```go
type User struct {
    Name     string `json:"name"`
    Email    string `json:"email"`
    Password string `json:"password"`
}

func CreateUser(c *fiber.Ctx) error {
    user := new(User)
    if err := c.BodyParser(user); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(
            fiber.Map{"error": "invalid request body"},
        )
    }
    return c.JSON(user)
}

// 或使用结构体实例
func CreateUser(c *fiber.Ctx) error {
    var user User
    if err := c.BodyParser(&user); err != nil {
        return err
    }
    return c.JSON(user)
}
```

### XML 解析

```go
type Data struct {
    XMLName xml.Name `xml:"root"`
    Field1  string   `xml:"field1"`
    Field2  int      `xml:"field2"`
}

func CreateData(c *fiber.Ctx) error {
    var data Data
    if err := c.BodyParser(&data); err != nil {
        return err
    }
    return c.JSON(data)
}
```

### Form 解析

```go
type FormData struct {
    Name    string `form:"name"`
    Email   string `form:"email"`
    Age     int    `form:"age"`
    File    string `form:"file"`
}

func SubmitForm(c *fiber.Ctx) error {
    var data FormData
    if err := c.BodyParser(&data); err != nil {
        return err
    }
    return c.JSON(data)
}
```

## ReqParser

```go
// 使用 ReqParser 解析任意来源
type Params struct {
    Name string `query:"name" json:"name" xml:"name" form:"name"`
}

func handler(c *fiber.Ctx) error {
    var p Params
    if err := c.ReqParser(&p); err != nil {
        return err
    }
    return c.JSON(p)
}
```

## QueryParser

```go
type QueryParams struct {
    Search string `query:"search"`
    Page   int    `query:"page"`
    Limit  int    `query:"limit"`
    Tags   string `query:"tags"`
}

func ListItems(c *fiber.Ctx) error {
    var params QueryParams
    if err := c.QueryParser(&params); err != nil {
        return err
    }
    return c.JSON(params)
}
```

## ParamsParser

```go
type URIParams struct {
    ID int `params:"id"`
}

func GetUser(c *fiber.Ctx) error {
    var params URIParams
    if err := c.ParamsParser(&params); err != nil {
        return err
    }
    return c.JSON(fiber.Map{"id": params.ID})
}
```

## CookieParser

```go
type CookieData struct {
    Session string `cookie:"session"`
    UserID  string `cookie:"user_id"`
}

func handler(c *fiber.Ctx) error {
    var cookies CookieData
    if err := c.CookieParser(&cookies); err != nil {
        return err
    }
    return c.JSON(cookies)
}
```

## HeaderParser

```go
type HeaderData struct {
    Authorization string `header:"Authorization"`
    ContentType   string `header:"Content-Type"`
    UserAgent     string `header:"User-Agent"`
}

func handler(c *fiber.Ctx) error {
    var headers HeaderData
    if err := c.HeaderParser(&headers); err != nil {
        return err
    }
    return c.JSON(headers)
}
```

## 数据验证

### 使用 validator

```go
import "github.com/go-playground/validator/v10"

type User struct {
    Name     string `json:"name" validate:"required,min=3,max=50"`
    Email    string `json:"email" validate:"required,email"`
    Password string `json:"password" validate:"required,min=8"`
    Age      int    `json:"age" validate:"gte=0,lte=130"`
    Website  string `json:"website" validate:"url"`
}

func CreateUser(c *fiber.Ctx) error {
    user := new(User)
    if err := c.BodyParser(user); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(
            fiber.Map{"error": "invalid request body"},
        )
    }

    validate := validator.New()
    if err := validate.Struct(user); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(
            fiber.Map{"error": err.Error()},
        )
    }

    return c.JSON(user)
}
```

### 自定义验证器

```go
func customValidator(fl validator.FieldLevel) bool {
    value := fl.Field().String()
    return len(value) > 0 && value[0] == '@'
}

func main() {
    app := fiber.New()

    // 注册自定义验证器
    if v, ok := validator.New().(*validator.Validate); ok {
        v.RegisterValidation("startswithat", customValidator)
    }

    type Tweet struct {
        Content string `validate:"required,startswithat"`
    }
}
```

### 验证错误处理

```go
func formatValidationErrors(err error) []string {
    var errors []string

    if validationErrors, ok := err.(validator.ValidationErrors); ok {
        for _, e := range validationErrors {
            errors = append(errors, fmt.Sprintf(
                "Field '%s' failed validation '%s'",
                e.Field(),
                e.Tag(),
            ))
        }
    }

    return errors
}

func CreateUser(c *fiber.Ctx) error {
    user := new(User)
    if err := c.BodyParser(user); err != nil {
        return c.Status(fiber.StatusBadRequest).JSON(
            fiber.Map{"error": "invalid request body"},
        )
    }

    validate := validator.New()
    if err := validate.Struct(user); err != nil {
        errors := formatValidationErrors(err)
        return c.Status(fiber.StatusBadRequest).JSON(
            fiber.Map{"errors": errors},
        )
    }

    return c.JSON(user)
}
```

## 验证标签

| 标签 | 说明 | 示例 |
|------|------|------|
| required | 必填 | `validate:"required"` |
| min | 最小值/长度 | `validate:"min=3"` |
| max | 最大值/长度 | `validate:"max=50"` |
| len | 固定长度 | `validate:"len=10"` |
| email | 邮箱格式 | `validate:"email"` |
| url | URL 格式 | `validate:"url"` |
| gte | 大于等于 | `validate:"gte=0"` |
| lte | 小于等于 | `validate:"lte=130"` |
| alpha | 字母 | `validate:"alpha"` |
| alphanum | 字母数字 | `validate:"alphanum"` |
| numeric | 数字 | `validate:"numeric"` |

## 文件上传

### 单文件上传

```go
func UploadFile(c *fiber.Ctx) error {
    file, err := c.FormFile("file")
    if err != nil {
        return err
    }

    // 保存文件
    err = c.SaveFile(file, fmt.Sprintf("./uploads/%s", file.Filename))
    if err != nil {
        return err
    }

    return c.JSON(fiber.Map{
        "filename": file.Filename,
        "size":     file.Size,
    })
}
```

### 多文件上传

```go
func UploadFiles(c *fiber.Ctx) error {
    form, err := c.MultipartForm()
    if err != nil {
        return err
    }

    files := form.File["files"]
    var uploaded []string

    for _, file := range files {
        filename := fmt.Sprintf("./uploads/%s", file.Filename)
        if err := c.SaveFile(file, filename); err != nil {
            return err
        }
        uploaded = append(uploaded, file.Filename)
    }

    return c.JSON(fiber.Map{"files": uploaded})
}
```

### 文件流式处理

```go
func ProcessFileStream(c *fiber.Ctx) error {
    // 获取文件流
    fileHeader, err := c.FormFile("file")
    if err != nil {
        return err
    }

    file, err := fileHeader.Open()
    if err != nil {
        return err
    }
    defer file.Close()

    // 流式读取处理
    scanner := bufio.NewScanner(file)
    for scanner.Scan() {
        line := scanner.Text()
        // 处理每一行
    }

    return c.SendString("File processed")
}
```

## 请求限制

### BodyLimit

```go
// 全局限制
app := fiber.New(fiber.Config{
    BodyLimit: 4 * 1024 * 1024, // 4MB
})

// 路由级限制
app.Post("/upload", func(c *fiber.Ctx) error {
    return c.SendString("Upload endpoint")
}).BodyLimit(10 * 1024 * 1024) // 10MB
```

## 最佳实践

### 1. 使用结构体验证

```go
// ✅ 好的做法
type CreateUserRequest struct {
    Name     string `json:"name" validate:"required,min=3,max=50"`
    Email    string `json:"email" validate:"required,email"`
    Password string `json:"password" validate:"required,min=8"`
}

func CreateUser(c *fiber.Ctx) error {
    var req CreateUserRequest
    if err := c.BodyParser(&req); err != nil {
        return err
    }

    validate := validator.New()
    if err := validate.Struct(&req); err != nil {
        return err
    }

    return c.JSON(req)
}

// ❌ 不好的做法
func CreateUser(c *fiber.Ctx) error {
    name := c.Query("name")
    email := c.Query("email")
    password := c.Query("password")
    // 没有验证
}
```

### 2. 统一错误处理

```go
type APIError struct {
    Field   string `json:"field"`
    Message string `json:"message"`
}

func HandleValidationError(err error) error {
    var errors []APIError

    if validationErrors, ok := err.(validator.ValidationErrors); ok {
        for _, e := range validationErrors {
            errors = append(errors, APIError{
                Field:   e.Field(),
                Message: getErrorMessage(e),
            })
        }
    }

    return fiber.NewError(fiber.StatusBadRequest,
        fmt.Sprintf("Validation failed: %+v", errors))
}
```

### 3. 分离 DTO 和领域模型

```go
// DTO（数据传输对象）
type CreateUserDTO struct {
    Name     string `json:"name" validate:"required,min=3,max=50"`
    Email    string `json:"email" validate:"required,email"`
    Password string `json:"password" validate:"required,min=8"`
}

// 领域模型
type User struct {
    ID        uint
    Name      string
    Email     string
    Password  string
    CreatedAt time.Time
}

func CreateUser(c *fiber.Ctx) error {
    var dto CreateUserDTO
    if err := c.BodyParser(&dto); err != nil {
        return err
    }

    // 验证
    validate := validator.New()
    if err := validate.Struct(&dto); err != nil {
        return err
    }

    // 转换为领域模型
    user := User{
        Name:      dto.Name,
        Email:     dto.Email,
        Password:  hashPassword(dto.Password),
        CreatedAt: time.Now(),
    }

    // 保存...
    return c.JSON(user)
}
```
