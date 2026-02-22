---
name: nodejs
description: TypeScript Node.js 开发规范：Node.js 20+、ESM、性能优化。开发 Node.js 应用时必须加载。
---

# TypeScript Node.js 开发规范

## 相关 Skills

| 场景     | Skill         | 说明                 |
| -------- | ------------- | -------------------- |
| 核心规范 | Skills(core)  | TS 5.9+、严格模式    |
| 异步编程 | Skills(async) | async/await、Promise |

## ESM 模块

```typescript
// package.json
{
  "type": "module"
}

// tsconfig.json
{
  "compilerOptions": {
    "module": "NodeNext",
    "moduleResolution": "NodeNext"
  }
}

// 使用 ESM
import { readFile } from 'fs/promises';
import path from 'path';

const data = await readFile(path.join(__dirname, 'data.json'), 'utf-8');
```

## 错误处理

```typescript
// ✅ 正确
try {
	const data = await fs.readFile(path, "utf-8");
	return JSON.parse(data);
} catch (error) {
	console.error("error:", error);
	throw error;
}
```

## 性能优化

```typescript
// 流处理
import { createReadStream } from "fs";

async function processLargeFile(path: string) {
	const stream = createReadStream(path, "utf-8");
	for await (const chunk of stream) {
		await processChunk(chunk);
	}
}

// Worker Threads
import { Worker } from "worker_threads";

function runWorker<T>(data: T): Promise<T> {
	return new Promise((resolve, reject) => {
		const worker = new Worker("./worker.js", { workerData: data });
		worker.on("message", resolve);
		worker.on("error", reject);
	});
}
```

## 检查清单

- [ ] 使用 ESM 模块
- [ ] 使用 fs/promises
- [ ] 正确处理错误
- [ ] 大文件使用流处理
