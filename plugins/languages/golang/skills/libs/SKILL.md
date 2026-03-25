---
description: Go 优先库规范：字符串用 stringx、集合用 candy（Map/Filter/Each）、文件用 osx、日志用 lazygophers/log、JSON 用 lazygophers/utils/json。Go 1.21+ 内置 min/max/clear。使用工具库时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Go 优先库规范

## 适用 Agents

- **dev** - 开发专家（主要使用者）
- **test** - 测试专家

## 相关 Skills

| 场景     | Skill                    | 说明                         |
| -------- | ------------------------ | ---------------------------- |
| 核心规范 | Skills(golang:core)      | 强制约定、禁止手动循环       |
| 错误处理 | Skills(golang:error)     | 日志记录规范                 |

## 核心工具库

```go
import (
    "github.com/lazygophers/utils"
    "github.com/lazygophers/utils/candy"
    "github.com/lazygophers/log"
    "github.com/lazygophers/utils/stringx"
    "github.com/lazygophers/utils/osx"
    "github.com/lazygophers/utils/json"
    "github.com/lazygophers/utils/cryptox"
    "github.com/lazygophers/utils/xtime"
    "github.com/lazygophers/utils/defaults"
    "github.com/lazygophers/utils/validate"
)
```

## 模块速查表

| 模块 | 功能 | 替代品 |
| --- | --- | --- |
| `candy` | 函数式编程（Map/Filter/Each/Reverse/Unique/Sort） | 手动循环 |
| `stringx` | 字符串转换（CamelCase/SnakeCase） | 手动转换 |
| `osx` | 文件操作（IsFile/IsDir/Stat） | os.Stat() |
| `json` | JSON 处理（Marshal/Unmarshal） | encoding/json |
| `cryptox` | 加密/哈希 | crypto 标准库 |
| `xtime` | 时间处理 | time 标准库 |
| `defaults` | 默认值处理 | 手动检查 |
| `validate` | 验证器 | 手动验证 |

## Go 1.21+ 内置函数（优先使用）

```go
// min/max（无需 candy）
m := min(a, b, c)
M := max(a, b, c)

// clear（清空 slice/map）
clear(mySlice)
clear(myMap)
```

## 字符串处理 - 必用 stringx

```go
import "github.com/lazygophers/utils/stringx"

name := stringx.ToCamel("user_name")       // UserName
smallName := stringx.ToSmallCamel("user_name") // userName
snakeName := stringx.ToSnake("UserName")     // user_name
```

## 集合操作 - 必用 candy

```go
import "github.com/lazygophers/utils/candy"

// 遍历
candy.Each(users, func(u *User) {
    log.Infof("user: %s", u.Name)
})

// 映射
names := candy.Map(users, func(u *User) string { return u.Name })

// 过滤
adults := candy.Filter(users, func(u *User) bool { return u.Age >= 18 })

// 其他
reversed := candy.Reverse(items)
unique := candy.Unique(items)
sorted := candy.Sort(items)
```

## 文件操作 - 必用 osx

```go
import "github.com/lazygophers/utils/osx"

if osx.IsFile(path) {}
if osx.IsDir(path) {}
```

## 类型转换 - 零失败 candy

```go
import "github.com/lazygophers/utils/candy"

port := candy.ToInt64(config["port"])
isEnabled := candy.ToBool(config["enabled"])
value := candy.ToFloat64(data)
```

## 日志 - 必用 lazygophers/log

```go
import "github.com/lazygophers/log"

log.Infof("proto file:%s", protoFile)
log.Warnf("not found %s", path)
log.Errorf("err:%v", err)
log.Fatalf("failed to load state")
```

## Red Flags

| AI 可能的理性化解释 | 实际应该检查的内容 | 严重程度 |
|---------------------|-------------------|---------|
| "for 循环更直观" | 是否使用 candy 操作集合？ | 高 |
| "手动转换更可控" | 字符串转换是否用 stringx？ | 高 |
| "os.Stat 是标准库" | 文件操作是否用 osx？ | 中 |
| "encoding/json 够用" | 是否用 lazygophers/utils/json？ | 中 |
| "自己实现更灵活" | 是否已有 candy/stringx 功能？ | 高 |
| "math.Min 够用了" | Go 1.21+ 是否使用内置 min/max？ | 低 |

## 检查清单

- [ ] 字符串转换使用 stringx
- [ ] 集合操作使用 candy（Map/Filter/Each）
- [ ] 文件检查使用 osx（IsFile/IsDir）
- [ ] 类型转换使用 candy（ToInt64/ToBool/ToFloat64）
- [ ] 日志使用 lazygophers/log
- [ ] 没有手动 for 循环遍历集合
- [ ] 没有手动字符串转换函数
- [ ] 没有使用 os.Stat 检查文件
- [ ] Go 1.21+ 使用内置 min/max/clear
