// TypeScript 异步编程示例

// ========== Promise 基础 ==========

// ✅ 正确: 创建 Promise
function fetchUser(id: string): Promise<User> {
  return new Promise((resolve, reject) => {
    fetch(`/api/users/${id}`)
      .then(response => {
        if (!response.ok) {
          reject(new Error(`HTTP ${response.status}`));
          return;
        }
        return response.json();
      })
      .then(data => resolve(UserSchema.parse(data)))
      .catch(error => reject(error));
  });
}

// ✅ 正确: async/await 版本
async function fetchUserAsync(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = await response.json();
  return UserSchema.parse(data);
}

// ========== 并发处理 ==========

// ✅ 正确: 并发执行多个独立操作
async function fetchUserData(userId: string) {
  const [user, posts, comments] = await Promise.all([
    fetchUser(userId),
    fetchUserPosts(userId),
    fetchUserComments(userId),
  ]);

  return { user, posts, comments };
}

// ✅ 正确: 部分失败不影响其他
async function fetchUserDataPartial(userId: string) {
  const results = await Promise.allSettled([
    fetchUser(userId),
    fetchUserPosts(userId),
    fetchUserComments(userId),
  ]);

  const [user, posts, comments] = results.map((result, index) => {
    if (result.status === 'fulfilled') {
      return result.value;
    }
    console.error(`Operation ${index} failed:`, result.reason);
    return null;
  });

  return { user, posts, comments };
}

// ✅ 正确: 谁先完成用谁的 Promise.race
async function fetchWithFallback(urls: string[]): Promise<User> {
  const errors: Error[] = [];

  for (const url of urls) {
    try {
      // 使用 AbortController 实现超时
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      errors.push(error as Error);
    }
  }

  throw new Error(`All URLs failed: ${errors.map(e => e.message).join(', ')}`);
}

// ========== 并发控制 ==========

// ✅ 正确: 限制并发数量
async function processManyItems<T>(
  items: T[],
  processor: (item: T) => Promise<void>,
  concurrency: number = 5,
): Promise<void> {
  const executing: Promise<void>[] = [];

  for (const item of items) {
    const promise = processor(item).then(() => {
      // 完成后从 executing 数组移除
      executing.splice(executing.indexOf(promise), 1);
    });

    executing.push(promise);

    if (executing.length >= concurrency) {
      await Promise.race(executing);
    }
  }

  await Promise.all(executing);
}

// ✅ 使用 p-limit 库
import pLimit from 'p-limit';

async function processItemsWithLimit(items: Item[]) {
  const limit = pLimit(5);  // 最多 5 个并发

  const tasks = items.map(item =>
    limit(() => processItem(item))
  );

  await Promise.all(tasks);
}

// ========== 取消异步操作 ==========

// ✅ 使用 AbortController 取消请求
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
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout');
    }
    throw error;
  }
}

// 使用
try {
  const data = await fetchWithTimeout('/api/users', 3000);
} catch (error) {
  console.error('error:', error);
}

// ========== 异步迭代 ==========

// ✅ 异步生成器处理分页
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

// ========== React 异步模式 ==========

// ✅ useEffect 清理异步操作
import { useEffect, useState } from 'react';

function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchUser() {
      try {
        setLoading(true);
        const data = await userService.getUser(userId);

        if (!cancelled) {
          setUser(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchUser();

    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return <div>{user?.name}</div>;
}

// ✅ 使用 AbortController
function UserProfileWithAbort({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchUser() {
      try {
        const data = await userService.getUser(userId, {
          signal: controller.signal,
        });
        setUser(data);
      } catch (err) {
        if (err instanceof Error && err.name !== 'AbortError') {
          setError(err);
        }
      }
    };

    fetchUser();

    return () => {
      controller.abort();
    };
  }, [userId]);

  return user ? <div>{user.name}</div> : <div>Loading...</div>;
}

// ========== 错误示例 ==========

// ❌ 错误: 串行等待（可以并行）
async function badFetchUserData(userId: string) {
  const user = await fetchUser(userId);
  const posts = await fetchUserPosts(userId);  // 不必要地等待
  const comments = await fetchUserComments(userId);  // 不必要地等待
  return { user, posts, comments };
}

// ❌ 错误: 无限制并发
async function badProcessMany(items: Item[]) {
  // 危险：可能创建数千个并发请求
  await Promise.all(items.map(item => processItem(item)));
}

// ❌ 错误: 忘记 await
async function badProcessUsers(ids: string[]) {
  const users = ids.map(id => fetchUser(id));  // 返回 Promise[]
  return users[0].name;  // 错误：访问 Promise 的属性
}

// ❌ 错误: 在 async 函数中使用同步阻塞
async function badBlockingOperation() {
  // 阻塞事件循环！
  const data = readFileSync('./large-file.json');  // 不要这样做
  return JSON.parse(data);
}

// ✅ 正确: 使用异步版本
async function goodNonBlockingOperation() {
  const data = await readFile('./large-file.json', 'utf-8');
  return JSON.parse(data);
}
