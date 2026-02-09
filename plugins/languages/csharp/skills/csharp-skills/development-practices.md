# C# 开发实践

## 异步编程 (async/await)

### 基本模式

```csharp
// ✅ 正确的 async/await 使用
public async Task<User?> GetUserAsync(int id, CancellationToken ct = default)
{
    return await _context.Users
        .AsNoTracking()
        .FirstOrDefaultAsync(u => u.Id == id, ct);
}

// ✅ CancellationToken 传递
public async Task ProcessAsync(CancellationToken ct = default)
{
    await foreach (var item in _repository.GetItemsAsync(ct).WithCancellation(ct))
    {
        await ProcessItemAsync(item, ct);
    }
}

// ✅ ValueTask 避免分配
public ValueTask<int> GetValueAsync()
{
    return _cachedValue.HasValue
        ? new(_cachedValue.Value)
        : new(LoadValueAsync());
}
```

### 异步反模式

```csharp
// ❌ 使用 .Result 导致死锁
var result = SomeAsync().Result;

// ❌ 使用 .Wait() 导致死锁
SomeAsync().Wait();

// ❌ 不传递 CancellationToken
public async Task ProcessAsync()
{
    // 无法取消的操作
}

// ✅ 正确方式
public async Task ProcessAsync(CancellationToken ct = default)
{
    await SomeAsync(ct);
}
```

## LINQ

### 方法语法

```csharp
// ✅ 链式调用
var activeUsers = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.Name)
    .Select(u => new { u.Id, u.Name })
    .ToList();

// ✅ 复杂查询
var results = from order in orders
             join customer in customers on order.CustomerId equals customer.Id
             where order.Total > 1000
             group order by customer.Country into g
             select new { Country = g.Key, Total = g.Sum(o => o.Total) };
```

### LINQ 最佳实践

```csharp
// ✅ 避免多次枚举
var filtered = items.Where(x => x.IsValid).ToList();

// ❌ 多次枚举
var filtered = items.Where(x => x.IsValid);
var count = filtered.Count();
var first = filtered.First();

// ✅ 使用索引（C# 9+）
var items = source.Where((x, i) => i % 2 == 0);

// ✅ 使用 Chunk（.NET 6）
var chunks = items.Chunk(100);
foreach (var chunk in chunks)
{
    ProcessBatch(chunk);
}
```

## 空安全

### 可空引用类型

```csharp
// ✅ 启用可空引用类型
#nullable enable

public class UserService
{
    // 不可为空
    public string Name { get; set; }

    // 可为空
    public string? Email { get; set; }

    // 数组不可为空
    public User[] Users { get; set; } = Array.Empty<User>();

    public string GetDisplayName()
    {
        // Name 不可为空，不需要检查
        return Name;
    }

    public string? GetEmail()
    {
        // Email 可能为空
        return Email?.ToLower();
    }
}
```

### 空合并运算符

```csharp
// ✅ 空合并运算符
string name = user?.Name ?? "Unknown";
int age = user?.Age ?? 0;

// ✅ 空合并赋值
users ??= new List<User>();

// ✅ 条件 null 运算符
int? length = text?.Length;
```

## 依赖注入

### 服务注册

```csharp
// ✅ 正确的服务生命周期
public static IServiceCollection AddServices(this IServiceCollection services)
{
    // 瞬态：轻量无状态服务
    services.AddTransient<IValidator, Validator>();

    // 作用域：每个请求一个实例
    services.AddScoped<IUserRepository, UserRepository>();
    services.AddScoped<IUserService, UserService>();

    // 单例：全局唯一实例
    services.AddSingleton<ICacheService, CacheService>();

    return services;
}
```

### 构造函数注入

```csharp
// ✅ 使用主构造函数（C# 12）
public class UserService(IUserRepository repository, ILogger<UserService> logger)
{
    public async Task<User?> GetUserAsync(int id)
    {
        logger.LogInformation("Getting user {UserId}", id);
        return await repository.FindAsync(id);
    }
}
```

## 资源管理

### using 声明

```csharp
// ✅ using 声明（自动释放）
public async Task ProcessAsync(string path)
{
    using var stream = File.OpenRead(path);
    using var reader = new StreamReader(stream);

    return await reader.ReadToEndAsync();
} // 自动释放

// ✅ 传统 using 语句
public async Task ProcessAsync(string path)
{
    using (var stream = File.OpenRead(path))
    using (var reader = new StreamReader(stream))
    {
        return await reader.ReadToEndAsync();
    }
}
```

## 异常处理

### 标准模式

```csharp
// ✅ 正确的异常处理
public async Task<Result> ProcessAsync(Input input, CancellationToken ct = default)
{
    try
    {
        // 验证输入
        if (input == null)
            throw new ArgumentNullException(nameof(input));

        // 处理逻辑
        var result = await _service.ProcessAsync(input, ct);

        return Result.Success(result);
    }
    catch (OperationCanceledException)
    {
        _logger.LogInformation("Operation cancelled");
        throw;
    }
    catch (Exception ex)
    {
        _logger.LogError(ex, "Processing failed for input {InputId}", input.Id);
        return Result.Failure(ex.Message);
    }
}
```

---

**最后更新**：2026-02-09
