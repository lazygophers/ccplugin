---
description: "C# 异步并发编程规范：async/await 最佳实践、IAsyncEnumerable 异步流、System.Threading.Channels 生产者消费者、Parallel.ForEachAsync 并行处理、CancellationToken 取消机制。编写异步代码、排查死锁、优化并发性能时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# C# 异步编程规范

## 适用 Agents

- **csharp:dev** - 异步 API 开发
- **csharp:debug** - 异步死锁排查
- **csharp:test** - 异步测试模式
- **csharp:perf** - 异步性能优化

## 相关 Skills

- **Skills(csharp:core)** - 核心规范：C# 12/.NET 8 标准
- **Skills(csharp:web)** - Web 开发：ASP.NET Core 异步管道
- **Skills(csharp:data)** - 数据访问：EF Core 异步查询

## async/await 基本模式

```csharp
// ✅ 标准异步方法 + CancellationToken
public async Task<User?> GetUserAsync(int id, CancellationToken ct = default)
{
    return await _context.Users
        .AsNoTracking()
        .FirstOrDefaultAsync(u => u.Id == id, ct);
}

// ✅ 多个独立异步操作并行执行
public async Task<(User user, List<Order> orders)> GetDashboardAsync(
    int userId, CancellationToken ct = default)
{
    var userTask = _userRepo.FindAsync(userId, ct);
    var ordersTask = _orderRepo.GetByUserAsync(userId, ct);
    await Task.WhenAll(userTask, ordersTask);
    return (await userTask, await ordersTask);
}
```

## IAsyncEnumerable（流式异步）

```csharp
// ✅ 异步流：逐条产出而非一次性加载
public async IAsyncEnumerable<User> GetActiveUsersAsync(
    [EnumeratorCancellation] CancellationToken ct = default)
{
    await foreach (var user in _context.Users
        .Where(u => u.IsActive)
        .AsAsyncEnumerable()
        .WithCancellation(ct))
    {
        yield return user;
    }
}

// ✅ 消费异步流
await foreach (var user in service.GetActiveUsersAsync(ct))
{
    await ProcessUserAsync(user, ct);
}
```

## System.Threading.Channels（高吞吐管道）

```csharp
// ✅ 生产者-消费者模式
public class DataPipeline(ILogger<DataPipeline> logger)
{
    public async Task RunAsync(CancellationToken ct)
    {
        var channel = Channel.CreateBounded<WorkItem>(new BoundedChannelOptions(100)
        {
            FullMode = BoundedChannelFullMode.Wait,
            SingleReader = false,
            SingleWriter = true
        });

        // 生产者
        var producer = Task.Run(async () =>
        {
            await foreach (var item in GetItemsAsync(ct))
            {
                await channel.Writer.WriteAsync(item, ct);
            }
            channel.Writer.Complete();
        }, ct);

        // 多消费者
        var consumers = Enumerable.Range(0, 4).Select(_ => Task.Run(async () =>
        {
            await foreach (var item in channel.Reader.ReadAllAsync(ct))
            {
                await ProcessAsync(item, ct);
            }
        }, ct));

        await Task.WhenAll(consumers.Append(producer));
    }
}
```

## Parallel.ForEachAsync（并行 I/O）

```csharp
// ✅ 并行批量 I/O 操作
public async Task ProcessAllAsync(IEnumerable<int> ids, CancellationToken ct)
{
    await Parallel.ForEachAsync(ids,
        new ParallelOptions { MaxDegreeOfParallelism = 10, CancellationToken = ct },
        async (id, token) =>
        {
            var data = await _httpClient.GetAsync($"/api/items/{id}", token);
            await ProcessResponseAsync(data, token);
        });
}
```

## ValueTask（减少分配）

```csharp
// ✅ 缓存命中时零分配
public ValueTask<User?> GetUserAsync(int id, CancellationToken ct = default)
{
    if (_cache.TryGetValue(id, out var user))
        return new(user);  // 同步返回，零分配
    return new(LoadUserFromDbAsync(id, ct));
}

// ⚠️ ValueTask 使用规则
// - 不要多次 await 同一个 ValueTask
// - 不要并发 await
// - 仅在高性能场景使用
```

## ConfigureAwait

```csharp
// ✅ 库代码：使用 ConfigureAwait(false)
public async Task<string> GetDataAsync(CancellationToken ct = default)
{
    var data = await _httpClient.GetStringAsync(url, ct).ConfigureAwait(false);
    return ProcessData(data);
}

// ✅ ASP.NET Core 应用代码：不需要 ConfigureAwait
// ASP.NET Core 没有 SynchronizationContext

// ✅ UI 应用（WPF/MAUI）：不使用 ConfigureAwait(false)
public async void OnClick(object sender, EventArgs e)
{
    var data = await GetDataAsync();
    textBox.Text = data;  // 需要 UI 线程上下文
}
```

## 异步反模式

```csharp
// ❌ sync-over-async 死锁
var result = SomeAsync().Result;
SomeAsync().Wait();
SomeAsync().GetAwaiter().GetResult();  // 仅在极少数启动场景可接受

// ❌ async void（无法捕获异常）
public async void DoWork() { }

// ❌ 不传递 CancellationToken
public async Task ProcessAsync() { await _db.QueryAsync(); }

// ❌ 忽略返回的 Task
_ = FireAndForgetAsync();  // 异常会丢失

// ✅ 如果确实需要 fire-and-forget
_ = Task.Run(async () =>
{
    try { await FireAndForgetAsync(ct); }
    catch (Exception ex) { _logger.LogError(ex, "Background task failed"); }
}, ct);
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "同步方法更简单" | ✅ I/O 操作是否使用 async/await？ |
| ".Result 在这里安全" | ✅ 是否存在 sync-over-async？ |
| "不需要 CancellationToken" | ✅ 所有异步方法是否接受并传递 ct？ |
| "Task 够用了" | ✅ 缓存场景是否用 ValueTask？ |
| "一次性加载没问题" | ✅ 大数据集是否用 IAsyncEnumerable？ |
| "用 List 缓冲就行" | ✅ 高吞吐是否用 Channel？ |
| "foreach + await 就行" | ✅ 批量 I/O 是否用 Parallel.ForEachAsync？ |

## 检查清单

- [ ] 所有 I/O 方法使用 async/await
- [ ] 所有异步方法接受 CancellationToken 参数
- [ ] 无 .Result、.Wait()、.GetAwaiter().GetResult()
- [ ] 无 async void（除事件处理）
- [ ] 库代码使用 ConfigureAwait(false)
- [ ] 流式数据使用 IAsyncEnumerable
- [ ] 高吞吐管道使用 Channels
- [ ] 批量并行 I/O 使用 Parallel.ForEachAsync
- [ ] 缓存场景考虑 ValueTask
