# Node.js 开发规范

## 核心原则

### ✅ 必须遵守

1. **Node.js 20+** - 使用最新的 LTS 版本
2. **ESM 优先** - 优先使用 ES Modules 而非 CommonJS
3. **异步优先** - 使用 async/await 而非回调
4. **类型安全** - 使用 TypeScript 严格模式
5. **错误处理** - 正确处理异步错误
6. **环境变量** - 使用 dotenv 管理配置

### ❌ 禁止行为

- 使用 CommonJS (`require`)
- 使用回调地狱
- 阻塞事件循环
- 同步文件操作（除非必要）
- 硬编码配置

## 模块系统

### ESM 配置

```jsonc
// package.json
{
  "type": "module",  // 启用 ESM
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "require": "./dist/index.cjs",
      "types": "./dist/index.d.ts"
    },
    "./package.json": "./package.json"
  }
}
```

```typescript
// ✅ 正确 - 使用 ES Modules
import express from 'express';
import { router } from './routes/index.js';

const app = express();
app.use(router);

// ❌ 错误 - 使用 CommonJS
const express = require('express');
const router = require('./routes');
```

### 文件扩展名

```typescript
// ✅ 正确 - 使用 .js 扩展名（运行时）
import { myFunction } from './utils.js';

// ✅ TypeScript 配置
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": false  // 不允许导入 .ts 文件
  }
}

// ⚠️ 开发时可以使用 .ts，但编译后需要 .js
// TypeScript 会在输出时自动处理
```

## Express 应用

### 基础设置

```typescript
// ✅ 正确 - Express + TypeScript
import express, { type Request, type Response, type NextFunction } from 'express';
import cors from 'cors';

const app = express();

// 中间件
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 错误处理中间件
interface ErrorWithStatus extends Error {
  status?: number;
}

app.use((err: ErrorWithStatus, req: Request, res: Response, next: NextFunction) => {
  console.error('error:', err);
  res.status(err.status || 500).json({
    error: {
      message: err.message,
      status: err.status || 500,
    },
  });
});

// 路由
app.get('/api/health', (req: Request, res: Response) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 启动服务器
const PORT = process.env.PORT ?? '3000';
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
```

### 路由组织

```typescript
// ✅ 正确 - 模块化路由
// routes/users/index.ts
import { Router } from 'express';
import { getUsers, getUserById, createUser, updateUser, deleteUser } from './handlers.js';

const router = Router();

router.get('/', getUsers);
router.get('/:id', getUserById);
router.post('/', createUser);
router.put('/:id', updateUser);
router.delete('/:id', deleteUser);

export { router };

// routes/index.ts
import { Router } from 'express';
import { userRoutes } from './users/index.js';
import { postRoutes } from './posts/index.js';

const router = Router();

router.use('/users', userRoutes);
router.use('/posts', postRoutes);

export { router };
```

### 控制器

```typescript
// ✅ 正确 - 控制器模式
// controllers/user.controller.ts
import { Request, Response, NextFunction } from 'express';
import { UserService } from '../services/user.service.js';

export class UserController {
  constructor(private readonly userService: UserService) {}

  async getAll(req: Request, res: Response, next: NextFunction) {
    try {
      const users = await this.userService.findAll();
      res.json(users);
    } catch (error) {
      next(error);
    }
  }

  async getById(req: Request, res: Response, next: NextFunction) {
    try {
      const { id } = req.params;
      const user = await this.userService.findById(id);
      if (!user) {
        return res.status(404).json({ error: 'User not found' });
      }
      res.json(user);
    } catch (error) {
      next(error);
    }
  }

  async create(req: Request, res: Response, next: NextFunction) {
    try {
      const input = CreateUserSchema.parse(req.body);
      const user = await this.userService.create(input);
      res.status(201).json(user);
    } catch (error) {
      next(error);
    }
  }
}
```

### 中间件

```typescript
// ✅ 正确 - 自定义中间件
import { Request, Response, NextFunction } from 'express';

// 日志中间件
export function logger(req: Request, res: Response, next: NextFunction) {
  const start = Date.now();
  res.on('finish', () => {
    const duration = Date.now() - start;
    console.log(`${req.method} ${req.path} ${res.statusCode} ${duration}ms`);
  });
  next();
}

// 认证中间件
export function authenticate(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const payload = verifyToken(token);
    req.user = payload;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// 错误处理中间件
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction,
) {
  console.error('error:', err);

  if (err instanceof ValidationError) {
    return res.status(400).json({
      error: {
        message: err.message,
        field: err.field,
      },
    });
  }

  if (err instanceof NotFoundError) {
    return res.status(404).json({
      error: {
        message: err.message,
      },
    });
  }

  res.status(500).json({
    error: {
      message: 'Internal server error',
    },
  });
}
```

## 文件操作

### 异步文件操作

```typescript
// ✅ 正确 - 使用 fs/promises
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';

async function readConfig(configPath: string) {
  try {
    const content = await readFile(configPath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error('error:', error);
    throw new Error(`Failed to read config: ${configPath}`);
  }
}

async function writeConfig(configPath: string, config: unknown) {
  try {
    const dir = join(process.cwd(), 'config');
    await mkdir(dir, { recursive: true });
    await writeFile(join(dir, configPath), JSON.stringify(config, null, 2));
  } catch (error) {
    console.error('error:', error);
    throw new Error(`Failed to write config: ${configPath}`);
  }
}

// ❌ 避免 - 同步文件操作（阻塞事件循环）
import { readFileSync } from 'node:fs';

function readConfigBad(configPath: string) {
  return JSON.parse(readFileSync(configPath, 'utf-8'));  // 阻塞！
}
```

### Stream 处理

```typescript
// ✅ 正确 - 使用 Stream 处理大文件
import { createReadStream, createWriteStream } from 'node:fs';
import { pipeline } from 'node:stream/promises';
import { createGzip } from 'node:zlib';

async function compressFile(inputPath: string, outputPath: string) {
  try {
    await pipeline(
      createReadStream(inputPath),
      createGzip(),
      createWriteStream(outputPath),
    );
    console.log(`Compressed ${inputPath} to ${outputPath}`);
  } catch (error) {
    console.error('error:', error);
    throw error;
  }
}

// ✅ 正确 - 处理上传文件
import formidable from 'formidable';
import { createWriteStream } from 'node:fs';

export async function uploadFile(req: Request, res: Response) {
  const form = formidable({
    uploadDir: '/tmp',
    keepExtensions: true,
  });

  try {
    const [fields, files] = await form.parse(req);
    const file = files.file?.[0];

    if (!file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    // 处理文件...
    res.json({ message: 'File uploaded', filename: file.originalFilename });
  } catch (error) {
    console.error('error:', error);
    res.status(500).json({ error: 'Upload failed' });
  }
}
```

## 环境变量

### 配置管理

```typescript
// ✅ 正确 - 使用 dotenv 和类型验证
import { config } from 'dotenv';
import { z } from 'zod';

// 加载 .env 文件
config();

// 定义环境变量 schema
const EnvSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().transform(Number).default(3000),
  DATABASE_URL: z.string(),
  REDIS_URL: z.string().optional(),
  JWT_SECRET: z.string().min(32),
  CORS_ORIGIN: z.string().url().default('http://localhost:3000'),
});

// 验证和解析环境变量
const env = EnvSchema.parse(process.env);

// 导出类型安全的配置
export const appConfig = {
  env: env.NODE_ENV,
  port: env.PORT,
  database: {
    url: env.DATABASE_URL,
  },
  redis: env.REDIS_URL ? {
    url: env.REDIS_URL,
  } : null,
  jwt: {
    secret: env.JWT_SECRET,
  },
  cors: {
    origin: env.CORS_ORIGIN,
  },
} as const;

export type AppConfig = typeof appConfig;
```

### .env.example

```bash
# .env.example
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-at-least-32-characters-long
CORS_ORIGIN=http://localhost:3000
```

## 日志

### 使用 Pino

```typescript
// ✅ 正确 - 使用 Pino 日志库
import pino from 'pino';

const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = pino({
  level: process.env.LOG_LEVEL ?? 'info',
  transport: isDevelopment
    ? {
        target: 'pino-pretty',
        options: {
          colorize: true,
          translateTime: 'HH:MM:ss Z',
          ignore: 'pid,hostname',
        },
      }
    : undefined,
});

// 使用
logger.info('Server starting');
logger.error({ err }, 'Database connection failed');
logger.debug({ userId }, 'User fetched');
```

## 数据库

### Prisma 配置

```typescript
// ✅ 正确 - 使用 Prisma
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as {
  prisma: PrismaClient | undefined;
};

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: process.env.NODE_ENV === 'development' ? ['query', 'error', 'warn'] : ['error'],
  });

if (process.env.NODE_ENV !== 'production') {
  globalForPrisma.prisma = prisma;
}

// 优雅关闭
process.on('beforeExit', async () => {
  await prisma.$disconnect();
});
```

## 检查清单

提交 Node.js 代码前，确保：

- [ ] 使用 Node.js 20+ LTS
- [ ] 使用 ESM 而非 CommonJS
- [ ] 使用 async/await 而非回调
- [ ] 没有阻塞事件循环的操作
- [ ] 环境变量有类型验证
- [ ] 错误处理完善
- [ ] 日志使用 Pino
- [ ] API 响应有一致的格式
- [ ] 文件操作使用异步版本
