# LINQ 高级用法

## 延迟执行

```csharp
// ✅ 理解延迟执行
var query = users.Where(u => u.IsActive);  // 不执行

var count = query.Count();  // 执行
var first = query.First();  // 再次执行

// ✅ 使用 ToList 避免多次执行
var activeUsers = users.Where(u => u.IsActive).ToList();
var count = activeUsers.Count;
var first = activeUsers[0];
```

## 投影和分组

```csharp
// ✅ 匿名类型投影
var summaries = orders
    .GroupBy(o => o.CustomerId)
    .Select(g => new
    {
        CustomerId = g.Key,
        OrderCount = g.Count(),
        TotalAmount = g.Sum(o => o.Amount)
    });

// ✅ 元组返回（C# 7+）
var (topCustomers, others) = customers
    .Select(c => (c, c.Orders.Sum(o => o.Amount)))
    .Partition(tuple => tuple.Item2 > 10000);
```

## 连接

```csharp
// ✅ Join 语法
var results = from order in orders
             join customer in customers
                 on order.CustomerId equals customer.Id
             select new
             {
                 OrderId = order.Id,
                 CustomerName = customer.Name,
                 Amount = order.Amount
             };

// ✅ GroupJoin
var customerOrders = from customer in customers
                    join order in orders
                        on customer.Id equals order.CustomerId into gj
                    select new
                    {
                        Customer = customer,
                        Orders = gj
                    };
```

## 分区

```csharp
// ✅ Chunk (.NET 6)
var batches = items.Chunk(100);
foreach (var batch in batches)
{
    ProcessBatch(batch);
}

// ✅ Skip/Take 分页
var page = query
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize);
```

## 量词

```csharp
// ✅ Any 优于 Count
bool hasActive = users.Any(u => u.IsActive);

// ❌ 避免计数
bool hasActiveBad = users.Count(u => u.IsActive) > 0;

// ✅ Contains
bool isValid = status.ValidValues.Contains(value);

// ✅ All
bool allValid = items.All(i => i.IsValid());
```

---

**最后更新**：2026-02-09
