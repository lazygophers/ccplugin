---
name: security
description: JavaScript Web 安全规范：XSS 防护、CORS、输入验证。处理安全问题时必须加载。
---

# JavaScript Web 安全规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | ES2024-2025 标准、强制约定 |

## XSS 防护

```javascript
// ✅ 使用 DOMPurify
import DOMPurify from 'dompurify';

const clean = DOMPurify.sanitize(userInput);
element.innerHTML = clean;

// ✅ React 自动转义
<div>{userInput}</div>

// ❌ 危险
element.innerHTML = userInput;
```

## CORS 配置

```javascript
// Vite 代理配置
export default {
  server: {
    proxy: {
      '/api': {
        target: 'https://api.example.com',
        changeOrigin: true,
      }
    }
  }
}
```

## 输入验证

```javascript
// ✅ 验证用户输入
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
}

function validateInput(input) {
  if (typeof input !== 'string') return false;
  if (input.length > 1000) return false;
  return true;
}
```

## CSP 配置

```html
<meta http-equiv="Content-Security-Policy" content="
  default-src 'self';
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
">
```

## 检查清单

- [ ] 使用 DOMPurify 清理 HTML
- [ ] 配置 CORS
- [ ] 验证所有用户输入
- [ ] 配置 CSP
