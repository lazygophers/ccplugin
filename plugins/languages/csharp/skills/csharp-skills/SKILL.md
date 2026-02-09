---
name: csharp-skills
description: C# 12/.NET 8 开发规范 - 提供现代 C# 开发标准、最佳实践和代码智能支持。包括 LINQ、async/await、Entity Framework、WPF、MAUI、ASP.NET Core 和 Blazor
---

# C# 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心原则、优先级速览 | 快速入门 |
| [development-practices.md](development-practices.md) | LINQ、async/await、空安全、依赖注入 | 日常开发 |
| [framework-development.md](framework-development.md) | ASP.NET Core、Entity Framework、WPF、MAUI、Blazor | 框架开发 |
| [coding-standards/](coding-standards/) | 详细编码规范 | 代码规范 |
| [specialized/](specialized/) | 异步编程、LINQ、WPF、ASP.NET 开发 | 高级主题 |
| [examples/](examples/) | 可运行代码示例 | 学习参考 |

## 核心原则

C# 是一门现代、类型安全的面向对象语言。本规范定义了高质量、安全、高效的 C# 开发标准。

### ✅ 必须遵守

1. **现代优先** - 优先使用 C# 12/.NET 8 新特性
2. **异步优先** - IO 操作使用 async/await
3. **空安全** - 启用可空引用类型
4. **LINQ 优先** - 使用 LINQ 进行数据操作
5. **依赖注入** - 使用 DI 容器管理依赖
6. **异常安全** - 规范的异常处理
7. **资源管理** - using 语句管理资源

### ❌ 禁止行为

- 使用 .Result 或 .Wait()（导致死锁）
- 不传递 CancellationToken
- 禁用可空引用类型
- 使用 async void（除事件处理）
- LINQ 查询中的副作用
- 不规范地处理异常
- 忽略异步方法返回的 Task

## C# 版本

### C# 12 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| 主构造函数 | 在类/结构上声明参数 | `public record Person(string Name);` |
| 集合表达式 | 简化集合初始化 | `int[] nums = [1, 2, 3];` |
| Lambda 改进 | 默认参数、属性 | `var add = (int x = 0) => x + 1;` |
| 别名任意类型 | using 别名任何类型 | `using IntArray = int[];` |
| 内联数组 | 高效固定大小数组 | `inline int Buffer[16];` |

### .NET 8 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| Primary Constructor | 记录和类的简化构造 | `public record Person(string Name);` |
| Random Shared | 改进的随机数生成 | `Random.Shared.Next(1, 100);` |
| Time Abstraction | 抽象时间提供者 | `ITimeProvider` |
| Span<T> 改进 | 更多 API 支持 | `string.Split(ReadOnlySpan<char>)` |
| MAUI 升级 | 跨平台改进 | .NET MAUI |

## 扩展文档

参见 [development-practices.md](development-practices.md) 了解 LINQ、async/await、空安全和依赖注入最佳实践。

参见 [framework-development.md](framework-development.md) 了解 ASP.NET Core、Entity Framework、WPF、MAUI 和 Blazor 框架开发。

参见 [coding-standards/](coding-standards/) 目录了解详细的编码规范。

参见 [specialized/](specialized/) 目录了解异步编程、LINQ 高级用法和框架特定开发。

---

**规范版本**：1.0
**最后更新**：2026-02-09
