/**
 * JavaScript 异步编程示例
 *
 * 本文件展示了异步编程的正确模式。
 * 遵循 javascript-skills/specialized/async-programming.md 规范。
 */

// =============================================================================
// 1. async/await 基本用法
// =============================================================================

// ✅ 正确 - async/await 与错误处理
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
async function fetchUserBad(userId) {
  const response = await fetch(`/api/users/${userId}`);
  return await response.json();
}

// =============================================================================
// 2. Promise.allSettled - 处理多个异步操作
// =============================================================================

// ✅ 正确 - 使用 allSettled
async function fetchAllData() {
  const results = await Promise.allSettled([
    fetch('/api/users').then(r => r.json()),
    fetch('/api/posts').then(r => r.json()),
    fetch('/api/comments').then(r => r.json()),
  ]);

  const data = {
    users: results[0].status === 'fulfilled' ? results[0].value : null,
    posts: results[1].status === 'fulfilled' ? results[1].value : null,
    comments: results[2].status === 'fulfilled' ? results[2].value : null,
  };

  // 处理失败的情况
  results.forEach((result, index) => {
    if (result.status === 'rejected') {
      const endpoints = ['users', 'posts', 'comments'];
      console.warn(`Failed to fetch ${endpoints[index]}:`, result.reason.message);
    }
  });

  return data;
}

// ✅ 正确 - 使用 allSettled 过滤成功结果
async function fetchMultipleItems(ids) {
  const promises = ids.map(id => fetchItem(id));
  const results = await Promise.allSettled(promises);

  return results
    .filter(result => result.status === 'fulfilled')
    .map(result => result.value);
}

// 模拟函数
async function fetchItem(id) {
  // 模拟 API 调用
  await new Promise(resolve => setTimeout(resolve, 100));
  return { id, name: `Item ${id}` };
}

// =============================================================================
// 3. 并发控制 - 限制并发数量
// =============================================================================

// ✅ 正确 - Promise Pool 模式
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

// 使用示例
async function fetchWithPool(items, limit = 5) {
  const pool = new PromisePool(limit);
  const results = await Promise.all(
    items.map(item => pool.add(() => fetchItem(item.id)))
  );
  return results;
}

// =============================================================================
// 4. 超时控制
// =============================================================================

// ✅ 正确 - 使用 AbortController
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

// =============================================================================
// 5. 异步迭代器
// =============================================================================

// ✅ 正确 - 异步生成器
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

// 使用异步迭代器
async function processAllItems(url) {
  const items = [];

  for await (const item of fetchPaginated(url)) {
    console.log('Processing:', item);
    items.push(item);
  }

  return items;
}

// =============================================================================
// 6. 防抖和节流
// =============================================================================

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

// 使用示例
const debouncedSearch = asyncDebounce(async (query) => {
  const response = await fetch(`/api/search?q=${query}`);
  return response.json();
}, 300);

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

// =============================================================================
// 7. 避免阻塞事件循环
// =============================================================================

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

// 模拟复杂计算
function heavyComputation(item) {
  // 模拟计算
  let result = 0;
  for (let i = 0; i < 1000; i++) {
    result += Math.sqrt(i);
  }
  return { ...item, result };
}

// =============================================================================
// 8. async 队列
// =============================================================================

// ✅ 正确 - 异步队列
class AsyncQueue {
  constructor() {
    this.queue = [];
    this.pending = false;
  }

  enqueue(fn) {
    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
      this.process();
    });
  }

  async process() {
    if (this.pending || this.queue.length === 0) {
      return;
    }

    this.pending = true;

    const { fn, resolve, reject } = this.queue.shift();

    try {
      const result = await fn();
      resolve(result);
    } catch (error) {
      reject(error);
    } finally {
      this.pending = false;
      this.process();  // 处理下一个
    }
  }
}

// =============================================================================
// 运行示例
// =============================================================================

async function main() {
  console.log('JavaScript 异步编程示例');
  console.log('========================\n');

  // 1. 测试基本 async/await
  console.log('=== 测试 async/await ===');
  try {
    const user = await fetchUser(1);
    console.log('Fetched user:', user);
  } catch (error) {
    console.log('Expected error (fetch fails in demo):', error.message);
  }

  // 2. 测试 Promise.allSettled
  console.log('\n=== 测试 Promise.allSettled ===');
  const items = [
    { id: 1 },
    { id: 2 },
    { id: 3 },
  ];
  const results = await fetchMultipleItems(items);
  console.log('Fetched items:', results);

  // 3. 测试并发控制
  console.log('\n=== 测试并发控制 ===');
  const poolResults = await fetchWithPool(items, 2);
  console.log('Pool results:', poolResults);

  // 4. 测试超时
  console.log('\n=== 测试超时 ===');
  try {
    // 模拟超时
    await new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Timeout')), 100);
    });
  } catch (error) {
    console.log('Timeout handled correctly');
  }

  // 5. 测试防抖
  console.log('\n=== 测试防抖 ===');
  const debounced = asyncDebounce(async (msg) => {
    console.log('Executing:', msg);
    return `Result: ${msg}`;
  }, 100);

  debounced('First');
  debounced('Second');
  debounced('Third');
  // 只有最后一个会执行
  await new Promise(resolve => setTimeout(resolve, 200));

  console.log('\n=== 示例完成 ===');
  console.log('✅ 所有异步编程示例已演示');
}

// 导出
export {
  fetchUser,
  fetchAllData,
  fetchMultipleItems,
  PromisePool,
  fetchWithTimeout,
  fetchWithTimeoutRace,
  fetchPaginated,
  asyncDebounce,
  asyncThrottle,
  processLargeArrayAsync,
  AsyncQueue,
};

// 运行示例
if (typeof window !== 'undefined') {
  main().catch(console.error);
}
