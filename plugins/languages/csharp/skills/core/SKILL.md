---
name: core
description: C# 开发核心规范：C# 12/.NET 8 标准、强制约定、代码格式。写任何 C# 代码前必须加载。
---

# C# 开发核心规范

## 相关 Skills

| 场景     | Skill           | 说明                           |
| -------- | --------------- | ------------------------------ |
| 异步编程 | Skills(async)   | async/await、CancellationToken |
| 数据查询 | Skills(linq)    | LINQ 查询、集合操作            |
| Web 开发 | Skills(web)     | ASP.NET Core、Blazor           |
| 桌面开发 | Skills(desktop) | WPF、MAUI                      |
| 数据访问 | Skills(data)    | Entity Framework Core          |

## 核心原则

C# 是一门现代、类型安全的面向对象语言。

### 必须遵守

1. **现代优先** - 优先使用 C# 12/.NET 8 新特性
2. **异步优先** - IO 操作使用 async/await
3. **空安全** - 启用可空引用类型
4. **LINQ 优先** - 使用 LINQ 进行数据操作
5. **依赖注入** - 使用 DI 容器管理依赖
6. **资源管理** - using 语句管理资源

### 禁止行为

- 使用 .Result 或 .Wait()（导致死锁）
- 不传递 CancellationToken
- 禁用可空引用类型
- 使用 async void（除事件处理）
- LINQ 查询中的副作用
- 忽略异步方法返回的 Task

## C# 12 核心特性

| 特性         | 说明                | 示例                                 |
| ------------ | ------------------- | ------------------------------------ |
| 主构造函数   | 在类/结构上声明参数 | `public record Person(string Name);` |
| 集合表达式   | 简化集合初始化      | `int[] nums = [1, 2, 3];`            |
| Lambda 改进  | 默认参数、属性      | `var add = (int x = 0) => x + 1;`    |
| 别名任意类型 | using 别名任何类型  | `using IntArray = int[];`            |

## 空安全

```csharp
#nullable enable

public class UserService
{
    public string Name { get; set; }
    public string? Email { get; set; }

    public string GetDisplayName() => Name;
    public string? GetEmail() => Email?.ToLower();
}

string name = user?.Name ?? "Unknown";
users ??= new List<User>();
```

## 依赖注入

```csharp
services.AddTransient<IValidator, Validator>();
services.AddScoped<IUserRepository, UserRepository>();
services.AddSingleton<ICacheService, CacheService>();

public class UserService(IUserRepository repository, ILogger<UserService> logger)
{
}
```

## 资源管理

```csharp
public async Task ProcessAsync(string path)
{
    using var stream = File.OpenRead(path);
    using var reader = new StreamReader(stream);
    return await reader.ReadToEndAsync();
}
```

## 检查清单

- [ ] 使用 C# 12/.NET 8 特性
- [ ] 启用可空引用类型
- [ ] IO 操作使用 async/await
- [ ] 传递 CancellationToken
- [ ] 使用 using 管理资源
- [ ] 无 .Result 或 .Wait()
