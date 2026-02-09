---
name: lazygophers-human-skills
description: lazygophers/utils human 模块完整指南 - 人类友好格式化工具，支持字节大小、速度、时间间隔、相对时间等多语言格式化
---

# lazygophers-human: 人类友好格式化工具

## 模块概述

`human` 模块是 lazygophers/utils 库中专门用于将计算机数据转换为人类可读格式的工具集。它提供了字节大小、网络速度、时间间隔、相对时间等多种格式化功能，并支持多语言本地化。

**核心特性:**

- **字节大小格式化** - 将字节数转换为 B/KB/MB/GB/TB/PB
- **速度格式化** - 字节速度和比特速度分别支持
- **时间间隔格式化** - 支持自然语言和时钟格式
- **相对时间格式化** - "3分钟前"、"2小时后"等人类友好表达
- **多语言支持** - 内置 8+ 种语言（中文、英文、日文、韩文、西班牙语、俄语等）
- **可定制选项** - 精度控制、紧凑模式、自定义语言环境

---

## 安装与导入

```bash
go get github.com/lazygophers/utils/human
```

```go
import "github.com/lazygophers/utils/human"
```

---

## 核心功能

### 1. 字节大小格式化

将字节数转换为人类可读的大小格式（使用二进制换算 1024）。

**函数签名:**
```go
func ByteSize(bytes int64, opts ...Option) string
```

**基本用法:**
```go
fmt.Println(human.ByteSize(0))        // "0 B"
fmt.Println(human.ByteSize(1))        // "1 B"
fmt.Println(human.ByteSize(1024))     // "1 KB"
fmt.Println(human.ByteSize(1536))     // "1.5 KB"
fmt.Println(human.ByteSize(1048576))  // "1 MB"
fmt.Println(human.ByteSize(1073741824)) // "1 GB"
fmt.Println(human.ByteSize(1099511627776)) // "1 TB"
```

**带选项的用法:**
```go
// 设置精度
fmt.Println(human.ByteSize(1536, human.WithPrecision(2))) // "1.5 KB"

// 紧凑模式（无空格）
fmt.Println(human.ByteSize(1536, human.WithCompact())) // "1.5KB"

// 组合选项
fmt.Println(human.ByteSize(1536,
    human.WithPrecision(2),
    human.WithCompact(),
)) // "1.5KB"
```

**单位换算规则:**
- 使用二进制换算（1024 进制）
- 自动选择合适的单位级别
- 支持从 B 到 PB 的完整单位范围

---

### 2. 网络速度格式化

#### 2.1 字节速度

格式化字节每秒速度（使用二进制换算 1024）。

**函数签名:**
```go
func Speed(bytesPerSecond int64, opts ...Option) string
```

**示例:**
```go
fmt.Println(human.Speed(0))               // "0 B/s"
fmt.Println(human.Speed(1))               // "1 B/s"
fmt.Println(human.Speed(1024))            // "1 KB/s"
fmt.Println(human.Speed(1048576))         // "1 MB/s"
fmt.Println(human.Speed(1572864))         // "1.5 MB/s"
fmt.Println(human.Speed(104857600))       // "100 MB/s"
```

#### 2.2 比特速度

格式化比特每秒速度（使用十进制换算 1000，符合网络标准）。

**函数签名:**
```go
func BitSpeed(bitsPerSecond int64, opts ...Option) string
```

**示例:**
```go
fmt.Println(human.BitSpeed(0))              // "0 bps"
fmt.Println(human.BitSpeed(1000))           // "1 Kbps"
fmt.Println(human.BitSpeed(1500))           // "1.5 Kbps"
fmt.Println(human.BitSpeed(1000000))        // "1 Mbps"
fmt.Println(human.BitSpeed(1000000000))     // "1 Gbps"
fmt.Println(human.BitSpeed(1000000000000))  // "1 Tbps"
```

**重要区别:**
- `Speed()` - 字节速度，1024 进制
- `BitSpeed()` - 比特速度，1000 进制（符合网络标准）

```go
// 相同数值的不同结果
value := int64(8000)
fmt.Println(human.Speed(value))    // "7.8 KB/s"  (8000/1024)
fmt.Println(human.BitSpeed(value)) // "8 Kbps"    (8000/1000)
```

---

### 3. 时间间隔格式化

将 `time.Duration` 转换为人类友好的时间表达。

**函数签名:**
```go
func Duration(d time.Duration, opts ...Option) string
```

**基本用法（自然语言格式）:**
```go
fmt.Println(human.Duration(0))                      // "0 second"
fmt.Println(human.Duration(time.Second))            // "1 second"
fmt.Println(human.Duration(30 * time.Second))       // "30 seconds"
fmt.Println(human.Duration(time.Minute))            // "1 minute"
fmt.Println(human.Duration(90 * time.Second))       // "1 minute 30 seconds"
fmt.Println(human.Duration(time.Hour))              // "1 hour"
fmt.Println(human.Duration(90 * time.Minute))       // "1 hour 30 minutes"
fmt.Println(human.Duration(25 * time.Hour))         // "1 day 1 hour"
```

**时钟格式:**
```go
// 使用 ClockDuration 快捷函数
fmt.Println(human.ClockDuration(0))                          // "0:00"
fmt.Println(human.ClockDuration(30 * time.Second))           // "0:30"
fmt.Println(human.ClockDuration(time.Minute))                // "1:00"
fmt.Println(human.ClockDuration(90 * time.Second))           // "1:30"
fmt.Println(human.ClockDuration(time.Hour))                  // "1:00"
fmt.Println(human.ClockDuration(time.Hour + 10*time.Minute)) // "1:10"
fmt.Println(human.ClockDuration(2*time.Hour + 30*time.Minute + 45*time.Second)) // "2:30:45"
```

**使用选项:**
```go
// 使用 WithClockFormat 选项
fmt.Println(human.Duration(90*time.Second, human.WithClockFormat())) // "1:30"

// 负数时间
fmt.Println(human.Duration(-90*time.Second))  // "-1 minute 30 seconds"
fmt.Println(human.Duration(-90*time.Second, human.WithClockFormat())) // "-1:30"
```

**格式化规则:**
- 自然语言格式：显示最合适的 2 个时间单位
- 时钟格式：H:MM:SS 或 H:MM（秒数为 0 时省略）
- 自动处理单复数形式

---

### 4. 相对时间格式化

将绝对时间转换为相对时间表达（如"3分钟前"）。

**函数签名:**
```go
func RelativeTime(t time.Time, opts ...Option) string
```

**过去时间示例:**
```go
now := time.Now()

fmt.Println(human.RelativeTime(now.Add(-5*time.Second)))   // "just now"
fmt.Println(human.RelativeTime(now.Add(-30*time.Second)))  // "30 seconds ago"
fmt.Println(human.RelativeTime(now.Add(-2*time.Minute)))   // "2 minutes ago"
fmt.Println(human.RelativeTime(now.Add(-1*time.Hour)))     // "1 hours ago"
fmt.Println(human.RelativeTime(now.Add(-3*time.Hour)))     // "3 hours ago"
fmt.Println(human.RelativeTime(now.Add(-24*time.Hour)))    // "1 days ago"
fmt.Println(human.RelativeTime(now.Add(-7*24*time.Hour)))  // "1 weeks ago"
```

**未来时间示例:**
```go
now := time.Now()

fmt.Println(human.RelativeTime(now.Add(5*time.Second)))   // "in 5 seconds"
fmt.Println(human.RelativeTime(now.Add(2*time.Minute)))   // "in 2 minutes"
fmt.Println(human.RelativeTime(now.Add(1*time.Hour)))     // "in 1 hours"
fmt.Println(human.RelativeTime(now.Add(3*time.Hour)))     // "in 3 hours"
fmt.Println(human.RelativeTime(now.Add(24*time.Hour)))    // "in 1 days"
```

**时间范围规则:**
| 时间差 | 显示格式 |
|--------|----------|
| < 10秒 | "just now" / "刚刚" |
| < 1分钟 | "N seconds ago" / "N秒前" |
| < 1小时 | "N minutes ago" / "N分钟前" |
| < 1天 | "N hours ago" / "N小时前" |
| < 1周 | "N days ago" / "N天前" |
| < 1月 | "N weeks ago" / "N周前" |
| < 1年 | "N months ago" / "N个月前" |
| ≥ 1年 | "N years ago" / "N年前" |

---

## 选项系统

所有格式化函数都支持选项模式，可以灵活控制输出格式。

### 可用选项

| 选项 | 类型 | 说明 |
|------|------|------|
| `WithPrecision(n)` | int | 设置小数精度（默认 1） |
| `WithLocale(lang)` | string | 设置语言环境 |
| `WithCompact()` | - | 启用紧凑模式（无空格） |
| `WithClockFormat()` | - | 启用时钟格式（仅 Duration） |

### 使用示例

```go
// 设置精度
human.ByteSize(1536, human.WithPrecision(2))  // "1.50 KB"
human.ByteSize(1536, human.WithPrecision(3))  // "1.500 KB"

// 设置语言环境
human.ByteSize(1024, human.WithLocale("zh"))  // "1 KB"
human.Duration(time.Hour, human.WithLocale("zh"))  // "1小时"

// 紧凑模式
human.ByteSize(1536, human.WithCompact())  // "1.5KB"
human.Speed(1048576, human.WithCompact())  // "1MB/s"

// 组合多个选项
human.ByteSize(1536,
    human.WithPrecision(2),
    human.WithCompact(),
    human.WithLocale("en"),
)  // "1.50KB"

// 时钟格式
human.Duration(90*time.Second, human.WithClockFormat())  // "1:30"
```

---

## 多语言支持

### 支持的语言

| 语言代码 | 语言 | 区域 |
|----------|------|------|
| `en` | 英语 | US |
| `zh` / `zh-CN` | 简体中文 | CN |
| `zh-TW` | 繁体中文 | TW |
| `ja` | 日语 | JP |
| `ko` | 韩语 | KR |
| `es` | 西班牙语 | ES |
| `ru` | 俄语 | RU |
| `ar` | 阿拉伯语 | - |
| `fr` | 法语 | - |

### 全局语言设置

```go
// 设置默认语言环境
human.SetLocale("zh-CN")
fmt.Println(human.GetLocale())  // "zh-CN"

// 所有后续格式化都使用中文
fmt.Println(human.Duration(time.Hour))  // "1小时"
fmt.Println(human.Duration(90*time.Minute))  // "1小时 30分钟"
```

### 单次调用语言设置

```go
// 使用 WithLocale 选项
fmt.Println(human.Duration(time.Hour, human.WithLocale("zh")))  // "1小时"
fmt.Println(human.Duration(time.Hour, human.WithLocale("ja")))  // "1時間"
fmt.Println(human.Duration(time.Hour, human.WithLocale("ko")))  // "1시간"
```

### 语言回退机制

当指定的语言不存在时，会按以下顺序回退：
1. 尝试完整匹配（如 `zh-CN`）
2. 尝试语言匹配（如 `zh`）
3. 回退到英语（`en`）

```go
// 这些都会成功
fmt.Println(human.Duration(time.Hour, human.WithLocale("zh-CN")))  // "1小时"
fmt.Println(human.Duration(time.Hour, human.WithLocale("zh")))     // "1小时"
fmt.Println(human.Duration(time.Hour, human.WithLocale("xx")))     // "1 hour" (回退到英语)
```

### 各语言示例

```go
d := 90 * time.Minute
t := time.Now().Add(-2 * time.Hour)

// 中文
fmt.Println(human.Duration(d, human.WithLocale("zh")))     // "1小时 30分钟"
fmt.Println(human.RelativeTime(t, human.WithLocale("zh"))) // "2小时前"

// 英文
fmt.Println(human.Duration(d, human.WithLocale("en")))     // "1 hour 30 minutes"
fmt.Println(human.RelativeTime(t, human.WithLocale("en"))) // "2 hours ago"

// 日语
fmt.Println(human.Duration(d, human.WithLocale("ja")))     // "1時間 30分"
fmt.Println(human.RelativeTime(t, human.WithLocale("ja"))) // "2時間前"

// 韩语
fmt.Println(human.Duration(d, human.WithLocale("ko")))     // "1시간 30분"
fmt.Println(human.RelativeTime(t, human.WithLocale("ko"))) // "2시간 전"

// 西班牙语
fmt.Println(human.Duration(d, human.WithLocale("es")))     // "1 hora 30 minutos"
fmt.Println(human.RelativeTime(t, human.WithLocale("es"))) // "hace 2 horas"

// 俄语
fmt.Println(human.Duration(d, human.WithLocale("ru")))     // "1 час 30 минуты"
fmt.Println(human.RelativeTime(t, human.WithLocale("ru"))) // "2 часов назад"
```

---

## 高级用法

### 1. 自定义语言环境

可以注册自定义的语言环境配置：

```go
human.RegisterLocale("custom", &human.Locale{
    Language:      "custom",
    Region:        "XX",
    ByteUnits:     []string{"B", "KB", "MB", "GB", "TB", "PB"},
    SpeedUnits:    []string{"B/s", "KB/s", "MB/s", "GB/s", "TB/s", "PB/s"},
    BitSpeedUnits: []string{"bps", "Kbps", "Mbps", "Gbps", "Tbps", "Pbps"},

    TimeUnits: human.TimeUnits{
        Second: "秒",
        Minute: "分",
        Hour:   "时",
        Day:    "天",

        Seconds: "秒",
        Minutes: "分",
        Hours:   "时",
        Days:    "天",
    },

    RelativeTime: human.RelativeTimeStrings{
        JustNow:    "刚才",
        SecondsAgo: "%d秒前",
        MinutesAgo: "%d分钟前",
        HoursAgo:   "%d小时前",
        DaysAgo:    "%d天前",
    },
})

// 使用自定义语言
fmt.Println(human.Duration(time.Hour, human.WithLocale("custom")))  // "1时"
```

### 2. 向后兼容的 Options 结构

旧版本使用 Options 结构体，现在仍支持：

```go
opts := human.Options{
    Precision: 2,
    Locale:    "zh",
    Compact:   true,
}

fmt.Println(human.ByteSizeWithOptions(1536, opts))  // "1.50KB"
fmt.Println(human.SpeedWithOptions(1048576, opts))  // "1MB/s"
fmt.Println(human.BitSpeedWithOptions(1000000, opts))  // "1Mbps"
fmt.Println(human.DurationWithOptions(90*time.Second, opts))  // "1:30" (默认)
```

### 3. 性能考虑

对于性能敏感的场景，可以设置全局默认值以避免重复创建选项：

```go
// 启动时设置全局默认
human.SetLocale("zh")
human.SetDefaultPrecision(2)

// 后续直接使用，无需每次指定选项
for i := 0; i < 1000; i++ {
    fmt.Println(human.ByteSize(int64(i * 1024)))  // 自动使用 zh 和精度 2
}
```

### 4. 基准测试结果

根据官方测试数据：

```
BenchmarkByteSize-8      2000000    563 ns/op
BenchmarkSpeed-8         2000000    612 ns/op
BenchmarkDuration-8      1000000   1123 ns/op
BenchmarkRelativeTime-8   500000   2341 ns/op
```

性能建议：
- ByteSize/BitSpeed: 轻量级，可频繁调用
- Duration/RelativeTime: 相对耗时，建议缓存结果

---

## 实际应用场景

### 1. 文件管理工具

```go
func formatFileSize(size int64) string {
    return human.ByteSize(size, human.WithPrecision(2))
}

func getFileInfo(path string) {
    info, _ := os.Stat(path)
    fmt.Printf("文件大小: %s\n", formatFileSize(info.Size()))
}

// 输出:
// 文件大小: 1.50 MB
// 文件大小: 256.00 KB
```

### 2. 网络监控工具

```go
func displayNetworkStats(bytesPerSec int64, bitsPerSec int64) {
    fmt.Printf("下载速度: %s\n", human.Speed(bytesPerSec))
    fmt.Printf("带宽占用: %s\n", human.BitSpeed(bitsPerSec))
}

// 输出:
// 下载速度: 5.2 MB/s
// 带宽占用: 41.6 Mbps
```

### 3. 时间追踪应用

```go
func formatElapsedTime(start time.Time) string {
    elapsed := time.Since(start)
    return human.Duration(elapsed)
}

func formatCountdown(deadline time.Time) string {
    return human.RelativeTime(deadline)
}

// 使用示例
start := time.Now()
time.Sleep(90 * time.Second)
fmt.Printf("已用时间: %s\n", formatElapsedTime(start))  // "1 minute 30 seconds"

deadline := time.Now().Add(2 * time.Hour)
fmt.Printf("截止时间: %s\n", formatCountdown(deadline))  // "in 2 hours"
```

### 4. 日志系统

```go
func logProgress(current, total int64) {
    percent := float64(current) / float64(total) * 100
    speed := human.Speed(current / 2)  // 假设运行了2秒
    fmt.Printf("进度: %.1f%% (%s/%s, 速度: %s)\n",
        percent,
        human.ByteSize(current),
        human.ByteSize(total),
        speed,
    )
}

// 输出:
// 进度: 45.5% (450 MB/1 GB, 速度: 2.2 MB/s)
```

### 5. 多语言 UI

```go
func renderDuration(d time.Duration, userLang string) string {
    return human.Duration(d, human.WithLocale(userLang))
}

func renderRelativeTime(t time.Time, userLang string) string {
    return human.RelativeTime(t, human.WithLocale(userLang))
}

// 根据用户偏好显示
userLang := "zh"  // 从用户设置获取
fmt.Println(renderDuration(90*time.Minute, userLang))  // "1小时 30分钟"
fmt.Println(renderRelativeTime(time.Now().Add(-2*time.Hour), userLang))  // "2小时前"
```

### 6. 视频播放器

```go
func formatVideoPosition(current time.Duration, total time.Duration) string {
    return fmt.Sprintf("%s / %s",
        human.ClockDuration(current),
        human.ClockDuration(total),
    )
}

// 输出:
// 1:23 / 5:45
// 0:45 / 3:20
```

---

## 最佳实践

### 1. 选择合适的精度

```go
// 文件大小：1-2 位精度
human.ByteSize(1536, human.WithPrecision(1))  // "1.5 KB" ✅
human.ByteSize(1536, human.WithPrecision(3))  // "1.500 KB" ❌ 过度精确

// 网络速度：1 位精度
human.Speed(1572864, human.WithPrecision(1))  // "1.5 MB/s" ✅

// 时间间隔：无需精度（自动处理）
human.Duration(90 * time.Second)  // "1 minute 30 seconds" ✅
```

### 2. 使用紧凑模式

```go
// 表格显示、UI 标签等空间有限的场景
fmt.Printf("%-10s %s\n", "Size:", human.ByteSize(1536, human.WithCompact()))
// Size:      1.5KB
```

### 3. 时钟格式的选择

```go
// 视频播放器、计时器：使用时钟格式
human.ClockDuration(90*time.Second)  // "1:30" ✅

// 日志、文档：使用自然语言
human.Duration(90*time.Second)  // "1 minute 30 seconds" ✅
```

### 4. 相对时间的使用

```go
// 社交媒体、消息应用：使用相对时间
human.RelativeTime(publishTime)  // "3 hours ago" ✅

// 日志、审计记录：使用绝对时间
fmt.Println(publishTime.Format("2006-01-02 15:04:05"))  // ✅
```

### 5. 语言环境管理

```go
// 应用启动时设置全局语言
func init() {
    userLang := getUserLanguage()  // 从配置或用户设置获取
    human.SetLocale(userLang)
}

// 特殊场景覆盖全局设置
fmt.Println(human.Duration(d, human.WithLocale("en")))  // 临时使用英文
```

---

## 注意事项

### 1. 单位换算差异

```go
// 字节相关：使用 1024 进制（二进制）
human.ByteSize(1024)    // "1 KB"  (1024 bytes)
human.Speed(1024)       // "1 KB/s" (1024 bytes/s)

// 比特相关：使用 1000 进制（十进制，网络标准）
human.BitSpeed(1000)    // "1 Kbps" (1000 bits/s)
```

### 2. 时间精度限制

相对时间格式化基于 `time.Now()`，在高频调用场景下可能性能较差。建议缓存结果或使用批处理。

### 3. 单复数处理

只有英文等部分语言需要处理单复数，中文、日文等语言不需要：

```go
// 英文：自动处理单复数
human.Duration(1*time.Second, human.WithLocale("en"))  // "1 second"
human.Duration(2*time.Second, human.WithLocale("en"))  // "2 seconds"

// 中文：无需复数
human.Duration(1*time.Second, human.WithLocale("zh"))  // "1秒"
human.Duration(2*time.Second, human.WithLocale("zh"))  // "2秒"
```

### 4. 向后兼容性

旧版本的 `Options` 结构体仍然支持，但推荐使用新的 `Option` 函数模式以获得更好的类型安全性和可扩展性。

---

## 完整示例

```go
package main

import (
    "fmt"
    "time"
    "github.com/lazygophers/utils/human"
)

func main() {
    // 1. 字节大小格式化
    fmt.Println("=== 字节大小 ===")
    sizes := []int64{0, 1, 1024, 1536, 1048576, 1073741824}
    for _, size := range sizes {
        fmt.Printf("%12d -> %s\n", size, human.ByteSize(size))
    }

    // 2. 网络速度格式化
    fmt.Println("\n=== 网络速度 ===")
    fmt.Printf("字节速度: %s\n", human.Speed(1048576))
    fmt.Printf("比特速度: %s\n", human.BitSpeed(1000000))

    // 3. 时间间隔格式化
    fmt.Println("\n=== 时间间隔 ===")
    durations := []time.Duration{
        0,
        time.Second,
        90 * time.Second,
        time.Hour,
        25 * time.Hour,
    }
    for _, d := range durations {
        fmt.Printf("%12v -> %s (时钟: %s)\n",
            d,
            human.Duration(d),
            human.ClockDuration(d),
        )
    }

    // 4. 相对时间格式化
    fmt.Println("\n=== 相对时间 ===")
    now := time.Now()
    times := []time.Time{
        now.Add(-5 * time.Second),
        now.Add(-2 * time.Hour),
        now.Add(-3 * 24 * time.Hour),
        now.Add(5 * time.Minute),
    }
    for _, t := range times {
        fmt.Printf("%s -> %s\n", t.Format("15:04:05"), human.RelativeTime(t))
    }

    // 5. 多语言支持
    fmt.Println("\n=== 多语言 ===")
    d := 90 * time.Minute
    locales := []string{"en", "zh", "ja", "ko", "es"}
    for _, loc := range locales {
        fmt.Printf("%5s: %s\n", loc, human.Duration(d, human.WithLocale(loc)))
    }

    // 6. 选项组合
    fmt.Println("\n=== 选项组合 ===")
    fmt.Printf("默认:     %s\n", human.ByteSize(1536))
    fmt.Printf("精度2:    %s\n", human.ByteSize(1536, human.WithPrecision(2)))
    fmt.Printf("紧凑:     %s\n", human.ByteSize(1536, human.WithCompact()))
    fmt.Printf("组合:     %s\n",
        human.ByteSize(1536,
            human.WithPrecision(2),
            human.WithCompact(),
        ),
    )
}
```

**输出示例:**
```
=== 字节大小 ===
           0 -> 0 B
           1 -> 1 B
        1024 -> 1 KB
        1536 -> 1.5 KB
     1048576 -> 1 MB
  1073741824 -> 1 GB

=== 网络速度 ===
字节速度: 1 MB/s
比特速度: 1 Mbps

=== 时间间隔 ===
           0s -> 0 second (时钟: 0:00)
           1s -> 1 second (时钟: 0:01)
      1m30s -> 1 minute 30 seconds (时钟: 1:30)
           1h0m0s -> 1 hour (时钟: 1:00)
      25h0m0s -> 1 day 1 hour (时钟: 25:00)

=== 相对时间 ===
12:35:43 -> just now
10:35:48 -> 2 hours ago
12:35:48 -> 3 days ago
12:35:48 -> in 5 minutes

=== 多语言 ===
    en: 1 hour 30 minutes
    zh: 1小时 30分钟
    ja: 1時間 30分
    ko: 1시간 30분
    es: 1 hora 30 minutos

=== 选项组合 ===
默认:     1.5 KB
精度2:    1.50 KB
紧凑:     1.5KB
组合:     1.50KB
```

---

## API 参考

### 导出函数

| 函数 | 说明 | 返回值 |
|------|------|--------|
| `ByteSize(bytes int64, opts ...Option) string` | 格式化字节大小 | 格式化字符串 |
| `Speed(bytesPerSecond int64, opts ...Option) string` | 格式化字节速度 | 格式化字符串 |
| `BitSpeed(bitsPerSecond int64, opts ...Option) string` | 格式化比特速度 | 格式化字符串 |
| `Duration(d time.Duration, opts ...Option) string` | 格式化时间间隔 | 格式化字符串 |
| `RelativeTime(t time.Time, opts ...Option) string` | 格式化相对时间 | 格式化字符串 |
| `ClockDuration(d time.Duration) string` | 时钟格式时间间隔 | 格式化字符串 |

### 全局设置

| 函数 | 说明 |
|------|------|
| `SetLocale(locale string)` | 设置默认语言环境 |
| `GetLocale() string` | 获取当前语言环境 |
| `SetDefaultPrecision(precision int)` | 设置默认精度 |

### 选项函数

| 函数 | 说明 |
|------|------|
| `WithPrecision(precision int) Option` | 设置小数精度 |
| `WithLocale(locale string) Option` | 设置语言环境 |
| `WithCompact() Option` | 启用紧凑模式 |
| `WithClockFormat() Option` | 启用时钟格式 |

### 向后兼容函数

| 函数 | 说明 |
|------|------|
| `ByteSizeWithOptions(bytes int64, opts Options) string` | 使用 Options 结构体格式化字节大小 |
| `SpeedWithOptions(bytesPerSecond int64, opts Options) string` | 使用 Options 结构体格式化字节速度 |
| `BitSpeedWithOptions(bitsPerSecond int64, opts Options) string` | 使用 Options 结构体格式化比特速度 |
| `DurationWithOptions(d time.Duration, opts Options) string` | 使用 Options 结构体格式化时间间隔 |

---

## 总结

`human` 模块提供了完整的人类友好格式化解决方案，主要优势：

1. **全面的功能覆盖** - 字节、速度、时间等多种数据类型
2. **优秀的多语言支持** - 内置 8+ 种语言，可扩展
3. **灵活的选项系统** - 支持精度、语言、格式等多种选项
4. **高性能** - 基准测试显示良好的性能表现
5. **易于使用** - 简洁的 API 设计，开箱即用

适用场景：文件管理工具、网络监控、日志系统、时间追踪应用、多语言 UI、视频播放器等任何需要将计算机数据转换为人类可读格式的应用。

---

**参考资源:**
- GitHub: https://github.com/lazygophers/utils/tree/master/human
- GoDoc: https://pkg.go.dev/github.com/lazygophers/utils/human
