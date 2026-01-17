---
name: gtpl-functions-performance-patterns
description: Go 模板函数、性能优化和常见错误模式 - 包括自定义函数、嵌套模板、缓存策略和最佳实践
---

# Go 模板函数、性能优化和常见错误模式

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
        err := tpl.Execute(&buf, data)
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
    err := tpl.Execute(&buf, data)
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

## 最佳实践检查清单 - 测试阶段

- [ ] 测试 HTML 安全性（特殊字符转义）
- [ ] 测试嵌套模板
- [ ] 测试自定义函数
- [ ] 测试错误场景
- [ ] 性能基准测试

## 最佳实践检查清单 - 生产阶段

- [ ] 监控模板渲染错误
- [ ] 监控渲染性能
- [ ] 定期审计模板安全性
- [ ] 更新模板时无需重启应用（如果支持热加载）

## 参考资源

- [Go text/template 文档](https://pkg.go.dev/text/template)
- [Go html/template 文档](https://pkg.go.dev/html/template)
- [OWASP XSS 防护](https://owasp.org/www-community/attacks/xss/)
- [Go Template 最佳实践](https://golang.org/pkg/html/template/)
