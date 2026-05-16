---
name: csharp-core
description: |
  C# 14 / .NET 10 LTS 核心开发规范。覆盖 nullable reference types、pattern matching、
  primary constructors、collection expressions、params collections、field keyword、
  ref struct interfaces、Roslyn analyzers 与 dotnet-format 配置。
  当用户新建 .NET 项目、审查 C# 代码、配置 csproj、启用 nullable、调整 LangVersion,
  或说 "C# 规范"、"现代 C#"、"C# 14"、".NET 10"、"nullable"、"primary constructor"、
  "collection expression"、"dotnet format" 时加载, 是所有 C# skill 的基础依赖。
allowed-tools: Read, Grep, Glob, Bash
---

# C# 核心规范

C# 14 + .NET 10 LTS 是当前主线 (LTS 至 2028-11)。任何 C# 文件改动必须先比对本规范。

## 项目基线

新项目 `.csproj` 必须显式声明:

```xml
<PropertyGroup>
  <TargetFramework>net10.0</TargetFramework>
  <LangVersion>14.0</LangVersion>
  <Nullable>enable</Nullable>
  <ImplicitUsings>enable</ImplicitUsings>
  <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  <AnalysisLevel>latest-all</AnalysisLevel>
  <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
</PropertyGroup>
```

仓库根放 `.editorconfig` + `Directory.Build.props`, 统一 LangVersion 与分析等级。

## 文件与命名

- 单文件 ≤ 600 行, 推荐 200~400 行; 超限按职责拆分
- `PascalCase` 类型/方法/属性/常量; `camelCase` 局部变量与参数; 私有字段 `_camelCase`
- 文件名 = 主类型名; 一个 public 类型一个文件
- 异步方法以 `Async` 结尾, 同时暴露 `CancellationToken`
- 文件级 namespace: `namespace Foo;`

## C# 14 必用特性

| 特性 | 用法 | 取代 |
|------|------|------|
| Primary constructors | `public class Svc(IDb db)` | 显式构造器 + 字段赋值 |
| Collection expressions | `int[] x = [1, 2, 3];` | `new int[] {1,2,3}` |
| Spread | `int[] all = [..a, ..b];` | `Concat` + `ToArray` |
| Params collections | `void F(params ReadOnlySpan<int> xs)` | `params int[]` 堆分配 |
| `field` keyword | `get; set => field = value?.Trim();` | 显式 backing field |
| Ref struct interfaces | `ref struct Buf : IDisposable` | 无 |
| Escape `\e` | `"\e[31mred"` | `"\x1b[31mred"` |
| `required` 成员 | `public required string Name { get; init; }` | 构造器强制 |
| Lock 类型 | `private readonly Lock _gate = new();` | `lock(object)` |
| `using` 别名任意类型 | `using Point = (int X, int Y);` | 无 |

## Nullable 强制

- 不允许 `#nullable disable`; 例外需 PR 注释说明
- 公共 API 显式标注 `?`; 内部不靠 `!` (null-forgiving) 兜底
- 不要 catch `NullReferenceException`; 从源头消除
- `ArgumentNullException.ThrowIfNull(x)` 优于手写判空

## Pattern Matching

优先 switch expression + property pattern:

```csharp
public decimal Discount(Customer c) => c switch
{
    { Tier: "vip", Age: > 60 } => 0.3m,
    { Tier: "vip" }            => 0.2m,
    { Orders.Count: > 10 }     => 0.1m,
    _                          => 0m
};
```

## 不可变与值语义

- DTO / 值对象用 `record` / `record struct` + `init`
- `with` 表达式产生副本
- 集合首选 `IReadOnlyList<T>` / `ImmutableArray<T>` 暴露

## 依赖注入

- 构造器注入优先, 避免 service locator
- 单一职责, 类不超过 7 个公开方法
- 不在静态类持有可变状态; 不在静态构造器做 IO
- `IOptions<T>` 管理配置; `ILogger<T>` 结构化日志
- .NET 9+ Keyed Services: `[FromKeyedServices("k")]`

## 异常与错误

- 异常只对**异常情况**抛出; 预期失败用 `bool TryX(out)` / 结果类型
- 不要吞异常 (空 catch / `catch (Exception)` 后无日志)
- 自定义异常继承 `Exception`, 提供三个标准构造器

## Roslyn Analyzers 与格式化

```xml
<PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="10.*" />
<PackageReference Include="Roslynator.Analyzers" Version="4.*" PrivateAssets="all" />
<PackageReference Include="StyleCop.Analyzers" Version="1.2.*" PrivateAssets="all" />
```

CI 强制:

```bash
dotnet format --verify-no-changes --severity warn
dotnet build /warnaserror
```

## AOT 友好

- 库标注 `<IsAotCompatible>true</IsAotCompatible>`
- 避免 `Activator.CreateInstance(string)` 反射构造泛型; 用 source generator
- 序列化用 `System.Text.Json` source generator (`JsonSerializerContext`)

## 禁止行为

- `.Result` / `.Wait()` (详见 csharp-async)
- `async void` 除 event handler 外一律禁止
- 公共可变静态字段
- 魔法字符串 / 魔法数字; 用常量或枚举
- 反射代替已知类型的强类型代码
- 手动实现 `INotifyPropertyChanged` 模板 (用 CommunityToolkit.Mvvm)

## 参考

- [C# 14 新特性](https://learn.microsoft.com/dotnet/csharp/whats-new/csharp-14)
- [.NET 10 公告](https://devblogs.microsoft.com/dotnet/announcing-dotnet-10/)
- [Roslyn analyzers](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/overview)
- [dotnet/runtime](https://github.com/dotnet/runtime)
- [dotnet format](https://learn.microsoft.com/dotnet/core/tools/dotnet-format)
