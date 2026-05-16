# TypeScript / JavaScript 插件

> TypeScript 6.0+ 与 JavaScript (ES2025-2026) 统一开发插件 — TS 优先，JS-only 项目通过 JSDoc + `tsc --checkJs` 兜底

> 本插件由原 `typescript` 与 `javascript` 两个插件合并而来，统一以 TypeScript 为推荐路径；纯 JavaScript 项目同样受支持，所有 skills 末尾都给出 JS-only 兜底章节。

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin typescript@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install typescript@ccplugin-market
```

## 功能特性

### 核心功能

- **TypeScript / JavaScript 全栈开发支持** — 类型安全、ES2025-2026 现代特性、React 19 / Vue 3.5 / Node.js 22-24
- **TS 优先 + JS 兜底** — TS strict 项目标准路径；JS 项目用 JSDoc + `checkJs` 获得 80% 类型保护
- **完整开发规范** — 7 个 skill 覆盖核心、类型、异步、React、Vue、Node.js、安全
- **代码智能** — 通过 TypeScript LSP 提供诊断、补全、重构

### 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `typescript-dev` | TypeScript / JavaScript 全栈开发专家 |
| Agent | `typescript-test` | 测试专家 (Vitest 3 / Playwright / MSW) |
| Agent | `typescript-debug` | 调试专家 (类型 / 异步 / 内存 / 性能) |
| Agent | `typescript-perf` | 性能优化专家 (编译 / bundle / Web Vitals) |
| Skill | `typescript-core` | TS 6.0+ 与 JS ES2025-2026 核心规范 (+ JS 兜底) |
| Skill | `typescript-types` | 类型系统 (DU / 守卫 / Zod / JSDoc 兜底) |
| Skill | `typescript-async` | 异步编程 (Promise / AbortController / Streams / Workers) |
| Skill | `typescript-react` | React 19 / Next.js 15 |
| Skill | `typescript-vue` | Vue 3.5 / Nuxt 4 / Pinia 2 |
| Skill | `typescript-nodejs` | Node 22-24 LTS / Hono / Fastify / Drizzle |
| Skill | `typescript-security` | XSS / CSP3 / Zod / 依赖审计 |

## 使用方式

### 开发专家代理 (`typescript-dev`)

用于 TS / JS 代码开发和架构设计。

**示例**：
```
实现一个类型安全的 API 客户端，支持泛型和类型推断
用 Nuxt 4 + Pinia 搭一个全栈用户管理页面
把当前 JS 项目加上 JSDoc 类型并启用 tsc --checkJs
```

### 测试专家代理 (`typescript-test`)

用于编写和优化测试用例。

**示例**：
```
使用 Vitest 编写组件测试和类型测试
为 Hono API 路由写集成测试 + Playwright E2E
```

## 开发规范摘要

- 启用 TypeScript 严格模式 (`strict: true`)；JS 项目用 `checkJs: true`
- 显式类型注解，避免 `any`
- ES 模块 ESM 优先 (`"type": "module"`)
- 包管理 pnpm 10 / Bun 1.x；测试 Vitest 3
- 边界 (HTTP / fs / env) 必经 Zod 4 校验
- 文件 ≤ 500 行 (推荐 200~400)

## 快速开始

```bash
# 创建 TS 项目
pnpm create vite my-app --template react-ts
cd my-app && pnpm install && pnpm dev

# 或创建 JS 项目
pnpm create vite my-app --template react
# 然后参考 typescript-core 的 JS 兜底章节添加 jsconfig.json + checkJs
```

## 许可证

AGPL-3.0-or-later
