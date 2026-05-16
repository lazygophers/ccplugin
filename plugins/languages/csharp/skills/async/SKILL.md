---
name: csharp-async
description: |
  C# 异步并发编程规范。涵盖 async/await、ConfigureAwait、CancellationToken 传播、
  IAsyncEnumerable 异步流、System.Threading.Channels 生产者-消费者、
  Parallel.ForEachAsync 并行处理、ValueTask 优化、TaskCompletionSource、
  死锁与线程池饥饿排查。当编写或审查异步代码、排查 deadlock、调优并发吞吐,
  或说 "async"、"await"、"Task"、"CancellationToken"、"死锁"、"thread pool starvation"、
  "异步流"、"Channels"、"ValueTask" 时加载。
allowed-tools: Read, Grep, Glob, Bash
---

# C# 异步编程规范

异步代码默认按 ASP.NET Core / library 场景; UI 场景在末尾单列。

## 核心红线

| 禁止 | 替代 |
|------|------|
| `task.Result` / `task.Wait()` | `await task` |
| `Task.Run(() => syncIO)` 来"异步化" | 使用真正的异步 API |
| `async void` 非事件处理器 | `async Task` |
| 漏传 `CancellationToken` | 全链路传递, 尊重 `ct.ThrowIfCancellationRequested()` |
| `Thread.Sleep` 在异步方法中 | `await Task.Delay(ts, ct)` |
| 同步上下文同步等异步 (库代码) | 全程异步 |
| `_ = FireAndForgetAsync()` 直接丢弃 | 包装 try/catch + 日志 |

## 方法签名规则

```csharp
public async Task<User> GetUserAsync(int id, CancellationToken ct = default)
{
    return await _db.Users.FirstAsync(u => u.Id == id, ct);
}
```

- 异步方法以 `Async` 后缀命名
- `CancellationToken` 永远是最后一个参数, 提供 `default`
- 库代码返回 `Task` / `ValueTask`; 不要返回 `void`
- 热路径单 await 用 `ValueTask`; 其余用 `Task`

## ConfigureAwait

- 库代码 `await x.ConfigureAwait(false)`, 避免捕获 SynchronizationContext
- ASP.NET Core 应用代码可省略 (无 SynchronizationContext)
- WPF / WinForms / MAUI UI 代码需回 UI 线程时省略; 后台代码用 `false`

## 取消传播

`ct` 必须穿透所有异步调用。组合多源取消:

```csharp
using var cts = CancellationTokenSource.CreateLinkedTokenSource(
    userCt, _appLifetime.ApplicationStopping);
cts.CancelAfter(TimeSpan.FromSeconds(30));
await DoWorkAsync(cts.Token);
```

## 并行独立操作

```csharp
var userTask   = _userRepo.FindAsync(id, ct);
var ordersTask = _orderRepo.GetByUserAsync(id, ct);
await Task.WhenAll(userTask, ordersTask);
return (await userTask, await ordersTask);
```

## IAsyncEnumerable 异步流

数据源是流式时优先使用, 按需消费、自动取消:

```csharp
public async IAsyncEnumerable<Order> StreamOrdersAsync(
    [EnumeratorCancellation] CancellationToken ct = default)
{
    await foreach (var o in _db.Orders.AsAsyncEnumerable().WithCancellation(ct))
        yield return o;
}
```

调用方: `await foreach (var o in svc.StreamOrdersAsync(ct)) { ... }`。

## Channels: 生产者-消费者

```csharp
var ch = Channel.CreateBounded<Job>(new BoundedChannelOptions(100)
{
    FullMode = BoundedChannelFullMode.Wait,
    SingleReader = false,
});
// Producer: await ch.Writer.WriteAsync(job, ct);  完成: ch.Writer.Complete();
// Consumer: await foreach (var j in ch.Reader.ReadAllAsync(ct)) ...
```

Bounded 提供背压; Unbounded 仅用于已知有界场景。

## 并行处理

CPU/IO 混合 → `Parallel.ForEachAsync` 控制并发:

```csharp
await Parallel.ForEachAsync(items,
    new ParallelOptions { MaxDegreeOfParallelism = 8, CancellationToken = ct },
    async (item, token) => await ProcessAsync(item, token));
```

纯 IO 限流 → `Task.WhenAll` + `SemaphoreSlim`:

```csharp
using var gate = new SemaphoreSlim(10);
var tasks = urls.Select(async url =>
{
    await gate.WaitAsync(ct);
    try { return await _http.GetAsync(url, ct); }
    finally { gate.Release(); }
});
var results = await Task.WhenAll(tasks);
```

## ValueTask 注意

- 单次 await, 且大概率同步完成 → `ValueTask`
- 同一个 `ValueTask` 不能 await 多次、不能并发 await
- 不确定就用 `Task`

```csharp
public ValueTask<User?> GetUserAsync(int id, CancellationToken ct = default)
    => _cache.TryGetValue(id, out var u) ? new(u) : new(LoadAsync(id, ct));
```

## 死锁与线程池饥饿

排查思路:

1. `dotnet-counters monitor --counters System.Runtime` 看 ThreadPool Queue Length
2. `dotnet-stack report` 找 sync-over-async 调用
3. 是否存在 `GetAwaiter().GetResult()` / `.Result`? 删除
4. UI 是否在 UI 线程 await 后回弹卡死? 库要 `ConfigureAwait(false)`

## Fire-and-forget

```csharp
_ = Task.Run(async () =>
{
    try { await DoBackgroundAsync(ct); }
    catch (OperationCanceledException) { }
    catch (Exception ex) { _logger.LogError(ex, "background failed"); }
}, ct);
```

## 测试异步代码

- xUnit v3 原生支持 `async Task` 测试
- 用 `FakeTimeProvider` 测试基于时间的异步逻辑, 避免真实 `Task.Delay`
- 死锁回归测试用 `Task.WaitAsync(timeout)` 兜底

## UI 应用例外

- UI 事件处理器允许 `async void`, 内部必须 `try/catch`
- 长任务交后台, 结果通过 `Dispatcher` / `MainThread.BeginInvokeOnMainThread`
- 详见 csharp-desktop

## 参考

- [Async guidance (David Fowler)](https://github.com/davidfowl/AspNetCoreDiagnosticScenarios/blob/master/AsyncGuidance.md)
- [IAsyncEnumerable](https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/generate-consume-asynchronous-stream)
- [System.Threading.Channels](https://learn.microsoft.com/dotnet/core/extensions/channels)
- [Parallel.ForEachAsync](https://learn.microsoft.com/dotnet/api/system.threading.tasks.parallel.foreachasync)
- [ValueTask guide](https://learn.microsoft.com/dotnet/api/system.threading.tasks.valuetask-1)
