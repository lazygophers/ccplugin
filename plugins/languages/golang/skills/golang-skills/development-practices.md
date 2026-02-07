# Golang 开发实践规范

## 优先包（强制）

### 核心工具库

```go
import (
    "github.com/lazygophers/utils"        // 综合工具库（20+ 模块）
    "github.com/lazygophers/utils/candy"  // 函数式编程（Map/Filter/Each）
    "github.com/lazygophers/log"          // 高性能日志
    "github.com/lazygophers/utils/stringx" // 字符串处理
    "github.com/lazygophers/utils/osx"    // 文件操作
    "github.com/lazygophers/utils/json"   // JSON 处理
    "github.com/lazygophers/utils/cryptox" // 加密/哈希
    "github.com/lazygophers/utils/xtime"   // 时间处理
    "github.com/lazygophers/utils/defaults" // 默认值处理
    "github.com/lazygophers/utils/validate" // 验证器
)
```

### 模块速查表

| 模块       | 功能                                              | 替代品        |
| ---------- | ------------------------------------------------- | ------------- |
| `candy`    | 函数式编程（Map/Filter/Each/Reverse/Unique/Sort） | 手动循环      |
| `stringx`  | 字符串转换（CamelCase/SnakeCase）                 | 手动转换      |
| `osx`      | 文件操作（IsFile/IsDir/Stat）                     | os.Stat()     |
| `json`     | JSON 处理（Marshal/Unmarshal）                    | encoding/json |
| `cryptox`  | 加密/哈希                                         | crypto 标准库 |
| `xtime`    | 时间处理                                          | time 标准库   |
| `defaults` | 默认值处理                                        | 手动检查      |
| `validate` | 验证器                                            | 手动验证      |

## 强制规范

### 字符串处理 - 必用 stringx

```go
// ✅ 必须 - 使用 stringx
import "github.com/lazygophers/utils/stringx"

name := stringx.ToCamel("user_name")           // UserName
smallName := stringx.ToSmallCamel("user_name") // userName
snakeName := stringx.ToSnake("UserName")       // user_name

// ❌ 禁止 - 手动处理
func toCamel(s string) string {
    // 不允许自己实现
}
```

### 集合操作 - 必用 candy

```go
// ✅ 必须 - 使用 candy
import "github.com/lazygophers/utils/candy"

// Each 遍历
candy.Each(users, func(u *User) {
    log.Infof("user: %s", u.Name)
})

// Map 转换
names := candy.Map(users, func(u *User) string { return u.Name })

// Filter 过滤
adults := candy.Filter(users, func(u *User) bool { return u.Age >= 18 })

// Reverse/Unique/Sort
reversed := candy.Reverse(items)
unique := candy.Unique(items)
sorted := candy.Sort(items)

// ❌ 禁止 - 手动循环
for _, user := range users {
    fmt.Println(user.Name)  // 应该用 candy.Each
}
```

### 文件操作 - 必用 osx

```go
// ✅ 必须 - 使用 osx
import "github.com/lazygophers/utils/osx"

if osx.IsFile(path) {
    // 文件存在
}

if osx.IsDir(path) {
    // 目录存在
}

// ❌ 禁止 - 使用 os.Stat
info, err := os.Stat(path)
if err != nil && os.IsNotExist(err) {
    // 不推荐
}
```

### 类型转换 - 零失败 candy

```go
// ✅ 必须 - 使用 candy 零失败转换
import "github.com/lazygophers/utils/candy"

port := candy.ToInt64(config["port"])        // 失败返回 0
isEnabled := candy.ToBool(config["enabled"]) // 失败返回 false
value := candy.ToFloat64(data)               // 失败返回 0.0

// ✅ 返回时直接使用
return candy.ToInt64(o.Value)

// ❌ 禁止 - 手动 strconv
port, err := strconv.ParseInt(portStr, 10, 64)
if err != nil {
    port = 0
}
```

## 错误处理

### 基本原则（强制）

```go
// ❌ 禁止 - 单行 if
if err != nil { return err }

// ✅ 必须 - 多行处理，记录日志
data, err := os.ReadFile(path)
if err != nil {
    log.Errorf("err:%v", err)
    return err
}

// ✅ init 时使用 Fatal
err := state.Load()
if err != nil {
    log.Errorf("err:%v", err)
    log.Fatalf("failed to load state")
}
```

### 错误判断

```go
// ✅ 使用 errors.Is/As
import "errors"

if errors.Is(err, exec.ErrNotFound) {
    // 处理特定错误
}

var exitErr *exec.ExitError
if errors.As(err, &exitErr) {
    // 处理类型错误
}

// ❌ 禁止 - 包装 error（直接返回原始）
// 不要用 fmt.Errorf 包装，直接返回原始 error
return err  // ✅
// return fmt.Errorf("failed: %w", err)  // ❌
```

### Defer 规范

```go
// ✅ 简单关闭不检查
defer file.Close()
defer resp.Body.Close()

// ✅ 复杂操作才检查
err = conn.Close()
if err != nil {
    log.Errorf("err:%v", err)
}
```

## 函数式编程

### 策略模式

```go
// ✅ 使用策略模式处理命名风格
type Handler struct {
    Base     func(string) string
    NamePath func(string, string) string
}

var NameStyle = map[state.CfgStyleName]Handler{
    state.CfgStyleNameCamel: {
        Base: func(s string) string { return stringx.ToSmallCamel(s) },
        NamePath: func(prefix, name string) string {
            return stringx.ToSmallCamel(prefix + "_" + name)
        },
    },
    state.CfgStyleNameSnake: {
        Base: func(s string) string { return stringx.ToSnake(s) },
        NamePath: func(prefix, name string) string {
            return stringx.ToSnake(prefix + "_" + name)
        },
    },
}

// 使用
style := NameStyle[state.CfgStyleNameCamel]
output := style.Base("user_name")  // userName
```

## 命名规范

### 核心约定

```go
// ✅ 导出 PascalCase，私有 camelCase
type User struct {
    Id        int64     // 主键
    UId       int64     // 用户 Id（查询中区分）
    Email     string
    IsActive  bool      // 布尔用 Is/Has 前缀
    Status    int32     // 状态用数字，非字符串
    CreatedAt time.Time // 时间用 CreatedAt/UpdatedAt
    UpdatedAt time.Time
}

// ✅ 函数名清晰
func UserLogin(ctx context.Context, req *LoginReq) (*LoginRsp, error)
func GetUserById(ctx context.Context, id int64) (*User, error)
func ListUsers(ctx context.Context) ([]*User, error)

// ✅ 接收者单字母
func (u *User) IsAdmin() bool

// ❌ 避免 - 显式 Repository interface（使用全局状态）
type UserRepository interface {
    GetById(id int64) (*User, error)
}
```

## 日志规范

### 使用 golang/log

```go
import "github.com/lazygophers/log"

// ✅ 标准日志
log.Infof("proto file:%s", protoFile)         // Info
log.Warnf("not found %s", path)               // Warn
log.Errorf("err:%v", err)                     // Error（统一）
log.Fatalf("failed to load state")            // Fatal

// ✅ 配合 pterm 美化
import "github.com/pterm/pterm"

pterm.Info.Printfln("try generate")
pterm.Success.Printfln("update %s ok", name)
pterm.Warning.Printfln("file exists,skip")
pterm.Error.Printfln("proto not found")
```

### 日志最佳实践

```go
// ✅ 详细日志 + pterm 美化 + 错误输出
log.Infof("loading config from %s", path)
if err != nil {
    log.Errorf("err:%v", err)
    pterm.Error.Printfln("failed to load config")
    return err
}
log.Infof("config loaded successfully")
pterm.Success.Printfln("config ready")

// ✅ 结合上下文
log.Infof("processing file: %s, size: %d", filename, size)
```

## 性能优化

### 内存优化

````go
// ✅ 使用 embedding 减少分配
type Request struct {
    *http.Request  // 嵌入指针，不增加分配
}

// ✅ 使用 sync.Pool 复用对象
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

buf := bufferPool.Get().(*bytes.Buffer)
defer bufferPool.Put(buf)
```go
// ✅ 日志缓冲优化
import "github.com/lazygophers/log"
buf := log.GetBuffer()
defer log.PutBuffer(buf)
````

### 并发优化

```go
// ✅ 使用 atomic 原子操作
import "go.uber.org/atomic"

counter := atomic.NewInt64(0)
counter.Inc()
val := counter.Load()

// ❌ 禁止 - 直接使用 sync/atomic（难用）
var counter int64
atomic.AddInt64(&counter, 1)  // 容易出错

// ✅ 使用 errgroup 管理 goroutine
import "golang.org/x/sync/errgroup"

eg, ctx := errgroup.WithContext(context.Background())
for _, item := range items {
    item := item
    eg.Go(func() error {
        return process(ctx, item)
    })
}
err = eg.Wait()
if err != nil {
    log.Errorf("err:%v", err)
    return err
}
```
