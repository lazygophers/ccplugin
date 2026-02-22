---
name: async
description: C# 异步编程规范：async/await、CancellationToken、ValueTask。写异步代码时必须加载。
---

# C# 异步编程规范

## 相关 Skills

| 场景     | Skill        | 说明                        |
| -------- | ------------ | --------------------------- |
| 核心规范 | Skills(core) | C# 12/.NET 8 标准、强制约定 |

## 基本模式

```csharp
public async Task<User?> GetUserAsync(int id, CancellationToken ct = default)
{
    return await _context.Users
        .AsNoTracking()
        .FirstOrDefaultAsync(u => u.Id == id, ct);
}

public async Task ProcessAsync(CancellationToken ct = default)
{
    await foreach (var item in _repository.GetItemsAsync(ct).WithCancellation(ct))
    {
        await ProcessItemAsync(item, ct);
    }
}
```

## ValueTask

```csharp
public ValueTask<int> GetValueAsync()
{
    return _cachedValue.HasValue
        ? new(_cachedValue.Value)
        : new(LoadValueAsync());
}
```

## 异步反模式

```csharp
// ❌ 使用 .Result 导致死锁
var result = SomeAsync().Result;

// ❌ 使用 .Wait() 导致死锁
SomeAsync().Wait();

// ❌ 不传递 CancellationToken
public async Task ProcessAsync()
{
}

// ✅ 正确方式
public async Task ProcessAsync(CancellationToken ct = default)
{
    await SomeAsync(ct);
}
```

## async void

```csharp
// ❌ 禁止（除事件处理）
public async void DoWork()
{
}

// ✅ 事件处理允许
public async void OnClick(object sender, EventArgs e)
{
    await ProcessAsync();
}
```

## ConfigureAwait

```csharp
// 库代码使用 ConfigureAwait(false)
public async Task<string> GetDataAsync()
{
    var data = await _httpClient.GetStringAsync(url).ConfigureAwait(false);
    return data;
}

// UI 应用不使用
public async void OnClick(object sender, EventArgs e)
{
    var data = await GetDataAsync();
    textBox.Text = data;
}
```

## 检查清单

- [ ] 所有异步方法返回 Task/Task<T>/ValueTask
- [ ] 传递 CancellationToken
- [ ] 无 .Result 或 .Wait()
- [ ] 无 async void（除事件）
- [ ] 库代码使用 ConfigureAwait(false)
