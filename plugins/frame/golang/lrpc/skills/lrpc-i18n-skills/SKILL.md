---
name: lrpc-i18n-skills
description: lrpc i18n 国际化中间件规范 - 提供多语言支持、本地化资源管理和语言切换功能
---

# lrpc-i18n - 国际化中间件

提供完整的国际化（i18n）支持，包括多语言切换、本地化资源管理和翻译功能。

## 特性

- 🌍 **多语言支持** - 支持任意语言扩展
- 🔄 **动态切换** - 运行时切换语言
- 📦 **资源管理** - JSON/YAML 翻译文件
- 🎯 **上下文感知** - 基于 HTTP Header 自动检测语言
- 🔧 **易于扩展** - 添加新语言只需添加翻译文件

## 基础使用

### 初始化中间件

```go
import (
    "github.com/lazygophers/lrpc"
    "github.com/lazygophers/lrpc/middleware/i18n"
)

// 创建 i18n 中间件
i18nMiddleware := i18n.New(
    i18n.WithLanguages("en", "zh-CN", "ja"),
    i18n.WithDefaultLanguage("en"),
    i18n.WithLoadPath("./locales"),
)

server := lrpc.NewServer()
server.Use(i18nMiddleware)
```

### 翻译文件结构

```
locales/
├── en.json
├── zh-CN.json
└── ja.json
```

### 翻译文件格式

```json
// locales/en.json
{
  "hello": "Hello",
  "welcome": "Welcome to our service",
  "user_profile": "User Profile",
  "errors": {
    "not_found": "Not Found",
    "unauthorized": "Unauthorized"
  }
}
```

```json
// locales/zh-CN.json
{
  "hello": "你好",
  "welcome": "欢迎使用我们的服务",
  "user_profile": "用户资料",
  "errors": {
    "not_found": "未找到",
    "unauthorized": "未授权"
  }
}
```

## 在代码中使用

### 获取翻译

```go
func Handler(ctx *lrpc.Context) error {
    // 获取当前语言
    lang := i18n.GetLanguage(ctx)
    fmt.Println("Current language:", lang)  // "en", "zh-CN", etc.

    // 简单翻译
    message := i18n.T(ctx, "hello")
    // "Hello" (en) or "你好" (zh-CN)

    // 嵌套翻译
    errorMsg := i18n.T(ctx, "errors.not_found")
    // "Not Found" (en) or "未找到" (zh-CN)

    return ctx.JSON(lrpc.H{
        "message": message,
    })
}
```

### 带参数的翻译

```json
// locales/en.json
{
  "welcome_user": "Welcome, {{.name}}!",
  "item_count": "You have {{.count}} items"
}
```

```go
func Handler(ctx *lrpc.Context) error {
    // 带参数的翻译
    message := i18n.T(ctx, "welcome_user", i18n.Params{
        "name": "John",
    })
    // "Welcome, John!"

    countMsg := i18n.T(ctx, "item_count", i18n.Params{
        "count": 5,
    })
    // "You have 5 items"

    return ctx.JSON(lrpc.H{"message": message})
}
```

### 复数形式

```json
// locales/en.json
{
  "item": {
    "one": "{{.count}} item",
    "other": "{{.count}} items"
  }
}
```

```go
func Handler(ctx *lrpc.Context) error {
    message := i18n.T(ctx, "item", i18n.Params{
        "count": 1,
    })
    // "1 item"

    message = i18n.T(ctx, "item", i18n.Params{
        "count": 5,
    })
    // "5 items"

    return ctx.JSON(lrpc.H{"message": message})
}
```

## 语言检测

### 自动检测

i18n 中间件按以下优先级检测语言：

1. **查询参数** - `?lang=zh-CN`
2. **Cookie** - `lang=zh-CN`
3. **HTTP Header** - `Accept-Language: zh-CN,zh;q=0.9`
4. **默认语言** - 配置的默认语言

### 手动设置语言

```go
func Handler(ctx *lrpc.Context) error {
    // 手动设置当前请求的语言
    i18n.SetLanguage(ctx, "zh-CN")

    // 后续翻译将使用设置的语言
    message := i18n.T(ctx, "hello")
    // "你好"

    return ctx.JSON(lrpc.H{"message": message})
}
```

### 获取支持的语言列表

```go
func Handler(ctx *lrpc.Context) error {
    // 获取所有支持的语言
    languages := i18n.GetLanguages()
    // ["en", "zh-CN", "ja"]

    return ctx.JSON(lrpc.H{
        "languages": languages,
    })
}
```

## 高级功能

### 热重载翻译文件

```go
// 开启热重载（开发模式）
i18nMiddleware := i18n.New(
    i18n.WithLoadPath("./locales"),
    i18n.WithHotReload(true),
)
```

### 自定义翻译存储

```go
// 使用自定义存储（如数据库）
type DBStore struct{}

func (s *DBStore) GetTranslation(lang, key string) (string, error) {
    // 从数据库获取翻译
    return db.GetTranslation(lang, key)
}

i18nMiddleware := i18n.New(
    i18n.WithCustomStore(&DBStore{}),
)
```

### 中间件顺序

```go
server := lrpc.NewServer()

// i18n 应该在其他需要翻译的中间件之前
server.Use(
    i18nMiddleware,     // 1. 先设置语言
    recoveryMiddleware, // 2. 然后是其他中间件
    authMiddleware,
)
```

## 最佳实践

### 1. 翻译键命名

```go
// ✅ 使用层级结构
"errors.not_found"
"errors.unauthorized"
"user.profile.title"

// ❌ 避免扁平结构
"NOT_FOUND_ERROR"
"USER_PROFILE_TITLE"
```

### 2. 默认值

```go
// 在翻译键不存在时返回键本身
message := i18n.T(ctx, "some.untranslated.key")
// 返回: "some.untranslated.key"
```

### 3. 客户端语言选择

```go
// 前端发送 Accept-Language 头
fetch('/api/data', {
    headers: {
        'Accept-Language': navigator.language || 'en'
    }
})
```

### 4. URL 路径

```go
// 支持语言前缀的路由
server.GET("/:lang/api/users", Handler)
server.GET("/api/users", Handler)

// 在 Handler 中使用 :lang 参数
func Handler(ctx *lrpc.Context) error {
    if lang := ctx.Param("lang"); lang != "" {
        i18n.SetLanguage(ctx, lang)
    }
    // ...
}
```

## 常见语言代码

| 语言 | 代码 |
|------|------|
| 英语 | `en` |
| 简体中文 | `zh-CN` |
| 繁体中文 | `zh-TW` |
| 日语 | `ja` |
| 韩语 | `ko` |
| 法语 | `fr` |
| 德语 | `de` |
| 西班牙语 | `es` |
| 俄语 | `ru` |
| 阿拉伯语 | `ar` |

## 参考资源

- [lazygophers/lrpc i18n](https://github.com/lazygophers/lrpc/tree/master/middleware/i18n)
- [i18n 最佳实践](https://www.w3.org/International/questions/qa-i18n)
- [BCP 47 语言标签](https://tools.ietf.org/html/bcp47)
