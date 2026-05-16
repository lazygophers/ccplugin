---
name: typescript-security
description: TypeScript / JavaScript Web 安全编码规范，覆盖 Zod 4 输入验证、CSP3 内容安全策略、Trusted Types、XSS / CSRF 防护、DOMPurify、SameSite cookie、CORS 配置、依赖审计 (pnpm audit / Socket / Snyk)、npm provenance、SubResource Integrity、Permissions Policy、敏感数据日志脱敏、速率限制。Use when 安全加固、漏洞修复、输入校验、安全审计、CSP 配置，或用户提到 "security"、"XSS"、"CSRF"、"CSP"、"CORS"、"input validation"、"audit"、"依赖漏洞"、"sanitize"、"innerHTML"。
user-invocable: true
---

# TypeScript / JavaScript Web 安全规范 (2026)

本 skill 同时覆盖 JavaScript 项目；示例以 TS 为主，JS 项目去掉类型即可。

边界即防线：所有外部输入 (HTTP body / query / headers / fs / env) 必须 Zod 验证；所有渲染必须经清洗或 React/Vue 自动转义。

## 配套 skills

- `typescript-core` — 工具链
- `typescript-async` — fetch 取消、AbortController

## 输入验证 (Zod 4)

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

// API 响应严格校验 (失败抛 ZodError)
async function fetchUser(id: string) {
  const r = await fetch(`/api/users/${id}`);
  return UserInputSchema.parse(await r.json());
}

// 环境变量启动时 fail-fast
const Env = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]),
  DATABASE_URL: z.url(),
  API_KEY: z.string().min(32),
});
export const env = Env.parse(process.env);
```

## XSS 防护

```typescript
// React 自动转义 (默认安全)
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

// React
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />

// Vue
<div v-html="DOMPurify.sanitize(html)" />

// 纯文本场景 (自动转义)
el.textContent = userInput;

// Trusted Types (Chrome / Edge) — 编译期拒绝裸字符串赋 innerHTML
// CSP: require-trusted-types-for 'script';
const policy = trustedTypes.createPolicy('safe', {
  createHTML: (s) => DOMPurify.sanitize(s),
});
el.innerHTML = policy.createHTML(userHtml);
```

## SQL 注入

```typescript
// ✅ 参数化查询 (Drizzle / Prisma 默认安全)
await db.select().from(users).where(eq(users.email, input));

// ❌ 字符串拼接
// await db.execute(`SELECT * FROM users WHERE email = '${input}'`);
```

## CSP3 (Content Security Policy)

```http
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'strict-dynamic' 'nonce-{random}';
  style-src 'self' 'nonce-{random}';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  frame-ancestors 'none';
  require-trusted-types-for 'script';
  upgrade-insecure-requests;
  report-to csp-endpoint;
```

```typescript
// Next.js middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(_req: NextRequest) {
  const nonce = crypto.randomUUID();
  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'strict-dynamic' 'nonce-${nonce}'`,
    `style-src 'self' 'nonce-${nonce}'`,
    `img-src 'self' data: https:`,
    `connect-src 'self' https://api.example.com`,
    `frame-ancestors 'none'`,
    `require-trusted-types-for 'script'`,
  ].join("; ");

  const res = NextResponse.next();
  res.headers.set("Content-Security-Policy", csp);
  res.headers.set("X-Frame-Options", "DENY");
  res.headers.set("X-Content-Type-Options", "nosniff");
  res.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  return res;
}
```

- 优先 nonce + `strict-dynamic` 而非 host 白名单
- 禁 `'unsafe-inline'` `'unsafe-eval'`
- 配套 `Report-To` / `report-uri` 收集违规

## CORS

```typescript
// Hono 4
import { cors } from "hono/cors";
app.use(cors({
  origin: ["https://myapp.com"],          // 禁 "*" 当 credentials: true
  allowMethods: ["GET", "POST", "PUT", "DELETE"],
  allowHeaders: ["Content-Type", "Authorization"],
  credentials: true,
  maxAge: 86400,
}));

// Express 5
import cors from 'cors';
app.use(cors({ origin: /\.example\.com$/, credentials: true }));

// Vite dev 代理 (绕开 CORS)
export default { server: { proxy: { '/api': { target: 'https://api.example.com', changeOrigin: true } } } };
```

- 禁 `Access-Control-Allow-Origin: *` + `credentials: true`
- 反射 Origin 必白名单校验

## Cookie 与 CSRF

```http
Set-Cookie: session=abc; HttpOnly; Secure; SameSite=Lax; Path=/
```

- 敏感操作: `SameSite=Strict` + double-submit token 或 `Origin`/`Sec-Fetch-Site` 校验
- 不把 token 放 localStorage / sessionStorage (XSS 可读)

## 敏感数据 / 日志脱敏

```typescript
// 禁硬编码 (const apiKey = "sk-xxx"; // 危险！)

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

## 依赖与供应链审计

```bash
pnpm audit --audit-level=high          # CI 卡 high+
pnpm audit --fix
pnpm dedupe                            # 减少重复版本

# 第三方
npx socket@latest scan                 # Socket.dev 行为级检测
npx snyk test                          # CVE 数据库
npx better-npm-audit audit             # 更严格

# 发布: npm provenance + sigstore (开箱即用)
# package.json: { "publishConfig": { "provenance": true } }
npm publish --provenance --access public

# 锁定: 仅信任锁文件
pnpm install --frozen-lockfile
```

## 其他

```typescript
// SubResource Integrity (CDN 脚本)
// <script src="https://cdn/lib.js" integrity="sha384-..." crossorigin="anonymous"></script>

// Permissions Policy (限关高危 API)
// Permissions-Policy: camera=(), microphone=(), geolocation=(self)

// URL 协议校验 (open redirect / javascript: 协议)
function safeUrl(input: string): string {
  const u = new URL(input, location.origin);
  if (!['http:', 'https:'].includes(u.protocol)) throw new Error('bad protocol');
  return u.toString();
}

// 禁 eval / new Function / setTimeout(string)
// 禁 prototype 污染: 对外 API 用 Object.create(null) 或 Map
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

## JS-only 兜底

所有规范在 JS 项目同样适用，去掉 TypeScript 类型注解即可。Zod、DOMPurify、CSP、CORS 都是运行时机制，不依赖 TS。

```js
import { z } from 'zod';
const Login = z.object({
  email: z.string().email('邮箱无效'),
  password: z.string().min(8, '至少 8 位'),
});
const r = Login.safeParse(form);
if (!r.success) return { errors: r.error.flatten().fieldErrors };
```

## Red Flags

| 现象 | 风险 | 严重 |
|------|------|------|
| 无输入验证 | 注入 / 类型不安全 | 高 |
| `innerHTML = userInput` | XSS | 高 |
| `dangerouslySetInnerHTML` / `v-html` 未清洗 | XSS | 高 |
| `eval` / `new Function(userInput)` | 代码注入 | 高 |
| 硬编码密钥 | 凭证泄露 | 高 |
| 无 CSP / `'unsafe-inline'` | XSS 防线失效 | 高 |
| `Access-Control-Allow-Origin: *` + credentials | 跨站请求伪造 | 高 |
| token 放 localStorage | 持久 XSS 风险 | 中 |
| 反射 Origin 无白名单 | CORS 绕过 | 高 |
| 日志输出原始 password / token | 数据泄露 | 高 |
| SQL 字符串拼接 | 注入 | 高 |
| `pnpm audit` 未跑 | 已知 CVE | 中 |
| 锁文件未提交 | 供应链漂移 | 中 |

## 检查清单

- [ ] 所有外部输入 Zod 4 验证
- [ ] env 走 Zod schema，启动 fail-fast
- [ ] 无 `innerHTML` / 未清洗 `dangerouslySetInnerHTML` / `v-html`
- [ ] DOMPurify 清理用户 HTML
- [ ] CSP3 配置 nonce + strict-dynamic，无 unsafe-*
- [ ] CORS 白名单 + credentials 隔离
- [ ] 敏感 token 只放 HttpOnly cookie
- [ ] CSRF: SameSite + Origin 校验
- [ ] CI: `pnpm audit --audit-level=high` 卡门
- [ ] CI: `pnpm install --frozen-lockfile`
- [ ] 发布开启 npm provenance
- [ ] 无 `eval` / `new Function` / 动态 `setTimeout(string)`
- [ ] 日志脱敏 sensitive 字段

## 参考

- OWASP Top 10 2025: <https://owasp.org/Top10/>
- MDN CSP: <https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP>
- Trusted Types: <https://web.dev/articles/trusted-types>
- Zod 4: <https://zod.dev>
- npm provenance: <https://docs.npmjs.com/generating-provenance-statements>
