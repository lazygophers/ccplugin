---
name: csharp-data
description: |
  C# 数据访问与 ORM 规范。覆盖 EF Core 10 compiled queries、JSON columns、
  complex types、bulk operations (ExecuteUpdate / ExecuteDelete)、SaveChanges
  interceptors、迁移策略、连接池、TestContainers 集成测试、Dapper micro-ORM 选型、
  EF Core 10 Vector / Native AOT。当访问数据库、设计数据模型、调优查询性能、
  写迁移脚本、配置 DbContext, 或说 "EF Core"、"Entity Framework"、"DbContext"、
  "migration"、"Dapper"、"Npgsql"、"SqlServer"、"compiled query" 时加载。
allowed-tools: Read, Grep, Glob, Bash
---

# C# 数据访问规范

EF Core 10 为主线; 高频热点 + 复杂报表用 Dapper。

## DbContext 配置

```csharp
public class AppDb(DbContextOptions<AppDb> opts) : DbContext(opts)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<Customer> Customers => Set<Customer>();

    protected override void OnModelCreating(ModelBuilder b)
    {
        b.ApplyConfigurationsFromAssembly(typeof(AppDb).Assembly);
    }
}

// Program.cs
builder.Services.AddDbContextPool<AppDb>(o => o
    .UseNpgsql(conn, npg => npg.EnableRetryOnFailure())
    .EnableSensitiveDataLogging(env.IsDevelopment())
    .ConfigureWarnings(w => w.Throw(RelationalEventId.MultipleCollectionIncludeWarning)));
```

- `AddDbContextPool` 减少分配; ctor 仅接受 `DbContextOptions<T>`
- 每个实体单独 `IEntityTypeConfiguration<T>` 文件, 不塞 `OnModelCreating`
- 启用 retry on failure 处理瞬态错误
- EF Core 10 自动编译模型, 不再需要 `.UseModel()`

## 实体设计

- 不可变 ID 用 `Guid` (UUIDv7) 或 `long` (Snowflake); 避免暴露自增整数
- 值对象用 `complex type` (EF Core 8+) 或 owned entity
- 软删除: 全局 query filter `b.HasQueryFilter(e => !e.IsDeleted)`
- 审计字段统一基类 + `SaveChangesInterceptor`

```csharp
public sealed class AuditInterceptor : SaveChangesInterceptor
{
    public override ValueTask<InterceptionResult<int>> SavingChangesAsync(
        DbContextEventData e, InterceptionResult<int> r, CancellationToken ct = default)
    {
        foreach (var entry in e.Context!.ChangeTracker.Entries<IAuditable>())
        {
            if (entry.State == EntityState.Added) entry.Entity.CreatedAt = DateTime.UtcNow;
            if (entry.State == EntityState.Modified) entry.Entity.UpdatedAt = DateTime.UtcNow;
        }
        return base.SavingChangesAsync(e, r, ct);
    }
}
```

## 查询规范

- 读路径 `AsNoTracking()`; 写路径走跟踪
- 投影到 DTO, 不把 entity 直接序列化返回 HTTP
- N+1 检测: 开发期设 `MultipleCollectionIncludeWarning` 为 Throw
- 多集合 Include → `AsSplitQuery()` 避免笛卡尔积
- 大集合避免 `.ToList()` 后内存过滤; 下推到 SQL
- 流式 `AsAsyncEnumerable()` + `await foreach`

```csharp
var dtos = await db.Orders.AsNoTracking()
    .Where(o => o.CustomerId == cid && o.CreatedAt >= since)
    .OrderByDescending(o => o.CreatedAt)
    .Select(o => new OrderListDto(o.Id, o.Amount, o.CreatedAt))
    .ToListAsync(ct);
```

## Compiled Queries

热路径用编译查询消除表达式树编译开销:

```csharp
private static readonly Func<AppDb, long, CancellationToken, Task<Order?>> GetOrderById =
    EF.CompileAsyncQuery((AppDb db, long id, CancellationToken ct) =>
        db.Orders.AsNoTracking().FirstOrDefault(o => o.Id == id));
```

## JSON Columns

EF Core 8+ 内置 JSON 映射, 简化半结构化字段:

```csharp
b.OwnsOne(c => c.Preferences, p => p.ToJson());
b.OwnsMany(c => c.PhoneNumbers, p => p.ToJson());
```

可在 LINQ 中直接查询 JSON 内属性 (Provider 支持时下推为 SQL JSON 操作)。

## EF Core 10 Vector (AI 嵌入)

```csharp
b.Property(d => d.Embedding).HasVector(1536);
var nearest = await db.Documents
    .OrderBy(d => d.Embedding.CosineDistance(query))
    .Take(10).ToListAsync(ct);
```

## 批量操作

```csharp
await db.Orders
    .Where(o => o.Status == OrderStatus.Cancelled && o.UpdatedAt < cutoff)
    .ExecuteDeleteAsync(ct);

await db.Products.Where(p => p.Discontinued)
    .ExecuteUpdateAsync(s => s.SetProperty(p => p.Price, p => p.Price * 0.5m), ct);
```

大量插入用 `EFCore.BulkExtensions` 或直接 `COPY` / `BULK INSERT`。

## 事务

```csharp
var strategy = db.Database.CreateExecutionStrategy();
await strategy.ExecuteAsync(async () =>
{
    await using var tx = await db.Database.BeginTransactionAsync(ct);
    // ...
    await db.SaveChangesAsync(ct);
    await tx.CommitAsync(ct);
});
```

`ExecutionStrategy` 处理 retry 重试; 不要手写循环。

## 迁移

- 一个 PR 一个迁移; 命名 `AddOrderStatusIndex`
- 检入生成的 SQL: `dotnet ef migrations script --idempotent` 给 DBA 评审
- 危险操作 (drop column / rename) 分两步: 先兼容写入新字段, 发布后再删旧
- 启动期自动迁移仅限 Dev:

```csharp
if (env.IsDevelopment())
{
    using var scope = app.Services.CreateScope();
    await scope.ServiceProvider.GetRequiredService<AppDb>().Database.MigrateAsync();
}
```

## 连接管理

- DbContext 是 unit-of-work, scoped 生命周期; 不要在 singleton 注入
- 不要长时间持有 DbContext; 长任务每批新建 scope
- 连接字符串放 `appsettings.json` + User Secrets / Azure Key Vault; 不入 git

## Dapper 何时用

| 用 EF Core | 用 Dapper |
|-----------|-----------|
| CRUD、聚合根 | 复杂报表、多表 join 投影 |
| 跟踪变更 | 只读热路径 |
| 迁移与建表 | 存储过程调用 |

```csharp
const string sql = """
    SELECT o.id, o.amount, c.name AS customer_name
    FROM orders o JOIN customers c ON c.id = o.customer_id
    WHERE o.created_at >= @since
    ORDER BY o.amount DESC LIMIT 100
""";
await using var conn = await dataSource.OpenConnectionAsync(ct);
var rows = await conn.QueryAsync<OrderReport>(
    new CommandDefinition(sql, new { since }, cancellationToken: ct));
```

## 测试

- 集成测试用 TestContainers 启真实 DB; 不要用 InMemory Provider (语义差异)
- `Respawn` 在每个测试前清表
- 共享 `WebApplicationFactory` + per-test transaction rollback 也是常见方案

```csharp
var pg = new PostgreSqlBuilder().WithImage("postgres:17").Build();
await pg.StartAsync();
```

## 参考

- [EF Core 10 新增](https://learn.microsoft.com/ef/core/what-is-new/ef-core-10/whatsnew)
- [EF Core 性能](https://learn.microsoft.com/ef/core/performance/)
- [Bulk operations](https://learn.microsoft.com/ef/core/saving/execute-insert-update-delete)
- [TestContainers .NET](https://dotnet.testcontainers.org/)
- [Npgsql](https://www.npgsql.org/efcore/)
