---
description: "C# 核心开发规范：C# 14/.NET 10 语言标准、nullable reference types、pattern matching、primary constructors、collection expressions、Roslyn analyzers 静态分析。新建或审查 C# 项目时加载，是所有 C# 技能的基础依赖。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C# 核心规范

## 适用 Agents

- **csharp:dev** - 开发阶段使用
- **csharp:debug** - 调试时遵守
- **csharp:test** - 测试代码规范
- **csharp:perf** - 性能优化时保持规范

## 相关 Skills

- **Skills(csharp:async)** - 异步编程：async/await、Channels
- **Skills(csharp:linq)** - LINQ：查询优化、新操作符
- **Skills(csharp:web)** - Web 开发：ASP.NET Core 10
- **Skills(csharp:desktop)** - 桌面开发：WPF、MAUI
- **Skills(csharp:data)** - 数据访问：EF Core 10

## 核心原则（2025-2026 版本）

### 1. C# 版本要求

- **推荐版本**：C# 14/.NET 10（LTS，支持至 2028-11-10）
- **兼容版本**：C# 12/.NET 8（LTS，支持至 2026-11-10）
- **nullable**：必须启用 `<Nullable>enable</Nullable>`

### 2. C# 12 核心特性

| 特性 | 说明 | 示例 |
|------|------|------|
| Primary constructors | 类/结构体参数化构造 | `public class Service(IRepo repo)` |
| Collection expressions | 统一集合初始化 | `int[] nums = [1, 2, 3];` |
| Inline arrays | 固定大小栈数组 | `[InlineArray(4)] struct Buffer { int _e; }` |
| Alias any type | using 别名任何类型 | `using Point = (int X, int Y);` |
| Lambda defaults | Lambda 默认参数 | `var add = (int x, int y = 1) => x + y;` |
| Interceptors | 编译时方法替换 | source generator 场景 |

### 3. C# 13 稳定特性（.NET 9）

| 特性 | 说明 | 示例 |
|------|------|------|
| params collections | params 支持任何集合 | `void Log(params ReadOnlySpan<string> msgs)` |
| Lock object | 新的 Lock 类型 | `private readonly Lock _lock = new();` |
| ref struct interfaces | ref struct 实现接口 | `ref struct MySpan : IEnumerable<T>` |
| \e escape | ESCAPE 字符字面量 | `char esc = '\e';` |
| Partial properties | 部分属性和索引器 | `public partial string Name { get; set; }` |

### 3b. C# 14 新特性（.NET 10）

| 特性 | 说明 | 示例 |
|------|------|------|
| field keyword | 访问自动属性后备字段 | `get => field; set => field = value?.Trim() ?? "";` |
| Extension blocks | 扩展方法和属性 | `extension StringExt for string { ... }` |
| Numeric string comparison | 数值字符串排序 | `StringComparer.Numeric` |
| Partial constructors | 部分构造函数 | `public partial MyClass(int x);` |

### 4. 必须遵守

1. **现代优先** - 优先使用 C# 14/.NET 10 新特性
2. **空安全** - 启用 `<Nullable>enable</Nullable>`
3. **异步优先** - I/O 操作使用 async/await（详见 Skills(csharp:async)）
4. **依赖注入** - 使用 DI 容器管理依赖
5. **资源管理** - using 语句管理 IDisposable/IAsyncDisposable
6. **不可变优先** - record 替代可变 class、init 属性

### 5. 禁止行为

- 使用 .Result 或 .Wait()（死锁风险）
- 禁用 nullable reference types
- 使用 async void（除事件处理）
- 忽略异步方法返回的 Task
- 不传递 CancellationToken
- LINQ 查询中的副作用

## Primary Constructors

```csharp
// ✅ C# 12 primary constructor（DI 场景）
public class UserService(IUserRepository repo, ILogger<UserService> logger)
{
    public async Task<User?> GetAsync(int id, CancellationToken ct = default)
    {
        logger.LogDebug("Getting user {UserId}", id);
        return await repo.FindAsync(id, ct);
    }
}

// ✅ record 类型（DTO/值对象）
public record CreateUserRequest(string Name, string Email, int Age);
public record UserResponse(int Id, string Name, string Email);

// ❌ 传统冗余构造函数
public class UserService
{
    private readonly IUserRepository _repo;
    private readonly ILogger<UserService> _logger;
    public UserService(IUserRepository repo, ILogger<UserService> logger)
    {
        _repo = repo;
        _logger = logger;
    }
}
```

## Collection Expressions

```csharp
// ✅ C# 12 collection expressions
int[] numbers = [1, 2, 3, 4, 5];
List<string> names = ["Alice", "Bob", "Charlie"];
Span<int> span = [1, 2, 3];
ReadOnlySpan<char> vowels = ['a', 'e', 'i', 'o', 'u'];

// ✅ Spread 运算符
int[] first = [1, 2, 3];
int[] second = [4, 5, 6];
int[] all = [..first, ..second];  // [1, 2, 3, 4, 5, 6]

// ❌ 传统初始化
var numbers = new int[] { 1, 2, 3, 4, 5 };
var names = new List<string> { "Alice", "Bob", "Charlie" };
```

## Nullable Reference Types

```csharp
// 项目文件启用
// <Nullable>enable</Nullable>

public class UserService(IUserRepository repo)
{
    // ✅ 明确可空性
    public string Name { get; set; } = "";
    public string? Email { get; set; }

    // ✅ 空条件运算符链
    public string GetDisplayEmail() => Email?.ToLower() ?? "N/A";

    // ✅ null 合并赋值
    public List<User> GetUsers(List<User>? input) => input ??= [];

    // ✅ 模式匹配空检查
    public string Describe(User? user) => user switch
    {
        { Name: var name, Email: not null } => $"{name} ({user.Email})",
        { Name: var name } => name,
        null => "Unknown"
    };
}
```

## 依赖注入

```csharp
// ✅ .NET 10 Keyed Services
builder.Services.AddKeyedScoped<ICache, RedisCache>("redis");
builder.Services.AddKeyedScoped<ICache, MemoryCache>("memory");

public class UserService([FromKeyedServices("redis")] ICache cache) { }

// ✅ IOptions 模式
builder.Services.Configure<SmtpSettings>(builder.Configuration.GetSection("Smtp"));

public class EmailService(IOptions<SmtpSettings> options)
{
    private readonly SmtpSettings _settings = options.Value;
}
```

## 工具链标准（2025-2026）

```xml
<!-- .csproj 推荐配置 -->
<PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
</PropertyGroup>

<ItemGroup>
    <!-- Roslyn analyzers -->
    <PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="8.*" />
    <PackageReference Include="SonarAnalyzer.CSharp" Version="9.*" />
    <PackageReference Include="StyleCop.Analyzers" Version="1.2.*" />
</ItemGroup>
```

```bash
# 格式化代码
dotnet format

# 运行 analyzers
dotnet build /p:TreatWarningsAsErrors=true
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "传统构造函数可读性更好" | ✅ 简单 DI 类是否用 primary constructors？ |
| "new List 已经够简洁" | ✅ 是否用 collection expressions？ |
| "不启用 nullable 更方便" | ✅ 是否启用 `<Nullable>enable</Nullable>`？ |
| "class 比 record 灵活" | ✅ DTO/值对象是否用 record？ |
| "不需要 analyzers" | ✅ 是否配置 Roslyn + SonarAnalyzer？ |
| "手动格式化就行" | ✅ 是否运行 dotnet format？ |

## 检查清单

### C# 12 特性
- [ ] 使用 primary constructors（DI 场景）
- [ ] 使用 collection expressions `[1, 2, 3]`
- [ ] 使用 alias any type 简化复杂类型
- [ ] 使用 record 定义 DTO/值对象

### 空安全
- [ ] 启用 `<Nullable>enable</Nullable>`
- [ ] 所有 API 明确可空性标注
- [ ] 使用 `?.`、`??`、`??=` 运算符
- [ ] 无 null suppression (`!`) 滥用

### 工具链
- [ ] Roslyn analyzers 配置并无警告
- [ ] SonarAnalyzer 配置
- [ ] .editorconfig 规范代码风格
- [ ] `dotnet format` 格式化
- [ ] `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`
