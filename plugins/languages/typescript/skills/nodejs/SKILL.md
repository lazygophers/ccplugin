---
name: typescript-nodejs
description: TypeScript Node.js 后端开发规范，覆盖 Node.js 22 LTS 原生 strip-types、ESM 模块、原生 fetch、fs/promises、stream pipeline、worker_threads、Hono / Fastify 框架、env Zod 验证、Drizzle ORM。Use when 开发 Node.js 服务端、CLI 工具、API 服务，或用户提到 "Node.js"、"fastify"、"hono"、"ESM"、"worker thread"、"process.env"。
user-invocable: true
---

# TypeScript Node.js 后端规范

Node 22 LTS 起原生支持 strip-types（`node --experimental-strip-types` / 22.18+ 默认）；新项目可不依赖 tsc 直接 run。

## Node.js 22 LTS 新特性速览

- **Native strip-types** — `node file.ts` 直接运行（无类型检查）
- **Native fetch** — 全局可用，无 node-fetch
- **AbortSignal.timeout** — 内置超时
- **fs/promises** — 原生异步文件 API
- **node --test** — 内置 test runner（轻量场景）
- **Single executable apps** — 单文件可执行打包
- **内置 WebSocket 客户端**
- **fs.glob()**（实验性）

## ESM 配置

```json
// package.json
{ "type": "module" }
```

```json
// tsconfig.json
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

// ESM 中获取目录路径（Node 21.2+）
const dir = import.meta.dirname;
const file = import.meta.filename;
```

## 文件操作（fs/promises）

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
```

## 流处理（stream pipeline）

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

## Worker Threads

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

## 环境变量（Zod 强制）

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

## Hono（推荐轻量 Web 框架）

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

替代：**Elysia**（Bun 原生）/ **Fastify v5**（生态成熟）/ **tRPC**（无 REST 类型契约）。

## Drizzle ORM（推荐 vs Prisma）

```typescript
import { drizzle } from "drizzle-orm/postgres-js";
import { eq } from "drizzle-orm";
import { users } from "./schema";

const db = drizzle(connectionString);

const user = await db.select().from(users).where(eq(users.id, id));
```

Drizzle = 零运行时、SQL-like、TypeScript-first；Prisma = 全功能但运行时引擎重。

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| `require()` | 用 ESM `import` | 高 |
| `fs.readFileSync` | 用 `fs/promises` | 中 |
| `node-fetch` 包 | Node 22 内置 fetch | 低 |
| CJS `__dirname` | 用 `import.meta.dirname` | 中 |
| 直接读 `process.env` | 必须 Zod 验证 | 高 |
| Express（新项目） | 考虑 Hono / Fastify | 低 |

## 检查清单

- [ ] `"type": "module"` + `module: "NodeNext"`
- [ ] `node:` 前缀导入内置模块
- [ ] `fs/promises`（无 sync API）
- [ ] native fetch + `AbortSignal.timeout`
- [ ] env 走 Zod schema
- [ ] 大文件用 stream pipeline
- [ ] CPU 密集用 worker_threads
- [ ] 新项目优先 Hono / Fastify
