# JavaScript 异步编程规范

## 核心原则

### 必须遵守

1. **优先 async/await** - 使用 async/await 而非 Promise 链
2. **错误处理** - 所有异步操作必须有错误处理
3. **超时控制** - 所有 I/O 操作都应该有超时限制
4. **避免阻塞** - 永远不要在异步函数中执行阻塞操作
5. **正确的并发控制** - 限制并发数量，避免资源耗尽

### 禁止行为

- 在 async 函数中使用阻塞操作
- 使用 `async function` 但不等待结果
- 在循环中无限制地创建异步任务
- 忽略 Promise 的异常
- 混用回调和 Promise

## async/await 最佳实践

### 基本用法

```javascript
// ✅ 正确 - 使用 async/await
async function fetchUser(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user:', error);
    throw error;
  }
}

// ❌ 错误 - 不处理错误
async function fetchUser(userId) {
  const response = await fetch(`/api/users/${userId}`);
  return await response.json();
}

// ❌ 错误 - 静默忽略错误
async function fetchUser(userId) {
  try {
    const response = await fetch(`/api/users/${userId}`);
    return await response.json();
  } catch (error) {
    // 静默忽略
  }
}
```

### Promise.allSettled

```javascript
// ✅ 推荐 - 使用 allSettled 处理多个异步操作
async function fetchAllData() {
  const results = await Promise.allSettled([
    fetchUsers(),
    fetchPosts(),
    fetchComments(),
  ]);

  const data = {
    users: results[0].status === 'fulfilled' ? results[0].value : null,
    posts: results[1].status === 'fulfilled' ? results[1].value : null,
    comments: results[2].status === 'fulfilled' ? results[2].value : null,
  };

  return data;
}

// ✅ 推荐 - 处理部分失败
async function fetchMultipleItems(ids) {
  const promises = ids.map(id => fetchItem(id));
  const results = await Promise.allSettled(promises);

  return results
    .filter(result => result.status === 'fulfilled')
    .map(result => result.value);
}

// ❌ 避免 - Promise.all 一个失败全部失败
async function fetchAllData() {
  const results = await Promise.all([
    fetchUsers(),
    fetchPosts(),  // 如果这个失败，全部失败
  ]);
  return results;
}
```

### 限制并发数量

```javascript
// ✅ 正确 - 使用 Promise.pool 限制并发
async function fetchWithLimit(items, limit = 5) {
  const results = [];
  const executing = [];

  for (const item of items) {
    const promise = fetchItem(item).then(result => {
      executing.splice(executing.indexOf(promise), 1);
      return result;
    });

    executing.push(promise);

    if (executing.length >= limit) {
      await Promise.race(executing);
    }
  }

  return Promise.all(executing);
}

// ✅ 正确 - 使用 p-limit 风格的并发控制
class PromisePool {
  constructor(concurrency) {
    this.concurrency = concurrency;
    this.running = 0;
    this.queue = [];
  }

  async add(fn) {
    while (this.running >= this.concurrency) {
      await new Promise(resolve => this.queue.push(resolve));
    }

    this.running++;

    try {
      return await fn();
    } finally {
      this.running--;
      const resolve = this.queue.shift();
      if (resolve) resolve();
    }
  }
}

// 使用
const pool = new PromisePool(5);
const results = await Promise.all(
  items.map(item => pool.add(() => fetchItem(item)))
);
```

## 错误处理

### try-catch-finally

```javascript
// ✅ 正确 - 完整的错误处理
async function processUser(userId) {
  let user;
  try {
    user = await fetchUser(userId);
    const posts = await fetchUserPosts(userId);
    user.posts = posts;
    return user;
  } catch (error) {
    if (error instanceof NetworkError) {
      console.error('Network error:', error.message);
      return { error: 'Network error, please try again' };
    }
    if (error instanceof ValidationError) {
      console.error('Validation error:', error.message);
      return { error: error.message };
    }
    // 未知错误
    console.error('Unexpected error:', error);
    return { error: 'Unexpected error occurred' };
  } finally {
    // 清理资源
    console.log('User processing completed');
  }
}
```

### 错误传播

```javascript
// ✅ 正确 - 错误正确传播
async function fetchUserData(userId) {
  const user = await fetchUser(userId);
  const posts = await fetchUserPosts(userId);
  return { user, posts };
}

// 调用者处理错误
async function loadPage(userId) {
  try {
    return await fetchUserData(userId);
  } catch (error) {
    if (error.message.includes('404')) {
      return { error: 'User not found' };
    }
    return { error: 'Failed to load data' };
  }
}
```

## 超时控制

### AbortController

```javascript
// ✅ 推荐 - 使用 AbortController
async function fetchWithTimeout(url, timeout = 5000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

// 使用
try {
  const data = await fetchWithTimeout('/api/data', 3000);
} catch (error) {
  console.error('Fetch failed:', error.message);
}
```

### Promise.race 超时

```javascript
// ✅ 兼容 - 使用 Promise.race 实现超时
async function fetchWithTimeoutRace(url, timeout = 5000) {
  const fetchPromise = fetch(url).then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  });

  const timeoutPromise = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('Request timeout')), timeout);
  });

  return Promise.race([fetchPromise, timeoutPromise]);
}
```

## 事件循环理解

### 微任务和宏任务

```javascript
// ✅ 理解事件循环顺序
console.log('1. Start');

setTimeout(() => console.log('2. setTimeout'), 0);

Promise.resolve().then(() => console.log('3. Promise'));

console.log('4. End');

// 输出顺序：
// 1. Start
// 4. End
// 3. Promise (微任务)
// 2. setTimeout (宏任务)
```

### 避免阻塞事件循环

```javascript
// ❌ 错误 - 同步循环阻塞事件循环
function processLargeArraySync(items) {
  const results = [];
  for (const item of items) {
    // 复杂计算，阻塞事件循环
    const result = heavyComputation(item);
    results.push(result);
  }
  return results;
}

// ✅ 正确 - 分块处理避免阻塞
async function processLargeArrayAsync(items, chunkSize = 100) {
  const results = [];

  for (let i = 0; i < items.length; i += chunkSize) {
    const chunk = items.slice(i, i + chunkSize);

    // 处理当前块
    const chunkResults = chunk.map(item => heavyComputation(item));
    results.push(...chunkResults);

    // 让出控制权，允许事件循环处理其他任务
    await new Promise(resolve => setTimeout(resolve, 0));
  }

  return results;
}
```

## 异步迭代器

### for await...of

```javascript
// ✅ 正确 - 使用异步迭代器
async function* fetchPaginated(url) {
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const response = await fetch(`${url}?page=${page}`);
    const data = await response.json();

    if (data.items.length === 0) {
      hasMore = false;
    } else {
      for (const item of data.items) {
        yield item;
      }
      page++;
    }
  }
}

// 使用
async function processAllItems() {
  for await (const item of fetchPaginated('/api/items')) {
    console.log('Processing:', item);
    await processItem(item);
  }
}
```

## 防抖和节流

### 异步防抖

```javascript
// ✅ 正确 - 异步防抖
function asyncDebounce(fn, delay) {
  let timeoutId;
  let pendingPromise;

  return function(...args) {
    clearTimeout(timeoutId);

    return new Promise((resolve, reject) => {
      pendingPromise = { resolve, reject };

      timeoutId = setTimeout(async () => {
        try {
          const result = await fn.apply(this, args);
          if (pendingPromise) {
            pendingPromise.resolve(result);
          }
        } catch (error) {
          if (pendingPromise) {
            pendingPromise.reject(error);
          }
        }
      }, delay);
    });
  };
}

// 使用
const debouncedFetch = asyncDebounce(fetchSuggestions, 300);
```

### 异步节流

```javascript
// ✅ 正确 - 异步节流
function asyncThrottle(fn, limit) {
  let inThrottle = false;
  let lastResult;

  return async function(...args) {
    if (!inThrottle) {
      inThrottle = true;
      try {
        lastResult = await fn.apply(this, args);
      } finally {
        setTimeout(() => {
          inThrottle = false;
        }, limit);
      }
    }
    return lastResult;
  };
}

// 使用
const throttledScroll = asyncThrottle(handleScroll, 100);
```

## 检查清单

提交异步代码前，确保：

- [ ] 所有异步函数使用 `async/await`
- [ ] 所有 Promise 有错误处理
- [ ] I/O 操作有超时设置
- [ ] 限制了并发数量
- [ ] 没有阻塞事件循环的操作
- [ ] 正确处理 `AbortError`
- [ ] 测试覆盖异步代码
- [ ] 没有混用回调和 Promise
- [ ] 异步资源正确清理
- [ ] 没有内存泄漏风险
