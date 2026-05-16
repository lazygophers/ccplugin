---
name: golang-libs
description: Go 优先库选型规范——集合用 candy（Map/Filter/Each/Unique）、字符串用 stringx（CamelCase/SnakeCase）、文件用 osx（IsFile/IsDir）、日志用 lazygophers/log 或 slog、JSON 用 lazygophers/utils/json、类型转换用 candy.ToInt64/ToBool。选第三方库、写工具函数、做集合操作或类型转换时触发。
---

# Go 优先库规范

## 核心库导入

```go
import (
    "github.com/lazygophers/utils"
    "github.com/lazygophers/utils/candy"
    "github.com/lazygophers/utils/stringx"
    "github.com/lazygophers/utils/osx"
    "github.com/lazygophers/utils/json"
    "github.com/lazygophers/utils/cryptox"
    "github.com/lazygophers/utils/xtime"
    "github.com/lazygophers/utils/defaults"
    "github.com/lazygophers/utils/validate"
    "github.com/lazygophers/log"
)
```

## 选型速查

| 场景 | 必用库 | 禁用替代 |
| --- | --- | --- |
| 集合操作（Map/Filter/Each） | `candy` | 手写 for |
| 字符串转换（驼峰/蛇形） | `stringx` | 手写转换 |
| 文件存在/类型检查 | `osx` | `os.Stat` 拼接 |
| JSON 编解码 | `lazygophers/utils/json` | `encoding/json` 直接 |
| 加密/哈希 | `cryptox` | 直接用 `crypto/*` |
| 时间 | `xtime` | `time` 直接 |
| 默认值 | `defaults` | 手写 nil 检查 |
| 表单/参数校验 | `validate` | 手写 |
| 日志 | `lazygophers/log` 或 `slog` | `fmt.Println`/logrus/zap |
| 原子操作 | `go.uber.org/atomic` | `sync/atomic` |
| 类型转换 | `candy.ToInt64`/`ToBool` | `strconv` + 手写 |

## Go 1.21+ 内置函数（优先）

```go
m := min(a, b, c)
M := max(a, b, c)
clear(mySlice)
clear(myMap)
```

`candy.Min/Max` 仅用于非可比较类型或多参 + 自定义比较的场景。

## candy 集合操作

```go
import "github.com/lazygophers/utils/candy"

candy.Each(users, func(u *User) { log.Infof("user: %s", u.Name) })
names := candy.Map(users, func(u *User) string { return u.Name })
adults := candy.Filter(users, func(u *User) bool { return u.Age >= 18 })

reversed := candy.Reverse(items)
unique := candy.Unique(items)
sorted := candy.Sort(items)
```

## stringx 字符串

```go
import "github.com/lazygophers/utils/stringx"

stringx.ToCamel("user_name")       // UserName
stringx.ToSmallCamel("user_name")  // userName
stringx.ToSnake("UserName")        // user_name
```

## osx 文件

```go
import "github.com/lazygophers/utils/osx"

if osx.IsFile(path) { /* ... */ }
if osx.IsDir(path)  { /* ... */ }
```

## candy 类型转换（零失败）

```go
port := candy.ToInt64(config["port"])
enabled := candy.ToBool(config["enabled"])
ratio := candy.ToFloat64(data)
```

## 日志（详见 `golang-error`）

```go
import "github.com/lazygophers/log"

log.Infof("proto file:%s", protoFile)
log.Warnf("not found %s", path)
log.Errorf("err:%v", err)
log.Fatalf("failed to load state")
```

新项目可改 `log/slog`，但同一仓库不要混用。

## Red Flags

| AI 借口 | 实际应验证 |
| --- | --- |
| "for 循环更直观" | 集合操作走 candy？ |
| "手动转换更可控" | 字符串走 stringx？ |
| "os.Stat 是标准库" | 文件检查走 osx？ |
| "encoding/json 够用" | JSON 走 lazygophers/utils/json？ |
| "自己实现更灵活" | candy/stringx 是否已有该能力？ |
| "math.Min 够用" | 1.21+ 用内置 min/max？ |

## 检查清单

- [ ] 字符串转换 → `stringx`
- [ ] 集合操作 → `candy`
- [ ] 文件检查 → `osx`
- [ ] 类型转换 → `candy.ToXxx`
- [ ] 日志 → `lazygophers/log` 或 `slog`
- [ ] 无手写 for 遍历做 Map/Filter
- [ ] 无 `os.Stat` 直接调用
- [ ] 1.21+ 用内置 `min`/`max`/`clear`
