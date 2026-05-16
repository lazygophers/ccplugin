---
name: javascript-security
description: |
  JavaScript Web 安全规范 (2026)：XSS 防护 (DOMPurify / Trusted Types),
  CSP3 内容安全策略, CORS 配置, Zod 4 / Valibot 运行时校验, SameSite cookie,
  CSRF 防护, npm/pnpm audit + Socket / Snyk 依赖审计, 供应链 (sigstore, npm provenance),
  SubResource Integrity, Permissions Policy。
  Use when reviewing security, hardening web apps, fixing XSS/CSRF/CORS issues,
  validating inputs, auditing dependencies. Triggers: "安全", "XSS", "CSRF",
  "CSP", "CORS", "依赖漏洞", "audit", "Zod 校验", "innerHTML", "sanitize".
context: fork
model: sonnet
---

# Web 安全规范 (2026)

## 配套

- `Skills(javascript:core)` — 工具链
- `Skills(javascript:async)` — fetch 取消, AbortController

## XSS 防护

```js
import DOMPurify from 'dompurify';

// 用户 HTML → 必经 sanitize
el.innerHTML = DOMPurify.sanitize(userHtml);

// 纯文本场景：textContent 自动转义
el.textContent = userInput;

// React 自动转义 {expr}, dangerouslySetInnerHTML 必 sanitize
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }} />

// Vue v-html 同理
<div v-html="DOMPurify.sanitize(html)" />

// Trusted Types (Chrome / Edge) — 编译期拒绝裸字符串赋 innerHTML
// CSP: require-trusted-types-for 'script';
const policy = trustedTypes.createPolicy('safe', {
  createHTML: (s) => DOMPurify.sanitize(s),
});
el.innerHTML = policy.createHTML(userHtml);
```

## Zod 4 运行时校验 (边界必做)

```js
import { z } from 'zod';

// API 响应
const User = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(['admin', 'user', 'guest']),
});

async function fetchUser(id) {
  const r = await fetch(`/api/users/${id}`);
  const data = await r.json();
  return User.parse(data);                  // 失败抛 ZodError
}

// 表单 — safeParse 返结构化错误
const Login = z.object({
  email: z.string().email('邮箱无效'),
  password: z.string().min(8, '至少 8 位'),
});
const r = Login.safeParse(form);
if (!r.success) return { errors: r.error.flatten().fieldErrors };

// 环境变量 — 启动时 fail-fast
const Env = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']),
  API_URL: z.url(),
  API_KEY: z.string().min(20),
});
export const env = Env.parse(process.env);
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

- 优先 nonce + `strict-dynamic` 而非 host 白名单
- 禁 `'unsafe-inline'` `'unsafe-eval'`
- 配套 `Report-To` / `report-uri` 收集违规

## CORS

```js
// Hono 4
import { cors } from 'hono/cors';
app.use('/api/*', cors({
  origin: ['https://app.example.com'],
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE'],
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

```js
// Cookie 三件套
Set-Cookie: session=abc; HttpOnly; Secure; SameSite=Lax; Path=/

// 敏感操作: SameSite=Strict + double-submit token 或 Origin/Sec-Fetch-Site 校验
// 不把 token 放 localStorage / sessionStorage (XSS 可读)
```

## 依赖与供应链审计

```bash
pnpm audit --audit-level=high          # CI 卡 high+
pnpm audit --fix
pnpm dedupe                            # 减少重复版本

# 第三方
npx socket@latest scan                 # Socket.dev 行为级检测
npx snyk test                          # CVE 数据库

# 发布: npm provenance + sigstore (开箱即用)
# package.json: { "publishConfig": { "provenance": true } }
npm publish --provenance --access public

# 锁定: 仅信任锁文件 (CI: pnpm install --frozen-lockfile)
```

## 其他

```js
// SubResource Integrity (CDN 脚本)
<script src="https://cdn/lib.js"
        integrity="sha384-..."
        crossorigin="anonymous"></script>

// Permissions Policy (限关高危 API)
// Permissions-Policy: camera=(), microphone=(), geolocation=(self)

// URL 协议校验 (open redirect / javascript: 协议)
function safeUrl(input) {
  const u = new URL(input, location.origin);
  if (!['http:', 'https:'].includes(u.protocol)) throw new Error('bad protocol');
  return u.toString();
}

// 禁 eval / new Function / setTimeout(string)
// 禁 prototype 污染: 对外 API 用 Object.create(null) 或 Map
```

## Red Flags

| 现象 | 风险 | 严重 |
|------|------|------|
| `innerHTML = userInput` | XSS | 高 |
| `JSON.parse(localStorage.token)` 含敏感 | XSS 偷 token | 高 |
| `eval` / `new Function(userInput)` | 代码注入 | 高 |
| `Access-Control-Allow-Origin: *` + 凭据 | 跨站请求伪造 | 高 |
| `'unsafe-inline'` 在 CSP | XSS 防线失效 | 高 |
| 无 Zod 校验 API/表单 | 数据污染下游 | 高 |
| 锁文件未提交 | 供应链漂移 | 中 |
| `npm install package` 无 audit | 已知 CVE | 中 |
| token 放 localStorage | 持久 XSS 风险 | 中 |
| 反射 Origin 无白名单 | CORS 绕过 | 高 |

## 检查清单

- [ ] 任何用户 HTML 经 DOMPurify
- [ ] 边界 (API / 表单 / env) 用 Zod
- [ ] CSP3 配置 nonce + strict-dynamic, 无 unsafe-*
- [ ] CORS 白名单 + credentials 隔离
- [ ] 敏感 token 只放 HttpOnly cookie
- [ ] CSRF: SameSite + Origin 校验
- [ ] CI: `pnpm audit --audit-level=high` 卡门
- [ ] CI: `pnpm install --frozen-lockfile`
- [ ] 发布开启 npm provenance
- [ ] 无 `eval` / `new Function` / 动态 `setTimeout(string)`

## 参考

- OWASP Top 10 2025: <https://owasp.org/Top10/>
- MDN CSP: <https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP>
- Trusted Types: <https://web.dev/articles/trusted-types>
- Zod 4: <https://zod.dev>
- npm provenance: <https://docs.npmjs.com/generating-provenance-statements>
