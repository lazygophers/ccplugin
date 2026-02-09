---
name: lazygophers-json-skills
description: lazygophers/utils/json JSON 处理库规范 - 平台优化的 JSON 编解码，支持 sonic 加速、文件操作和流式处理
---

# lazygophers-json - JSON 处理库

平台优化的 JSON 处理库，在 Linux/macOS/AMD64 自动使用 sonic，其他平台使用标准库。

## 特性

- ⚡ **2-10x 性能提升** - sonic 在 Linux/macOS/AMD64
- 🔄 **透明降级** - 其他平台自动使用标准库
- 📁 **文件操作** - MarshalToFile/UnmarshalFromFile
- 🌊 **流式处理** - Encoder/Decoder 支持
- 🔧 **Panic 版本** - MustMarshal/MustUnmarshal

## 平台选择

```go
import "github.com/lazygophers/utils/json"

// 无需手动选择，自动根据平台优化
// Linux/AMD64, macOS/AMD64 → sonic (2-10x faster)
// 其他平台 → encoding/json (标准库)
```

### 平台支持矩阵

| 平台 | 架构 | 实现库 | 性能 |
|------|------|--------|------|
| Linux | AMD64 | sonic | 2-10x |
| macOS | AMD64 | sonic | 2-10x |
| Linux | ARM64 | stdlib | 1x |
| macOS | ARM64 | stdlib | 1x |
| Windows | Any | stdlib | 1x |
| 其他 | Any | stdlib | 1x |

## 基础使用

### Marshal（序列化）

```go
import "github.com/lazygophers/utils/json"

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

user := User{
    ID:    1,
    Name:  "John",
    Email: "john@example.com",
}

// 序列化为 JSON
data, err := jsonx.Marshal(user)
if err != nil {
    return err
}
fmt.Println(string(data))
// {"id":1,"name":"John","email":"john@example.com"}

// 带缩进的序列化
data, err := jsonx.MarshalIndent(user, "", "  ")
/*
{
  "id": 1,
  "name": "John",
  "email": "john@example.com"
}
*/
```

### Unmarshal（反序列化）

```go
jsonStr := `{"id":1,"name":"John","email":"john@example.com"}`

// 反序列化
var user User
err := jsonx.Unmarshal([]byte(jsonStr), &user)
if err != nil {
    return err
}
fmt.Println(user.Name)  // John
```

### Panic 版本

```go
// MustMarshal - 失败时 panic
data := jsonx.MustMarshal(user)

// MustUnmarshal - 失败时 panic
jsonx.MustUnmarshal(data, &user)
```

## 文件操作

### MarshalToFile（写入文件）

```go
user := User{ID: 1, Name: "John"}

// 序列化并写入文件
err := jsonx.MarshalToFile("user.json", user)
if err != nil {
    return err
}

// 带缩进
err := jsonx.MarshalToFileIndent("user.json", user, "", "  ")
```

### UnmarshalFromFile（读取文件）

```go
// 从文件读取并反序列化
var user User
err := jsonx.UnmarshalFromFile("user.json", &user)
if err != nil {
    return err
}
```

### 应用场景

```go
// 配置文件加载
type Config struct {
    Host string `json:"host"`
    Port int    `json:"port"`
}

var cfg Config
err := jsonx.UnmarshalFromFile("config.json", &cfg)

// 数据持久化
err := jsonx.MarshalToFile("data.json", data)
```

## 流式处理

### Encoder（流式编码）

```go
file, err := os.Create("output.json")
if err != nil {
    return err
}
defer file.Close()

encoder := jsonx.NewEncoder(file)
encoder.SetIndent("", "  ")  // 设置缩进

// 编码多个对象
for _, user := range users {
    if err := encoder.Encode(user); err != nil {
        return err
    }
}
```

### Decoder（流式解码）

```go
file, err := os.Open("input.json")
if err != nil {
    return err
}
defer file.Close()

decoder := jsonx.NewDecoder(file)

// 解码多个对象
for decoder.More() {
    var user User
    if err := decoder.Decode(&user); err != nil {
        return err
    }
    // 处理 user
}
```

### 大文件处理

```go
// 逐行处理大型 JSON 文件
file, _ := os.Open("large-file.jsonl")
decoder := jsonx.NewDecoder(file)

for decoder.More() {
    var item Item
    if err := decoder.Decode(&item); err != nil {
        break
    }
    // 处理 item（不会一次性加载整个文件到内存）
}
```

## 高级功能

### 自定义 Marshal/Unmarshal

```go
type Time time.Time

// 自定义 MarshalJSON
func (t Time) MarshalJSON() ([]byte, error) {
    return jsonx.Marshal(time.Time(t).Format("2006-01-02"))
}

// 自定义 UnmarshalJSON
func (t *Time) UnmarshalJSON(data []byte) error {
    var s string
    if err := jsonx.Unmarshal(data, &s); err != nil {
        return err
    }
    parsed, err := time.Parse("2006-01-02", s)
    if err != nil {
        return err
    }
    *t = Time(parsed)
    return nil
}
```

### 嵌套结构

```go
type Address struct {
    City    string `json:"city"`
    Country string `json:"country"`
}

type User struct {
    ID      int     `json:"id"`
    Name    string  `json:"name"`
    Address Address `json:"address"`
}

// 反序列化嵌套结构
jsonStr := `{
    "id": 1,
    "name": "John",
    "address": {
        "city": "New York",
        "country": "USA"
    }
}`
var user User
jsonx.Unmarshal([]byte(jsonStr), &user)
```

### 动态 JSON

```go
// 使用 map[string]interface{}
var data map[string]interface{}
jsonx.Unmarshal([]byte(`{"name":"John","age":30}`), &data)
fmt.Println(data["name"])  // John

// 使用 []interface{}
var array []interface{}
jsonx.Unmarshal([]byte(`[1,2,3]`), &array)

// 使用 json.RawMessage 保留原始 JSON
type Data struct {
    Field1 string          `json:"field1"`
    Field2 json.RawMessage `json:"field2"`  // 延迟解析
}
```

## 性能优化

### 结构体字段重用

```go
// ✅ 使用 sync.Pool 重用缓冲区
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func toJSON(v interface{}) (string, error) {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufferPool.Put(buf)
    }()

    encoder := jsonx.NewEncoder(buf)
    err := encoder.Encode(v)
    return buf.String(), err
}
```

### 避免不必要的反射

```go
// ✅ 使用 map[string]interface{} 而非反射
data := map[string]interface{}{
    "id":   user.ID,
    "name": user.Name,
}
jsonx.Marshal(data)

// ❌ 避免使用 reflect 自行序列化
```

### 预分配缓冲区

```go
// 如果知道大致大小，预分配
data := make([]byte, 0, 1024)  // 预分配 1KB
buf := bytes.NewBuffer(data)
encoder := jsonx.NewEncoder(buf)
```

## 最佳实践

### 1. 错误处理

```go
// ✅ 总是检查错误
data, err := jsonx.Marshal(user)
if err != nil {
    log.Error("marshal failed", log.Field("error", err))
    return err
}

// ❌ 不要忽略错误
data, _ := jsonx.Marshal(user)
```

### 2. 文件路径

```go
// ✅ 使用绝对路径或相对项目的路径
path := filepath.Join(projectDir, "config", "app.json")
jsonx.UnmarshalFromFile(path, &cfg)

// ❌ 不要硬编码绝对路径
jsonx.UnmarshalFromFile("/home/user/project/config.json", &cfg)
```

### 3. 大文件处理

```go
// ✅ 使用流式处理
decoder := jsonx.NewDecoder(file)
for decoder.More() {
    // 逐个处理
}

// ❌ 不要一次性加载大文件
data, _ := os.ReadFile("large-file.json")
jsonx.Unmarshal(data, &result)  // 可能 OOM
```

### 4. 配置文件

```go
// ✅ 配置文件使用带缩进的 JSON
err := jsonx.MarshalToFileIndent("config.json", cfg, "", "  ")

// ❌ 生产配置不要用缩进（增加文件大小）
err := jsonx.MarshalToFile("config.json", cfg)
```

## 性能基准

```
# Linux/AMD64 (sonic)
BenchmarkMarshal-8     5000000    250 ns/op    512 B/op    2 allocs/op
BenchmarkUnmarshal-8   2000000    680 ns/op    640 B/op    12 allocs/op

# macOS/AMD64 (sonic)
BenchmarkMarshal-8     4000000    310 ns/op    512 B/op    2 allocs/op
BenchmarkUnmarshal-8   1500000    890 ns/op    640 B/op    12 allocs/op

# Linux/ARM64 (stdlib)
BenchmarkMarshal-8     1000000   1200 ns/op    768 B/op    5 allocs/op
BenchmarkUnmarshal-8    800000   1500 ns/op    896 B/op    18 allocs/op
```

## 参考资源

- [lazygophers/utils/jsonx GitHub](https://github.com/lazygophers/utils/tree/main/json)
- [sonic GitHub](https://github.com/bytedance/sonic)
- [encoding/json 文档](https://pkg.go.dev/encoding/json)
