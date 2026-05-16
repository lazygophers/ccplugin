所有 TypeScript / JavaScript 代码必须遵守以下 Skills 规范 (TS 优先，JS-only 项目同适用，见各 Skill 末尾兜底)：

- Skill(typescript-core) - 核心规范：TS 6.0+ strict 或 JS + JSDoc + checkJs、ESM、ES2025-2026 工具链
- Skill(typescript-types) - 类型系统：discriminated union、Zod 4、JSDoc 类型 (JS 兜底)
- Skill(typescript-async) - 异步编程：async/await、AbortController、Streams、Workers
- Skill(typescript-react) - React 19 / Next.js 15
- Skill(typescript-vue) - Vue 3.5 / Nuxt 4 / Pinia 2
- Skill(typescript-nodejs) - Node 22-24 LTS、Hono、Fastify、Drizzle
- Skill(typescript-security) - 输入验证、XSS、CSP3、依赖审计

每一个 `*.ts` / `*.tsx` / `*.mts` / `*.cts` / `*.js` / `*.jsx` 文件都不得超过 500 行，推荐 200~400 行。
