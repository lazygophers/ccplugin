---
description: TypeScript Node.js 开发规范：Node.js 22 LTS、ESM、native fetch、fs/promises、native test runner。开发 Node.js 应用时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# TypeScript Node.js 开发规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | TypeScript 开发专家 |
| test  | TypeScript 测试专家 |
| perf  | TypeScript 性能优化专家 |

## 相关 Skills

| 场景     | Skill            | 说明                              |
| -------- | ---------------- | --------------------------------- |
| 核心规范 | Skills(core)     | TS 5.7+、strict mode              |
| 类型系统 | Skills(types)    | Zod schema、类型安全 API          |
| 异步编程 | Skills(async)    | Promise、streams、async iterators |
| 安全编码 | Skills(security) | 输入验证、依赖审计                |

## Node.js 22 LTS 新特性

- **Native fetch** - 全局可用，无需 node-fetch
- **fs/promises** - 原生异步文件 API
- **Native test runner** - `node --test`（轻量场景）
- **Single executable apps** - 打包为单文件可执行
- **WebSocket** - 内置 WebSocket 客户端
- **Glob API** - `fs.glob()`（实验性）

## ESM 模块配置

```json
// package.json
{ "type": "module" }
```

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2024",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "verbatimModuleSyntax": true
  }
}
```

```typescript
// ESM 导入
import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

// ESM 中获取 __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 或使用 import.meta.dirname (Node.js 21.2+)
const dir = import.meta.dirname;
```

## 文件操作（fs/promises）

```typescript
import { readFile, writeFile, mkdir, readdir, stat } from "node:fs/promises";

// 读取文件
async function loadConfig(configPath: string): Promise<Config> {
  const content = await readFile(configPath, "utf-8");
  const data: unknown = JSON.parse(content);
  return ConfigSchema.parse(data); // Zod 验证
}

// 写入文件（确保目录存在）
async function saveData(filePath: string, data: unknown): Promise<void> {
  await mkdir(path.dirname(filePath), { recursive: true });
  await writeFile(filePath, JSON.stringify(data, null, 2), "utf-8");
}

// 递归遍历目录
async function* walkDir(dir: string): AsyncGenerator<string> {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      yield* walkDir(fullPath);
    } else {
      yield fullPath;
    }
  }
}
```

## Native Fetch API

```typescript
// GET 请求
async function getUser(id: string): Promise<User> {
  const response = await fetch(`https://api.example.com/users/${id}`, {
    headers: { "Content-Type": "application/json" },
    signal: AbortSignal.timeout(5000), // Node.js 22 内置超时
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data: unknown = await response.json();
  return UserSchema.parse(data);
}

// POST 请求
async function createUser(user: CreateUserInput): Promise<User> {
  const response = await fetch("https://api.example.com/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(user),
  });
  if (!response.ok) {
    const error: unknown = await response.json();
    throw new Error(`Create failed: ${JSON.stringify(error)}`);
  }
  return UserSchema.parse(await response.json());
}
```

## 流处理

```typescript
import { createReadStream, createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";
import { Transform } from "node:stream";

// 大文件流处理
async function processLargeFile(inputPath: string, outputPath: string): Promise<void> {
  const transform = new Transform({
    transform(chunk: Buffer, _encoding, callback) {
      const processed = chunk.toString("utf-8").toUpperCase();
      callback(null, processed);
    },
  });

  await pipeline(
    createReadStream(inputPath, "utf-8"),
    transform,
    createWriteStream(outputPath),
  );
}

// 异步迭代器消费 stream
async function readLines(filePath: string): Promise<string[]> {
  const content = await readFile(filePath, "utf-8");
  return content.split("\n").filter(Boolean);
}
```

## Worker Threads

```typescript
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";

// 主线程
function runWorker<T, R>(workerPath: string, data: T): Promise<R> {
  return new Promise((resolve, reject) => {
    const worker = new Worker(workerPath, { workerData: data });
    worker.on("message", resolve);
    worker.on("error", reject);
    worker.on("exit", (code) => {
      if (code !== 0) reject(new Error(`Worker exited with code ${code}`));
    });
  });
}

// Worker 文件
if (!isMainThread && parentPort) {
  const result = heavyComputation(workerData);
  parentPort.postMessage(result);
}
```

## 环境变量（Zod 验证）

```typescript
import { z } from "zod";

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]).default("development"),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
  DATABASE_URL: z.string().url(),
  API_KEY: z.string().min(32),
  LOG_LEVEL: z.enum(["debug", "info", "warn", "error"]).default("info"),
});

export const env = EnvSchema.parse(process.env);
```

## Hono（轻量 Web 框架）

```typescript
import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";

const app = new Hono();

app.get("/api/users/:id", async (c) => {
  const id = c.req.param("id");
  const user = await db.user.findUnique({ where: { id } });
  if (!user) return c.json({ error: "Not found" }, 404);
  return c.json(user);
});

app.post("/api/users",
  zValidator("json", CreateUserSchema),
  async (c) => {
    const data = c.req.valid("json");
    const user = await db.user.create({ data });
    return c.json(user, 201);
  },
);

export default app;
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| `require()` 导入 | 应使用 ESM `import` | 高 |
| `fs.readFileSync` | 应使用 `fs/promises` | 中 |
| `node-fetch` 包 | Node.js 22 有 native fetch | 低 |
| `__dirname`（CJS） | ESM 中使用 `import.meta.dirname` | 中 |
| 无环境变量验证 | 应使用 Zod 验证 `process.env` | 高 |
| Express（新项目） | 考虑 Hono / Fastify 替代 | 低 |

## 检查清单

- [ ] `"type": "module"` 在 package.json
- [ ] `module: "NodeNext"` 在 tsconfig.json
- [ ] 使用 `node:` 前缀导入内置模块
- [ ] 使用 `fs/promises`（非 sync API）
- [ ] 使用 native fetch（非 node-fetch）
- [ ] 环境变量使用 Zod 验证
- [ ] 大文件使用 stream 处理
- [ ] CPU 密集任务使用 Worker Threads
