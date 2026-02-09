# TypeScript 安全编码规范

## 核心原则

### ✅ 必须遵守

1. **验证所有输入** - 不信任任何用户输入
2. **运行时类型检查** - 使用 Zod 验证外部数据
3. **最小权限原则** - 代码只请求必需的权限
4. **敏感数据保护** - 密码、令牌必须加密存储
5. **定期更新依赖** - 修复已知漏洞
6. **安全响应头** - 设置正确的 HTTP 头

### ❌ 禁止行为

- 信任用户输入
- 直接拼接 SQL 查询
- 在日志中记录敏感信息
- 硬编码密钥和密码
- 使用不安全的随机数生成器
- 忽略安全警告

## 输入验证

### Zod 验证

```typescript
// ✅ 正确 - 使用 Zod 验证输入
import { z } from 'zod';

// 定义 schema
const UserRegistrationSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  name: z.string().min(2).max(100),
  age: z.number().int().min(0).max(150).optional(),
});

// 使用验证
function registerUser(input: unknown) {
  const result = UserRegistrationSchema.safeParse(input);

  if (!result.success) {
    // 格式化错误信息
    const errors = result.error.flatten();
    return {
      success: false,
      errors: errors.fieldErrors,
    };
  }

  // result.data 是类型安全的
  return createUser(result.data);
}

// Express 中间件
function validateBody<T extends z.ZodType>(schema: T) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);

    if (!result.success) {
      return res.status(400).json({
        error: 'Validation failed',
        details: result.error.flatten().fieldErrors,
      });
    }

    req.body = result.data;
    next();
  };
}

// 使用
app.post('/api/users', validateBody(UserRegistrationSchema), registerUserHandler);
```

### URL 验证

```typescript
// ✅ 正确 - 验证 URL 防止 SSRF
import { z } from 'zod';

const UrlSchema = z.string().url().refine(
  (url) => {
    const parsed = new URL(url);
    // 只允许 http/https
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return false;
    }
    // 防止访问内网
    const hostname = parsed.hostname;
    const blockedHosts = ['localhost', '127.0.0.1', '0.0.0.0'];
    return !blockedHosts.includes(hostname);
  },
  { message: 'Invalid URL or blocked hostname' },
);

async function fetchFromUrl(url: string) {
  const validUrl = UrlSchema.parse(url);
  const response = await fetch(validUrl);
  return response.json();
}
```

### 路径遍历防护

```typescript
// ✅ 正确 - 防止路径遍历攻击
import { join, normalize } from 'node:path';
import { existsSync } from 'node:fs';

const UPLOAD_DIR = join(process.cwd(), 'uploads');

function safeJoin(basePath: string, ...paths: string[]): string {
  const joinedPath = join(basePath, ...paths);
  const normalizedPath = normalize(joinedPath);

  // 确保解析后的路径仍然在基础目录内
  if (!normalizedPath.startsWith(basePath)) {
    throw new Error('Path traversal attempt detected');
  }

  return normalizedPath;
}

async function serveFile(filename: string) {
  const safePath = safeJoin(UPLOAD_DIR, filename);

  if (!existsSync(safePath)) {
    throw new Error('File not found');
  }

  return readFile(safePath);
}

// ❌ 错误 - 容易受到路径遍历攻击
function serveFileUnsafe(filename: string) {
  // 危险！filename 可能包含 ../../etc/passwd
  const path = join(UPLOAD_DIR, filename);
  return readFile(path);
}
```

## XSS 防护

### React 自动转义

```typescript
// ✅ React 默认转义 JSX 中的内容
function UserComponent({ name }: { name: string }) {
  // name 会被自动转义，即使用户输入 <script>alert('XSS')</script>
  return <div>Hello, {name}</div>;
}

// ⚠️ 使用 dangerouslySetInnerHTML 时要小心
function HtmlContent({ html }: { html: string }) {
  return (
    <div
      dangerouslySetInnerHTML={{
        __html: sanitizeHtml(html),  // 必须先清理
      }}
    />
  );
}
```

### 字符串清理

```typescript
// ✅ 正确 - HTML 转义
function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ✅ 使用 DOMPurify 清理 HTML
import DOMPurify from 'dompurify';

function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'u', 'a', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'title'],
  });
}
```

### JSON 安全输出

```typescript
// ✅ 正确 - 安全的 JSON 响应
function safeJsonResponse(data: unknown, res: Response) {
  // Express/Next.js 自动转义 JSON 输出
  return res.json(data);
}

// ✅ 排除敏感字段
function toPublicUser(user: User): PublicUser {
  const { password, ...publicUser } = user;
  return publicUser;
}
```

## SQL 注入防护

### 参数化查询

```typescript
// ✅ 正确 - 使用参数化查询
import { sql } from 'slonik';

async function getUserById(id: string): Promise<User | null> {
  return connection.oneMaybe<User>(
    sql`SELECT * FROM users WHERE id = ${id}`,
  );
}

async function findUsersByEmail(email: string): Promise<User[]> {
  return connection.many<User>(
    sql`SELECT * FROM users WHERE email = ${email}`,
  );
}

// ❌ 错误 - 字符串拼接（SQL 注入风险）
async function getUserByIdUnsafe(id: string): Promise<User> {
  // 危险！如果 id 是 "1 OR 1=1"，会返回所有用户
  return connection.one(
    sql`SELECT * FROM users WHERE id = '${id}'`,
  );
}
```

### ORM 使用

```typescript
// ✅ 正确 - 使用 Prisma ORM
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function getUserById(id: string): Promise<User | null> {
  return prisma.user.findUnique({
    where: { id },
  });
}

async function createUser(data: CreateUserInput): Promise<User> {
  return prisma.user.create({
    data,
  });
}

// ✅ 正确 - Prisma 自动防止 SQL 注入
async function findUsersByEmail(email: string): Promise<User[]> {
  return prisma.user.findMany({
    where: {
      email,  // Prisma 自动参数化
    },
  });
}
```

## 认证和授权

### 密码存储

```typescript
// ✅ 正确 - 使用 bcrypt 哈希密码
import bcrypt from 'bcrypt';

async function hashPassword(plainPassword: string): Promise<string> {
  const saltRounds = 10;
  return bcrypt.hash(plainPassword, saltRounds);
}

async function verifyPassword(
  plainPassword: string,
  hashedPassword: string,
): Promise<boolean> {
  return bcrypt.compare(plainPassword, hashedPassword);
}

// 使用
async function register(email: string, password: string) {
  const hashedPassword = await hashPassword(password);
  return createUser({
    email,
    hashedPassword,  // 永远不要存储明文密码
  });
}

async function login(email: string, password: string) {
  const user = await findUserByEmail(email);

  if (!user) {
    throw new Error('Invalid credentials');
  }

  const isValid = await verifyPassword(password, user.hashedPassword);

  if (!isValid) {
    throw new Error('Invalid credentials');
  }

  return user;
}

// ❌ 错误 - 存储明文密码
async function registerBad(email: string, password: string) {
  // 危险！永远不要存储明文密码
  return createUser({
    email,
    password,  // 不要这样做！
  });
}
```

### JWT 令牌

```typescript
// ✅ 正确 - JWT 令牌处理
import jwt from 'jsonwebtoken';
import { z } from 'zod';

const JWT_SECRET = process.env.JWT_SECRET!;
if (!JWT_SECRET || JWT_SECRET.length < 32) {
  throw new Error('JWT_SECRET must be at least 32 characters');
}

interface JwtPayload {
  userId: string;
  email: string;
}

function generateToken(payload: JwtPayload): string {
  return jwt.sign(payload, JWT_SECRET, {
    expiresIn: '1h',
    issuer: 'my-app',
    audience: 'my-app-users',
  });
}

function verifyToken(token: string): JwtPayload {
  try {
    return jwt.verify(token, JWT_SECRET, {
      issuer: 'my-app',
      audience: 'my-app-users',
    }) as JwtPayload;
  } catch (error) {
    throw new Error('Invalid token');
  }
}

// Express 中间件
function authenticate(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const token = authHeader.substring(7);

  try {
    const payload = verifyToken(token);
    req.user = payload;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}
```

## 敏感数据处理

### 环境变量

```typescript
// ✅ 正确 - 不在代码中硬编码敏感信息
import { config } from 'dotenv';

config();

// 从环境变量读取
const config = {
  database: {
    url: process.env.DATABASE_URL!,
  },
  jwt: {
    secret: process.env.JWT_SECRET!,
  },
  apiKeys: {
    stripe: process.env.STRIPE_API_KEY!,
  },
};

// ❌ 错误 - 硬编码敏感信息
const config = {
  database: {
    url: 'postgresql://user:password@localhost/db',  // 危险！
  },
  jwt: {
    secret: 'my-secret-key',  // 危险！
  },
};
```

### 日志过滤

```typescript
// ✅ 正确 - 日志时过滤敏感信息
import pino from 'pino';

const sensitiveKeys = ['password', 'token', 'apiKey', 'secret', 'creditCard'];

function sanitize(obj: unknown): unknown {
  if (typeof obj !== 'object' || obj === null) {
    return obj;
  }

  if (Array.isArray(obj)) {
    return obj.map(sanitize);
  }

  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(obj)) {
    const lowerKey = key.toLowerCase();
    if (sensitiveKeys.some(sensitive => lowerKey.includes(sensitive.toLowerCase()))) {
      result[key] = '[REDACTED]';
    } else {
      result[key] = sanitize(value);
    }
  }

  return result;
}

const logger = pino({
  serializers: {
    req: pino.stdSerializers.req,
    res: pino.stdSerializers.res,
    err: pino.stdSerializers.err,
    // 自定义序列化器
    user: (user) => sanitize(user),
  },
});

// 使用
logger.info({ user: { name: 'John', password: 'secret123' } }, 'User created');
// 输出: { user: { name: 'John', password: '[REDACTED]' } }
```

## CORS 配置

### 严格 CORS

```typescript
// ✅ 正确 - 严格的 CORS 配置
import cors from 'cors';

const allowedOrigins = [
  'https://example.com',
  'https://www.example.com',
];

app.use(cors({
  origin: (origin, callback) => {
    // 允许不带 origin 的请求（移动应用等）
    if (!origin) {
      return callback(null, true);
    }

    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  maxAge: 600,  // 10 分钟
}));

// ❌ 错误 - 过于宽松的 CORS
app.use(cors({
  origin: '*',  // 危险！允许所有来源
  credentials: true,
}));
```

## 安全响应头

### Helmet 配置

```typescript
// ✅ 正确 - 使用 Helmet 设置安全头
import helmet from 'helmet';

app.use(helmet());

// 自定义配置
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        scriptSrc: ["'self'"],
        imgSrc: ["'self'", 'data:', 'https:'],
        connectSrc: ["'self'"],
        fontSrc: ["'self'"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"],
      },
    },
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true,
    },
    noSniff: true,
    xssFilter: true,
  }),
);

// 添加额外的安全头
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=()');
  next();
});
```

## 依赖安全

### 定期审计

```bash
# ✅ 使用 npm audit 检查漏洞
npm audit

# ✅ 使用 pnpm audit
pnpm audit

# ✅ 使用 Snyk 检查漏洞
npx snyk test

# ✅ 使用 renovate 自动更新依赖
```

## 检查清单

提交代码前，确保：

- [ ] 所有用户输入都经过 Zod 验证
- [ ] SQL 查询使用参数化或 ORM
- [ ] 密码使用 bcrypt 哈希存储
- [ ] 日志中不包含敏感信息
- [ ] CORS 配置明确指定允许的域名
- [ ] 设置了安全响应头
- [ ] 环境变量不在代码中硬编码
- [ ] 运行 `pnpm audit` 检查依赖
- [ ] 敏感字段不暴露在 API 响应中
- [ ] 文件操作使用安全路径拼接
