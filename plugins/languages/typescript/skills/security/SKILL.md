---
description: TypeScript 安全编码规范：CSP、Zod 输入验证、XSS 防护、依赖审计。处理安全问题时必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# TypeScript 安全编码规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | TypeScript 开发专家 |
| debug | TypeScript 调试专家 |

## 相关 Skills

| 场景     | Skill         | 说明                         |
| -------- | ------------- | ---------------------------- |
| 核心规范 | Skills(core)  | TS 5.7+、strict mode         |
| 类型系统 | Skills(types) | Zod schema、类型安全验证     |
| 异步编程 | Skills(async) | 超时控制、AbortController    |
| Node.js  | Skills(nodejs)| Node.js 22 安全特性          |

## 输入验证（Zod）

```typescript
import { z } from "zod";

// 严格的输入 schema
const UserInputSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  email: z.string().email().toLowerCase(),
  age: z.number().int().min(0).max(150).optional(),
  bio: z.string().max(500).optional(),
});

// 安全解析（不抛异常）
function validateInput(input: unknown) {
  const result = UserInputSchema.safeParse(input);
  if (!result.success) {
    return { ok: false as const, errors: result.error.flatten().fieldErrors };
  }
  return { ok: true as const, data: result.data };
}

// 环境变量验证
const EnvSchema = z.object({
  DATABASE_URL: z.string().url(),
  API_KEY: z.string().min(32),
  NODE_ENV: z.enum(["development", "production", "test"]),
  PORT: z.coerce.number().int().min(1).max(65535).default(3000),
});

const env = EnvSchema.parse(process.env);
```

## XSS 防护

```typescript
// DOMPurify - HTML 清理
import DOMPurify from "dompurify";
const clean = DOMPurify.sanitize(userInput, { ALLOWED_TAGS: ["b", "i", "em"] });

// React 自动转义（安全）
<div>{userInput}</div>

// 危险：永远不要这样做
// element.innerHTML = userInput;
// dangerouslySetInnerHTML={{ __html: userInput }}  // 仅在 DOMPurify 后使用

// 模板字面量注入防护
function safeSQL(strings: TemplateStringsArray, ...values: unknown[]) {
  return strings.reduce((acc, str, i) =>
    acc + str + (i < values.length ? escapeSQL(String(values[i])) : ""), ""
  );
}
```

## Content Security Policy (CSP)

```typescript
// Next.js middleware CSP
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const nonce = crypto.randomUUID();
  const csp = [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}'`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: https:`,
    `connect-src 'self' https://api.example.com`,
  ].join("; ");

  const response = NextResponse.next();
  response.headers.set("Content-Security-Policy", csp);
  return response;
}
```

## 敏感数据处理

```typescript
// 环境变量（必须通过 Zod 验证）
const apiKey = env.API_KEY; // 已验证

// 禁止硬编码
// const apiKey = "sk-xxx"; // 危险！

// 日志脱敏
function sanitizeForLog<T extends Record<string, unknown>>(data: T): Partial<T> {
  const sensitiveKeys = new Set(["password", "token", "apiKey", "secret", "authorization"]);
  return Object.fromEntries(
    Object.entries(data).map(([k, v]) =>
      sensitiveKeys.has(k.toLowerCase()) ? [k, "***REDACTED***"] : [k, v]
    ),
  ) as Partial<T>;
}

// Zod 转换：自动脱敏
const LogSafeUserSchema = UserSchema.transform(({ password, ...rest }) => rest);
```

## 依赖审计

```bash
# pnpm 审计
pnpm audit
pnpm audit --fix

# npm audit（如果使用 npm）
npm audit --audit-level=high

# Socket.dev（供应链攻击检测）
npx socket-security/cli scan

# 锁文件完整性
pnpm install --frozen-lockfile  # CI 中使用
```

## CORS 配置

```typescript
// Express/Hono CORS
import { cors } from "hono/cors";

app.use(cors({
  origin: ["https://myapp.com"],
  allowMethods: ["GET", "POST", "PUT", "DELETE"],
  allowHeaders: ["Content-Type", "Authorization"],
  credentials: true,
}));
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| 无输入验证 | 注入攻击、类型不安全 | 高 |
| `innerHTML` / `dangerouslySetInnerHTML` | XSS 漏洞 | 高 |
| 硬编码密钥 | 凭证泄露 | 高 |
| 无 CSP 头 | 跨站脚本攻击 | 中 |
| `pnpm audit` 未运行 | 已知漏洞未修复 | 中 |
| CORS `origin: *` | 过于宽松的跨域策略 | 中 |

## 检查清单

- [ ] 所有外部输入使用 Zod 验证
- [ ] 环境变量使用 Zod schema 验证
- [ ] 无 `innerHTML` / 未清理的 `dangerouslySetInnerHTML`
- [ ] 使用 DOMPurify 清理 HTML
- [ ] CSP 头配置正确
- [ ] `pnpm audit` 无高危漏洞
- [ ] 敏感数据使用环境变量
- [ ] 日志输出已脱敏
