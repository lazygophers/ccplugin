---
name: core
description: JavaScript 核心规范：ES2024-2025 标准、ESM 模块、const/let、命名约定、Vite 6、ESLint 9 flat config。写任何 JavaScript 代码前必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# JavaScript 开发核心规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | JavaScript 开发专家 |
| debug | JavaScript 调试专家 |
| test  | JavaScript 测试专家 |
| perf  | JavaScript 性能优化专家 |

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 异步编程 | Skills(javascript:async) | async/await、Promise、AbortController |
| React 开发 | Skills(javascript:react) | React 19、Server Components、Next.js 15 |
| Vue 开发 | Skills(javascript:vue) | Vue 3.5、Composition API、Nuxt 4 |
| Web 安全 | Skills(javascript:security) | XSS 防护、CSP、Zod 验证 |

## 核心原则

JavaScript 生态追求**高性能、组件化、ESM 原生、运行时验证**。

### 必须遵守

1. **const/let** - 禁止 var，const 优先
2. **ESM 模块** - `import/export`，`"type": "module"`
3. **async/await** - 处理异步，配合 AbortController
4. **错误处理** - 所有 Promise 必须有错误处理（try-catch 或 .catch）
5. **命名规范** - camelCase 变量/函数, PascalCase 类/组件, UPPER_SNAKE_CASE 常量, kebab-case 文件名
6. **运行时验证** - Zod 验证外部数据（API 响应、表单输入）

### 禁止行为

- 使用 `var`
- 使用 CommonJS（`require` / `module.exports`）
- 没有 try-catch 的 await
- 生产代码中的 `console.log`（使用结构化日志）
- `innerHTML` 直接设置用户输入（XSS 漏洞）
- 变异方法操作原数组（使用 `.toSorted()`, `.toReversed()`）

## 版本与环境

- **JavaScript**: ES2024-2025
- **Node.js**: 22/24 LTS
- **运行时**: Node.js / Deno 2.x / Bun 1.x
- **包管理器**: pnpm（推荐）/ npm 10+ / yarn berry
- **构建工具**: Vite 6.x / esbuild / Rollup 4 / turbopack
- **测试框架**: Vitest 3.x
- **Lint**: ESLint 9 flat config / Biome / oxlint
- **Format**: Prettier / Biome

## ES2024-2025 新特性

```javascript
// Object.groupBy / Map.groupBy
const grouped = Object.groupBy(users, u => u.role);

// 非变异数组方法
const sorted = arr.toSorted((a, b) => a - b);
const reversed = arr.toReversed();
const updated = arr.with(0, 'new');

// Promise.withResolvers
const { promise, resolve, reject } = Promise.withResolvers();

// Array.fromAsync
const items = await Array.fromAsync(asyncIterable);

// Set 方法
const union = setA.union(setB);
const intersection = setA.intersection(setB);
const difference = setA.difference(setB);
```

## 命名约定

```javascript
// camelCase: 变量、函数
const getUserData = async (userId) => { };
const isActive = true;

// UPPER_SNAKE_CASE: 模块级常量
const MAX_RETRIES = 3;
const API_TIMEOUT = 5000;

// PascalCase: 类、组件
class UserManager { }
function UserCard({ user }) { }

// kebab-case: 文件名
// user-service.js, api-client.js
```

## ESLint 9 flat config

```javascript
// eslint.config.js
import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.js', 'src/**/*.jsx'],
    rules: {
      'no-var': 'error',
      'prefer-const': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'prefer-arrow-callback': 'error',
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    }
  }
];
```

## 项目结构

```
src/
├── features/
│   ├── auth/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── components/
│   └── shared/
├── config/
├── store/
└── main.js
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| 使用 `var` | 作用域不清晰，禁止使用 | 高 |
| `require()` | 应使用 ESM import | 高 |
| `arr.sort()` | 变异原数组，应使用 `.toSorted()` | 中 |
| `.eslintrc.js` | 旧版配置，应迁移到 flat config | 中 |
| `npm install` | 应使用 pnpm | 中 |
| Jest 配置 | 应迁移到 Vitest 3.x | 中 |
| Webpack | 应迁移到 Vite 6 | 中 |
| `moment.js` | 应使用 date-fns 或 Temporal API | 低 |

## 检查清单

- [ ] 使用 const/let，禁止 var
- [ ] 使用 ESM（import/export），`"type": "module"`
- [ ] 使用 ES2024-2025 非变异方法
- [ ] 所有 Promise 有错误处理
- [ ] 无 console.log 在生产代码
- [ ] ESLint 9 flat config 或 Biome
- [ ] Vitest 3.x 测试覆盖率 >= 80%
- [ ] pnpm 管理依赖，锁文件已提交
- [ ] Zod 验证外部数据
