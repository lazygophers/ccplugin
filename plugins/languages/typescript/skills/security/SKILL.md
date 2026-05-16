---
name: typescript-security
description: TypeScript 安全编码规范，覆盖 Zod 输入验证、CSP 内容安全策略、XSS / CSRF 防护、DOMPurify HTML 清理、依赖审计（pnpm audit / socket.dev）、CORS 配置、敏感数据日志脱敏、速率限制。Use when 安全加固、漏洞修复、输入校验、安全审计，或用户提到 "security"、"XSS"、"CSP"、"input validation"、"audit"。
user-invocable: true
---

# TypeScript 安全编码规范

边界即防线：所有外部输入（HTTP body / query / headers / fs / env）必须 Zod 验证；所有渲染必须经清洗或 React 自动转义。

## 输入验证（Zod 4）

```typescript
import { z } from "zod";

const UserInputSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  email: z.email().toLowerCase(),
  age: z.number().int().min(0).max(150).optional(),
  bio: z.string().max(500).optional(),
});

function validate(input: unknown) {
  const r = UserInputSchema.safeParse(input);
  return r.success
    ? { ok: true as const, data: r.data }
    : { ok: false as const, errors: z.flattenError(r.error).fieldErrors };
}

// 环境变量（参考 nodejs skill）
const env = z.object({
  DATABASE_URL: z.url(),
  API_KEY: z.string().min(32),
}).parse(process.env);
```

## XSS 防护

```typescript
// React 自动转义（默认安全）
<div>{userInput}</div>

// 危险：永不做
// element.innerHTML = userInput;
// <div dangerouslySetInnerHTML={{ __html: userInput }} />  // 仅在 DOMPurify 后

// DOMPurify HTML 白名单清理
import DOMPurify from "dompurify";
const clean = DOMPurify.sanitize(userHtml, {
  ALLOWED_TAGS: ["b", "i", "em", "strong", "a"],
  ALLOWED_ATTR: ["href"],
});
```

## SQL 注入

```typescript
// ✅ 参数化查询（Drizzle / Prisma 默认安全）
await db.select().from(users).where(eq(users.email, input));

// ❌ 字符串拼接
// await db.execute(`SELECT * FROM users WHERE email = '${input}'`);
```

## CSP（Content Security Policy）

```typescript
// Next.js middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(_req: NextRequest) {
  const nonce = crypto.randomUUID();
  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}'`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: https:`,
    `connect-src 'self' https://api.example.com`,
    `frame-ancestors 'none'`,
  ].join("; ");

  const res = NextResponse.next();
  res.headers.set("Content-Security-Policy", csp);
  res.headers.set("X-Frame-Options", "DENY");
  res.headers.set("X-Content-Type-Options", "nosniff");
  res.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  return res;
}
```

## CORS

```typescript
import { cors } from "hono/cors";

app.use(cors({
  origin: ["https://myapp.com"],            // 禁 "*" 当 credentials: true
  allowMethods: ["GET", "POST", "PUT", "DELETE"],
  allowHeaders: ["Content-Type", "Authorization"],
  credentials: true,
  maxAge: 86400,
}));
```

## 敏感数据 / 日志脱敏

```typescript
// 禁硬编码
// const apiKey = "sk-xxx"; // 危险！

// 日志脱敏
const SENSITIVE = new Set(["password", "token", "apikey", "secret", "authorization", "cookie"]);

function sanitize<T extends Record<string, unknown>>(data: T): Partial<T> {
  return Object.fromEntries(
    Object.entries(data).map(([k, v]) =>
      SENSITIVE.has(k.toLowerCase()) ? [k, "***REDACTED***"] : [k, v],
    ),
  ) as Partial<T>;
}
```

## 依赖审计

```bash
pnpm audit                          # 全量
pnpm audit --audit-level=high
pnpm audit --fix

# CI 锁文件完整性
pnpm install --frozen-lockfile

# 供应链
npx socket-security/cli scan        # socket.dev
npx better-npm-audit audit          # 更严格

# Renovate / Dependabot 自动 PR
```

## 速率限制 / Brute-force

```typescript
import { rateLimiter } from "hono-rate-limiter";

app.use("/api/*", rateLimiter({
  windowMs: 60_000,
  limit: 100,
  standardHeaders: "draft-7",
  keyGenerator: (c) => c.req.header("x-forwarded-for") ?? "anon",
}));
```

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| 无输入验证 | 注入 / 类型不安全 | 高 |
| `innerHTML` / `dangerouslySetInnerHTML` 未清洗 | XSS | 高 |
| 硬编码密钥 | 凭证泄露 | 高 |
| 无 CSP | XSS 缺乏纵深防御 | 中 |
| `pnpm audit` 未跑 | 已知漏洞未修 | 中 |
| CORS `origin: "*"` + credentials | 跨域风险 | 高 |
| 日志输出原始 password / token | 数据泄露 | 高 |
| SQL 字符串拼接 | 注入 | 高 |

## 检查清单

- [ ] 所有外部输入 Zod 4 验证
- [ ] env 走 Zod schema
- [ ] 无 `innerHTML` / 未清洗 `dangerouslySetInnerHTML`
- [ ] DOMPurify 清理用户 HTML
- [ ] CSP + X-Frame-Options + nosniff 头
- [ ] `pnpm audit` 无 high/critical
- [ ] 锁文件 `--frozen-lockfile`
- [ ] 日志脱敏 sensitive 字段
- [ ] CORS 白名单 origin
- [ ] 速率限制公开 API
