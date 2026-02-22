---
name: linq
description: C# LINQ 规范：查询语法、方法语法、集合操作。使用 LINQ 时必须加载。
---

# C# LINQ 规范

## 相关 Skills

| 场景     | Skill        | 说明                        |
| -------- | ------------ | --------------------------- |
| 核心规范 | Skills(core) | C# 12/.NET 8 标准、强制约定 |

## 方法语法

```csharp
var activeUsers = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.Name)
    .Select(u => new { u.Id, u.Name })
    .ToList();
```

## 查询语法

```csharp
var results = from order in orders
             join customer in customers on order.CustomerId equals customer.Id
             where order.Total > 1000
             group order by customer.Country into g
             select new { Country = g.Key, Total = g.Sum(o => o.Total) };
```

## 避免多次枚举

```csharp
// ✅ 避免多次枚举
var filtered = items.Where(x => x.IsValid).ToList();

// ❌ 多次枚举
var filtered = items.Where(x => x.IsValid);
var count = filtered.Count();
var first = filtered.First();
```

## 索引和分块

```csharp
// 使用索引
var items = source.Where((x, i) => i % 2 == 0);

// 使用 Chunk
var chunks = items.Chunk(100);
foreach (var chunk in chunks)
{
    ProcessBatch(chunk);
}
```

## 常用操作

```csharp
// 过滤
var active = users.Where(u => u.IsActive);

// 投影
var names = users.Select(u => u.Name);

// 排序
var sorted = users.OrderBy(u => u.Name).ThenBy(u => u.Age);

// 分组
var groups = users.GroupBy(u => u.Department);

// 聚合
var count = users.Count();
var sum = orders.Sum(o => o.Total);
var avg = products.Average(p => p.Price);

// 去重
var unique = users.Select(u => u.Department).Distinct();

// 合并
var all = list1.Concat(list2);
var union = list1.Union(list2);

// 集合操作
var except = list1.Except(list2);
var intersect = list1.Intersect(list2);
```

## 检查清单

- [ ] 避免多次枚举（使用 ToList）
- [ ] 无 LINQ 查询中的副作用
- [ ] 使用 Chunk 分批处理
- [ ] 大数据集使用 AsParallel
