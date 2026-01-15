---
name: gtpl
description: Go 模板(Golang Template)开发规范 - 提供 text/template 和 html/template 最佳实践指导，包括安全性、性能优化和常见错误模式
auto-activate:
  patterns:
    - "**/*template*"
    - "**/gtpl"
    - "**/tpl"
---

# Go 模板(Golang Template)开发规范

## 核心原则

Go 的模板库（`text/template` 和 `html/template`）提供了强大的文本生成能力。本规范定义了高质量、安全、高效的 Go 模板开发标准。

### ✅ 必须遵守

1. **优先 html/template** - 需要生成 HTML 时必须使用 `html/template` 而非 `text/template`
2. **自动转义** - 利用 `html/template` 的自动转义防止 XSS 攻击
3. **模板复用** - 使用 `ParseFiles` 或 `ParseGlob` 批量加载模板
4. **预编译** - 启动时预编译所有模板，避免运行时错误
5. **错误处理** - 渲染失败时明确处理，不应该忽略错误
6. **数据验证** - 在渲染前验证数据完整性
7. **缓存策略** - 对频繁使用的模板使用缓存

### ❌ 禁止行为

- 使用 `text/template` 生成 HTML（导致 XSS 漏洞）
- 动态构建模板字符串后解析
- 在模板中进行复杂业务逻辑
- 忽略模板渲染错误
- 直接使用用户输入到模板（未经验证）
- 模板中调用不安全函数
- 频繁编译同一模板

## 模板选择指南

### text/template - 仅用于非 HTML

```go
import "text/template"

// ✅ 用于配置文件、纯文本输出
const configTpl = `
server:
  host: {{.Host}}
  port: {{.Port}}
`

tpl, err := template.New("config").Parse(configTpl)
if err != nil {
    log.Fatalf("parse template: %v", err)
}

// 渲染配置
err = tpl.Execute(os.Stdout, config)
if err != nil {
    log.Errorf("render template: %v", err)
}
```

### html/template - 必须用于 HTML

```go
import (
    "html/template"
    "net/http"
)

// ✅ 生成 HTML 时必须用 html/template
const htmlTpl = `
<div class="user">
    <h1>{{.Name}}</h1>
    <p>{{.Bio}}</p>
</div>
`

tpl, err := template.New("user").Parse(htmlTpl)
if err != nil {
    log.Fatalf("parse template: %v", err)
}

// html/template 会自动转义 HTML 特殊字符
http.HandleFunc("/user", func(w http.ResponseWriter, r *http.Request) {
    user := map[string]string{
        "Name": "<script>alert('xss')</script>",  // 安全转义
        "Bio":  "Hello & welcome",                 // & 被转义为 &amp;
    }
    err = tpl.Execute(w, user)
    if err != nil {
        log.Errorf("render: %v", err)
        http.Error(w, "Internal Server Error", http.StatusInternalServerError)
    }
})
```

## 模板结构设计

### 模板组织（强制）

```go
// ✅ 推荐结构
project/
├── templates/
│   ├── layout.html       // 主布局
│   ├── header.html       // 头部
│   ├── footer.html       // 底部
│   ├── user/
│   │   ├── list.html     // 用户列表
│   │   └── detail.html   // 用户详情
│   └── admin/
│       └── dashboard.html
└── template.go           // 模板管理器
```

### 模板管理器（强制）

```go
package template

import (
    "html/template"
    "log"
    "path/filepath"
)

type Manager struct {
    templates map[string]*template.Template
}

// ✅ 启动时预编译所有模板
func New(templateDir string) (*Manager, error) {
    m := &Manager{
        templates: make(map[string]*template.Template),
    }

    // 使用 ParseGlob 加载所有模板
    patterns := []string{
        filepath.Join(templateDir, "*.html"),
        filepath.Join(templateDir, "*/*.html"),
    }

    for _, pattern := range patterns {
        tpls, err := template.ParseGlob(pattern)
        if err != nil {
            log.Errorf("parse template glob %s: %v", pattern, err)
            return nil, err
        }

        // 为每个模板创建独立的副本
        for _, tpl := range tpls.Templates() {
            newTpl := template.New(tpl.Name())
            // 复制所有函数
            if tpls.Funcs != nil {
                newTpl.Funcs(tpls.Funcs)
            }
            m.templates[tpl.Name()] = newTpl
        }
    }

    return m, nil
}

// ✅ 提供安全的渲染接口
func (m *Manager) Render(name string, data interface{}) (string, error) {
    tpl, exists := m.templates[name]
    if !exists {
        log.Errorf("template not found: %s", name)
        return "", ErrTemplateNotFound
    }

    var buf bytes.Buffer
    err = tpl.Execute(&buf, data)
    if err != nil {
        log.Errorf("render template %s: %v", name, err)
        return "", err
    }

    return buf.String(), nil
}
```

## 安全性规范

### XSS 防护（关键）

```go
import "html/template"

// ✅ html/template 自动转义
const tpl = `
<h1>{{.Title}}</h1>
<p>{{.Content}}</p>
`

data := map[string]string{
    "Title": "<script>alert('xss')</script>",
    "Content": "<img src=x onerror=alert('xss')>",
}

// 输出（安全）：
// <h1>&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;</h1>
// <p>&lt;img src=x onerror=alert(&#39;xss&#39;)&gt;</p>
```

### 属性转义

```go
const tpl = `
<input type="text" value="{{.UserInput}}" />
<a href="{{.URL}}">Link</a>
<img alt="{{.Alt}}" />
`

// html/template 根据上下文自动选择转义方式
data := map[string]string{
    "UserInput": `" onclick="alert('xss')`,  // 转义为 &quot;
    "URL": "javascript:alert('xss')",        // 过滤 javascript:
    "Alt": "image & text",                    // 转义为 image &amp; text
}
```

### 避免常见漏洞

```go
// ❌ 禁止 - HTML 注入
const unsafeTpl = `
<div>{{.HTML}}</div>  // 如果使用 text/template 会有 XSS
`

// ✅ 必须 - 使用 html/template
const safeTpl = `
<div>{{.Content | html}}</div>
`

// 如果必须插入不转义的 HTML（仅在完全信任数据时）
data := map[string]interface{}{
    "Content": template.HTML("<b>Bold Text</b>"),
}
```

## 模板函数设计

### 自定义函数（强制规范）

```go
import "html/template"

// ✅ 定义安全的自定义函数
func CreateTemplate() *template.Template {
    funcMap := template.FuncMap{
        // ✅ 格式化日期
        "formatDate": func(t time.Time) string {
            return t.Format("2006-01-02 15:04:05")
        },

        // ✅ 字符串截断
        "truncate": func(s string, length int) string {
            if len(s) <= length {
                return s
            }
            return s[:length] + "..."
        },

        // ✅ 判断列表是否为空
        "isEmpty": func(items interface{}) bool {
            v := reflect.ValueOf(items)
            switch v.Kind() {
            case reflect.Array, reflect.Slice:
                return v.Len() == 0
            default:
                return false
            }
        },

        // ✅ 条件选择
        "ternary": func(condition bool, trueVal, falseVal interface{}) interface{} {
            if condition {
                return trueVal
            }
            return falseVal
        },
    }

    const tpl = `
    <p>{{.Date | formatDate}}</p>
    <p>{{.Title | truncate 20}}</p>
    {{if not (isEmpty .Items)}}
        <ul>
        {{range .Items}}<li>{{.}}</li>{{end}}
        </ul>
    {{end}}
    `

    return template.New("test").Funcs(funcMap).Parse(tpl)
}

// ❌ 禁止 - 在函数中进行复杂业务逻辑
"complexLogic": func(data map[string]interface{}) string {
    // 不要在这里做复杂处理，应该在数据准备阶段完成
    return fmt.Sprintf("%v", data)
}
```

### 嵌套模板

```go
// layout.html
`
<!DOCTYPE html>
<html>
<head>
    {{template "header"}}
</head>
<body>
    {{template "content" .}}
</body>
<footer>
    {{template "footer"}}
</footer>
</html>
`

// ✅ 使用 named templates
tpl := template.New("page")
tpl.Parse("layout.html")
tpl.Parse("header.html")
tpl.Parse("footer.html")
// ...
```

## 性能优化

### 模板缓存（强制）

```go
import "sync"

type TemplateCache struct {
    templates map[string]*template.Template
    mu        sync.RWMutex
}

// ✅ 启动时预编译，运行时只读缓存
func NewTemplateCache(dir string) (*TemplateCache, error) {
    tc := &TemplateCache{
        templates: make(map[string]*template.Template),
    }

    // 启动时加载所有模板
    entries, err := os.ReadDir(dir)
    if err != nil {
        return nil, err
    }

    for _, entry := range entries {
        if entry.IsDir() {
            continue
        }

        path := filepath.Join(dir, entry.Name())
        tpl, err := template.ParseFiles(path)
        if err != nil {
            return nil, err
        }

        tc.templates[entry.Name()] = tpl
    }

    return tc, nil
}

// ✅ 读缓存时加读锁
func (tc *TemplateCache) Get(name string) *template.Template {
    tc.mu.RLock()
    defer tc.mu.RUnlock()
    return tc.templates[name]
}

// ❌ 禁止 - 每次渲染都编译
for i := 0; i < 1000; i++ {
    tpl, _ := template.Parse(tplString)  // 性能差
    tpl.Execute(os.Stdout, data)
}
```

### 批量渲染

```go
// ✅ 使用 bytes.Buffer 缓冲输出
func RenderBatch(tpl *template.Template, dataList []interface{}) (string, error) {
    var buf bytes.Buffer
    for _, data := range dataList {
        err = tpl.Execute(&buf, data)
        if err != nil {
            log.Errorf("render: %v", err)
            return "", err
        }
    }
    return buf.String(), nil
}

// ❌ 禁止 - 多次字符串拼接
result := ""
for _, data := range dataList {
    var buf bytes.Buffer
    tpl.Execute(&buf, data)
    result += buf.String()  // 低效的字符串拼接
}
```

## 常见错误模式

### 错误 1：忽略编译错误

```go
// ❌ 错误 - 忽略错误
tpl, _ := template.Parse(input)  // 编译错误被忽略
tpl.Execute(os.Stdout, data)     // 可能 panic

// ✅ 正确 - 处理错误
tpl, err := template.Parse(input)
if err != nil {
    log.Fatalf("parse template: %v", err)
}
tpl.Execute(os.Stdout, data)
```

### 错误 2：渲染时不处理错误

```go
// ❌ 错误 - HTTP 响应中
http.HandleFunc("/page", func(w http.ResponseWriter, r *http.Request) {
    tpl.Execute(w, data)  // 错误无法恢复
})

// ✅ 正确 - 先渲染到缓冲区
http.HandleFunc("/page", func(w http.ResponseWriter, r *http.Request) {
    var buf bytes.Buffer
    err = tpl.Execute(&buf, data)
    if err != nil {
        log.Errorf("render: %v", err)
        http.Error(w, "Internal Error", http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "text/html; charset=utf-8")
    w.Write(buf.Bytes())
})
```

### 错误 3：模板中的复杂逻辑

```go
// ❌ 错误 - 在模板中进行复杂处理
`
{{$total := 0}}
{{range .Items}}
    {{$total = add $total .Price}}
{{end}}
<p>Total: {{$total}}</p>
`

// ✅ 正确 - 在数据准备阶段计算
type PageData struct {
    Items []Item
    Total float64
}

data := PageData{
    Items: items,
    Total: calculateTotal(items),
}
```

## 最佳实践检查清单

### 设计阶段

- [ ] 确定使用 `html/template` 还是 `text/template`
- [ ] 设计模板目录结构
- [ ] 识别可复用的模板片段
- [ ] 定义必要的自定义函数
- [ ] 规划模板缓存策略

### 实现阶段

- [ ] 创建模板管理器
- [ ] 启动时预编译所有模板
- [ ] 实现错误处理
- [ ] 验证数据完整性
- [ ] 添加自动转义（html/template）

### 测试阶段

- [ ] 测试 HTML 安全性（特殊字符转义）
- [ ] 测试嵌套模板
- [ ] 测试自定义函数
- [ ] 测试错误场景
- [ ] 性能基准测试

### 生产阶段

- [ ] 监控模板渲染错误
- [ ] 监控渲染性能
- [ ] 定期审计模板安全性
- [ ] 更新模板时无需重启应用（如果支持热加载）

## 参考资源

- [Go text/template 文档](https://pkg.go.dev/text/template)
- [Go html/template 文档](https://pkg.go.dev/html/template)
- [OWASP XSS 防护](https://owasp.org/www-community/attacks/xss/)
- [Go Template 最佳实践](https://golang.org/pkg/html/template/)

---

**规范版本**：1.0
**最后更新**：2026-01-11
