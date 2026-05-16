---
name: typescript-core
description: TypeScript 核心开发规范，覆盖 TS 6.0+ strict mode、tsconfig 配置、Biome 2 / ESLint flat config、pnpm 与现代工具链（tsgo / Bun / Deno 2 / Node 22 LTS）。Use when 新建 TypeScript 项目、配置 tsconfig、设置 linter/formatter、选型工具链，或用户提到 "TypeScript 规范"、"strict mode"、"tsconfig"、"biome"、"eslint"、"package manager"。
user-invocable: true
---

# TypeScript 核心开发规范

适用范围：所有 TypeScript 源码（`.ts` / `.tsx` / `.mts` / `.cts`）。

## 核心原则

类型安全 > 类型体操；编译期错误 > 运行期错误；显式 > 隐式。

### 必须遵守

1. **严格模式** — `strict: true` + `noUncheckedIndexedAccess` + `noImplicitOverride` + `exactOptionalPropertyTypes`
2. **禁 `any`** — 用 `unknown` + 类型守卫，或 Zod 4 / Valibot 在边界验证
3. **运行时验证** — 所有外部输入（HTTP / fs / env）走 Zod 4 schema
4. **ESM 优先** — `"type": "module"` + `import type` 分离类型导入
5. **pnpm 9+** 或 **Bun 1.x** — 禁 npm install（除非项目历史约束）
6. **Vitest 3.x** — 替代 Jest（ESM 原生，类型测试）
7. **每文件 ≤ 500 行**，推荐 200~400

### 禁止行为

- `any`、`@ts-ignore`、`enum`（用 `as const` 对象代替）、`namespace`
- 单行错误处理（`if (err) return err`）
- 硬编码密钥 / URL
- `.eslintrc.js`（旧）→ flat config 或 Biome
- `node-fetch`（Node 22 已内置 fetch）
- `React.FC`（隐式 children、泛型受限）

## 版本与工具链（2026-05 现状）

| 项 | 推荐 | 说明 |
|----|------|------|
| TypeScript | **6.0** 稳定 | `target: ES2025`，strict 默认开 |
| TS 7.0 / tsgo | **CI type-check 可用** | Go 重写 10x 加速；编译产物未 GA；用 `@typescript/native-preview` |
| Node.js | **22 LTS** | 原生 strip-types（22.18+）、原生 fetch、test runner |
| 包管理 | pnpm 9 / Bun 1.x | 禁 npm 新项目 |
| Linter+Formatter | **Biome 2** 优先 / ESLint 9 flat（重 plugin 时） | Biome 2.3+ 423 规则 + 部分类型感知 |
| 测试 | Vitest 3.x | bench、type 测试、ESM 原生 |
| 构建 | Vite 6 / tsdown（Rolldown）/ tsup / unbuild | 库优先 tsdown |
| 运行时 | Node 22 / Bun 1.x / Deno 2 | 三选一 |

## tsconfig.json 推荐基线

```json
{
  "compilerOptions": {
    "target": "ES2025",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2025"],

    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true,

    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "skipLibCheck": true,

    "declaration": true,
    "sourceMap": true,
    "outDir": "./dist"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

## Biome 2 配置（推荐新项目）

```jsonc
// biome.json
{
  "$schema": "https://biomejs.dev/schemas/2.3.0/schema.json",
  "linter": { "enabled": true, "rules": { "recommended": true } },
  "formatter": { "enabled": true, "indentStyle": "space", "indentWidth": 2 },
  "javascript": { "formatter": { "quoteStyle": "double", "semicolons": "always" } }
}
```

```bash
pnpm dlx @biomejs/biome init
pnpm biome check --write .   # lint + format 一把梭
```

## ESLint 9 flat config（仅在依赖 typed-rules 时）

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
    },
  },
);
```

## 命名约定

```typescript
type UserDTO = { id: string };                  // 类型 PascalCase（禁 I 前缀）
type Status = "active" | "inactive";
const userName = "John";                        // 变量 camelCase
function getUserById(id: string) { /* ... */ } // 函数 camelCase
const MAX_RETRIES = 3;                          // 常量 UPPER_SNAKE_CASE

// as const 替代 enum
const Role = { Admin: "admin", User: "user" } as const;
type Role = (typeof Role)[keyof typeof Role];
```

## tsgo 试用（TS 7 native preview）

```bash
pnpm add -D @typescript/native-preview
pnpm exec tsgo --noEmit          # CI 快速类型检查
# 注意：emit/decorators/older targets 尚未完整，构建仍用 tsc
```

## Red Flags

| 现象 | 问题 | 严重 |
|------|------|------|
| `any` | 类型安全漏洞 | 高 |
| `@ts-ignore` | 隐藏真实错误（用 `@ts-expect-error` + 注释） | 高 |
| `enum` | tree-shaking 不友好 | 中 |
| `.eslintrc.js` | 旧 schema | 中 |
| 文件 > 500 行 | 拆分信号 | 中 |
| `npm install` 新项目 | pnpm/Bun 更优 | 中 |
| Jest 配置 | Vitest 3.x 替代 | 中 |

## 检查清单

- [ ] `strict: true` + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes`
- [ ] 无 `any` / `@ts-ignore`
- [ ] `as const` 替代 `enum`
- [ ] `import type` 分离类型导入
- [ ] Biome 2 或 ESLint flat config（二选一）
- [ ] pnpm 9 / Bun 锁文件
- [ ] Vitest 3.x，覆盖率 ≥ 80%
- [ ] 文件 ≤ 500 行
