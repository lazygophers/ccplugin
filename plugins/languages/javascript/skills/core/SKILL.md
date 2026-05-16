---
name: javascript-core
description: |
  JavaScript / TypeScript 核心开发规范 (2026 版)：ES2025 + ES2026 stage 3+ 特性、
  ESM-only 模块系统、const/let、命名约定、Node 24 LTS / Bun / Deno 2 运行时、
  pnpm 10 / Bun 包管理、Vite 6 + Rolldown 构建、Biome 2 或 ESLint 9 flat config、
  Vitest 3 / node:test 测试、Zod 4 运行时校验。
  Use when writing or reviewing JS/TS code, scaffolding projects, choosing
  toolchain, or migrating from CommonJS/Webpack/Jest. Triggers:
  "写 JS/TS", "新建 Node 项目", "配置 ESLint/Biome", "迁移 ESM",
  "JS 规范", "modern JavaScript", "ES2025 features".
context: fork
model: sonnet
---

# JavaScript / TypeScript 核心规范 (2026)

## 配套 skills

| 场景 | Skill |
|------|-------|
| 异步、并发、Streams、Workers | `Skills(javascript:async)` |
| React 19 / Next.js 15 | `Skills(javascript:react)` |
| Vue 3.5 / Nuxt 4 | `Skills(javascript:vue)` |
| XSS / CSP / Zod / 依赖审计 | `Skills(javascript:security)` |

## 必须遵守 (Must)

1. **`const` 优先, `let` 次之, 禁 `var`**
2. **ESM only**: `import/export`, `"type": "module"`；禁 `require` / `module.exports`
3. **非变异**: `.toSorted()` / `.toReversed()` / `.with()` / `structuredClone()`
4. **错误处理**: 所有 `await` 在 try-catch 内或调用方有 `.catch`；try-catch 内必 `return await`
5. **命名**: `camelCase` 变量/函数, `PascalCase` 类/组件, `UPPER_SNAKE_CASE` 常量, `kebab-case` 文件
6. **运行时校验**: API/表单/env 必经 Zod 4 (`safeParse` 优先)
7. **单文件 ≤ 500 行**, 推荐 200-400 行
8. **生产禁 `console.log`**: 用 pino 9 / `console.warn`/`console.error` 结构化输出

## 版本与生态 (2026)

| 类别 | 推荐 | 兼容 |
| ---- | ---- | ---- |
| 语言 | ES2025 + ES2026 stage 3+ | ES2024 |
| Runtime | Node.js 24 Active LTS | Node 22 LTS / Bun 1.2 / Deno 2.x |
| 包管理 | pnpm 10 (workspace) | Bun / npm 11 |
| Bundler | Vite 6 (内置 Rolldown) | tsdown (lib) / esbuild / Turbopack |
| Lint+Format | Biome 2 (一体) | ESLint 9 flat + Prettier / oxlint |
| 测试 | Vitest 3 | `node:test` / Playwright |
| HTTP 框架 | Hono 4 / Fastify 5 | Express 5 (legacy) |
| 全栈 | Next.js 15 / Nuxt 4 / SvelteKit 2 | Remix on Vite |
| 校验 | Zod 4 | Valibot / ArkType |
| TS | TypeScript 5.7+ | 或 JSDoc + tsc --checkJs |

## ES2025 / ES2026 关键特性

```js
// ES2025 - Iterator helpers
const evens = arr.values().filter(x => x % 2 === 0).take(10).toArray();

// ES2025 - Set methods
const u = a.union(b);
const i = a.intersection(b);
const d = a.difference(b);

// ES2025 - Object.groupBy / Map.groupBy
const byRole = Object.groupBy(users, u => u.role);

// ES2025 - Promise.try (同步异常也进 Promise 链)
const p = Promise.try(() => mayThrowSync());

// ES2024 - Promise.withResolvers
const { promise, resolve, reject } = Promise.withResolvers();

// ES2025 - Array.fromAsync
const items = await Array.fromAsync(asyncIterable);

// ES2025 - RegExp /v flag (set notation + properties of strings)
const re = /[\p{Emoji}--\p{ASCII}]/v;

// ES2026 stage 3 - using / await using (Explicit Resource Management)
{
  using file = openFile('data.txt');           // Symbol.dispose at block end
  await using db = await connectDB();          // Symbol.asyncDispose
}

// ES2026 stage 3 - Decorators
class Service {
  @logged @cached
  async fetch() { /* ... */ }
}

// Temporal (stage 3) - 替代 Date / moment
const now = Temporal.Now.zonedDateTimeISO();
const future = now.add({ days: 7, hours: 3 });
```

## 项目骨架

```
src/
├── features/
│   ├── auth/
│   │   ├── service.js
│   │   ├── schema.js      # Zod
│   │   └── ui/
│   └── ...
├── shared/                 # 跨 feature 通用
├── config/
└── main.js
```

## Biome 2 配置 (推荐, 替代 ESLint+Prettier)

```jsonc
// biome.json
{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": { "noUnusedVariables": "error" },
      "style": { "noVar": "error", "useConst": "error" },
      "suspicious": { "noConsole": "warn" }
    }
  },
  "formatter": { "enabled": true, "indentWidth": 2, "lineWidth": 100 }
}
```

## ESLint 9 flat config (备选)

```js
// eslint.config.js
import js from '@eslint/js';
export default [
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx,ts,tsx}'],
    rules: {
      'no-var': 'error',
      'prefer-const': 'error',
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  },
];
```

## Red Flags

| 现象 | 应改为 | 严重 |
|------|--------|------|
| `var` | `const`/`let` | 高 |
| `require()` / `module.exports` | ESM import/export | 高 |
| `arr.sort()` (变异) | `arr.toSorted()` | 中 |
| `.eslintrc.js` | flat config 或 Biome 2 | 中 |
| `npm install` (无锁意图) | pnpm / bun | 中 |
| Jest | Vitest 3 / node:test | 中 |
| Webpack | Vite 6 / Rolldown | 中 |
| `moment.js` | Temporal / date-fns | 低 |
| Express 4 新项目 | Hono / Fastify | 中 |
| 无运行时校验 | Zod 4 边界校验 | 高 |

## 检查清单

- [ ] `"type": "module"`, ESM only
- [ ] const/let, 无 var
- [ ] 非变异数组方法
- [ ] await 有错误处理路径
- [ ] 生产无 `console.log`
- [ ] Biome 2 或 ESLint 9 flat config 通过
- [ ] Vitest 3 覆盖率 ≥ 80%
- [ ] pnpm 10 锁文件已提交
- [ ] Zod 校验外部数据
- [ ] 文件 ≤ 500 行

## 权威参考

- TC39: <https://github.com/tc39/proposals>
- MDN JS Reference: <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference>
- Node.js 24 LTS: <https://nodejs.org/en/blog/release>
- Vite: <https://vite.dev>
- Biome 2: <https://biomejs.dev>
- Vitest 3: <https://vitest.dev>
