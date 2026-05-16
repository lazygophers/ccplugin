---
name: csharp-linq
description: |
  C# LINQ 查询与集合操作规范。覆盖 .NET 10 新操作符 (CountBy/AggregateBy/Index)、
  方法链 vs 查询语法、延迟执行陷阱、EF Core 查询转换、Span<T> 高性能替代、
  ToList/ToArray 时机、可枚举二次遍历、HashSet/DistinctBy。当编写数据查询、
  集合处理、序列操作、优化 LINQ 性能, 或说 "LINQ"、"Where Select"、"GroupBy"、
  "查询性能"、"IEnumerable"、"PLINQ"、"DistinctBy" 时加载。
allowed-tools: Read, Grep, Glob, Bash
---

# C# LINQ 规范

LINQ 让代码声明式, 但用错会带来性能与正确性陷阱。

## 风格

- 方法语法优先; 链长 ≥3 时每个操作单独一行
- 简单单一 `Where` 可写在一行
- 不混用查询语法与方法语法
- 范围变量名有意义, 业务集合用 `user`、`order`, 避免单字母 `x`
- 复杂 join + group 用查询语法更清晰

```csharp
var top = orders
    .Where(o => o.Status == OrderStatus.Paid)
    .GroupBy(o => o.CustomerId)
    .Select(g => new { CustomerId = g.Key, Total = g.Sum(o => o.Amount) })
    .OrderByDescending(x => x.Total)
    .Take(10)
    .ToList();
```

## 延迟执行陷阱

- LINQ 链是惰性的; 二次遍历 = 重复执行
- 多次使用 → 立即物化为 `List<T>` / `T[]`
- 不要在 LINQ 链中触发副作用 (IO、日志、状态变更)
- `TryGetNonEnumeratedCount(out var n)` 判数量不强求枚举

```csharp
// ❌ 每次遍历都重新查 DB
var q = db.Users.Where(u => u.Active);
foreach (var u in q) Log(u);
foreach (var u in q) Save(u);

// ✅
var users = await db.Users.Where(u => u.Active).ToListAsync(ct);
```

## .NET 10 新操作符

| 操作符 | 取代 |
|--------|------|
| `CountBy(keySelector)` | `GroupBy(...).Select(g => new { g.Key, Count = g.Count() })` |
| `AggregateBy(key, seed, agg)` | 手写 GroupBy + Aggregate |
| `Index()` | `Select((item, i) => (i, item))` |
| `Chunk(n)` | 手写批分 |
| `DistinctBy(k)` / `UnionBy` / `ExceptBy` / `IntersectBy` | 自定义 `IEqualityComparer` |
| `MinBy` / `MaxBy` | `OrderBy(k).First()` |

```csharp
var hotTags = posts.CountBy(p => p.Tag).OrderByDescending(kv => kv.Value).Take(5);
```

## 性能要点

- `Any()` 优于 `Count() > 0`
- `Count(predicate)` 优于 `Where(p).Count()`
- `FirstOrDefault(predicate)` 合并谓词
- 已知 `List` 时 `for` 略快, 但优先可读
- 不要在链中段 `ToList`; 只在终点物化
- 大集合 `Contains` 用 `HashSet<T>`, 避免 O(n²)
- 热路径用 `Span<T>` / `ReadOnlySpan<T>` 取代 LINQ on small arrays
- 大数据 CPU 处理用 PLINQ: `.AsParallel().WithDegreeOfParallelism(n)`

```csharp
// 热路径: 单次扫描, 零分配
public int SumPositive(ReadOnlySpan<int> data)
{
    var sum = 0;
    foreach (var x in data) if (x > 0) sum += x;
    return sum;
}
```

## EF Core 查询转换

- 仅服务端可翻译的表达式能下推 SQL; 客户端求值在 EF Core 3+ 默认禁用 (除显式 `AsEnumerable` 后)
- `AsNoTracking()` 读取无需跟踪的数据
- N+1: 用 `Include` / `ThenInclude` / `AsSplitQuery`
- 投影仅需字段: `Select(u => new UserDto(u.Id, u.Name))`
- 大列表用 `AsAsyncEnumerable()` + 流式消费

```csharp
var page = await db.Orders.AsNoTracking()
    .Where(o => o.CustomerId == cid)
    .OrderByDescending(o => o.CreatedAt)
    .Skip(skip).Take(pageSize)
    .Select(o => new OrderListDto(o.Id, o.Amount, o.CreatedAt))
    .ToListAsync(ct);
```

## 异步 LINQ

EF Core: `ToListAsync`/`FirstOrDefaultAsync`/`AnyAsync`/`CountAsync`, 全部接受 `CancellationToken`。
对 `IAsyncEnumerable<T>` 使用 `System.Linq.Async` 提供的异步 LINQ 操作。

## 常见反模式

| 反模式 | 修复 |
|--------|------|
| `list.Count() > 0` | `list.Any()` 或 `list.Count > 0` (ICollection) |
| `list.OrderBy(k).First()` | `list.MinBy(k)` |
| `list.Where(p).Count()` | `list.Count(p)` |
| `list.Select(...).Where(...)` | 调换: 先 Where 后 Select |
| `Distinct()` 自定义对象 | 实现 `IEquatable<T>` 或 `DistinctBy(key)` |
| 链中 `ToList().Where(...)` | 删除中段 `ToList` |
| 大集合 `list.Contains(x)` | `HashSet<T>` |

## 不可变与函数式

- 优先 immutable: `record` / `ImmutableArray<T>`
- LINQ 操作返回新序列; 不要修改源集合
- `with` 表达式产生记录副本

## 参考

- [LINQ 教程](https://learn.microsoft.com/dotnet/csharp/linq/)
- [.NET 10 LINQ 新增](https://learn.microsoft.com/dotnet/core/whats-new/dotnet-10)
- [EF Core 查询转换](https://learn.microsoft.com/ef/core/querying/)
- [System.Linq.Async](https://www.nuget.org/packages/System.Linq.Async)
