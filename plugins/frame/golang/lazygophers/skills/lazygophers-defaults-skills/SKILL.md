---
name: lazygophers-defaults-skills
description: lazygophers/utils defaults 模块完整指南 - 结构体默认值设置、配置覆盖、类型处理和最佳实践
---

# lazygophers-defaults - lazygophers/utils defaults 模块完整指南

## 概述

`defaults` 是 lazygophers/utils 库中用于设置结构体默认值的核心模块。它通过 struct tag `default` 声明默认值，支持所有基础类型、复杂类型、嵌套结构体，并提供灵活的配置选项和错误处理机制。

### 核心特性

- ✅ **声明式默认值**：通过 struct tag 定义默认值
- ✅ **类型全覆盖**：支持所有基础类型、指针、切片、映射、通道、时间等
- ✅ **嵌套结构体**：自动处理嵌套结构体的默认值
- ✅ **自定义默认值**：支持类型级别的自定义默认值函数
- ✅ **错误处理模式**：Panic、Ignore、Return 三种错误处理策略
- ✅ **配置覆盖**：可选的值覆盖机制

---

## 1. 基础用法

### 1.1 快速开始

```go
import "github.com/lazygophers/utils/defaults"

type Config struct {
    Host     string  `default:"localhost"`
    Port     int     `default:"8080"`
    Timeout  float64 `default:"30.0"`
    Debug    bool    `default:"true"`
}

func main() {
    var cfg Config
    defaults.SetDefaults(&cfg)

    // cfg.Host = "localhost"
    // cfg.Port = 8080
    // cfg.Timeout = 30.0
    // cfg.Debug = true
}
```

### 1.2 支持的基础类型

| 类型 | Tag 示例 | 说明 |
|------|---------|------|
| string | `default:"hello"` | 字符串 |
| int/int8/int16/int32/int64 | `default:"42"` | 有符号整数 |
| uint/uint8/uint16/uint32/uint64 | `default:"100"` | 无符号整数 |
| float32/float64 | `default:"3.14"` | 浮点数 |
| bool | `default:"true"` | 布尔值（true/false） |

**示例**：

```go
type BasicTypes struct {
    StringField  string  `default:"test_string"`
    IntField     int     `default:"42"`
    UintField    uint    `default:"100"`
    FloatField   float64 `default:"3.14"`
    BoolField    bool    `default:"true"`
    Int8Field    int8    `default:"8"`
    Int16Field   int16   `default:"16"`
    Int32Field   int32   `default:"32"`
    Int64Field   int64   `default:"64"`
    Uint8Field   uint8   `default:"8"`
    Uint16Field  uint16  `default:"16"`
    Uint32Field  uint32  `default:"32"`
    Uint64Field  uint64  `default:"64"`
    Float32Field float32 `default:"2.71"`
}
```

---

## 2. 指针类型

### 2.1 指针自动初始化

```go
type PointerTypes struct {
    StringPtr *string  `default:"ptr_string"`
    IntPtr    *int     `default:"999"`
    FloatPtr  *float64 `default:"9.99"`
    BoolPtr   *bool    `default:"false"`
}

var pt PointerTypes
defaults.SetDefaults(&pt)

// *pt.StringPtr = "ptr_string"
// *pt.IntPtr = 999
// *pt.FloatPtr = 9.99
// *pt.BoolPtr = false
```

### 2.2 多层指针

```go
type MultiLevelPointers struct {
    DoublePtr **int     `default:"123"`
    TriplePtr ***string `default:"triple"`
}

var mlp MultiLevelPointers
defaults.SetDefaults(&mlp)

// **mlp.DoublePtr = 123
// ***mlp.TriplePtr = "triple"
```

### 2.3 结构体指针

```go
type Nested struct {
    Name string `default:"nested_name"`
    Value int `default:"100"`
}

type Container struct {
    StructPtr *Nested  // 无需 default tag，自动初始化
}

var c Container
defaults.SetDefaults(&c)

// c.StructPtr != nil
// c.StructPtr.Name = "nested_name"
// c.StructPtr.Value = 100
```

---

## 3. 复杂类型

### 3.1 切片（Slice）

#### JSON 格式

```go
type SliceTypes struct {
    SliceInt    []int    `default:"[1,2,3,4,5]"`
    SliceString []string `default:"[\"a\",\"b\",\"c\"]"`
}

var st SliceTypes
defaults.SetDefaults(&st)

// st.SliceInt = []int{1, 2, 3, 4, 5}
// st.SliceString = []string{"a", "b", "c"}
```

#### 逗号分隔格式

```go
type CommaSeparatedSlice struct {
    SliceInt    []int    `default:"10,20,30"`
    SliceString []string `default:"a,b,c,d"`
}

var css CommaSeparatedSlice
defaults.SetDefaults(&css)

// css.SliceInt = []int{10, 20, 30}
// css.SliceString = []string{"a", "b", "c", "d"}
```

#### 空切片初始化

```go
type EmptySlice struct {
    SliceField []string  // 无 default tag
}

var es EmptySlice
defaults.SetDefaults(&es)

// es.SliceField != nil（已初始化为空切片）
// len(es.SliceField) == 0
```

### 3.2 数组（Array）

```go
type ArrayTypes struct {
    ArrayInt    [3]int    `default:"[10,20,30]"`
    ArrayString [2]string `default:"[\"x\",\"y\"]"`
}

var at ArrayTypes
defaults.SetDefaults(&at)

// at.ArrayInt = [3]int{10, 20, 30}
// at.ArrayString = [2]string{"x", "y"}
```

**逗号分隔格式**：

```go
type CommaSeparatedArray struct {
    ArrayInt [3]int `default:"100,200,300"`
}

var csa CommaSeparatedArray
defaults.SetDefaults(&csa)

// csa.ArrayInt = [3]int{100, 200, 300}
```

**数组长度处理**：

```go
type ArrayOverflow struct {
    ArrayField [2]int `default:"1,2,3,4,5"` // 提供 5 个元素但数组只有 2 个位置
}

var ao ArrayOverflow
defaults.SetDefaults(&ao)

// ao.ArrayField = [2]int{1, 2}（只设置前两个元素）
```

### 3.3 映射（Map）

```go
type MapTypes struct {
    MapIntString map[int]string         `default:"{\"1\":\"one\",\"2\":\"two\"}"`
    MapString    map[string]interface{} `default:"{\"key1\":\"value1\",\"key2\":42}"`
}

var mt MapTypes
defaults.SetDefaults(&mt)

// mt.MapIntString[1] = "one"
// mt.MapIntString[2] = "two"
// mt.MapString["key1"] = "value1"
// mt.MapString["key2"] = 42.0（JSON 数字转为 float64）
```

**空映射初始化**：

```go
type EmptyMap struct {
    MapField map[string]int  // 无 default tag
}

var em EmptyMap
defaults.SetDefaults(&em)

// em.MapField != nil（已初始化为空映射）
// len(em.MapField) == 0
```

### 3.4 通道（Channel）

```go
type ChannelTypes struct {
    UnbufferedChan chan int `default:"0"`
    BufferedChan   chan int `default:"10"`
}

var ct ChannelTypes
defaults.SetDefaults(&ct)

// ct.UnbufferedChan：无缓冲通道
// ct.BufferedChan：缓冲区大小为 10 的通道
```

### 3.5 接口（Interface）

```go
type InterfaceTypes struct {
    Interface    interface{} `default:"test_interface"`
    JSONInterface interface{} `default:"{\"key\":\"value\",\"num\":42}"`
}

var it InterfaceTypes
defaults.SetDefaults(&it)

// it.Interface = "test_interface"
// it.JSONInterface = map[string]interface{}{"key": "value", "num": 42.0}
```

---

## 4. 时间类型

### 4.1 支持的时间格式

```go
type TimeTypes struct {
    TimeNow    time.Time `default:"now"`                          // 当前时间
    TimeRFC    time.Time `default:"2023-01-01T12:00:00Z"`        // RFC3339
    TimeCustom time.Time `default:"2023-12-25 15:30:45"`         // 自定义格式
    TimeDate   time.Time `default:"2023-06-15"`                  // 仅日期
}
```

**支持的时间格式**（按优先级）：

1. `time.RFC3339` - `"2023-01-01T12:00:00Z"`
2. `time.RFC3339Nano` - `"2023-01-01T12:00:00.999999999Z"`
3. `"2006-01-02 15:04:05"` - `"2023-12-25 15:30:45"`
4. `"2006-01-02"` - `"2023-06-15"`
5. `"15:04:05"` - 仅时间

### 4.2 特殊值 "now"

```go
type Timestamp struct {
    CreatedAt time.Time `default:"now"`
    UpdatedAt time.Time `default:"now"`
}

var ts Timestamp
defaults.SetDefaults(&ts)

// ts.CreatedAt 和 ts.UpdatedAt 被设置为当前时间
// 两者时间几乎相同（取决于调用间隔）
```

---

## 5. 嵌套结构体

### 5.1 值嵌套

```go
type Level3 struct {
    Value string `default:"level3"`
}

type Level2 struct {
    Value  string `default:"level2"`
    Level3 Level3
}

type Level1 struct {
    Value  string `default:"level1"`
    Level2 Level2
}

var l1 Level1
defaults.SetDefaults(&l1)

// l1.Value = "level1"
// l1.Level2.Value = "level2"
// l1.Level2.Level3.Value = "level3"
```

### 5.2 指针嵌套

```go
type Inner struct {
    Name  string `default:"inner_name"`
    Value int    `default:"200"`
}

type Outer struct {
    ID       int    `default:"1"`
    PtrInner *Inner // 指针自动初始化
}

var o Outer
defaults.SetDefaults(&o)

// o.PtrInner != nil
// o.PtrInner.Name = "inner_name"
// o.PtrInner.Value = 200
```

---

## 6. 配置选项

### 6.1 Options 结构

```go
type Options struct {
    ErrorMode        ErrorMode              // 错误处理模式
    CustomDefaults   map[string]DefaultFunc // 自定义默认值函数
    ValidateDefaults bool                   // 是否验证默认值
    AllowOverwrite   bool                   // 是否允许覆盖非零值
}
```

### 6.2 错误处理模式

#### ErrorModePanic（默认）

```go
type InvalidConfig struct {
    Port int `default:"invalid_port"`
}

var cfg InvalidConfig
defaults.SetDefaults(&cfg) // panic: invalid default value for int field: invalid_port
```

#### ErrorModeIgnore

```go
var cfg InvalidConfig
opts := &defaults.Options{ErrorMode: defaults.ErrorModeIgnore}
defaults.SetDefaultsWithOptions(&cfg, opts) // 忽略错误，继续处理
// cfg.Port = 0（零值）
```

#### ErrorModeReturn

```go
var cfg InvalidConfig
opts := &defaults.Options{ErrorMode: defaults.ErrorModeReturn}
err := defaults.SetDefaultsWithOptions(&cfg, opts)
if err != nil {
    log.Printf("Failed to set defaults: %v", err)
    // cfg.Port = 0（零值）
}
```

### 6.3 自定义默认值函数

```go
// 定义自定义默认值函数
opts := &defaults.Options{
    CustomDefaults: map[string]defaults.DefaultFunc{
        "string": func() interface{} {
            return "custom_string"
        },
        "int": func() interface{} {
            return int64(777)
        },
    },
}

type CustomTest struct {
    StringField string `default:"original"`
    IntField    int    `default:"original_int"`
}

var ct CustomTest
defaults.SetDefaultsWithOptions(&ct, opts)

// ct.StringField = "custom_string"（使用自定义函数）
// ct.IntField = 777（使用自定义函数）
```

**全局注册自定义默认值**：

```go
// 注册全局自定义默认值
defaults.RegisterCustomDefault("string", func() interface{} {
    return "global_custom"
})

type GlobalTest struct {
    StringField string `default:"ignored"`
}

var gt GlobalTest
defaults.SetDefaults(&gt)

// gt.StringField = "global_custom"

// 清除所有自定义默认值
defaults.ClearCustomDefaults()
```

### 6.4 值覆盖控制

```go
type OverwriteTest struct {
    StringField string `default:"default_value"`
    IntField    int    `default:"100"`
}

// 不允许覆盖（默认）
ot1 := OverwriteTest{StringField: "existing", IntField: 50}
defaults.SetDefaults(&ot1)
// ot1.StringField = "existing"（保持原值）
// ot1.IntField = 50（保持原值）

// 允许覆盖
ot2 := OverwriteTest{StringField: "existing", IntField: 50}
opts := &defaults.Options{AllowOverwrite: true}
defaults.SetDefaultsWithOptions(&ot2, opts)
// ot2.StringField = "default_value"（被覆盖）
// ot2.IntField = 100（被覆盖）
```

---

## 7. 高级特性

### 7.1 零值处理

```go
type ZeroTest struct {
    StringField string  `default:"zero_string"`
    IntField    int     `default:"0"`
    FloatField  float64 `default:"0.0"`
    BoolField   bool    `default:"false"`
}

var zt ZeroTest
defaults.SetDefaults(&zt)

// zt.StringField = "zero_string"
// zt.IntField = 0（显式设置为零值）
// zt.FloatField = 0.0（显式设置为零值）
// zt.BoolField = false（显式设置为零值）
```

**注意事项**：
- `default:"0"` 会将字段设置为 0，即使是零值
- 如果字段已经是非零值，默认不会被覆盖（除非 `AllowOverwrite: true`）

### 7.2 私有字段处理

```go
type UnexportedFieldTest struct {
    ExportedField   string `default:"exported"`
    unexportedField string `default:"unexported"` // 会被忽略
}

var uft UnexportedFieldTest
defaults.SetDefaults(&uft)

// uft.ExportedField = "exported"
// uft.unexportedField = ""（保持零值，无法设置）
```

### 7.3 接口类型特殊处理

```go
type InterfaceTest struct {
    SimpleInterface  interface{} `default:"simple"`
    JSONInterface    interface{} `default:"{\"key\":\"value\"}"`
    NumberInterface  interface{} `default:"42"`
    BoolInterface    interface{} `default:"true"`
}

var it InterfaceTest
defaults.SetDefaults(&it)

// it.SimpleInterface = "simple"
// it.JSONInterface = map[string]interface{}{"key": "value"}
// it.NumberInterface = 42
// it.BoolInterface = "true"（作为字符串，非布尔值）
```

---

## 8. 错误处理

### 8.1 类型解析错误

```go
type ParseErrorTest struct {
    InvalidInt    int     `default:"not_a_number"`
    InvalidFloat  float64 `default:"not_a_float"`
    InvalidBool   bool    `default:"not_a_bool"`
    InvalidTime   time.Time `default:"invalid_time"`
    InvalidSlice  []int   `default:"[invalid,json]"`
    InvalidMap    map[string]int `default:"{invalid:json}"`
}
```

**处理方式**：

```go
var pet ParseErrorTest
opts := &defaults.Options{ErrorMode: defaults.ErrorModeReturn}
err := defaults.SetDefaultsWithOptions(&pet, opts)
if err != nil {
    log.Printf("Error setting defaults: %v", err)
    // 所有字段保持零值
}
```

### 8.2 错误恢复

```go
func safeSetDefaults(v interface{}) error {
    defer func() {
        if r := recover(); r != nil {
            log.Printf("Recovered from panic: %v", r)
        }
    }()

    err := defaults.SetDefaultsWithOptions(v, &defaults.Options{
        ErrorMode: defaults.ErrorModeReturn,
    })
    return err
}

cfg := &Config{}
if err := safeSetDefaults(cfg); err != nil {
    log.Printf("Failed to set defaults: %v", err)
    // 使用备用配置或返回错误
}
```

---

## 9. 性能考虑

### 9.1 基准测试

```go
func BenchmarkSetDefaults(b *testing.B) {
    type BenchmarkStruct struct {
        StringField string            `default:"benchmark"`
        IntField    int               `default:"123"`
        FloatField  float64           `default:"1.23"`
        BoolField   bool              `default:"true"`
        SliceField  []int             `default:"[1,2,3]"`
        MapField    map[string]string `default:"{\"key\":\"value\"}"`
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        var bs BenchmarkStruct
        defaults.SetDefaults(&bs)
    }
}
```

**性能特点**：
- 基于反射，有一定性能开销
- 适合初始化阶段使用，不适合热路径
- 嵌套层级越深，性能开销越大

### 9.2 优化建议

```go
// ❌ 不推荐：在热路径中调用
func handleRequest(req *Request) {
    var cfg Config
    defaults.SetDefaults(&cfg) // 每次请求都调用
    // ...
}

// ✅ 推荐：初始化时调用一次
var globalConfig Config

func init() {
    defaults.SetDefaults(&globalConfig)
}

func handleRequest(req *Request) {
    cfg := globalConfig // 使用已初始化的配置
    // ...
}
```

---

## 10. 完整示例

### 10.1 配置管理

```go
type DatabaseConfig struct {
    Host            string        `default:"localhost"`
    Port            int           `default:"5432"`
    Username        string        `default:"user"`
    Password        string        `default:"password"`
    Database        string        `default:"mydb"`
    MaxConnections  int           `default:"100"`
    ConnectionTimeout float64     `default:"30.0"`
    EnableSSL       bool          `default:"true"`
    SSLMode         string        `default:"require"`
    Tables          []string      `default:"[\"users\",\"products\",\"orders\"]"`
    Metadata        map[string]interface{} `default:"{\"env\":\"prod\",\"version\":\"1.0\"}"`
}

type ServerConfig struct {
    Host            string        `default:"0.0.0.0"`
    Port            int           `default:"8080"`
    ReadTimeout     time.Duration `default:"30s"`
    WriteTimeout    time.Duration `default:"30s"`
    DebugMode       bool          `default:"false"`
    TrustedProxies  []string      `default:"[\"10.0.0.0/8\",\"172.16.0.0/12\"]"`
}

type AppConfig struct {
    Environment     string        `default:"production"`
    LogLevel        string        `default:"info"`
    Database        DatabaseConfig
    Server          ServerConfig
    InitializedAt   time.Time     `default:"now"`
}

func main() {
    var cfg AppConfig
    defaults.SetDefaults(&cfg)

    fmt.Printf("Environment: %s\n", cfg.Environment)
    fmt.Printf("Database Host: %s\n", cfg.Database.Host)
    fmt.Printf("Server Port: %d\n", cfg.Server.Port)
    fmt.Printf("Initialized At: %s\n", cfg.InitializedAt.Format(time.RFC3339))
}
```

### 10.2 API 响应模型

```go
type Address struct {
    Street  string `default:""`
    City    string `default:""`
    State   string `default:""`
    ZipCode string `default:""`
    Country string `default:"USA"`
}

type User struct {
    ID        uint64    `default:"0"`
    Username  string    `default:"anonymous"`
    Email     string    `default:""`
    Active    bool      `default:"true"`
    CreatedAt time.Time `default:"now"`
    UpdatedAt time.Time `default:"now"`
    Roles     []string  `default:"[\"user\"]"`
    Metadata  map[string]interface{} `default:"{}"`
    Address   *Address // 指针自动初始化
}

func NewUser() *User {
    user := &User{}
    defaults.SetDefaults(user)
    return user
}

func main() {
    user := NewUser()

    fmt.Printf("ID: %d\n", user.ID)
    fmt.Printf("Username: %s\n", user.Username)
    fmt.Printf("Active: %v\n", user.Active)
    fmt.Printf("Roles: %v\n", user.Roles)
    fmt.Printf("Address: %+v\n", user.Address)
}
```

### 10.3 表单验证

```go
type RegistrationForm struct {
    Username     string    `default:""`
    Email        string    `default:""`
    Password     string    `default:""`
    Age          int       `default:"0"`
    Country      string    `default:"US"`
    Subscribe    bool      `default:"true"`
    Interests    []string  `default:"[]"`
    SubmittedAt  time.Time `default:"now"`
}

func (f *RegistrationForm) Validate() error {
    defaults.SetDefaults(f)

    if f.Username == "" {
        return errors.New("username is required")
    }
    if f.Email == "" {
        return errors.New("email is required")
    }
    if f.Password == "" {
        return errors.New("password is required")
    }
    if f.Age < 18 {
        return errors.New("must be 18 or older")
    }

    return nil
}

func main() {
    form := &RegistrationForm{
        Username: "john_doe",
        Email:    "john@example.com",
        Password: "secret123",
        Age:      25,
    }

    if err := form.Validate(); err != nil {
        log.Printf("Validation error: %v", err)
        return
    }

    fmt.Printf("Form valid: %+v\n", form)
}
```

---

## 11. 最佳实践

### 11.1 默认值设计原则

```go
// ✅ 推荐：使用合理的默认值
type Config struct {
    Timeout     time.Duration `default:"30s"`
    MaxRetries  int           `default:"3"`
    EnableDebug bool          `default:"false"`
}

// ❌ 不推荐：无意义的默认值
type BadConfig struct {
    Timeout     time.Duration `default:"0"` // 零值容易引起混淆
    MaxRetries  int           `default:"-1"` // 负数无意义
    EnableDebug bool          `default:"maybe"` // 无效的布尔值
}
```

### 11.2 错误处理策略

```go
// ✅ 推荐：使用 ErrorModeReturn 并处理错误
func loadConfig(configFile string) (*Config, error) {
    cfg := &Config{}

    // 先设置默认值
    if err := defaults.SetDefaultsWithOptions(cfg, &defaults.Options{
        ErrorMode: defaults.ErrorModeReturn,
    }); err != nil {
        return nil, fmt.Errorf("failed to set defaults: %w", err)
    }

    // 再覆盖配置文件中的值
    if err := loadFromFile(cfg, configFile); err != nil {
        return nil, fmt.Errorf("failed to load config: %w", err)
    }

    return cfg, nil
}

// ❌ 不推荐：忽略错误
func loadConfigUnsafe(configFile string) *Config {
    cfg := &Config{}
    defaults.SetDefaults(cfg) // 可能 panic
    loadFromFile(cfg, configFile)
    return cfg
}
```

### 11.3 配置层级管理

```go
// ✅ 推荐：分层设置默认值
type DatabaseConfig struct {
    Host     string `default:"localhost"`
    Port     int    `default:"5432"`
    Username string `default:"user"`
    Password string `default:"password"`
}

type AppConfig struct {
    Environment string         `default:"production"`
    Database    DatabaseConfig // 嵌套配置
}

func loadAppConfig() (*AppConfig, error) {
    cfg := &AppConfig{}

    // 1. 设置代码中的默认值
    defaults.SetDefaults(cfg)

    // 2. 覆盖配置文件中的值
    if err := loadFromFile(cfg, "config.yaml"); err != nil {
        return nil, err
    }

    // 3. 覆盖环境变量中的值
    if err := loadFromEnv(cfg); err != nil {
        return nil, err
    }

    return cfg, nil
}
```

### 11.4 指针使用建议

```go
// ✅ 推荐：可选字段使用指针
type OptionalFields struct {
    RequiredField string  `default:"required"`
    OptionalField *string `default:"optional"` // 可以区分零值和未设置
}

func (f *OptionalFields) Process() {
    value := "default_value"
    if f.OptionalField != nil {
        value = *f.OptionalField
    }
    fmt.Println(value)
}

// ❌ 不推荐：必需字段使用指针
type RequiredFields struct {
    RequiredField *string `default:"required"` // 增加不必要的复杂性
}
```

---

## 12. 常见问题

### Q1: 为什么需要传递指针？

```go
// ❌ 错误：传递值
var cfg Config
defaults.SetDefaults(cfg) // 不会修改 cfg

// ✅ 正确：传递指针
var cfg Config
defaults.SetDefaults(&cfg) // 会修改 cfg
```

**原因**：
- Go 语言中函数参数是值传递
- 传递指针才能修改原始变量
- 内部使用反射修改指针指向的值

### Q2: 如何区分零值和未设置？

```go
type DistinguishZero struct {
    Port     *int    `default:"8080"` // 使用指针
    Enabled  *bool   `default:"true"` // 使用指针
}

var dz DistinguishZero
defaults.SetDefaults(&dz)

// dz.Port != nil，可以区分已设置和未设置
if dz.Port != nil {
    fmt.Printf("Port: %d\n", *dz.Port)
}
```

### Q3: 默认值支持环境变量吗？

```go
// defaults 模块不直接支持环境变量
// 需要手动实现

type Config struct {
    Host string `default:"localhost"`
    Port int    `default:"8080"`
}

func loadConfig() *Config {
    cfg := &Config{}
    defaults.SetDefaults(cfg)

    // 手动覆盖环境变量
    if host := os.Getenv("DB_HOST"); host != "" {
        cfg.Host = host
    }
    if portStr := os.Getenv("DB_PORT"); portStr != "" {
        if port, err := strconv.Atoi(portStr); err == nil {
            cfg.Port = port
        }
    }

    return cfg
}
```

### Q4: 如何处理时间类型的时区？

```go
type TimeConfig struct {
    Timestamp time.Time `default:"2023-01-01T00:00:00Z"` // UTC 时间
}

var tc TimeConfig
defaults.SetDefaults(&tc)

// tc.Timestamp 的时区为 UTC
// 如需其他时区，需要手动转换
loc, _ := time.LoadLocation("Asia/Shanghai")
tc.Timestamp = tc.Timestamp.In(loc)
```

### Q5: 支持动态默认值吗？

```go
// defaults 模块不支持动态默认值
// 但可以使用自定义默认值函数

type DynamicConfig struct {
    Port int `default:"0"` // 占位符
}

func loadDynamicConfig() *DynamicConfig {
    opts := &defaults.Options{
        CustomDefaults: map[string]defaults.DefaultFunc{
            "int": func() interface{} {
                // 动态计算端口
                return getAvailablePort()
            },
        },
    }

    cfg := &DynamicConfig{}
    defaults.SetDefaultsWithOptions(cfg, opts)
    return cfg
}

func getAvailablePort() int64 {
    // 实现获取可用端口的逻辑
    return 8080
}
```

### Q6: 如何处理循环引用？

```go
// ❌ 不支持：循环引用会导致无限递归
type A struct {
    B *B `default:""`
}

type B struct {
    A *A `default:""`
}

// ✅ 推荐：避免循环引用，或手动初始化
type A struct {
    B *B
}

type B struct {
    A *A // 不设置 default，手动处理
}

func initAB() *A {
    a := &A{}
    b := &B{A: a}
    a.B = b
    return a
}
```

### Q7: 性能开销有多大？

```go
// 性能测试结果（参考）
// BenchmarkSetDefaults-8    50000    30000 ns/op    10000 B/op    200 allocs/op

// 适合场景：
// ✅ 应用初始化
// ✅ 配置加载
// ✅ 偶尔调用

// 不适合场景：
// ❌ 热路径中的频繁调用
// ❌ 高性能要求场景
// ❌ 每次请求都调用
```

---

## 13. 限制与注意事项

### 13.1 不支持的类型

```go
type UnsupportedTypes struct {
    UnsafeField uintptr `default:"123"` // ❌ 不支持
    FuncField   func()  `default:""`    // ❌ 不直接支持
}

// 函数类型需要通过自定义默认值函数处理
```

### 13.2 私有字段限制

```go
type PrivateField struct {
    publicField  string `default:"public"`   // ✅ 支持
    privateField string `default:"private"`  // ❌ 忽略
}
```

### 13.3 JSON 数字处理

```go
type JSONNumber struct {
    Number map[string]interface{} `default:"{\"value\":42}"`
}

var jn JSONNumber
defaults.SetDefaults(&jn)

// jn.Number["value"] 是 float64(42.0)，而非 int(42)
// JSON 标准将数字解析为 float64
```

### 13.4 时间精度

```go
type TimePrecision struct {
    Timestamp time.Time `default:"2023-01-01T12:00:00.999999999Z"`
}

var tp TimePrecision
defaults.SetDefaults(&tp)

// 纳秒级精度会被保留
// 但取决于时间格式的支持
```

---

## 14. 总结

### 核心优势

1. **声明式配置**：通过 struct tag 定义默认值，清晰直观
2. **类型全覆盖**：支持所有 Go 基础类型和复杂类型
3. **嵌套支持**：自动处理嵌套结构体的默认值
4. **灵活配置**：提供多种错误处理和自定义选项
5. **易于使用**：简洁的 API，零学习成本

### 适用场景

- ✅ 配置管理（应用配置、数据库配置等）
- ✅ 表单验证（注册表单、设置页面等）
- ✅ API 模型（请求/响应模型默认值）
- ✅ 数据模型（数据库实体默认值）
- ✅ 初始化逻辑（结构体初始化）

### 不适用场景

- ❌ 热路径中的频繁调用（性能敏感场景）
- ❌ 需要复杂默认值逻辑（如依赖其他字段）
- ❌ 运行时动态配置（需要实时计算）

---

## 15. 参考资源

- **GitHub 仓库**: https://github.com/lazygophers/utils/tree/master/defaults
- **源码文件**:
  - default.go: 核心实现（约 400 行）
  - default_test.go: 完整测试覆盖（约 1400 行）
- **相关模块**:
  - candy: https://github.com/lazygophers/utils/tree/master/candy（类型转换）
  - anyx: https://github.com/lazygophers/utils/tree/master/anyx（动态类型处理）
