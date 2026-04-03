---
description: "探索前端项目架构：分析组件树层级、状态管理流向、路由结构、样式体系。当需要理解前端页面组织、组件props/事件传递、代码分割策略时触发。支持React/Vue/Svelte/Angular。"
model: sonnet
context: fork
user-invocable: false
agent: task:explorer-frontend
---


# Skills(task:explorer-frontend) - 前端项目探索规范

## 范围

深入理解前端项目架构：组件树/状态管理/路由结构/样式体系。支持React 18+/Next.js/Remix、Vue 3/Nuxt 3、Svelte/SvelteKit、Angular 17+。

## 核心原则

- **组件优先**：从入口(App/Layout)向下遍历组件树，理解props/事件/组合模式
- **状态溯源**：从store定义追踪到组件消费，理解作用域/更新方式/持久化
- **路由驱动**：通过路由配置理解页面层级/权限/预加载/代码分割
- **样式识别**：识别Tailwind/CSS Modules/CSS-in-JS等方案和设计系统

## 框架识别

| 框架 | 标志 | 入口文件 |
|------|------|---------|
| React | `react` in package.json | `src/main.tsx`, `src/index.tsx` |
| Next.js | `next.config.*` | `app/layout.tsx`, `pages/index.tsx` |
| Vue 3 | `vue` in package.json | `src/main.ts`, `src/App.vue` |
| Nuxt 3 | `nuxt.config.ts` | `app.vue` |
| Svelte | `svelte.config.js` | `src/App.svelte` |
| SvelteKit | `svelte.config.js` + routes | `src/routes/+layout.svelte` |
| Angular | `angular.json` | `src/app/app.component.ts` |

## 状态管理识别

| 方案 | 依赖/标志 | 搜索模式 |
|------|----------|---------|
| Redux Toolkit | `@reduxjs/toolkit` | `createSlice`, `configureStore` |
| Zustand | `zustand` | `create()`, `useStore` |
| Jotai | `jotai` | `atom()`, `useAtom` |
| TanStack Query | `@tanstack/react-query` | `useQuery`, `useMutation` |
| Context API | 内置 | `createContext`, `useContext` |
| Pinia | `pinia` | `defineStore`, `useXxxStore` |
| Vuex | `vuex` | `createStore`, `mutations` |
| Composition API | Vue 3内置 | `ref()`, `reactive()` |
| Svelte Stores | 内置 | `writable()`, `$store` |

## 路由识别

| 方案 | 标志 | 模式 |
|------|------|------|
| React Router v6 | `react-router-dom` | `createBrowserRouter`, `<Route>` |
| Next.js App Router | `app/`目录 | 文件系统路由 |
| Vue Router | `vue-router` | `createRouter` |
| Nuxt | `pages/`目录 | 文件系统路由 |

## 输出格式

JSON包含：`framework{name,version,variant}` + `component_tree[{name,path,type,children,props,state}]` + `state_management{solution,stores}` + `routing{solution,routes}` + `styling{solution,config,design_system}` + `build_tool{name,config}` + `architecture`

## 工具指南

- 组件搜索：`glob("**/*.tsx")` / `glob("**/*.vue")` / `glob("**/*.svelte")`
- 状态搜索：按上表搜索模式使用grep
- 路由搜索：`grep("createBrowserRouter|useNavigate")` / 文件系统 `glob("**/pages/**")`
- 样式搜索：`glob("tailwind.config.*")` / `glob("**/*.module.css")`
- 符号分析：`serena:get_symbols_overview` / `serena:find_symbol` / `serena:find_referencing_symbols`

## 指南

**必须**：先识别框架版本 → 从入口组件开始 → 先高层后深入 → 覆盖状态和路由

**禁止**：忽略样式体系 | 遗漏构建配置 | 假设组件无业务逻辑 | 跳过composables/hooks分析

**Monorepo**：先识别前端包再分析内部。**设计系统**：先理解约定再分析业务组件。

