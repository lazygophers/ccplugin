# TypeScript 异步编程规范

## 核心原则

### ✅ 必须遵守

1. **使用 async/await** - 优于 Promise 链
2. **正确处理错误** - 所有异步操作都有错误处理
3. **避免阻塞** - 不在异步函数中使用同步阻塞操作
4. **并发控制** - 限制并发数量，避免资源耗尽
5. **取消处理** - 使用 AbortController 取消异步操作

### ❌ 禁止行为

- 在 async 函数中使用同步阻塞操作
- 忽略 Promise 拒绝
- 创建无限并发的 Promise
- 使用回调而非 Promise
- 在循环中串行等待（可以并行时）

## async/await 基础

### 基本用法

```typescript
// ✅ 正确 - 使用 async/await
async function getUser(id: string): Promise<User> {
  try {
    const response = await fetch(`/api/users/${id}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return UserSchema.parse(data);
  } catch (error) {
    console.error('error:', error);
    throw error;
  }
}

// ❌ 错误 - Promise 链（难以阅读）
function getUserBad(id: string): Promise<User> {
  return fetch(`/api/users/${id}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(data => UserSchema.parse(data))
    .catch(error => {
      console.error('error:', error);
      throw error;
    });
}
```

### 并发处理

```typescript
// ✅ 正确 - 并发执行多个独立操作
async function fetchUserData(userId: string) {
  const [user, posts, comments] = await Promise.all([
    fetchUser(userId),
    fetchUserPosts(userId),
    fetchUserComments(userId),
  ]);

  return { user, posts, comments };
}

// ✅ 正确 - 部分失败不影响其他
async function fetchUserDataPartial(userId: string) {
  const results = await Promise.allSettled([
    fetchUser(userId),
    fetchUserPosts(userId),
    fetchUserComments(userId),
  ]);

  const successful = results
    .filter((r): r is PromiseFulfilledResult<unknown> => r.status === 'fulfilled')
    .map(r => r.value);

  const failed = results
    .filter((r): r is PromiseRejectedResult => r.status === 'rejected')
    .map(r => r.reason);

  return { successful, failed };
}

// ❌ 错误 - 串行等待（可以并行）
async function fetchUserDataBad(userId: string) {
  const user = await fetchUser(userId);
  const posts = await fetchUserPosts(userId);  // 不必要地等待 user
  const comments = await fetchUserComments(userId);  // 不必要地等待 posts
  return { user, posts, comments };
}
```

### 并发控制

```typescript
// ✅ 正确 - 限制并发数量
async function processManyItems<T>(
  items: T[],
  processor: (item: T) => Promise<void>,
  concurrency: number = 5,
): Promise<void> {
  const queue: Promise<void>[] = [];

  for (const item of items) {
    const promise = processor(item);
    queue.push(promise);

    if (queue.length >= concurrency) {
      await Promise.race(queue);
      // 移除已完成的 Promise
      const settled = await Promise.allSettled(queue);
      queue.length = 0;
      queue.push(...settled.filter(s => s.status === 'pending').map(() => promise));
    }
  }

  await Promise.all(queue);
}

// ✅ 使用 p-limit 库
import pLimit from 'p-limit';

const limit = pLimit(5);  // 最多 5 个并发

async function processItems(items: Item[]) {
  const tasks = items.map(item =>
    limit(() => processItem(item))
  );

  await Promise.all(tasks);
}

// ❌ 错误 - 无限制并发
async function processManyItemsBad(items: Item[]) {
  // 危险：可能创建数千个并发请求
  await Promise.all(items.map(item => processItem(item)));
}
```

## 错误处理

### async/await 错误处理

```typescript
// ✅ 正确 - try-catch 包裹 await
async function updateUser(id: string, data: UpdateUserInput): Promise<User> {
  try {
    const response = await fetch(`/api/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('error:', error);
    throw error;
  }
}

// ✅ 使用 Result 类型
type Result<T> =
  | { ok: true; value: T }
  | { ok: false; error: Error };

async function safeUpdateUser(
  id: string,
  data: UpdateUserInput,
): Promise<Result<User>> {
  try {
    const response = await fetch(`/api/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const user = await response.json();
    return { ok: true, value: user };
  } catch (error) {
    console.error('error:', error);
    return { ok: false, error: error as Error };
  }
}
```

### Promise 错误处理

```typescript
// ✅ 正确 - Promise 链中的错误处理
fetchUser(userId)
  .then(user => validateUser(user))
  .then(valid => saveUser(valid))
  .catch(error => {
    console.error('error:', error);
    handleError(error);
  });

// ✅ 使用 finally 清理
let connection: Connection | null = null;

connect()
  .then(conn => {
    connection = conn;
    return conn.query('SELECT * FROM users');
  })
  .then(results => processResults(results))
  .catch(error => {
    console.error('error:', error);
  })
  .finally(() => {
    connection?.close();
  });

// ❌ 错误 - 忽略错误处理
fetchUser(userId).then(user => {
  processData(user);
  // 如果这里抛出错误，会变成未捕获的 Promise 拒绝
});
```

## 取消异步操作

### AbortController

```typescript
// ✅ 正确 - 使用 AbortController 取消请求
async function fetchWithTimeout(
  url: string,
  timeout: number = 5000,
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}

// 使用
try {
  const data = await fetchWithTimeout('/api/users');
} catch (error) {
  console.error('error:', error);
}

// 取消正在进行的请求
const controller = new AbortController();
fetch('/api/users', { signal: controller.signal });

// 取消请求
controller.abort();
```

### 取消令牌

```typescript
// ✅ 创建可取消的异步操作
interface CancellablePromise<T> extends Promise<T> {
  cancel: () => void;
}

function createCancellablePromise<T>(
  executor: (signal: AbortSignal) => Promise<T>,
): CancellablePromise<T> {
  const controller = new AbortController();

  const promise = new Promise<T>((resolve, reject) => {
    const signal = controller.signal;

    signal.addEventListener('abort', () => {
      reject(new Error('Cancelled'));
    });

    executor(signal).then(resolve, reject);
  }) as CancellablePromise<T>;

  promise.cancel = () => controller.abort();

  return promise;
}

// 使用
const cancellable = createCancellablePromise(async (signal) => {
  const response = await fetch('/api/users', { signal });
  return response.json();
});

// 取消
cancellable.cancel();
```

## 异步迭代

### 异步生成器

```typescript
// ✅ 正确 - 使用异步生成器处理流式数据
async function* fetchPaginatedUsers(
  endpoint: string,
  pageSize: number = 100,
): AsyncGenerator<User[]> {
  let page = 1;

  while (true) {
    const response = await fetch(
      `${endpoint}?page=${page}&pageSize=${pageSize}`,
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const users: User[] = await response.json();

    if (users.length === 0) {
      break;
    }

    yield users;
    page++;
  }
}

// 使用
for await (const users of fetchPaginatedUsers('/api/users')) {
  console.log(`Fetched ${users.length} users`);
  for (const user of users) {
    await processUser(user);
  }
}
```

### 异步列表推导

```typescript
// ✅ 正确 - 使用 Promise.all + map
async function fetchUsers(ids: string[]): Promise<User[]> {
  return Promise.all(
    ids.map(id => fetchUser(id))
  );
}

// ✅ 正确 - 过滤异步结果
async function fetchActiveUsers(ids: string[]): Promise<User[]> {
  const users = await Promise.all(
    ids.map(id => fetchUser(id))
  );

  return users.filter(user => user.status === 'active');
}

// ✅ 正确 - 异步 map
async function processUsers(ids: string[]): Promise<ProcessedUser[]> {
  const users = await Promise.all(
    ids.map(async (id) => {
      const user = await fetchUser(id);
      return processUser(user);
    })
  );

  return users;
}
```

## React 异步模式

### useEffect 清理

```typescript
// ✅ 正确 - 清理异步操作
useEffect(() => {
  let cancelled = false;

  async function fetchUser() {
    const data = await userService.getUser(userId);

    if (!cancelled) {
      setUser(data);
    }
  }

  fetchUser();

  return () => {
    cancelled = true;
  };
}, [userId]);

// ✅ 正确 - 使用 AbortController
useEffect(() => {
  const controller = new AbortController();

  async function fetchUser() {
    try {
      const data = await userService.getUser(userId, {
        signal: controller.signal,
      });
      setUser(data);
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('error:', error);
      }
    }
  }

  fetchUser();

  return () => {
    controller.abort();
  };
}, [userId]);
```

## 性能优化

### 缓存异步结果

```typescript
// ✅ 正确 - 缓存异步操作结果
const cache = new Map<string, Promise<User>>();

async function getCachedUser(id: string): Promise<User> {
  if (cache.has(id)) {
    return cache.get(id)!;
  }

  const promise = fetchUser(id);
  cache.set(id, promise);

  return promise;
}

// ✅ 使用 React Query 自动缓存
function useUser(userId: string) {
  return useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
    staleTime: 5 * 60 * 1000,  // 5 分钟
  });
}
```

## 检查清单

提交异步代码前，确保：

- [ ] 所有 async 函数都有错误处理
- [ ] 使用了并发而非串行（可以并行时）
- [ ] 限制了并发数量
- [ ] 长时间运行的操作支持取消
- [ ] 没有在 async 函数中使用同步阻塞操作
- [ ] Promise 拒绝被正确处理
- [ ] useEffect 清理了异步操作
