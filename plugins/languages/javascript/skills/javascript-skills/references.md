# JavaScript 参考资源

## ECMAScript 规范

### ES2024-2025 新特性

| 特性 | 描述 | 链接 |
|------|------|------|
| `Promise.withResolvers` | 不需要 executor 创建 Promise | [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise/withResolvers) |
| `Object.groupBy` / `Map.groupBy` | 分组数组元素 | [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/groupBy) |
| `Temporal` (Stage 3) | 现代日期时间 API | [Proposal](https://tc39.es/proposal-temporal/) |
| `ArrayBuffer.transfer` | 转移 ArrayBuffer 所有权 | [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/ArrayBuffer/transfer) |
| `String.isWellFormed` / `toWellFormed` | UTF-16 字符串验证 | [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/isWellFormed) |
| `Atomics.waitAsync` | 异步等待原子操作 | [MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics/waitAsync) |
| Decorators (Stage 3) | 装饰器语法 | [Proposal](https://github.com/tc39/proposal-decorators) |

### TC39 提案

- [TC39 Proposals](https://github.com/tc39/proposals) - TC39 提案仓库
- [ECMA-262 Specification](https://tc39.es/ecma262/) - ECMAScript 语言规范

## 官方文档

### MDN Web Docs

- [JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide) - JavaScript 完整指南
- [JavaScript Reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference) - JavaScript 参考
- [Promise](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise) - Promise 文档
- [Async function](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function) - async/await 文档

### V8 引擎

- [V8 Blog](https://v8.dev/blog) - V8 引擎官方博客
- [V8 Docs](https://v8.dev/docs) - V8 文档

## 工具文档

### 包管理器

| 工具 | 描述 | 链接 |
|------|------|------|
| pnpm | 快速、节省磁盘空间的包管理器 | [pnpm.io](https://pnpm.io) |
| npm | Node.js 默认包管理器 | [docs.npmjs.com](https://docs.npmjs.com) |
| Yarn | 现代、快速的包管理器 | [yarnpkg.com](https://yarnpkg.com) |

### 构建工具

| 工具 | 描述 | 链接 |
|------|------|------|
| Vite | 下一代前端构建工具 | [vitejs.dev](https://vitejs.dev) |
| webpack | 模块打包工具 | [webpack.js.org](https://webpack.js.org) |
| Rollup | ES 模块打包工具 | [rollupjs.org](https://rollupjs.org) |
| esbuild | 极速 JavaScript 打包器 | [esbuild.github.io](https://esbuild.github.io) |

### 代码质量

| 工具 | 描述 | 链接 |
|------|------|------|
| ESLint 9+ | JavaScript 代码检查工具 | [eslint.org](https://eslint.org) |
| Prettier 3+ | 代码格式化工具 | [prettier.io](https://prettier.io) |
| TypeScript | JavaScript 类型系统 | [typescriptlang.org](https://www.typescriptlang.org) |

### 测试框架

| 工具 | 描述 | 链接 |
|------|------|------|
| Vitest | Vite 原生测试框架 | [vitest.dev](https://vitest.dev) |
| Jest | JavaScript 测试框架 | [jestjs.io](https://jestjs.io) |
| Playwright | 端到端测试框架 | [playwright.dev](https://playwright.dev) |
| Testing Library | React/Vue 组件测试 | [testing-library.com](https://testing-library.com) |

## 框架文档

### React

| 资源 | 描述 | 链接 |
|------|------|------|
| React Docs | React 18+ 官方文档 | [react.dev](https://react.dev) |
| Hooks | Hooks 完整参考 | [react.dev/reference/react](https://react.dev/reference/react) |
| React Query | 服务端状态管理 | [tanstack.com/query/latest](https://tanstack.com/query/latest) |
| Redux Toolkit | Redux 官方工具集 | [redux-toolkit.js.org](https://redux-toolkit.js.org) |
| Next.js | React 全栈框架 | [nextjs.org](https://nextjs.org) |

### Vue

| 资源 | 描述 | 链接 |
|------|------|------|
| Vue Docs | Vue 3 官方文档 | [vuejs.org](https://vuejs.org) |
| Composition API | Composition API 参考 | [vuejs.org/api/composition-api-setup](https://vuejs.org/api/composition-api-setup) |
| Pinia | Vue 状态管理 | [pinia.vuejs.org](https://pinia.vuejs.org) |
| Nuxt | Vue 全栈框架 | [nuxt.com](https://nuxt.com) |

### 其他框架

| 框架 | 描述 | 链接 |
|------|------|------|
| Svelte | 编译型框架 | [svelte.dev](https://svelte.dev) |
| Solid | 响应式框架 | [solidjs.com](https://www.solidjs.com) |
| Preact | 轻量级 React | [preactjs.com](https://preactjs.com) |

## 安全资源

### 安全指南

| 资源 | 描述 | 链接 |
|------|------|------|
| OWASP Top 10 | Web 应用安全风险 | [owasp.org](https://owasp.org/www-project-top-ten) |
| MDN Security | Web 安全指南 | [developer.mozilla.org/en-US/docs/Web/Security) |
| CSP | 内容安全策略 | [developer.mozilla.org/en-US/docs/Web/HTTP/CSP) |
| DOMPurify | XSS 防护库 | [github.com/cure53/DOMPurify](https://github.com/cure53/DOMPurify) |

### 安全工具

| 工具 | 描述 | 链接 |
|------|------|------|
| npm audit | 依赖漏洞扫描 | `npm audit` |
| Snyk | 安全漏洞扫描 | [snyk.io](https://snyk.io) |
| Semgrep | 代码安全扫描 | [semgrep.dev](https://semgrep.dev) |

## 学习资源

### 教程和课程

| 资源 | 描述 | 链接 |
|------|------|------|
| JavaScript.info | 现代 JavaScript 教程 | [javascript.info](https://javascript.info) |
| You Don't Know JS | JavaScript 深度系列 | [github.com/getify/You-Dont-Know-JS](https://github.com/getify/You-Dont-Know-JS) |
| Frontend Masters | 前端开发课程 | [frontendmasters.com](https://frontendmasters.com) |

### 社区

| 社区 | 描述 | 链接 |
|------|------|------|
| Stack Overflow | JavaScript 标签 | [stackoverflow.com/questions/tagged/javascript](https://stackoverflow.com/questions/tagged/javascript) |
| Reddit - r/javascript | JavaScript 社区 | [reddit.com/r/javascript](https://www.reddit.com/r/javascript/) |
| Dev.to | 开发者社区 | [dev.to/t/javascript](https://dev.to/t/javascript) |

## 风格指南

### 流行风格指南

| 风格指南 | 描述 | 链接 |
|----------|------|------|
| Airbnb Style Guide | Airbnb JavaScript 风格指南 | [github.com/airbnb/javascript](https://github.com/airbnb/javascript) |
| Standard Style | 零配置代码风格 | [standardjs.com](https://standardjs.com) |
| Google Style Guide | Google JavaScript 风格指南 | [google.github.io/styleguide/jsguide.html](https://google.github.io/styleguide/jsguide.html) |

### ESLint 配置

| 配置 | 描述 | 链接 |
|------|------|------|
| eslint-config-airbnb | Airbnb ESLint 配置 | [npmjs.com/package/eslint-config-airbnb](https://www.npmjs.com/package/eslint-config-airbnb) |
| eslint-config-standard | Standard ESLint 配置 | [npmjs.com/package/eslint-config-standard](https://www.npmjs.com/package/eslint-config-standard) |
| @eslint/js | ESLint 9+ 官方配置 | [npmjs.com/package/@eslint/js](https://www.npmjs.com/package/@eslint/js) |

## Node.js 资源

### 官方文档

| 资源 | 描述 | 链接 |
|------|------|------|
| Node.js Docs | Node.js 官方文档 | [nodejs.org/en/docs](https://nodejs.org/en/docs) |
| Node.js API | Node.js API 参考 | [nodejs.org/docs/latest/api](https://nodejs.org/docs/latest/api) |
| Node.js Blog | Node.js 官方博客 | [nodejs.org/en/blog](https://nodejs.org/en/blog) |

## 浏览器 API

### Web APIs

| API | 描述 | 链接 |
|-----|------|------|
| Fetch API | 网络请求 | [developer.mozilla.org/en-US/docs/Web/API/Fetch_API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) |
| Web Storage | 本地存储 | [developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API) |
| Service Worker | 后台服务 | [developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API) |
| Web Workers | 多线程 | [developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API) |

## 性能优化

### 性能资源

| 资源 | 描述 | 链接 |
|------|------|------|
| Web Vitals | 核心性能指标 | [web.dev/vitals](https://web.dev/vitals) |
| Lighthouse | 性能分析工具 | [developers.google.com/web/tools/lighthouse](https://developers.google.com/web/tools/lighthouse) |
| Performance API | 性能测量 API | [developer.mozilla.org/en-US/docs/Web/API/Performance](https://developer.mozilla.org/en-US/docs/Web/API/Performance) |

## TypeScript 资源

### 官方文档

| 资源 | 描述 | 链接 |
|------|------|------|
| TypeScript Docs | TypeScript 官方文档 | [www.typescriptlang.org/docs](https://www.typescriptlang.org/docs) |
| TypeScript Handbook | TypeScript 手册 | [www.typescriptlang.org/docs/handbook/intro.html](https://www.typescriptlang.org/docs/handbook/intro.html) |
| DefinitelyTyped | TypeScript 类型定义 | [github.com/DefinitelyTyped/DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped) |
