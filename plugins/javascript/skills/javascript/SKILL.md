---
name: javascript-development
description: JavaScript 开发规范 - 涵盖现代 ES2024-2025 标准、异步编程、模块系统、工具链和最佳实践。基于官方标准和业界共识
auto-activate: always:true
---

# JavaScript 开发规范

## 概述

本规范提供现代 JavaScript（ES2024-2025）的完整开发指导，涵盖语言特性、编码规范、异步编程、工具链和框架集成。

## 版本和环境

- **JavaScript**：ES2024-2025（最新标准）
- **Node.js**：24 LTS（推荐）或 22 LTS
- **包管理器**：pnpm（推荐）→ Yarn → npm
- **构建工具**：Vite（推荐）
- **测试框架**：Vitest（优于 Jest）
- **代码检查**：ESLint 9+ + Prettier

## 部分 1: 现代 JavaScript 特性

### 1.1 ES2024-2025 关键新特性

**非变异数组方法**（ES2024）：
```javascript
// 不修改原数组
const sorted = arr.toSorted((a, b) => a - b);
const reversed = arr.toReversed();
const updated = arr.with(0, 'new'); // 替换指定索引
const spliced = arr.toSpliced(0, 1, 'new'); // 返回新数组
```

**Object.groupBy 和 Map.groupBy**（ES2024）：
```javascript
const grouped = Object.groupBy(users, u => u.role);
const mapGrouped = Map.groupBy(users, u => u.role);
```

**Promise.withResolvers()**（ES2024）：
```javascript
const { promise, resolve, reject } = Promise.withResolvers();
// 更清晰的 Promise 构造
```

**RegExp.escape()**（ES2025）：
```javascript
// 防止正则注入
const pattern = RegExp.escape(userInput);
```

**JSON 模块导入**（ES2025）：
```javascript
import data from './config.json' with { type: 'json' };
```

### 1.2 异步编程标准

**async/await 必须**：
```javascript
// ✅ 推荐：async/await
async function fetchData() {
  try {
    const response = await fetch('/api/data');
    return await response.json();
  } catch (error) {
    console.error('Error:', error);
  }
}

// ❌ 避免：回调地狱
fetch('/api/data', (err, data) => {
  if (err) console.error(err);
});
```

**Promise 并发控制**：
```javascript
// ✅ Promise.allSettled()：推荐
const results = await Promise.allSettled([
  fetchUser(), fetchPosts(), fetchComments()
]);

// ⚠️ Promise.all()：任一失败则失败
const results = await Promise.all([/* ... */]);

// Promise.race()：第一个完成即返回
const fastest = await Promise.race([/* ... */]);
```

### 1.3 ESM 模块系统

**导入导出规范**：
```javascript
// ✅ 具名导出（推荐）
export const getUserData = async (id) => { };
export const validateUser = (user) => { };

// ✅ 默认导出仅用于主要功能
export default class UserService { }

// ✅ type-only 导入（避免副作用）
import type { User } from './types.js';

// ✅ 动态导入
const lib = await import('./heavy-lib.js');

// ❌ 避免：多个默认导出用途
export default {
  getUser: async (id) => { },
  validateUser: (user) => { }
};
```

**package.json 配置**：
```json
{
  "type": "module",  // 强制使用 ESM
  "exports": {
    ".": "./dist/index.js",
    "./types": "./dist/types.js"
  }
}
```

## 部分 2: 编码规范

### 2.1 命名约定（强制）

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量/函数 | camelCase | `getUserData`, `isActive` |
| 类/构造函数 | PascalCase | `UserManager`, `HttpClient` |
| 常量 | UPPER_SNAKE_CASE | `MAX_TIMEOUT`, `API_KEY` |
| 布尔值 | is/has/can 前缀 | `isActive`, `hasChildren` |
| 文件名 | kebab-case | `user-service.js` |
| 私有属性 | # 或 _ 前缀 | `#privateField`, `_internal` |

**强制规则**：
```javascript
// ✅ 正确
const userName = 'John';
const isActive = true;
const MAX_RETRIES = 3;
function getUserData(id) { }

// ❌ 错误
const user_name = 'John';
const active = true; // 应使用 is 前缀
const maxRetries = 3; // 常量应使用大写
```

### 2.2 代码风格

**使用 const/let，禁止 var**：
```javascript
// ✅ 推荐
const immutable = 'value'; // 不会改变
let mutable = 0;           // 会改变

// ❌ 禁止
var oldStyle = 'avoid';
```

**ESLint + Prettier 配置**：
```javascript
// eslint.config.js (ESLint 9+ Flat Config)
import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    rules: {
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-var': 'error',
      'prefer-const': 'error'
    }
  }
];
```

```json
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2
}
```

### 2.3 错误处理

**具体错误类型**：
```javascript
// ✅ 推荐：自定义错误类
class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

// 使用
try {
  validateUser(data);
} catch (error) {
  if (error instanceof ValidationError) {
    handleValidationError(error);
  } else {
    throw error;
  }
}

// ❌ 避免：通用 Error
throw new Error('Something went wrong');
```

## 部分 3: 项目结构

### 3.1 功能驱动架构（推荐）

```
src/
├── features/
│   ├── auth/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── components/
│   │   └── types.js
│   ├── dashboard/
│   └── shared/
│       ├── hooks/
│       ├── services/
│       ├── components/
│       ├── utils/
│       ├── constants/
│       └── types.js
├── config/
├── middleware/
├── store/  (Pinia/Redux)
└── main.js
```

**好处**：高内聚、低耦合、易于扩展

### 3.2 文件命名

- **组件**：`Button.jsx`, `UserCard.jsx`（PascalCase）
- **工具**：`utils.js`, `validators.js`（camelCase）
- **样式**：`Button.css`, `Button.module.css`
- **测试**：`Button.test.js`, `Button.spec.js`

## 部分 4: 工具链配置

### 4.1 包管理器：pnpm

```bash
# 初始化
pnpm init

# 安装依赖
pnpm install
pnpm add lodash-es
pnpm add -D vite @vitejs/plugin-react

# 运行脚本
pnpm run dev
pnpm run build
pnpm run test
```

**优势**：
- 速度快 3-5 倍（相比 npm）
- 磁盘效率高（共享依赖）
- 严格依赖隔离

### 4.2 构建工具：Vite

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  },
  build: {
    target: 'ES2020',
    minify: 'terser'
  }
});
```

### 4.3 测试框架：Vitest

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'node',
    globals: true,
    coverage: {
      provider: 'v8',
      lines: 80,
      functions: 80
    }
  }
});
```

## 部分 5: 测试标准

### 5.1 单元测试

```javascript
import { describe, it, expect, beforeEach } from 'vitest';

describe('UserService', () => {
  let service;

  beforeEach(() => {
    service = new UserService();
  });

  it('should return user when found', async () => {
    const result = await service.getUserById('123');
    expect(result).toBeDefined();
    expect(result.id).toBe('123');
  });

  it('should handle errors gracefully', async () => {
    await expect(service.getUserById('invalid')).rejects.toThrow();
  });
});
```

### 5.2 覆盖率目标

- **语句覆盖**：80%+
- **分支覆盖**：75%+
- **函数覆盖**：80%+
- **关键路径**：100%

## 部分 6: 框架集成

### 6.1 React 19

```jsx
// ✅ 推荐：函数组件 + Hooks
export function UserCard({ userId }) {
  const [user, setUser] = React.useState(null);

  React.useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  return user ? <div>{user.name}</div> : <Loading />;
}
```

### 6.2 Vue 3 Composition API

```vue
<script setup>
import { ref, computed } from 'vue';

const count = ref(0);
const doubled = computed(() => count.value * 2);
</script>

<template>
  <div>
    <p>Count: {{ count }}, Doubled: {{ doubled }}</p>
    <button @click="count++">Increment</button>
  </div>
</template>
```

## 部分 7: 性能优化

### 7.1 编译/构建优化

- ✅ 使用代码分割（路由级别）
- ✅ Tree shaking（ESM）
- ✅ 延迟加载非关键资源
- ❌ 避免大型单一 bundle

### 7.2 运行时优化

- ✅ 使用虚拟滚动处理大列表
- ✅ 事件委托减少监听器
- ✅ 及时清理事件和计时器
- ❌ 避免内存泄漏

### 7.3 Core Web Vitals

- **LCP**（最大内容绘制）：< 2.5 秒
- **INP**（交互到下一绘制）：< 200 毫秒
- **CLS**（累积布局偏移）：< 0.1

## 部分 8: 安全最佳实践

### 8.1 防御 XSS

```javascript
// ✅ 推荐：框架自动转义
<div>{userInput}</div>

// ✅ 推荐：使用 DOMPurify
const cleanHTML = DOMPurify.sanitize(userInput);

// ❌ 避免：直接渲染 HTML
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

### 8.2 防御 CSRF

```javascript
// ✅ 推荐：使用 CSRF token
const token = document.querySelector('meta[name="csrf-token"]').content;

fetch('/api/action', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': token,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
});
```

### 8.3 输入验证

```javascript
// ✅ 推荐：始终验证输入
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function sanitizeInput(input) {
  return input
    .trim()
    .replace(/<script>/g, '')
    .slice(0, 1000); // 长度限制
}
```

## 部分 9: 常见反模式

| 反模式 | 问题 | 解决方案 |
|--------|------|---------|
| 回调地狱 | 代码嵌套深，难读 | 使用 async/await |
| 忘记 await | Promise 未解决 | 始终 await 异步操作 |
| 全局变量 | 状态难追踪 | 使用局部变量或模块导出 |
| 内存泄漏 | 资源未释放 | 及时清理事件和计时器 |
| 未处理错误 | 应用崩溃 | 使用 try-catch 和 .catch() |

## 部分 10: 快速检查清单

- [ ] 使用 const/let，禁止 var
- [ ] 使用 ESM（import/export）
- [ ] 使用 async/await 处理异步
- [ ] 所有 Promise 都有错误处理
- [ ] 命名遵循规范（camelCase, UPPER_SNAKE_CASE）
- [ ] 没有 console.log 在生产代码
- [ ] 测试覆盖率 80%+
- [ ] 没有内存泄漏
- [ ] 没有 XSS 或 CSRF 漏洞
- [ ] Bundle 大小合理（< 150KB gzipped）

## 工具版本参考（2024-2025）

- ESLint：9+（支持 Flat Config）
- Prettier：3+
- Vite：5+
- Node.js：24 LTS
- pnpm：8+
- Vitest：1+
