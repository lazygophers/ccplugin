---
description: "JavaScript Web安全规范：XSS跨站脚本防护、CSP内容安全策略、CORS跨域配置、Zod运行时输入验证、npm依赖安全审计。处理安全漏洞修复、输入校验、权限控制、安全加固时加载。"
user-invocable: true
context: fork
model: sonnet
memory: project
---

# JavaScript Web 安全规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | JavaScript 开发专家 |
| debug | JavaScript 调试专家 |

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(javascript:core) | ES2024-2025 标准、ESM、工具链 |
| 异步编程 | Skills(javascript:async) | async/await、AbortController |

## XSS 防护

```javascript
// DOMPurify 清理 HTML（必须用于任何用户输入的 HTML）
import DOMPurify from 'dompurify';

const clean = DOMPurify.sanitize(userInput);
element.innerHTML = clean;

// textContent 替代 innerHTML（纯文本场景）
element.textContent = userInput; // 自动转义

// React 自动转义（安全）
<div>{userInput}</div>

// React dangerouslySetInnerHTML（必须先清理）
<div dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(userInput) }} />

// 禁止：直接设置用户输入
element.innerHTML = userInput; // XSS 漏洞
```

## Zod 运行时验证

```javascript
import { z } from 'zod';

// API 响应验证
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'user', 'guest']),
});

async function fetchUser(id) {
  const response = await fetch(`/api/users/${id}`);
  const data = await response.json();
  return UserSchema.parse(data); // 运行时验证，无效数据抛出异常
}

// 表单输入验证
const LoginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'At least 8 characters'),
});

function handleSubmit(formData) {
  const result = LoginSchema.safeParse(formData);
  if (!result.success) {
    return { errors: result.error.flatten().fieldErrors };
  }
  return login(result.data);
}

// 环境变量验证
const EnvSchema = z.object({
  API_URL: z.string().url(),
  API_KEY: z.string().min(1),
  NODE_ENV: z.enum(['development', 'production', 'test']),
});

const env = EnvSchema.parse(process.env);
```

## CSP（Content Security Policy）

```javascript
// HTTP 头配置（推荐）
// Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;

// Meta 标签配置
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  font-src 'self' https://fonts.gstatic.com;
">

// Vite 开发服务器 CSP
// vite.config.js
export default {
  server: {
    headers: {
      'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-eval';"
    }
  }
};
```

## CORS 配置

```javascript
// Vite 代理（开发环境）
export default {
  server: {
    proxy: {
      '/api': {
        target: 'https://api.example.com',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      }
    }
  }
};

// Express CORS 配置（生产环境）
import cors from 'cors';

app.use(cors({
  origin: ['https://example.com', 'https://app.example.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true,
  maxAge: 86400, // 预检请求缓存 24h
}));
```

## 依赖安全审计

```bash
# pnpm 安全审计
pnpm audit
pnpm audit --fix

# npm 安全审计
npm audit
npm audit fix

# 自动化：CI 中集成审计
# .github/workflows/audit.yml
# - run: pnpm audit --audit-level=high
```

## 其他安全实践

```javascript
// CSRF 防护：SameSite Cookie
document.cookie = 'session=abc; SameSite=Strict; Secure; HttpOnly';

// 敏感数据不存 localStorage
// 使用 httpOnly cookie 存储 token

// URL 参数验证
const url = new URL(userProvidedUrl);
if (!['http:', 'https:'].includes(url.protocol)) {
  throw new Error('Invalid protocol');
}

// 避免 eval 和 Function 构造器
// eval(userInput); // 禁止
// new Function(userInput); // 禁止
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| `innerHTML = userInput` | XSS 漏洞 | 高 |
| 无 Zod 验证 API 响应 | 不可信数据直接使用 | 高 |
| 无 CSP 头 | 缺少内容安全策略 | 中 |
| `eval()` / `new Function()` | 代码注入风险 | 高 |
| token 存 localStorage | 应使用 httpOnly cookie | 中 |
| 无 CORS 限制 | `origin: '*'` 允许任意来源 | 中 |
| 无依赖审计 | 可能包含已知漏洞 | 中 |

## 检查清单

- [ ] 使用 DOMPurify 清理所有用户提供的 HTML
- [ ] Zod 验证 API 响应、表单输入、环境变量
- [ ] 配置 CSP 头限制资源加载
- [ ] 配置 CORS 限制跨域请求来源
- [ ] 无 `eval()` 或 `new Function()`
- [ ] 敏感数据使用 httpOnly cookie
- [ ] CI 集成 `pnpm audit` 依赖审计
- [ ] URL 参数验证 protocol
