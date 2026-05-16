---
name: typescript-async
description: TypeScript 异步编程规范，覆盖 async/await 错误处理、AbortController 取消、Promise.all / allSettled / race 并发模式、async iterators 流式处理、tRPC 类型安全 API、Effect-TS 类型化错误。Use when 编写异步逻辑、并发控制、流式数据、超时取消、API 客户端，或用户提到 "async"、"Promise"、"取消请求"、"AbortController"、"并发"、"超时"、"streaming"。
user-invocable: true
---

# TypeScript 异步编程规范

异步两条铁律：**显式取消** + **结构化错误**。

## async/await 错误处理

```typescript
// ✅ 多行结构化
async function getUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data: unknown = await response.json();
  return UserSchema.parse(data); // Zod 边界验证
}

// ❌ 单行
// if (err) return err;
```

## AbortController 取消控制（必备）

```typescript
async function fetchWithTimeout(url: string, ms = 5000): Promise<Response> {
  // Node 22+ / 现代浏览器：AbortSignal.timeout 内置
  const signal = AbortSignal.timeout(ms);
  return fetch(url, { signal });
}

// React 19 中取消
useEffect(() => {
  const controller = new AbortController();
  fetchData({ signal: controller.signal })
    .then(setData)
    .catch((err) => {
      if (!controller.signal.aborted) console.error(err);
    });
  return () => controller.abort();
}, []);
```

## 并发模式

```typescript
// Promise.all — 全成功 or 快速失败
const [users, posts] = await Promise.all([fetchUsers(), fetchPosts()]);

// Promise.allSettled — 容错并发
const results = await Promise.allSettled([fetchA(), fetchB(), fetchC()]);
const ok = results
  .filter((r): r is PromiseFulfilledResult<Data> => r.status === "fulfilled")
  .map((r) => r.value);

// Promise.any — 任一成功（fallback 场景）
const fastest = await Promise.any([primary(), mirror1(), mirror2()]);

// 限流并发
async function pMap<T, R>(items: T[], fn: (i: T) => Promise<R>, n = 5): Promise<R[]> {
  const out: R[] = [];
  for (let i = 0; i < items.length; i += n) {
    out.push(...await Promise.all(items.slice(i, i + n).map(fn)));
  }
  return out;
}
```

## Async Iterators（分页 / 流式）

```typescript
async function* fetchPages(base: string): AsyncGenerator<Page[]> {
  let cursor: string | null = null;
  do {
    const r = await fetch(`${base}?cursor=${cursor ?? ""}`);
    const data = await r.json();
    yield data.items;
    cursor = data.nextCursor;
  } while (cursor);
}

for await (const page of fetchPages("/api/items")) {
  for (const item of page) process(item);
}
```

## tRPC 类型安全 API

```typescript
import { initTRPC } from "@trpc/server";
import { z } from "zod";

const t = initTRPC.create();

export const appRouter = t.router({
  getUser: t.procedure
    .input(z.object({ id: z.uuid() }))
    .query(({ input }) => db.user.findUnique({ where: { id: input.id } })),
  createUser: t.procedure
    .input(CreateUserSchema)
    .mutation(({ input }) => db.user.create({ data: input })),
});

export type AppRouter = typeof appRouter;
// 客户端：完全类型推断
```

## Effect-TS（typed errors 进阶）

```typescript
import { Effect, pipe } from "effect";

const getUser = (id: string) =>
  pipe(
    Effect.tryPromise({
      try: () => fetch(`/api/users/${id}`),
      catch: () => new NetworkError(),
    }),
    Effect.flatMap((res) =>
      res.ok
        ? Effect.tryPromise({ try: () => res.json(), catch: () => new ParseError() })
        : Effect.fail(new HttpError(res.status)),
    ),
  );
// Effect<unknown, NetworkError | ParseError | HttpError>
```

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| 顺序 await 独立请求 | 应 `Promise.all` 并发 | 高 |
| 未 catch / 漏 await | unhandled rejection | 高 |
| 无超时 | 请求挂死 | 中 |
| 无 AbortController | 组件卸载继续请求 | 中 |
| `.then().catch()` 链 | async/await 更可读 | 低 |
| callback 风格 | 全面 promisify | 中 |
| `Promise.all` 中混含可失败任务 | 用 `allSettled` | 中 |

## 检查清单

- [ ] async/await（非 callback / 链式 then）
- [ ] 多行结构化错误处理
- [ ] 独立请求 `Promise.all` 并发
- [ ] 网络请求有 `AbortSignal.timeout`
- [ ] React useEffect 中 abort
- [ ] 容错场景用 `allSettled`
- [ ] 分页用 async iterator
- [ ] API 边界 Zod 校验
