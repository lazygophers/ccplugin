# 异步编程进阶

## Task vs ValueTask

### 选择指南

```csharp
// ✅ 使用 Task - 大多数情况
public async Task<User> GetUserAsync(int id)
{
    return await _repository.FindAsync(id);
}

// ✅ 使用 ValueTask - 已缓存结果
private int _cachedValue;

public ValueTask<int> GetValueAsync()
{
    return _cachedValue != 0
        ? new(_cachedValue)
        : new(LoadValueAsync());
}
```

## ConfigureAwait

```csharp
// ✅ 库代码：使用 ConfigureAwait(false)
public async Task ProcessAsync()
{
    await _service.DoWorkAsync().ConfigureAwait(false);
    // 继续在线程池线程执行
}

// ✅ 应用代码：不使用 ConfigureAwait
public async Task OnButtonClicked()
{
    await _service.DoWorkAsync();
    // 继续在同步上下文执行（可访问 UI）
}
```

## 并行处理

```csharp
// ✅ 并行执行多个任务
public async Task<Result> ProcessAsync(Input input, CancellationToken ct = default)
{
    var (user, orders, recommendations) = await (
        _userService.GetUserAsync(input.UserId, ct),
        _orderService.GetOrdersAsync(input.UserId, ct),
        _recommendationService.GetRecommendationsAsync(ct)
    );

    return new Result(user, orders, recommendations);
}

// ✅ Task.WhenAll
public async Task ProcessAllAsync(IEnumerable<int> ids, CancellationToken ct = default)
{
    var tasks = ids.Select(id => ProcessAsync(id, ct));
    await Task.WhenAll(tasks);
}

// ✅ Task.WhenAny - 获取第一个完成的
public async Task<Result> GetFirstResultAsync(CancellationToken ct = default)
{
    var tasks = new[] {
        TrySourceAAsync(ct),
        TrySourceBAsync(ct),
        TrySourceCAsync(ct)
    };

    var completed = await Task.WhenAny(tasks);
    return await completed;
}
```

## 异步流

```csharp
// ✅ IAsyncEnumerable 生产
public async IAsyncEnumerable<User> GetUsersAsync(
    [EnumeratorCancellation] CancellationToken ct = default)
{
    var hasMore = true;
    var page = 0;

    while (hasMore && !ct.IsCancellationRequested)
    {
        var users = await _repository.GetPageAsync(page, ct);
        if (!users.Any())
        {
            hasMore = false;
        }
        else
        {
            foreach (var user in users)
            {
                yield return user;
            }
            page++;
        }
    }
}

// ✅ IAsyncEnumerable 消费
await foreach (var user in _service.GetUsersAsync(cancellationToken))
{
    Console.WriteLine(user.Name);
}
```

## 取消令牌

```csharp
// ✅ 传递 CancellationToken
public async Task ProcessAsync(
    string input,
    CancellationToken ct = default)
{
    // 传递给其他异步方法
    var result = await _service.ProcessAsync(input, ct);

    // 传递给延迟操作
    await Task.Delay(1000, ct);

    // 传递给异步流
    await foreach (var item in _service.GetItemsAsync(ct).WithCancellation(ct))
    {
        // 处理
    }
}

// ✅ 链式取消
var linkedCts = CancellationTokenSource.CreateLinkedTokenSource(
    userCancellationToken,
    timeoutToken);

try
{
    await ProcessAsync(linkedCts.Token);
}
finally
{
    linkedCts.Dispose();
}
```

---

**最后更新**：2026-02-09
