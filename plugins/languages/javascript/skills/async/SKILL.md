---
name: javascript-async
description: |
  JavaScript 异步编程规范 (2026)：async/await + AbortController, Promise.try / withResolvers /
  allSettled / any, Streams API (ReadableStream / TransformStream), Web Workers ESM,
  Node Worker threads, 事件循环, 长任务切片 scheduler.yield。
  Use when writing or reviewing async code, handling concurrency, request cancellation,
  timeouts, race conditions, streaming, or CPU-heavy offloading.
  Triggers: "异步", "并发", "取消请求", "超时", "竞态", "Promise", "stream",
  "Web Worker", "race condition", "async/await".
context: fork
model: sonnet
---

# JavaScript 异步编程规范 (2026)

## 配套

- `Skills(javascript:core)` — 工具链与基线
- `Skills(javascript:security)` — fetch 边界校验

## async/await 契约

```js
// ✅ try-catch 内必 return await
async function fetchUser(id) {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();        // return await: 错误才能进 catch
  } catch (e) {
    logger.error({ err: e, id }, 'fetchUser failed');
    throw e;
  }
}

// ✅ Promise.try (ES2025): 同步异常也进 Promise 链
const p = Promise.try(() => mayThrowSync());
```

## 并发模式

```js
// 全成功 / 快速失败
const [u, p] = await Promise.all([fetchUser(id), fetchPosts(id)]);

// 部分失败可接受 (推荐用于聚合)
const results = await Promise.allSettled([a(), b(), c()]);
const ok = results.filter(r => r.status === 'fulfilled').map(r => r.value);

// 任意一个成功
const fastest = await Promise.any([cdn1(), cdn2(), cdn3()]);

// 限并发 (无外部依赖)
async function pool(items, n, fn) {
  const out = []; let i = 0;
  const workers = Array.from({ length: n }, async () => {
    while (i < items.length) {
      const idx = i++;
      out[idx] = await fn(items[idx]);
    }
  });
  await Promise.all(workers);
  return out;
}
```

## AbortController: 取消 / 超时 / 清理

```js
// 超时
async function fetchWithTimeout(url, ms = 5000) {
  const ctrl = AbortSignal.timeout(ms);    // ES2024 静态方法
  return fetch(url, { signal: ctrl });
}

// 组合多个 signal (ES2024)
const signal = AbortSignal.any([userSignal, timeoutSignal]);

// 竞态：取消过期请求
let inflight = null;
async function search(q) {
  inflight?.abort();
  inflight = new AbortController();
  try {
    const r = await fetch(`/api/search?q=${q}`, { signal: inflight.signal });
    return await r.json();
  } catch (e) {
    if (e.name === 'AbortError') return;   // 静默忽略取消
    throw e;
  }
}

// 统一清理事件监听
function setup(el) {
  const ctrl = new AbortController();
  const { signal } = ctrl;
  el.addEventListener('click', onClick, { signal });
  el.addEventListener('keydown', onKey, { signal });
  window.addEventListener('resize', onResize, { signal });
  return () => ctrl.abort();
}
```

## Promise.withResolvers (ES2024)

```js
// 替代手动 new Promise(...)
const { promise, resolve, reject } = Promise.withResolvers();
element.addEventListener('click', () => resolve('clicked'), { once: true });
const value = await promise;
```

## Streams API

```js
// 流式 NDJSON 处理 (前端 / Node 通用)
async function* lines(stream) {
  const reader = stream.pipeThrough(new TextDecoderStream()).getReader();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += value;
    const parts = buf.split('\n');
    buf = parts.pop();
    for (const p of parts) if (p) yield JSON.parse(p);
  }
  if (buf) yield JSON.parse(buf);
}

// TransformStream 管线
const res = await fetch(url);
await res.body
  .pipeThrough(new TextDecoderStream())
  .pipeThrough(new TransformStream({ transform(c, ctl) { ctl.enqueue(c.toUpperCase()); } }))
  .pipeTo(writableSink);

// Array.fromAsync (ES2025)
const items = await Array.fromAsync(asyncGen(), x => x.id);
```

## Web Workers (ESM)

```js
const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });
worker.postMessage({ task: 'parse', payload: data });
worker.addEventListener('message', (e) => console.log(e.data), { once: true });
worker.addEventListener('error', console.error);
// 销毁: worker.terminate();
```

## Node Worker threads (CPU-heavy)

```js
import { Worker } from 'node:worker_threads';
const w = new Worker(new URL('./heavy.js', import.meta.url));
w.postMessage(data);
w.on('message', (r) => console.log(r));
```

## 长任务切片

```js
// scheduler.yield() (Chrome 129+, fallback setTimeout 0)
async function processBig(items) {
  for (const item of items) {
    work(item);
    if ('scheduler' in globalThis && 'yield' in scheduler) {
      await scheduler.yield();
    } else {
      await new Promise(r => setTimeout(r, 0));
    }
  }
}
```

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| `await` 无 try-catch / 无上层 catch | unhandled rejection | 高 |
| try 内 `return fetch(...)` 不 await | 错误逃出 try | 高 |
| `Promise.all` 用于"尽量都跑" | 应 `allSettled` | 中 |
| 手写 `new Promise((res,rej)=>...)` | 用 `withResolvers` | 低 |
| `setTimeout(controller.abort, ms)` | 用 `AbortSignal.timeout(ms)` | 低 |
| 搜索框无取消 | 必 AbortController | 高 |
| 大数组同步 `forEach` 阻塞主线程 | 切片 + scheduler.yield | 中 |
| 回调嵌套 / `.then` 链 | 换 async/await | 高 |

## 检查清单

- [ ] 所有 await 有错误路径
- [ ] try-catch 内 `return await`
- [ ] 多任务用 `Promise.allSettled` (聚合) 或 `Promise.all` (全有效)
- [ ] 用户输入触发的请求有 AbortController
- [ ] 超时用 `AbortSignal.timeout()`
- [ ] 事件监听经 `{ signal }` 统一清理
- [ ] CPU 密集 → Web Worker / worker_threads
- [ ] 大流数据 → Streams, 不 `JSON.parse` 整文件
