---
name: linq
description: C# LINQ 规范 - .NET 8 新操作符、性能优化、EF Core query translation、Span 替代方案。使用 LINQ 或集合操作时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C# LINQ 规范

## 适用 Agents

- **csharp:dev** - 数据查询和集合操作
- **csharp:perf** - LINQ 性能优化

## 相关 Skills

- **Skills(csharp:core)** - 核心规范：C# 12 collection expressions
- **Skills(csharp:data)** - 数据访问：EF Core LINQ to SQL translation
- **Skills(csharp:async)** - 异步编程：IAsyncEnumerable

## .NET 8 新操作符

```csharp
// ✅ Index（按索引选择）
var third = items.ElementAt(new Index(2));
var lastTwo = items.TakeLast(2);

// ✅ CountBy（按 key 计数，.NET 9）
var countByDept = employees.CountBy(e => e.Department);

// ✅ AggregateBy（按 key 聚合，.NET 9）
var salaryByDept = employees.AggregateBy(
    e => e.Department,
    0m,
    (sum, e) => sum + e.Salary);

// ✅ Chunk（分批处理）
foreach (var batch in items.Chunk(100))
{
    await ProcessBatchAsync(batch, ct);
}

// ✅ DistinctBy / UnionBy / ExceptBy / IntersectBy
var uniqueByName = users.DistinctBy(u => u.Name);
var merged = list1.UnionBy(list2, x => x.Id);
```

## 方法语法（推荐）

```csharp
// ✅ 链式方法语法
var activeUsers = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.Name)
    .ThenByDescending(u => u.CreatedAt)
    .Select(u => new UserDto(u.Id, u.Name, u.Email))
    .ToList();

// ✅ 使用 projection 避免过度加载
var userNames = _context.Users
    .Where(u => u.IsActive)
    .Select(u => new { u.Id, u.Name })  // 只查询需要的列
    .ToListAsync(ct);
```

## 查询语法（复杂 Join/Group）

```csharp
// ✅ 复杂查询用查询语法更清晰
var report = from order in orders
             join customer in customers on order.CustomerId equals customer.Id
             where order.CreatedAt >= startDate
             group order by new { customer.Country, order.CreatedAt.Year } into g
             select new
             {
                 g.Key.Country,
                 g.Key.Year,
                 TotalRevenue = g.Sum(o => o.Total),
                 OrderCount = g.Count()
             };
```

## 避免多次枚举

```csharp
// ❌ 多次枚举 IEnumerable（每次重新执行查询）
IEnumerable<User> filtered = users.Where(u => u.IsActive);
var count = filtered.Count();      // 枚举 1
var first = filtered.First();      // 枚举 2
var list = filtered.ToList();      // 枚举 3

// ✅ 缓存结果
var filtered = users.Where(u => u.IsActive).ToList();
var count = filtered.Count;        // O(1)
var first = filtered[0];           // O(1)

// ✅ 使用 TryGetNonEnumeratedCount 优化
if (source.TryGetNonEnumeratedCount(out var count))
{
    // 不需要枚举就能获取数量
}
```

## EF Core LINQ Translation

```csharp
// ✅ 可翻译为 SQL 的 LINQ
var users = await _context.Users
    .Where(u => u.IsActive && u.Age > 18)
    .OrderBy(u => u.Name)
    .Select(u => new UserDto(u.Id, u.Name, u.Email))
    .ToListAsync(ct);

// ❌ 不可翻译（导致客户端评估或异常）
var users = await _context.Users
    .Where(u => MyCustomMethod(u.Name))  // 无法翻译！
    .ToListAsync(ct);

// ✅ EF Core 8 JSON 列查询
var users = await _context.Users
    .Where(u => u.Address.City == "Beijing")  // JSON 列内查询
    .ToListAsync(ct);

// ✅ 使用 AsNoTracking 优化只读查询
var users = await _context.Users
    .AsNoTracking()
    .Where(u => u.IsActive)
    .ToListAsync(ct);
```

## 性能优化

```csharp
// ❌ LINQ 在热路径上的性能问题
var sum = numbers.Where(n => n > 0).Sum();  // 委托分配 + 迭代器分配

// ✅ 热路径使用 Span + 手动循环
public static int SumPositive(ReadOnlySpan<int> numbers)
{
    var sum = 0;
    foreach (var n in numbers)
    {
        if (n > 0) sum += n;
    }
    return sum;
}

// ✅ 大数据集使用 PLINQ
var results = largeDataSet
    .AsParallel()
    .WithDegreeOfParallelism(Environment.ProcessorCount)
    .Where(x => x.IsValid)
    .Select(x => Transform(x))
    .ToArray();

// ✅ 使用 HashSet 优化 Contains 查询
var validIds = new HashSet<int>(validIdList);
var filtered = items.Where(x => validIds.Contains(x.Id));

// ❌ List.Contains 在大集合上是 O(n)
var filtered = items.Where(x => validIdList.Contains(x.Id));
```

## IAsyncEnumerable + LINQ

```csharp
// ✅ 异步 LINQ（System.Linq.Async 包）
await foreach (var user in _context.Users
    .Where(u => u.IsActive)
    .AsAsyncEnumerable()
    .Where(u => PassesComplexValidation(u))  // 客户端过滤
    .WithCancellation(ct))
{
    await ProcessAsync(user, ct);
}
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "LINQ 够快了" | ✅ 热路径是否用 Span + 手动循环？ |
| "Select * 没问题" | ✅ 是否用 projection 只查需要的列？ |
| "客户端过滤更灵活" | ✅ Where 条件是否可翻译为 SQL？ |
| "foreach 循环更清晰" | ✅ 简单集合操作是否用 LINQ？ |
| "多次枚举没关系" | ✅ IEnumerable 是否缓存为 List？ |
| "不需要分批" | ✅ 大数据集是否用 Chunk 分批？ |
| "List.Contains 够用" | ✅ 大集合是否用 HashSet.Contains？ |

## 检查清单

- [ ] 避免多次枚举（缓存为 List 或使用 TryGetNonEnumeratedCount）
- [ ] 使用 projection（Select）只查需要的字段
- [ ] LINQ to EF Core 条件可翻译为 SQL
- [ ] 只读查询使用 AsNoTracking
- [ ] 大数据集使用 Chunk 分批处理
- [ ] 热路径考虑 Span + 手动循环替代 LINQ
- [ ] 大集合 Contains 使用 HashSet
- [ ] 无 LINQ 查询中的副作用
- [ ] 使用 .NET 8+ 新操作符（DistinctBy、Chunk 等）
