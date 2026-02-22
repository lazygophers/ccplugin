---
name: data
description: C# 数据访问规范：Entity Framework Core、DbContext、查询优化。访问数据库时必须加载。
---

# C# 数据访问规范

## 相关 Skills

| 场景     | Skill         | 说明                           |
| -------- | ------------- | ------------------------------ |
| 核心规范 | Skills(core)  | C# 12/.NET 8 标准、强制约定    |
| 异步编程 | Skills(async) | async/await、CancellationToken |

## DbContext 配置

```csharp
public class ApplicationDbContext : DbContext
{
    public DbSet<User> Users { get; set; }
    public DbSet<Order> Orders { get; set; }

    public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
        : base(options)
    {
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(x => x.Id);
            entity.Property(x => x.Email).IsRequired().HasMaxLength(256);
            entity.HasIndex(x => x.Email).IsUnique();
        });

        modelBuilder.Entity<User>()
            .HasQueryFilter(x => !x.IsDeleted);
    }
}
```

## 查询优化

```csharp
// 使用 AsNoTracking（只读）
public async Task<User?> GetUserAsync(int id, CancellationToken ct = default)
{
    return await _context.Users
        .AsNoTracking()
        .FirstOrDefaultAsync(u => u.Id == id, ct);
}

// 使用 Include 预加载
public async Task<User?> GetUserWithOrdersAsync(int id, CancellationToken ct = default)
{
    return await _context.Users
        .Include(u => u.Orders)
        .FirstOrDefaultAsync(u => u.Id == id, ct);
}

// 使用 SplitQuery 避免笛卡尔积
public async Task<List<User>> GetUsersWithOrdersAsync(CancellationToken ct = default)
{
    return await _context.Users
        .Include(u => u.Orders)
        .AsSplitQuery()
        .ToListAsync(ct);
}
```

## 批量操作

```csharp
// 批量更新
await _context.Users
    .Where(u => u.IsActive)
    .ExecuteUpdateAsync(s => s.SetProperty(u => u.LastLogin, DateTime.UtcNow), ct);

// 批量删除
await _context.Users
    .Where(u => !u.IsActive && u.LastLogin < DateTime.UtcNow.AddYears(-1))
    .ExecuteDeleteAsync(ct);
```

## 事务

```csharp
public async Task TransferAsync(int fromId, int toId, decimal amount, CancellationToken ct = default)
{
    await using var transaction = await _context.Database.BeginTransactionAsync(ct);

    try
    {
        var from = await _context.Accounts.FindAsync([fromId], ct);
        var to = await _context.Accounts.FindAsync([toId], ct);

        from.Balance -= amount;
        to.Balance += amount;

        await _context.SaveChangesAsync(ct);
        await transaction.CommitAsync(ct);
    }
    catch
    {
        await transaction.RollbackAsync(ct);
        throw;
    }
}
```

## 检查清单

- [ ] 只读查询使用 AsNoTracking
- [ ] 预加载使用 Include
- [ ] 多集合使用 AsSplitQuery
- [ ] 批量操作使用 ExecuteUpdate/Delete
- [ ] 事务使用 using 声明
