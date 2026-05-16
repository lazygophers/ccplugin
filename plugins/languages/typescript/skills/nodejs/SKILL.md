---
name: typescript-nodejs
description: TypeScript / JavaScript Node.js 后端开发规范，覆盖 Node 22-24 LTS 原生 strip-types、ESM 模块、原生 fetch、fs/promises、stream pipeline、worker_threads、Hono 4 / Fastify 5 框架、Drizzle ORM、env Zod 验证、undici 高性能 HTTP。Use when 开发 Node.js 服务端、CLI、API 服务、迁移 CommonJS→ESM、env 校验，或用户提到 "Node.js"、"fastify"、"hono"、"ESM"、"worker thread"、"process.env"、"backend"。
user-invocable: true
---

# TypeScript / JavaScript Node.js 后端规范

本 skill 同时覆盖 JavaScript 项目；示例以 TS 为主，JS 项目去掉类型注解即可。

Node 22 LTS 起原生支持 strip-types (`node --experimental-strip-types` / 22.18+ 默认)；Node 24 进一步打磨。新项目可不依赖 tsc 直接 run。

## Node.js 22-24 LTS 速览

- **Native strip-types** — `node file.ts` 直接运行 (无类型检查)
- **Native fetch** — 全局可用，无 node-fetch
- **AbortSignal.timeout / AbortSignal.any** — 内置超时与组合
- **fs/promises** — 原生异步文件 API
- **node --test** — 内置 test runner (轻量场景)
- **Single executable apps** — 单文件可执行打包
- **内置 WebSocket 客户端**
- **fs.glob()** (实验性)

## ESM 配置

```json
// package.json
{ "type": "module" }
```

```json
// tsconfig.json (TS 项目)
{
  "compilerOptions": {
    "target": "ES2025",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "verbatimModuleSyntax": true
  }
}
```

```typescript
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";

// ESM 中获取目录路径 (Node 21.2+)
const dir = import.meta.dirname;
const file = import.meta.filename;
```

## 文件操作 (fs/promises)

```typescript
import { readFile, writeFile, mkdir, readdir } from "node:fs/promises";

async function loadConfig(p: string): Promise<Config> {
  const content = await readFile(p, "utf-8");
  const data: unknown = JSON.parse(content);
  return ConfigSchema.parse(data);
}

async function saveData(p: string, data: unknown): Promise<void> {
  await mkdir(path.dirname(p), { recursive: true });
  await writeFile(p, JSON.stringify(data, null, 2), "utf-8");
}

async function* walkDir(dir: string): AsyncGenerator<string> {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) yield* walkDir(full);
    else yield full;
  }
}
```

## Native Fetch

```typescript
async function getUser(id: string): Promise<User> {
  const r = await fetch(`https://api.example.com/users/${id}`, {
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(5000),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);
  const data: unknown = await r.json();
  return UserSchema.parse(data);
}

// 高吞吐：undici 直连 + keepalive
import { request, Agent } from 'undici';
const agent = new Agent({ keepAliveTimeout: 60_000 });
```

## 流处理 (stream pipeline)

```typescript
import { createReadStream, createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";
import { Transform } from "node:stream";

async function processLargeFile(inPath: string, outPath: string): Promise<void> {
  const transform = new Transform({
    transform(chunk: Buffer, _enc, cb) {
      cb(null, chunk.toString("utf-8").toUpperCase());
    },
  });
  await pipeline(createReadStream(inPath), transform, createWriteStream(outPath));
}
```

## Worker Threads (CPU 密集)

```typescript
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";

function runWorker<T, R>(workerPath: string, data: T): Promise<R> {
  return new Promise((resolve, reject) => {
    const w = new Worker(workerPath, { workerData: data });
    w.on("message", resolve);
    w.on("error", reject);
    w.on("exit", (code) => {
      if (code !== 0) reject(new Error(`Worker exited ${code}`));
    });
  });
}

if (!isMainThread && parentPort) {
  parentPort.postMessage(heavyComputation(workerData));
}
```

## 环境变量 (Zod 强制)

```typescript
import { z } from "zod";

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  DATABASE_URL: z.url(),
  API_KEY: z.string().min(32),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
});

export const env = EnvSchema.parse(process.env);
```

## Hono 4 (推荐轻量 Web 框架)

```typescript
import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";

const app = new Hono();

app.get("/api/users/:id", async (c) => {
  const id = c.req.param("id");
  const user = await db.user.findUnique({ where: { id } });
  return user ? c.json(user) : c.json({ error: "Not found" }, 404);
});

app.post("/api/users", zValidator("json", CreateUserSchema), async (c) => {
  const data = c.req.valid("json");
  return c.json(await db.user.create({ data }), 201);
});

export default app;
```

替代：**Elysia** (Bun 原生) / **Fastify 5** (生态成熟) / **tRPC** (无 REST 类型契约) / **Express 5** (legacy)。

## Drizzle ORM (推荐 vs Prisma)

```typescript
import { drizzle } from "drizzle-orm/postgres-js";
import { eq } from "drizzle-orm";
import { users } from "./schema";

const db = drizzle(connectionString);

const user = await db.select().from(users).where(eq(users.id, id));
```

Drizzle = 零运行时、SQL-like、TypeScript-first；Prisma = 全功能但运行时引擎重；Kysely = query builder。

## JS-only 兜底

所有 Node API 在 JS 项目同样可用。env 校验、Hono、Drizzle 都支持纯 JS，去掉类型即可：

```js
import { z } from 'zod';
const EnvSchema = z.object({
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.url(),
});
export const env = EnvSchema.parse(process.env);
```

JSDoc + `jsconfig.json` (`checkJs: true`) 提供类型提示，详见 `typescript-core` JS 兜底章节。

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| `require()` | 用 ESM `import` | 高 |
| `fs.readFileSync` | 用 `fs/promises` | 中 |
| `node-fetch` 包 | Node 22+ 内置 fetch | 低 |
| CJS `__dirname` | 用 `import.meta.dirname` | 中 |
| 直接读 `process.env` | 必须 Zod 验证 | 高 |
| Express 4 新项目 | 考虑 Hono / Fastify | 中 |
| 无连接池 HTTP | undici Agent + keepalive | 中 |

## 检查清单

- [ ] `"type": "module"` + TS: `module: "NodeNext"`
- [ ] `node:` 前缀导入内置模块
- [ ] `fs/promises` (无 sync API)
- [ ] native fetch + `AbortSignal.timeout`
- [ ] env 走 Zod schema，启动时 fail-fast
- [ ] 大文件用 stream pipeline
- [ ] CPU 密集用 worker_threads
- [ ] 新项目优先 Hono / Fastify
- [ ] 锁文件提交 (`pnpm install --frozen-lockfile`)
