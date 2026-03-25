---
description: TypeScript 核心规范：TS 5.7+、strict mode、ESLint flat config、Biome、现代工具链。写任何 TypeScript 代码前必须加载。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# TypeScript 开发核心规范

## 适用 Agents

| Agent | 说明 |
| ----- | ---- |
| dev   | TypeScript 开发专家 |
| debug | TypeScript 调试专家 |
| test  | TypeScript 测试专家 |
| perf  | TypeScript 性能优化专家 |

## 相关 Skills

| 场景       | Skill            | 说明                                    |
| ---------- | ---------------- | --------------------------------------- |
| 类型系统   | Skills(types)    | discriminated unions、Zod、模板字面量   |
| 异步编程   | Skills(async)    | Promise、AbortController、async iterators |
| React 开发 | Skills(react)    | React 19、Server Components、Next.js 15  |
| Node.js    | Skills(nodejs)   | Node.js 22 LTS、ESM、fetch API          |
| 安全编码   | Skills(security) | CSP、输入验证、XSS 防护                 |

## 核心原则

TypeScript 生态追求**类型安全、现代工程、可维护性**。

### 必须遵守

1. **严格模式** - `strict: true` + `noUncheckedIndexedAccess` + `noImplicitOverride`
2. **类型安全** - 禁止 `any`，使用 `unknown` + 类型守卫
3. **运行时验证** - Zod 4 / Valibot 验证外部数据
4. **pnpm 9** - 推荐包管理器（硬链接、严格依赖）
5. **Vitest 3.x** - 测试框架（ESM 原生、替代 Jest）
6. **ESLint flat config** - `eslint.config.ts` 或 Biome

### 禁止行为

- 使用 `any` 类型（使用 `unknown` 代替）
- 使用 `@ts-ignore`（使用 `@ts-expect-error` 并附注释）
- 使用 `enum`（使用 `as const` 对象替代）
- 单行错误处理（`if (err) return err;`）
- 硬编码密钥和配置
- 忽略测试覆盖率

## 版本与环境

- **TypeScript**: 5.7+（target ES2024，path rewriting，inferred type predicates）
- **Node.js**: 22 LTS（native fetch，fs/promises，single executable apps）
- **包管理器**: pnpm 9（推荐）/ Bun 1.x（替代）
- **测试框架**: Vitest 3.x
- **构建工具**: Vite 6 / tsup / unbuild
- **Linter**: ESLint 9 flat config / Biome
- **运行时**: Node.js 22 / Bun 1.x / Deno 2

## 命名约定

```typescript
// 类型：PascalCase
type UserDTO = { id: string; name: string };
type Status = "active" | "inactive" | "pending";

// 变量/函数：camelCase
const userName = "John";
function getUserById(id: string): Promise<User> { /* ... */ }

// 常量：UPPER_SNAKE_CASE（模块级不可变值）
const MAX_RETRIES = 3;
const API_BASE_URL = "https://api.example.com";

// as const 替代 enum
const Role = { Admin: "admin", User: "user", Guest: "guest" } as const;
type Role = (typeof Role)[keyof typeof Role];
```

## tsconfig.json（推荐严格配置）

```json
{
  "compilerOptions": {
    "target": "ES2024",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "declaration": true,
    "sourceMap": true,
    "outDir": "./dist"
  }
}
```

## ESLint flat config

```typescript
// eslint.config.ts
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/consistent-type-imports": ["error", { prefer: "type-imports" }],
      "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    },
  },
);
```

## Red Flags

| 现象 | 问题 | 严重程度 |
|------|------|---------|
| 使用 `any` | 类型安全漏洞 | 高 |
| `@ts-ignore` | 隐藏真实类型错误 | 高 |
| `enum` 关键字 | tree-shaking 不友好 | 中 |
| `.eslintrc.js` | 旧版配置，应迁移到 flat config | 中 |
| `npm install` | 应使用 pnpm | 中 |
| Jest 配置 | 应迁移到 Vitest 3.x | 中 |

## 检查清单

- [ ] `strict: true` + `noUncheckedIndexedAccess`
- [ ] 无 `any` 类型
- [ ] 无 `@ts-ignore`
- [ ] 使用 `as const` 替代 `enum`
- [ ] `import type` 分离类型导入
- [ ] ESLint flat config 或 Biome
- [ ] Vitest 3.x 测试覆盖率 >= 80%
- [ ] pnpm 管理依赖
