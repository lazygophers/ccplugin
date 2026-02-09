---
name: lazygophers-xtime-skills
description: lazygophers/utils xtime 模块完整指南 - 时间常量、时间计算、农历转换、节气日历等时间处理功能
---

# lazygophers-xtime: Go 时间处理扩展库完整指南

## 目录

- [模块概述](#模块概述)
- [核心功能](#核心功能)
- [时间常量](#时间常量)
- [时间解析](#时间解析)
- [时间计算](#时间计算)
- [时间范围计算](#时间范围计算)
- [农历功能](#农历功能)
- [节气与季节](#节气与季节)
- [综合日历](#综合日历)
- [完整示例](#完整示例)

---

## 模块概述

`xtime` 是 `lazygophers/utils` 提供的 Go 时间处理扩展库，基于标准库 `time` 封装，提供以下增强功能：

1. **扩展时间常量** - 半小时、半天、工作日、周、月、季度、年、十年、世纪等
2. **灵活时间解析** - 支持多种格式自动识别
3. **便捷时间计算** - 获取时间范围（月初/月末、季初/季末、年初/年末等）
4. **农历支持** - 公历/农历转换、闰月判断、生肖计算
5. **节气系统** - 24节气精确计算（支持1904-3000年）
6. **综合日历** - 公历、农历、干支、节气一体化展示

**安装：**

```bash
go get github.com/lazygophers/utils/xtime
```

**导入：**

```go
import "github.com/lazygophers/utils/xtime"
```

---

## 核心功能

### 1. Time 结构体

增强的时间类型，封装了标准库 `time.Time` 并附加配置：

```go
type Time struct {
    time.Time              // 标准库时间
    *Config                // 配置信息
}

type Config struct {
    WeekStartDay time.Weekday   // 周起始日（默认周一）
    TimeLocation *time.Location // 时区（默认本地时区）
    TimeFormats  []string       // 自定义时间格式
}
```

### 2. 创建时间对象

```go
// 获取当前时间
now := xtime.Now()

// 从标准库 time.Time 创建
t := xtime.With(time.Now())

// 解析时间字符串
t, err := xtime.Parse("2023-01-15")
t, err := xtime.Parse("2023-01-15 14:30:00")
t, err := xtime.Parse("01/15/2023")

// MustParse - 解析失败会 panic
t := xtime.MustParse("2023-01-15")
```

---

## 时间常量

### 基础时间单位

```go
xtime.Nanosecond   // 纳秒（time.Nanosecond）
xtime.Microsecond  // 微秒（time.Microsecond）
xtime.Millisecond // 毫秒（time.Millisecond）
xtime.Second       // 秒（time.Second）
xtime.Minute       // 分钟（time.Minute）
xtime.Hour         // 小时（time.Hour）
```

### 扩展时间常量

```go
xtime.HalfHour  // 30分钟（time.Minute * 30）
xtime.HalfDay   // 半天（time.Hour * 12）
xtime.Day       // 一天（time.Hour * 24）
```

### 工作日相关

```go
xtime.WorkDayWeek  // 工作日周（5天）
xtime.ResetDayWeek // 周末（2天）
xtime.Week         // 一周（7天）

xtime.WorkDayMonth  // 工作日月（21.5天）
xtime.ResetDayMonth // 重置日月（8.5天）
xtime.Month         // 一个月（30天）
```

### 长周期常量

```go
xtime.QUARTER  // 一个季度（91天）
xtime.Year     // 一年（365天）
xtime.Decade   // 十年（3652天 = 10年 + 2天）
xtime.Century  // 世纪（36525天 = 100年 + 25天）
```

### 使用示例

```go
// 计算过期时间
expiry := time.Now().Add(xtime.Week)        // 一周后
expiry := time.Now().Add(xtime.WorkDayMonth) // 21.5个工作日后

// 计算间隔
if elapsed > xtime.Hour {
    fmt.Println("超过1小时")
}

// 循环间隔
ticker := time.NewTicker(xtime.Minute * 5)
```

---

## 时间解析

### Parse 函数

支持多种时间格式的自动识别：

```go
// ISO 格式
t, _ := xtime.Parse("2023-01-15")
t, _ := xtime.Parse("2023-01-15T14:30:00Z")

// 日期时间
t, _ := xtime.Parse("2023-01-15 14:30:00")

// 美国日期格式
t, _ := xtime.Parse("01/15/2023")

// 仅时间
t, _ := xtime.Parse("14:30")

// 多个参数
t, _ := xtime.Parse("2023-01-15", "14:30:00")
```

### MustParse 函数

解析失败会 panic，适合配置文件等场景：

```go
// 确保时间格式正确
t := xtime.MustParse("2023-01-15")

// 在 init 中使用
var startTime time.Time
func init() {
    startTime = xtime.MustParse("2023-01-01 00:00:00").Time
}
```

### With 函数

包装标准库 time.Time 为增强类型：

```go
// 包装时间对象
t := xtime.With(time.Now())

// 自动配置默认值
fmt.Println(t.Config.WeekStartDay)   // Monday
fmt.Println(t.Config.TimeLocation)   // Local
fmt.Println(t.Config.TimeFormats)    // []
```

---

## 时间计算

### Unix 时间戳

```go
// 当前时间戳（秒）
timestamp := xtime.NowUnix()

// 当前时间戳（毫秒）
timestampMs := xtime.NowUnixMilli()

// 指定时间戳
timestamp := xtime.Now().Unix()
timestampMs := xtime.Now().UnixMilli()
```

### 时间加减

```go
now := xtime.Now()

// 加减时间（使用标准库）
tomorrow := now.Add(xtime.Day)
nextWeek := now.Add(xtime.Week)
nextMonth := now.Add(xtime.Month)

// 减时间
yesterday := now.Add(-xtime.Day)
lastWeek := now.Add(-xtime.Week)
```

### 时间比较

```go
now := xtime.Now()
future := now.Add(xtime.Day)

// 判断先后
now.Before(future)  // true
now.After(future)   // false
now.Equal(future)   // false

// 计算间隔
duration := future.Sub(now)
fmt.Println(duration.Hours())  // 24
```

### 随机延迟

```go
// 默认随机睡眠 1-3 秒
xtime.RandSleep()

// 指定最大睡眠时间
xtime.RandSleep(time.Second * 5)  // 0-5秒

// 指定范围
xtime.RandSleep(time.Second, time.Second*3)  // 1-3秒
```

---

## 时间范围计算

### 方法列表

| 方法 | 说明 |
|------|------|
| `BeginningOfMinute()` | 分钟开始（00秒） |
| `BeginningOfHour()` | 小时开始（00分00秒） |
| `BeginningOfDay()` | 天开始（00:00:00） |
| `BeginningOfWeek()` | 周开始（周一） |
| `BeginningOfMonth()` | 月开始（1号） |
| `BeginningOfQuarter()` | 季度开始 |
| `BeginningOfHalf()` | 半年开始 |
| `BeginningOfYear()` | 年开始（1月1日） |
| `EndOfMinute()` | 分钟结束（59秒） |
| `EndOfHour()` | 小时结束（59分59秒） |
| `EndOfDay()` | 天结束（23:59:59） |
| `EndOfWeek()` | 周结束（周日） |
| `EndOfMonth()` | 月结束（月末） |
| `EndOfQuarter()` | 季度结束 |
| `EndOfHalf()` | 半年结束 |
| `EndOfYear()` | 年结束（12月31日） |
| `Quarter()` | 季度编号（1-4） |

### 实例方法

```go
now := xtime.Now()

// 分钟范围
start := now.BeginningOfMinute()  // 2023-08-15 14:30:00
end := now.EndOfMinute()          // 2023-08-15 14:30:59

// 小时范围
start := now.BeginningOfHour()    // 2023-08-15 14:00:00
end := now.EndOfHour()            // 2023-08-15 14:59:59

// 天范围
start := now.BeginningOfDay()     // 2023-08-15 00:00:00
end := now.EndOfDay()             // 2023-08-15 23:59:59

// 周范围
start := now.BeginningOfWeek()    // 2023-08-14 00:00:00（周一）
end := now.EndOfWeek()            // 2023-08-20 23:59:59（周日）

// 月范围
start := now.BeginningOfMonth()   // 2023-08-01 00:00:00
end := now.EndOfMonth()           // 2023-08-31 23:59:59

// 季度范围
start := now.BeginningOfQuarter() // 2023-07-01 00:00:00
end := now.EndOfQuarter()         // 2023-09-30 23:59:59
quarter := now.Quarter()          // 3

// 年范围
start := now.BeginningOfYear()    // 2023-01-01 00:00:00
end := now.EndOfYear()            // 2023-12-31 23:59:59
```

### 全局函数

```go
// 基于当前时间的快捷方法
start := xtime.BeginningOfDay()   // 今天 00:00:00
end := xtime.EndOfDay()           // 今天 23:59:59

start := xtime.BeginningOfMonth() // 本月 1号
end := xtime.EndOfMonth()         // 本月月末

quarter := xtime.Quarter()        // 当前季度（1-4）
```

### 使用场景

```go
// 查询今天的数据
todayStart := xtime.BeginningOfDay()
todayEnd := xtime.EndOfDay()
db.Where("created_at >= ? AND created_at <= ?", todayStart, todayEnd)

// 查询本月数据
monthStart := xtime.BeginningOfMonth()
monthEnd := xtime.EndOfMonth()

// 统计本季度数据
quarter := xtime.Quarter()
quarterStart := xtime.BeginningOfQuarter()
quarterEnd := xtime.EndOfQuarter()

// 计算年度进度
now := xtime.Now()
yearStart := now.BeginningOfYear()
yearEnd := now.EndOfYear()
yearProgress := float64(now.Sub(yearStart.Time)) / float64(yearEnd.Sub(yearStart.Time))
fmt.Printf("年度进度: %.1f%%\n", yearProgress * 100)
```

---

## 农历功能

### Lunar 结构体

```go
type Lunar struct {
    time.Time      // 公历时间
    year    int64  // 农历年份
    month   int64  // 农历月份（1-12）
    day     int64  // 农历日期（1-30）
    monthIsLeap bool // 是否闰月
}
```

### 创建农历对象

```go
// 从公历时间创建农历
lunar := xtime.WithLunar(time.Now())

// 获取农历信息
fmt.Println(lunar.Year())   // 2023
fmt.Println(lunar.Month())  // 8
fmt.Println(lunar.Day())    // 15
fmt.Println(lunar.IsLeapMonth()) // false
```

### 农历方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `Year()` | int64 | 农历年份数字 |
| `Month()` | int64 | 农历月份数字 |
| `Day()` | int64 | 农历日期数字 |
| `IsLeap()` | bool | 是否闰年 |
| `LeapMonth()` | int64 | 闰月月份（0表示无） |
| `IsLeapMonth()` | bool | 当月是否闰月 |
| `Animal()` | string | 生肖（鼠、牛、虎...） |
| `YearAlias()` | string | 汉字年份（二零二三年） |
| `MonthAlias()` | string | 汉字月份（八月、闰六月） |
| `DayAlias()` | string | 汉字日期（十五、初一） |
| `Date()` | string | 格式化日期（2023-08-15） |
| `MonthDayAlias()` | string | 月日组合（8-15、闰6-15） |

### 使用示例

```go
lunar := xtime.WithLunar(time.Now())

// 基本信息输出
fmt.Printf("农历日期: %s\n", lunar.Date())                    // 2023-08-15
fmt.Printf("汉字年份: %s\n", lunar.YearAlias())              // 二零二三年
fmt.Printf("汉字月份: %s\n", lunar.MonthAlias())             // 八月
fmt.Printf("汉字日期: %s\n", lunar.DayAlias())               // 十五
fmt.Printf("月日组合: %s\n", lunar.MonthDayAlias())          // 8-15

// 闰月判断
if lunar.IsLeap() {
    fmt.Printf("今年闰月: %d月\n", lunar.LeapMonth())
}
if lunar.IsLeapMonth() {
    fmt.Println("当前是闰月")
}

// 生肖信息
fmt.Printf("生肖: %s\n", lunar.Animal())  // 兔
```

### 公历转农历

```go
// 转换函数（内部使用）
lunarYear, lunarMonth, lunarDay, isLeap := xtime.FromSolarTimestamp(timestamp)

fmt.Printf("农历: %d年%d月%d日", lunarYear, lunarMonth, lunarDay)
if isLeap {
    fmt.Print("（闰月）")
}
```

---

## 节气与季节

### Solarterm 类型

```go
type Solarterm struct {
    time.Time
}

// 获取指定时间的下一个节气
nextTerm := xtime.NextSolarterm(time.Now())
fmt.Printf("下个节气: %s (%s)\n", nextTerm.String(), nextTerm.Time.Format("2006-01-02 15:04"))
```

### 24 节气

支持精确计算 1904-3000 年的所有节气：

```go
// 立春、雨水、惊蛰、春分、清明、谷雨
// 立夏、小满、芒种、夏至、小暑、大暑
// 立秋、处暑、白露、秋分、寒露、霜降
// 立冬、小雪、大雪、冬至、小寒、大寒
```

### 节气方法

```go
now := time.Now()

// 下个节气
nextTerm := xtime.NextSolarterm(now)
fmt.Printf("下个节气: %s\n", nextTerm.String())
fmt.Printf("节气时间: %s\n", nextTerm.Time.Format("2006-01-02 15:04:05"))

// 计算距离天数
daysUntil := int(nextTerm.Time.Sub(now).Hours() / 24)
fmt.Printf("还有 %d 天\n", daysUntil)
```

---

## 综合日历

### Calendar 结构体

整合公历、农历、干支、节气的综合日历类型：

```go
type Calendar struct {
    *Time                  // 公历时间
    lunar  *Lunar          // 农历信息
    zodiac ZodiacInfo      // 生肖干支
    season SeasonInfo      // 节气季节
}
```

### 创建日历

```go
// 从指定时间创建
cal := xtime.NewCalendar(time.Now())

// 获取当前日历
cal := xtime.NowCalendar()
```

### 公历方法

```go
cal.Time.Format("2006-01-02")    // 2023-08-15
cal.Time.Weekday().String()      // Tuesday
cal.Time.Unix()                  // 时间戳
```

### 农历方法

| 方法 | 返回值 | 示例 |
|------|--------|------|
| `Lunar()` | *Lunar | 农历对象 |
| `LunarDate()` | string | "农历二零二三年八月十五" |
| `LunarDateShort()` | string | "八月十五" |
| `IsLunarLeapYear()` | bool | 是否闰年 |
| `LunarLeapMonth()` | int64 | 闰月月份（0=无） |

```go
fmt.Println(cal.LunarDate())       // 农历二零二三年八月十五
fmt.Println(cal.LunarDateShort())  // 八月十五
fmt.Println(cal.IsLunarLeapYear()) // false
fmt.Println(cal.LunarLeapMonth())  // 0
```

### 干支方法

| 方法 | 返回值 | 示例 |
|------|--------|------|
| `Animal()` | string | "兔" |
| `AnimalWithYear()` | string | "兔年" |
| `YearGanZhi()` | string | "癸卯" |
| `MonthGanZhi()` | string | "庚申" |
| `DayGanZhi()` | string | "己巳" |
| `HourGanZhi()` | string | "甲午" |
| `FullGanZhi()` | string | "癸卯年 庚申月 己巳日 甲午时" |

```go
fmt.Println(cal.Animal())         // 兔
fmt.Println(cal.AnimalWithYear()) // 兔年
fmt.Println(cal.FullGanZhi())     // 癸卯年 庚申月 己巳日 甲午时
```

### 节气季节方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `CurrentSolarTerm()` | string | 当前节气 |
| `NextSolarTerm()` | string | 下个节气 |
| `NextSolarTermTime()` | time.Time | 下个节气时间 |
| `DaysToNextTerm()` | int | 距下个节气天数 |
| `Season()` | string | 当前季节 |
| `SeasonProgress()` | float64 | 季节进度（0-1） |
| `YearProgress()` | float64 | 年度进度（0-1） |

```go
fmt.Println(cal.CurrentSolarTerm())  // 立秋
fmt.Println(cal.NextSolarTerm())     // 处暑
fmt.Println(cal.DaysToNextTerm())    // 5
fmt.Println(cal.Season())            // 夏
fmt.Printf("季节进度: %.1f%%\n", cal.SeasonProgress() * 100)  // 85.5%
fmt.Printf("年度进度: %.1f%%\n", cal.YearProgress() * 100)    // 62.3%
```

### 格式化输出

```go
// 简短格式
fmt.Println(cal.String())
// 输出: 2023年08月15日 八月十五 兔年 立秋

// 详细格式
fmt.Println(cal.DetailedString())
// 输出:
// 公历：2023年08月15日 14:30:00 Tuesday
// 农历：农历二零二三年八月十五
// 干支：癸卯年 庚申月 己巳日 甲午时
// 节气：立秋（下个：处暑，5天后）
// 季节：夏（进度：85.5%）
```

### JSON 序列化

```go
// 转换为 map，便于 JSON 序列化
data := cal.ToMap()

jsonBytes, _ := json.MarshalIndent(data, "", "  ")
fmt.Println(string(jsonBytes))

// 输出结构:
// {
//   "solar": {
//     "date": "2023-08-15",
//     "time": "14:30:00",
//     "weekday": "Tuesday",
//     "timestamp": 1692097800
//   },
//   "lunar": {
//     "year": 2023,
//     "month": 8,
//     "day": 15,
//     "date": "农历二零二三年八月十五",
//     "dateShort": "八月十五",
//     "isLeapYear": false,
//     "leapMonth": 0
//   },
//   "zodiac": {
//     "animal": "兔",
//     "yearGanZhi": "癸卯",
//     "monthGanZhi": "庚申",
//     "dayGanZhi": "己巳",
//     "hourGanZhi": "甲午",
//     "fullGanZhi": "癸卯年 庚申月 己巳日 甲午时"
//   },
//   "season": {
//     "current": "立秋",
//     "next": "处暑",
//     "nextTime": "2023-08-23T17:01:00+08:00",
//     "daysToNext": 8,
//     "season": "夏",
//     "seasonProgress": 0.855,
//     "yearProgress": 0.623
//   }
// }
```

---

## 完整示例

### 示例 1：时间范围查询

```go
package main

import (
    "fmt"
    "github.com/lazygophers/utils/xtime"
)

func main() {
    // 查询今天创建的订单
    todayStart := xtime.BeginningOfDay()
    todayEnd := xtime.EndOfDay()

    fmt.Printf("查询时间范围: %s - %s\n", todayStart, todayEnd)

    // SQL 示例
    // SELECT * FROM orders
    // WHERE created_at >= ? AND created_at <= ?
    // args: todayStart.Time, todayEnd.Time
}
```

### 示例 2：农历生日提醒

```go
package main

import (
    "fmt"
    "time"
    "github.com/lazygophers/utils/xtime"
)

func main() {
    // 生日（公历）
    birthday := time.Date(1990, 5, 20, 0, 0, 0, 0, time.Local)

    // 转换为农历
    lunarBirthday := xtime.WithLunar(birthday)

    fmt.Printf("您的农历生日: %s%s\n",
        lunarBirthday.MonthAlias(),
        lunarBirthday.DayAlias())

    // 今年生日
    now := xtime.Now()
    lunarNow := xtime.WithLunar(now.Time)

    if lunarNow.Month() == lunarBirthday.Month() &&
       lunarNow.Day() == lunarBirthday.Day() {
        fmt.Println("今天是您的农历生日！")
    }
}
```

### 示例 3：节气养生提醒

```go
package main

import (
    "fmt"
    "time"
    "github.com/lazygophers/utils/xtime"
)

func main() {
    cal := xtime.NowCalendar()

    fmt.Printf("当前节气: %s\n", cal.CurrentSolarTerm())
    fmt.Printf("下个节气: %s（%d天后）\n",
        cal.NextSolarTerm(),
        cal.DaysToNextTerm())

    // 根据节气给出建议
    switch cal.CurrentSolarTerm() {
    case "立春", "雨水", "惊蛰":
        fmt.Println("春季养生：注意保暖，多吃绿色蔬菜")
    case "立夏", "小满", "芒种":
        fmt.Println("夏季养生：防暑降温，清淡饮食")
    case "立秋", "处暑", "白露":
        fmt.Println("秋季养生：润燥养肺，早睡早起")
    case "立冬", "小雪", "大雪":
        fmt.Println("冬季养生：保暖御寒，温补饮食")
    }
}
```

### 示例 4：日历信息展示

```go
package main

import (
    "encoding/json"
    "fmt"
    "github.com/lazygophers/utils/xtime"
)

func main() {
    cal := xtime.NowCalendar()

    // 文本格式
    fmt.Println("=== 今日日历 ===")
    fmt.Println(cal.String())
    fmt.Println()
    fmt.Println("详细信息:")
    fmt.Println(cal.DetailedString())
    fmt.Println()

    // JSON 格式
    fmt.Println("=== JSON 格式 ===")
    data := cal.ToMap()
    jsonBytes, _ := json.MarshalIndent(data, "", "  ")
    fmt.Println(string(jsonBytes))
}
```

### 示例 5：工作日计算

```go
package main

import (
    "fmt"
    "time"
    "github.com/lazygophers/utils/xtime"
)

func main() {
    now := xtime.Now()

    // 本月工作日天数
    workDays := xtime.WorkDayMonth
    fmt.Printf("本月工作日: %.1f 天\n", workDays.Hours()/24)

    // 计算截止日期（21.5个工作日）
    deadline := now.Add(workDays)
    fmt.Printf("截止日期: %s\n", deadline.Format("2006-01-02"))

    // 计算项目周期
    start := xtime.BeginningOfMonth()
    end := start.Add(xtime.WorkDayMonth)
    duration := end.Sub(start.Time)
    fmt.Printf("项目周期: %.0f 天\n", duration.Hours()/24)
}
```

### 示例 6：时间对比分析

```go
package main

import (
    "fmt"
    "time"
    "github.com/lazygophers/utils/xtime"
)

func main() {
    // 两个时间点
    t1 := xtime.MustParse("2023-01-01")
    t2 := xtime.MustParse("2023-12-31")

    // 时间差
    duration := t2.Sub(t1.Time)
    fmt.Printf("相差: %.0f 天\n", duration.Hours()/24)

    // 季度对比
    fmt.Printf("Q1 开始: %s\n", t1.BeginningOfQuarter())
    fmt.Printf("Q4 开始: %s\n", t2.BeginningOfQuarter())

    // 年度进度对比
    progress1 := float64(t1.Sub(t1.BeginningOfYear().Time)) /
                float64(t1.EndOfYear().Sub(t1.BeginningOfYear().Time))
    progress2 := float64(t2.Sub(t2.BeginningOfYear().Time)) /
                float64(t2.EndOfYear().Sub(t2.BeginningOfYear().Time))

    fmt.Printf("年度进度: %.1f%% vs %.1f%%\n", progress1*100, progress2*100)
}
```

---

## 最佳实践

### 1. 时间解析

```go
// ✅ 推荐：使用 Parse 处理多种格式
t, err := xtime.Parse("2023-01-15")
if err != nil {
    return err
}

// ✅ 推荐：配置文件使用 MustParse
var startTime = xtime.MustParse("2023-01-01 00:00:00").Time

// ❌ 避免：直接使用 time.Parse（格式限制）
t, err := time.Parse("2006-01-02", "2023-01-15")
```

### 2. 时间范围计算

```go
// ✅ 推荐：使用 xtime 的时间范围方法
todayStart := xtime.BeginningOfDay()
todayEnd := xtime.EndOfDay()

// ❌ 避免：手动计算
now := time.Now()
todayStart := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())
todayEnd := time.Date(now.Year(), now.Month(), now.Day(), 23, 59, 59, int(time.Second-time.Nanosecond), now.Location())
```

### 3. 农历转换

```go
// ✅ 推荐：使用综合日历获取所有信息
cal := xtime.NowCalendar()
fmt.Println(cal.LunarDate())
fmt.Println(cal.FullGanZhi())

// ✅ 推荐：仅需农历时使用 Lunar
lunar := xtime.WithLunar(time.Now())
fmt.Println(lunar.MonthAlias(), lunar.DayAlias())

// ❌ 避免：手动计算农历（算法复杂）
```

### 4. 常量使用

```go
// ✅ 推荐：使用语义化常量
time.Sleep(xtime.Minute)
time.Sleep(xtime.WorkDayWeek)
time.Sleep(xtime.Month)

// ❌ 避免：硬编码数字
time.Sleep(60 * time.Second)
time.Sleep(5 * 24 * time.Hour)
time.Sleep(30 * 24 * time.Hour)
```

---

## 注意事项

1. **时区处理**：默认使用 `time.Local`，需要时区时应显式指定
2. **农历范围**：仅支持 1900-2100 年的公历时间转换
3. **节气范围**：支持 1904-3000 年的精确节气计算
4. **闰月处理**：农历闰月通过 `IsLeapMonth()` 判断
5. **周起始日**：默认周一，可通过 `Config.WeekStartDay` 修改

---

## 相关资源

- **GitHub**: https://github.com/lazygophers/utils/tree/master/xtime
- **标准库 time**: https://pkg.go.dev/time
- **农历算法**: 基于紫金山天文台《中国天文年历》
- **节气数据**: J2000 历表计算

---

## 更新日志

- **2023-08**: 添加综合日历功能
- **2023-06**: 优化节气计算精度
- **2023-01**: 初始版本，支持基础时间常量和农历转换
