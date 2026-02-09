# Web 安全编码规范

## 核心原则

### 必须遵守

1. **永远验证输入** - 不信任任何用户输入
2. **输出编码** - 对输出到页面的数据进行编码
3. **使用 CSP** - 配置内容安全策略
4. **HTTPS 优先** - 使用 HTTPS 传输敏感数据
5. **最小权限** - 请求和存储最少必要的数据

### 禁止行为

- 直接将用户输入插入 DOM
- 使用 `innerHTML` 处理用户数据
- 在 URL 中传递敏感信息
- 使用 eval() 处理用户数据
- 忽略 CORS 安全限制

## XSS 防护

### 输入验证

```javascript
// ✅ 正确 - 使用 DOMPurify 清理 HTML
import DOMPurify from 'dompurify';

function sanitizeHTML(html) {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'b', 'i', 'u', 'a', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'title'],
  });
}

// 使用
const userInput = '<script>alert("XSS")</script><p>Hello</p>';
const cleanHTML = sanitizeHTML(userInput);
// 结果: <p>Hello</p>

// ❌ 错误 - 直接使用用户输入
function renderHTML(html) {
  document.getElementById('content').innerHTML = html;  // 危险！
}
```

### React 中的 XSS

```jsx
// ✅ 正确 - React 自动转义
function UserComment({ comment }) {
  // React 默认转义，XSS 会被阻止
  return <div>{comment.text}</div>;
}

// ❌ 错误 - dangerouslySetInnerHTML
function UserComment({ comment }) {
  // 危险！除非是已清理的 HTML
  return <div dangerouslySetInnerHTML={{ __html: comment.text }} />;
}

// ✅ 正确 - 结合 DOMPurify 使用
import DOMPurify from 'dompurify';

function UserComment({ comment }) {
  const cleanHTML = DOMPurify.sanitize(comment.text, {
    ALLOWED_TAGS: ['p', 'br', 'b', 'i'],
  });
  return <div dangerouslySetInnerHTML={{ __html: cleanHTML }} />;
}
```

### Vue 中的 XSS

```vue
<template>
  <!-- ✅ 正确 - Mustache 语法自动转义 -->
  <div>{{ userInput }}</div>

  <!-- ❌ 错误 - v-html 不转义 -->
  <div v-html="userInput"></div>  <!-- 危险！ -->

  <!-- ✅ 正确 - 先清理再使用 v-html -->
  <div v-html="sanitizedInput"></div>
</template>

<script setup>
import { computed } from 'vue';
import DOMPurify from 'dompurify';

const props = defineProps({
  userInput: String,
});

const sanitizedInput = computed(() => {
  return DOMPurify.sanitize(props.userInput, {
    ALLOWED_TAGS: ['p', 'br', 'b', 'i'],
  });
});
</script>
```

## URL 安全

### 路径遍历防护

```javascript
// ✅ 正确 - 验证路径
function safeJoin(basePath, userPath) {
  // 规范化路径
  const normalizedPath = userPath.replace(/[^a-zA-Z0-9-_]/g, '');

  // 检查是否尝试遍历
  if (normalizedPath.includes('..')) {
    throw new Error('Invalid path');
  }

  // 确保结果在基础路径内
  const fullPath = new URL(normalizedPath, basePath);
  if (!fullPath.href.startsWith(basePath)) {
    throw new Error('Path traversal detected');
  }

  return fullPath.href;
}

// ❌ 错误 - 不验证路径
function readFile(userPath) {
  const path = '/app/files/' + userPath;  // 危险！可能是 ../../../etc/passwd
  return fetch(path);
}
```

### Query 参数处理

```javascript
// ✅ 正确 - 使用 URLSearchParams
function getQueryParams(url) {
  const params = new URLSearchParams(url.search);
  return {
    query: params.get('q') || '',
    page: parseInt(params.get('page') || '1', 10),
    limit: Math.min(parseInt(params.get('limit') || '10', 10), 100),  // 限制最大值
  };
}

// ❌ 错误 - 直接使用 query 参数
function search(url) {
  const query = url.searchParams.get('q');
  // 直接插入 SQL - SQL 注入风险
  return fetch(`/api/search?q=${query}`);
}
```

## CSRF 防护

### CSRF Token

```javascript
// ✅ 正确 - 使用 CSRF Token
async function makeRequest(url, data) {
  // 从 meta 标签获取 CSRF token
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken,
    },
    body: JSON.stringify(data),
    credentials: 'same-origin',  // 包含 cookie
  });

  return response.json();
}

// ✅ 正确 - 双重 Cookie 验证
async function makeRequestWithDoubleSubmit(url, data) {
  const csrfToken = getCookie('csrf_token');

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken,  // Header 中发送
    },
    body: JSON.stringify({
      ...data,
      csrf_token: csrfToken,  // Body 中也发送
    }),
  });

  return response.json();
}
```

### SameSite Cookie

```javascript
// 服务端设置 SameSite Cookie
// Set-Cookie: sessionId=xxx; SameSite=Strict; Secure; HttpOnly

// 前端确保请求携带凭证
fetch('/api/data', {
  credentials: 'same-origin',  // 或 'include' 跨域
});
```

## 内容安全策略（CSP）

### CSP Header

```javascript
// 服务端设置 CSP Header
// Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'

// 前端使用 CSP meta 标签
/*
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdn.example.com;
  style-src 'self' 'unsafe-inline' https://cdn.example.com;
  img-src 'self' data: https:;
  connect-src 'self' https://api.example.com;
  font-src 'self' https://cdn.example.com;
  object-src 'none';
  base-uri 'self';
  form-action 'self';
">
*/
```

### CSP 报告

```javascript
// 使用 report-uri 监控违规
// Content-Security-Policy: default-src 'self'; report-uri /csp-report

// 前端报告 CSP 违规
window.addEventListener('securitypolicyviolation', (event) => {
  console.error('CSP Violation:', {
    violatedDirective: event.violatedDirective,
    blockedURI: event.blockedURI,
    originalPolicy: event.originalPolicy,
  });

  // 发送到监控服务
  sendToMonitoring({
    type: 'csp_violation',
    data: {
      directive: event.violatedDirective,
      uri: event.blockedURI,
    },
  });
});
```

## CORS 配置

### CORS Header

```javascript
// ✅ 正确 - 严格的 CORS 配置
// 服务端设置
/*
Access-Control-Allow-Origin: https://example.com  // 具体域名，不要用 *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
*/

// 前端请求
fetch('https://api.example.com/data', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include',  // 携带凭证
});
```

### 预检请求

```javascript
// 浏览器自动发送 OPTIONS 预检请求
// 可以缓存预检结果

fetch('https://api.example.com/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Custom-Header': 'value',  // 触发预检
  },
  body: JSON.stringify({ data: 'value' }),
});
```

## 敏感数据处理

### Token 存储

```javascript
// ✅ 正确 - 使用 httpOnly cookie 存储 token
// 服务端设置: Set-Cookie: token=xxx; HttpOnly; Secure; SameSite=Strict

// ❌ 错误 - 使用 localStorage 存储 token
localStorage.setItem('token', token);  // 容易受到 XSS 攻击

// ✅ 正确 - 使用内存存储（SPA）
let authToken = null;

function login(credentials) {
  return fetch('/api/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
    credentials: 'include',  // 使用 cookie
  }).then(res => res.json());
}

// ✅ 正确 - 如果必须使用 token，使用短期 token + 刷新机制
const authState = {
  accessToken: null,  // 短期（如 15 分钟）
  refreshToken: null, // 长期（如 7 天）
};

// 自动刷新 token
async function refreshAccessToken() {
  const response = await fetch('/api/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authState.refreshToken}`,
    },
  });

  if (response.ok) {
    const { accessToken } = await response.json();
    authState.accessToken = accessToken;
  } else {
    // 刷新失败，重新登录
    logout();
  }
}
```

### 日志安全

```javascript
// ✅ 正确 - 过滤敏感信息
function sanitizeForLogging(data) {
  const sensitiveKeys = ['password', 'token', 'secret', 'apiKey', 'ssn'];
  const result = { ...data };

  for (const key of sensitiveKeys) {
    if (result[key]) {
      result[key] = '[REDACTED]';
    }
  }

  return result;
}

// 使用
console.log('User data:', sanitizeForLogging(userData));

// ❌ 错误 - 记录敏感信息
console.log('Login data:', { username, password });  // 危险！
```

## 输入验证

```javascript
// ✅ 正确 - 使用 Zod 进行验证
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  age: z.number().min(0).max(150).optional(),
});

function validateUser(data) {
  return UserSchema.parse(data);
}

// 使用
try {
  const validUser = validateUser(userData);
  // 使用验证后的数据
} catch (error) {
  console.error('Validation error:', error.errors);
}

// ✅ 正确 - URL 验证
function isValidURL(url) {
  try {
    const parsed = new URL(url);
    // 只允许 HTTP/HTTPS
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

// ✅ 正确 - 文件类型验证
function validateFile(file) {
  // 检查文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Invalid file type');
  }

  // 检查文件大小（如 5MB）
  const maxSize = 5 * 1024 * 1024;
  if (file.size > maxSize) {
    throw new Error('File too large');
  }

  // 检查文件扩展名
  const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif'];
  const extension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
  if (!allowedExtensions.includes(extension)) {
    throw new Error('Invalid file extension');
  }

  return true;
}
```

## 检查清单

提交代码前，确保：

- [ ] 所有用户输入都经过验证
- [ ] HTML 输出使用 DOMPurify 清理
- [ ] 不使用 `eval()` 或 `new Function()`
- [ ] 不使用 `innerHTML` 处理用户数据
- [ ] URL 参数经过验证和编码
- [ ] 敏感数据不在 URL 中传递
- [ ] Token 存储在 httpOnly cookie
- [ ] 配置了 CSP Header
- [ ] CORS 配置明确指定允许的域名
- [ ] 日志中不包含敏感信息
