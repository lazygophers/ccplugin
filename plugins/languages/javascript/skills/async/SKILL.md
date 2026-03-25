---
name: async
description: JavaScript 异步编程规范：async/await、Promise.withResolvers、AbortController、Streams API。处理异步代码时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# JavaScript 异步编程规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | JavaScript 开发专家 |
| debug | JavaScript 调试专家 |
| test  | JavaScript 测试专家 |
| perf  | JavaScript 性能优化专家 |

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(javascript:core) | ES2024-2025 标准、ESM、工具链 |
| 安全编码 | Skills(javascript:security) | CORS、CSP、输入验证 |

## async/await 最佳实践

```javascript
// 所有 await 必须有错误处理
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('Fetch failed:', error);
    throw error;
  }
}

// try-catch 中必须 return await（否则错误不被捕获）
async function safeFetch(url) {
  try {
    return await fetch(url); // 必须 await
  } catch (e) {
    // 这样才能捕获错误
    throw new Error(`Request failed: ${e.message}`);
  }
}
```

## Promise 并行模式

```javascript
// Promise.allSettled - 等待全部完成（推荐，处理部分失败）
const results = await Promise.allSettled([
  fetchUser(id),
  fetchPosts(id),
  fetchComments(id),
]);

const succeeded = results.filter(r => r.status === 'fulfilled').map(r => r.value);
const failed = results.filter(r => r.status === 'rejected').map(r => r.reason);

// Promise.all - 全部成功或快速失败
const [user, posts] = await Promise.all([
  fetchUser(id),
  fetchPosts(id),
]);

// Promise.withResolvers (ES2024) - 外部控制 resolve/reject
const { promise, resolve, reject } = Promise.withResolvers();
element.addEventListener('click', () => resolve('clicked'));
const result = await promise;

// Promise.any - 第一个成功
const fastest = await Promise.any([
  fetch('https://cdn1.example.com/data'),
  fetch('https://cdn2.example.com/data'),
]);
```

## AbortController 超时与取消

```javascript
// 超时控制
async function fetchWithTimeout(url, timeout = 5000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, { signal: controller.signal });
    return response;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeout}ms`);
    }
    throw error;
  } finally {
    clearTimeout(id);
  }
}

// 竞态条件处理 - 取消过期请求
let activeController = null;

async function loadData(id) {
  activeController?.abort();
  activeController = new AbortController();

  const response = await fetch(`/api/data/${id}`, {
    signal: activeController.signal,
  });
  return response.json();
}

// AbortController 统一清理事件监听
function setupListeners(element) {
  const controller = new AbortController();
  const { signal } = controller;

  element.addEventListener('click', handleClick, { signal });
  element.addEventListener('keydown', handleKey, { signal });
  window.addEventListener('resize', handleResize, { signal });

  return () => controller.abort(); // 一次性清理所有监听
}
```

## Streams API

```javascript
// 读取大文件流
async function processStream(url) {
  const response = await fetch(url);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    processChunk(chunk);
  }
}

// Array.fromAsync (ES2025)
async function* generateItems() {
  for (let i = 0; i < 10; i++) {
    yield await fetchItem(i);
  }
}

const items = await Array.fromAsync(generateItems());
```

## Web Workers

```javascript
// worker.js
self.onmessage = (event) => {
  const result = heavyComputation(event.data);
  self.postMessage(result);
};

// main.js - ESM Worker
const worker = new Worker(
  new URL('./worker.js', import.meta.url),
  { type: 'module' }
);

worker.postMessage(data);
worker.onmessage = (e) => handleResult(e.data);
worker.onerror = (e) => handleError(e);
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| await 无 try-catch | 未处理的 Promise rejection | 高 |
| `return fetch()` 在 try 中 | 应 `return await fetch()` 否则错误不被捕获 | 高 |
| `Promise.all` 不容错 | 应使用 `Promise.allSettled` 处理部分失败 | 中 |
| 手动创建 Promise | 应使用 `Promise.withResolvers()` | 低 |
| 无超时控制 | 应使用 AbortController 设置超时 | 中 |
| 竞态条件 | 应使用 AbortController 取消过期请求 | 高 |
| 回调嵌套 | 应使用 async/await | 高 |

## 检查清单

- [ ] 所有 await 有 try-catch
- [ ] try-catch 中使用 `return await`
- [ ] 使用 `Promise.allSettled()` 处理并行
- [ ] 使用 `Promise.withResolvers()` 替代手动 Promise
- [ ] 使用 AbortController 设置超时
- [ ] 使用 AbortController 处理竞态条件
- [ ] 使用 AbortController 统一清理事件监听
- [ ] CPU 密集任务使用 Web Workers
