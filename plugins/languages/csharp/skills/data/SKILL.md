---
description: C# 数据访问规范 - EF Core 8 compiled queries、JSON columns、complex types、bulk operations、interceptors。访问数据库时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C# 数据访问规范

## 适用 Agents

- **csharp:dev** - 数据层开发
- **csharp:perf** - 查询性能优化
- **csharp:test** - 数据层集成测试（TestContainers）

## 相关 Skills

- **Skills(csharp:core)** - 核心规范：C# 12/.NET 8 标准
- **Skills(csharp:async)** - 异步编程：异步查询模式
- **Skills(csharp:linq)** - LINQ：查询优化、EF Core translation

## DbContext 配置（EF Core 8）

```csharp
public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Fluent API 配置
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(x => x.Id);
            entity.Property(x => x.Email).IsRequired().HasMaxLength(256);
            entity.HasIndex(x => x.Email).IsUnique();
            entity.HasQueryFilter(x => !x.IsDeleted);  // 全局过滤（软删除）
        });

        // EF Core 8: JSON column
        modelBuilder.Entity<User>()
            .OwnsOne(u => u.Address, b => b.ToJson());

        // EF Core 8: Complex type（值对象）
        modelBuilder.Entity<Order>()
            .ComplexProperty(o => o.ShippingAddress);

        // 自动应用所有 IEntityTypeConfiguration
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
}
```

## Compiled Queries（热路径）

```csharp
// ✅ 预编译查询 - 避免每次重新编译表达式树
public class UserRepository(AppDbContext context)
{
    // 静态编译查询
    private static readonly Func<AppDbContext, int, CancellationToken, Task<User?>>
        GetByIdQuery = EF.CompileAsyncQuery(
            (AppDbContext db, int id, CancellationToken ct) =>
                db.Users.AsNoTracking().FirstOrDefault(u => u.Id == id));

    private static readonly Func<AppDbContext, string, CancellationToken, Task<User?>>
        GetByEmailQuery = EF.CompileAsyncQuery(
            (AppDbContext db, string email, CancellationToken ct) =>
                db.Users.AsNoTracking().FirstOrDefault(u => u.Email == email));

    public Task<User?> FindAsync(int id, CancellationToken ct = default)
        => GetByIdQuery(context, id, ct);

    public Task<User?> FindByEmailAsync(string email, CancellationToken ct = default)
        => GetByEmailQuery(context, email, ct);
}
```

## 批量操作（EF Core 7+）

```csharp
// ✅ ExecuteUpdate - 批量更新（不加载实体）
await context.Users
    .Where(u => u.IsActive && u.LastLogin < DateTime.UtcNow.AddYears(-1))
    .ExecuteUpdateAsync(s => s
        .SetProperty(u => u.IsActive, false)
        .SetProperty(u => u.DeactivatedAt, DateTime.UtcNow),
    ct);

// ✅ ExecuteDelete - 批量删除
await context.Users
    .Where(u => !u.IsActive && u.DeactivatedAt < DateTime.UtcNow.AddYears(-2))
    .ExecuteDeleteAsync(ct);

// ✅ 批量插入（EF Core 8 优化）
var users = Enumerable.Range(0, 1000)
    .Select(i => new User { Name = $"User_{i}", Email = $"user{i}@example.com" })
    .ToList();
context.Users.AddRange(users);
await context.SaveChangesAsync(ct);
```

## JSON Columns（EF Core 8）

```csharp
// ✅ 实体定义
public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public Address Address { get; set; } = new();
    public List<PhoneNumber> PhoneNumbers { get; set; } = [];
}

public record Address(string Street, string City, string ZipCode);
public record PhoneNumber(string Type, string Number);

// ✅ 查询 JSON 列内字段
var usersInBeijing = await context.Users
    .Where(u => u.Address.City == "Beijing")
    .ToListAsync(ct);

// ✅ 查询 JSON 数组
var usersWithMobile = await context.Users
    .Where(u => u.PhoneNumbers.Any(p => p.Type == "Mobile"))
    .ToListAsync(ct);
```

## 查询优化

```csharp
// ✅ AsNoTracking（只读查询）
var users = await context.Users
    .AsNoTracking()
    .Where(u => u.IsActive)
    .ToListAsync(ct);

// ✅ Projection 减少数据传输
var userDtos = await context.Users
    .Where(u => u.IsActive)
    .Select(u => new UserDto(u.Id, u.Name, u.Email))
    .ToListAsync(ct);

// ✅ Include + AsSplitQuery 避免笛卡尔积
var usersWithOrders = await context.Users
    .Include(u => u.Orders)
        .ThenInclude(o => o.Items)
    .AsSplitQuery()
    .ToListAsync(ct);

// ✅ 分页查询
var page = await context.Users
    .OrderBy(u => u.Id)
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize)
    .ToListAsync(ct);
```

## 事务管理

```csharp
// ✅ 显式事务
public async Task TransferAsync(int fromId, int toId, decimal amount, CancellationToken ct)
{
    var strategy = context.Database.CreateExecutionStrategy();
    await strategy.ExecuteAsync(async () =>
    {
        await using var transaction = await context.Database.BeginTransactionAsync(ct);
        try
        {
            var from = await context.Accounts.FindAsync([fromId], ct)
                ?? throw new NotFoundException($"Account {fromId} not found");
            var to = await context.Accounts.FindAsync([toId], ct)
                ?? throw new NotFoundException($"Account {toId} not found");

            from.Balance -= amount;
            to.Balance += amount;

            await context.SaveChangesAsync(ct);
            await transaction.CommitAsync(ct);
        }
        catch
        {
            await transaction.RollbackAsync(ct);
            throw;
        }
    });
}
```

## Interceptors（EF Core 8）

```csharp
// ✅ 自动设置审计字段
public class AuditInterceptor : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData eventData,
        InterceptionResult<int> result,
        CancellationToken ct = default)
    {
        var context = eventData.Context!;
        foreach (var entry in context.ChangeTracker.Entries<IAuditable>())
        {
            if (entry.State == EntityState.Added)
            {
                entry.Entity.CreatedAt = DateTime.UtcNow;
            }
            entry.Entity.UpdatedAt = DateTime.UtcNow;
        }
        return base.SavingChangesAsync(eventData, result, ct);
    }
}

// 注册
builder.Services.AddDbContext<AppDb>((sp, o) =>
    o.UseSqlServer(connectionString)
     .AddInterceptors(new AuditInterceptor()));
```

## Migrations 最佳实践

```bash
# 创建迁移
dotnet ef migrations add AddUserAddress --project Infrastructure --startup-project WebApi

# 应用迁移
dotnet ef database update

# 生成 SQL 脚本（生产环境推荐）
dotnet ef migrations script --idempotent --output migration.sql
```

```csharp
// ✅ 程序启动时自动迁移（开发环境）
if (app.Environment.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDb>();
    await db.Database.MigrateAsync();
}
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "EF Core 自动优化" | ✅ 热路径是否用 compiled queries？ |
| "Select * 方便" | ✅ 是否用 projection 只查需要的列？ |
| "Include 一切" | ✅ 多集合 Include 是否用 AsSplitQuery？ |
| "逐条更新没问题" | ✅ 批量操作是否用 ExecuteUpdate/Delete？ |
| "tracking 无所谓" | ✅ 只读查询是否用 AsNoTracking？ |
| "InMemory 测试够用" | ✅ 集成测试是否用 TestContainers？ |
| "JSON 存 string 就行" | ✅ 是否用 EF Core 8 JSON columns？ |
| "手动设置审计字段" | ✅ 是否用 SaveChanges interceptor？ |

## 检查清单

- [ ] 只读查询使用 AsNoTracking
- [ ] 使用 projection（Select）减少数据传输
- [ ] 多集合 Include 使用 AsSplitQuery
- [ ] 热路径使用 compiled queries
- [ ] 批量操作使用 ExecuteUpdate/ExecuteDelete
- [ ] 复杂值对象使用 JSON columns 或 complex types
- [ ] 审计字段使用 SaveChanges interceptor
- [ ] 事务使用 ExecutionStrategy 处理重试
- [ ] 迁移使用 idempotent SQL 脚本部署
- [ ] 集成测试使用 TestContainers
