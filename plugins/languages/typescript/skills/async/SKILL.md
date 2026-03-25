---
name: async
description: TypeScript 异步编程规范：Promise patterns、AbortController、async iterators、tRPC。处理异步代码时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# TypeScript 异步编程规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | TypeScript 开发专家 |
| debug | TypeScript 调试专家 |
| test  | TypeScript 测试专家 |

## 相关 Skills

| 场景     | Skill            | 说明                           |
| -------- | ---------------- | ------------------------------ |
| 核心规范 | Skills(core)     | TS 5.7+、strict mode           |
| 类型系统 | Skills(types)    | Promise 类型、泛型约束         |
| Node.js  | Skills(nodejs)   | Node.js 22 streams、fetch API  |
| 安全编码 | Skills(security) | 超时控制、资源泄漏防护         |

## async/await 最佳实践

```typescript
// 正确的错误处理（多行，结构化）
async function getUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data: unknown = await response.json();
  return UserSchema.parse(data); // Zod 运行时验证
}

// 禁止：单行错误处理
// if (err) return err;
```

## AbortController 取消控制

```typescript
async function fetchWithTimeout(url: string, timeoutMs = 5000): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

// React 中取消请求
useEffect(() => {
  const controller = new AbortController();
  fetchData(controller.signal).then(setData).catch((err) => {
    if (!controller.signal.aborted) console.error(err);
  });
  return () => controller.abort();
}, []);
```

## 并发模式

```typescript
// Promise.all - 全部成功或快速失败
const [users, posts] = await Promise.all([fetchUsers(), fetchPosts()]);

// Promise.allSettled - 容错并发（不因一个失败而中断）
const results = await Promise.allSettled([fetchA(), fetchB(), fetchC()]);
const successes = results
  .filter((r): r is PromiseFulfilledResult<Data> => r.status === "fulfilled")
  .map((r) => r.value);

// Promise.race - 竞争（超时控制）
const result = await Promise.race([
  fetchData(),
  new Promise<never>((_, reject) =>
    setTimeout(() => reject(new Error("Timeout")), 5000)
  ),
]);

// 限流并发
async function pMap<T, R>(
  items: T[],
  fn: (item: T) => Promise<R>,
  concurrency = 5,
): Promise<R[]> {
  const results: R[] = [];
  for (let i = 0; i < items.length; i += concurrency) {
    const batch = items.slice(i, i + concurrency).map(fn);
    results.push(...await Promise.all(batch));
  }
  return results;
}
```

## Async Iterators

```typescript
// 异步生成器
async function* fetchPages(baseUrl: string): AsyncGenerator<Page[]> {
  let cursor: string | null = null;
  do {
    const response = await fetch(`${baseUrl}?cursor=${cursor ?? ""}`);
    const data = await response.json();
    yield data.items;
    cursor = data.nextCursor;
  } while (cursor);
}

// 消费异步迭代器
for await (const page of fetchPages("/api/items")) {
  for (const item of page) {
    process(item);
  }
}
```

## tRPC 类型安全 API

```typescript
import { initTRPC } from "@trpc/server";
import { z } from "zod";

const t = initTRPC.create();

const appRouter = t.router({
  getUser: t.procedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      return db.user.findUnique({ where: { id: input.id } });
    }),
  createUser: t.procedure
    .input(CreateUserSchema)
    .mutation(async ({ input }) => {
      return db.user.create({ data: input });
    }),
});

// 客户端：完全类型安全
const user = await trpc.getUser.query({ id: "123" });
```

## Effect-TS（typed error handling）

```typescript
import { Effect, pipe } from "effect";

// 类型化的错误处理（替代 try/catch）
const getUser = (id: string) =>
  pipe(
    Effect.tryPromise({
      try: () => fetch(`/api/users/${id}`),
      catch: () => new NetworkError("Failed to fetch"),
    }),
    Effect.flatMap((res) =>
      res.ok
        ? Effect.tryPromise({ try: () => res.json(), catch: () => new ParseError() })
        : Effect.fail(new HttpError(res.status))
    ),
  );
// 类型：Effect<unknown, NetworkError | ParseError | HttpError>
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| 顺序 `await` 独立请求 | 应使用 `Promise.all` 并发 | 高 |
| 忽略 `catch` | 未捕获的 Promise rejection | 高 |
| 无超时控制 | 请求可能永远挂起 | 中 |
| 无 AbortController | 组件卸载后继续请求 | 中 |
| `callback` 风格 | 应使用 async/await | 中 |
| `.then().catch()` 链 | 优先使用 async/await | 低 |

## 检查清单

- [ ] 使用 async/await（非 callback）
- [ ] 多行结构化错误处理
- [ ] 独立请求使用 `Promise.all` 并发
- [ ] 网络请求有超时控制（AbortController）
- [ ] React useEffect 中取消请求
- [ ] `Promise.allSettled` 处理容错并发
- [ ] 分页数据使用 async iterators
- [ ] API 层考虑 tRPC 类型安全
