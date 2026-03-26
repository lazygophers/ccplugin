---
description: 前端项目探索规范 - React/Vue 组件树分析、状态管理溯源、路由结构和样式体系的探索方法
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:explorer-frontend) - 前端项目探索规范

<scope>

当你需要深入理解前端项目的组件架构、状态管理、路由结构和样式体系时使用此 skill。适用于分析 React/Vue/Svelte 组件树和层级关系、追踪状态管理的定义与消费链路、理解路由配置和页面组织、识别样式方案和设计系统、分析构建配置和性能优化策略。

支持的前端技术栈：
- **React**: React 18+、Next.js（App Router/Pages Router）、Remix、Gatsby
- **Vue**: Vue 3（Composition API）、Nuxt 3、Vue 2（Options API）
- **Svelte**: SvelteKit、Svelte 5（Runes）
- **Angular**: Angular 17+（Standalone Components）

</scope>

<core_principles>

组件优先原则。前端应用的核心是组件树，组件定义了 UI 的结构和行为。必须从入口组件（App/Layout）向下遍历，建立完整的组件依赖树，理解 props 传递、事件通信和组件组合模式。

状态溯源策略。状态管理反映了应用的数据流设计。必须从 store 定义追踪到组件消费，理解状态的作用域（全局/局部/组件）、更新方式（同步/异步）和持久化策略。状态管理方案的选择直接影响应用的可维护性和性能。

路由驱动的页面组织。路由结构定义了用户的导航体验和页面组织。通过分析路由配置，可以理解页面层级、权限控制、数据预加载和代码分割策略。

样式体系识别。现代前端项目可能采用多种样式方案（Tailwind CSS、CSS Modules、CSS-in-JS、全局样式），识别样式体系有助于理解设计系统和组件样式隔离策略。

</core_principles>

<framework_detection>

**React 项目识别**：
- `package.json` 包含 `react`、`react-dom` 依赖
- `tsconfig.json` 或 `jsconfig.json` 中 `jsx` 配置
- `next.config.js/mjs/ts` → Next.js 项目
- `remix.config.js` → Remix 项目
- 入口文件：`src/main.tsx`、`src/index.tsx`、`app/layout.tsx`

**Vue 项目识别**：
- `package.json` 包含 `vue` 依赖
- `vite.config.ts` 中 `@vitejs/plugin-vue`
- `nuxt.config.ts` → Nuxt 项目
- 入口文件：`src/main.ts`、`src/App.vue`、`app.vue`

**Svelte 项目识别**：
- `package.json` 包含 `svelte` 依赖
- `svelte.config.js` 存在
- 入口文件：`src/routes/+layout.svelte`、`src/App.svelte`

**Angular 项目识别**：
- `angular.json` 存在
- `package.json` 包含 `@angular/core`
- 入口文件：`src/app/app.component.ts`

</framework_detection>

<state_management_patterns>

**React 状态管理**：

| 方案 | 识别标志 | 文件模式 |
|------|---------|---------|
| Redux Toolkit | `@reduxjs/toolkit` in package.json | `store/`、`slices/`、`createSlice`、`configureStore` |
| Zustand | `zustand` in package.json | `stores/`、`create()`、`useStore` |
| Jotai | `jotai` in package.json | `atoms/`、`atom()`、`useAtom` |
| React Query/TanStack | `@tanstack/react-query` in package.json | `queries/`、`useQuery`、`useMutation` |
| Context API | 无额外依赖 | `createContext`、`useContext`、`Provider` |
| useState/useReducer | 内置 hooks | `useState`、`useReducer` |

**Vue 状态管理**：

| 方案 | 识别标志 | 文件模式 |
|------|---------|---------|
| Pinia | `pinia` in package.json | `stores/`、`defineStore`、`useXxxStore` |
| Vuex | `vuex` in package.json | `store/`、`createStore`、`mutations`、`actions` |
| Composition API | Vue 3 内置 | `ref()`、`reactive()`、`computed()`、`composables/` |

**Svelte 状态管理**：

| 方案 | 识别标志 | 文件模式 |
|------|---------|---------|
| Svelte Stores | 内置 | `writable()`、`readable()`、`derived()`、`$store` |
| Svelte 5 Runes | Svelte 5+ | `$state()`、`$derived()`、`$effect()` |

</state_management_patterns>

<routing_patterns>

**React 路由**：

| 方案 | 识别标志 | 路由定义模式 |
|------|---------|-------------|
| React Router v6 | `react-router-dom` | `createBrowserRouter`、`<Route>`、`<Outlet>` |
| Next.js App Router | `app/` 目录 | 文件系统路由：`app/page.tsx`、`app/layout.tsx` |
| Next.js Pages Router | `pages/` 目录 | 文件系统路由：`pages/index.tsx`、`pages/[id].tsx` |
| Remix | `app/routes/` 目录 | 文件系统路由 + loader/action 模式 |

**Vue 路由**：

| 方案 | 识别标志 | 路由定义模式 |
|------|---------|-------------|
| Vue Router | `vue-router` | `createRouter`、`routes: [{ path, component }]` |
| Nuxt | `pages/` 目录 | 文件系统路由：`pages/index.vue`、`pages/[id].vue` |

</routing_patterns>

<output_format>

前端架构报告的标准 JSON 格式：

```json
{
  "framework": {
    "name": "React|Vue|Svelte|Angular",
    "version": "18.x|3.x|5.x|17.x",
    "variant": "Next.js|Nuxt|SvelteKit|null",
    "variant_version": "14.x|3.x|2.x|null"
  },
  "component_tree": [
    {
      "name": "组件名",
      "path": "文件路径",
      "type": "page|layout|component|widget",
      "children": ["子组件名"],
      "props": ["prop 名称"],
      "state": ["使用的状态"]
    }
  ],
  "state_management": {
    "solution": "Redux|Zustand|Pinia|Context|null",
    "stores": [
      {
        "name": "store 名称",
        "path": "文件路径",
        "state_keys": ["状态字段"],
        "actions": ["操作名称"]
      }
    ]
  },
  "routing": {
    "solution": "react-router|vue-router|file-system",
    "routes": [
      {
        "path": "URL 路径",
        "component": "组件名",
        "file": "文件路径",
        "children": [],
        "guards": ["权限守卫"]
      }
    ]
  },
  "styling": {
    "solution": "Tailwind|CSS Modules|styled-components|Sass|CSS-in-JS",
    "config": "配置文件路径",
    "design_system": "是否有设计系统"
  },
  "build_tool": {
    "name": "Vite|Webpack|Turbopack|esbuild",
    "config": "配置文件路径"
  },
  "architecture": "架构总结（简短描述）"
}
```

</output_format>

<tools_guide>

**组件文件搜索**：
- React 组件：`glob("**/*.tsx")` + `glob("**/*.jsx")`
- Vue SFC：`glob("**/*.vue")`
- Svelte 组件：`glob("**/*.svelte")`

**状态管理搜索**：
- Redux: `grep("createSlice|configureStore|useSelector|useDispatch")`
- Zustand: `grep("create\\(|useStore")`
- Pinia: `grep("defineStore|useXxxStore")`
- Context: `grep("createContext|useContext|Provider")`
- Composition API: `grep("ref\\(|reactive\\(|computed\\(")`

**路由搜索**：
- React Router: `grep("createBrowserRouter|Route|useNavigate|useParams")`
- Vue Router: `grep("createRouter|useRouter|useRoute")`
- 文件系统路由：`glob("**/pages/**/*.{tsx,vue}")` + `glob("**/app/**/page.tsx")`

**样式搜索**：
- Tailwind: `glob("tailwind.config.*")` + `grep("className=")`
- CSS Modules: `glob("**/*.module.css")` + `glob("**/*.module.scss")`
- styled-components: `grep("styled\\.|css\`")`

**符号级分析**（继承 explorer-code 能力）：
- `serena:get_symbols_overview` → 分析组件导出
- `serena:find_symbol` → 查找组件定义
- `serena:find_referencing_symbols` → 追踪组件引用关系
- `serena:search_for_pattern` → 搜索 hooks 和状态模式

**用户交互**：
- `SendMessage(@main)` → 报告探索进度和结果

</tools_guide>

<guidelines>

优先识别框架和版本，框架决定了探索策略和工具用法。从入口组件开始，不要从随机文件开始分析。先建立组件树的高层结构，再深入具体组件。状态管理和路由是理解前端架构的两个关键维度，必须覆盖。

不要忽略样式体系（影响组件复用性），不要遗漏构建配置（影响性能和开发体验），不要假设所有组件都是简单的 UI 组件（可能包含复杂业务逻辑），不要跳过 composables/hooks 分析（它们是逻辑复用的核心）。

当项目使用 monorepo 结构时（packages/、apps/），先识别前端包再分析其内部结构。当存在设计系统或组件库时，先理解其约定再分析业务组件。

</guidelines>

<!-- /STATIC_CONTENT -->
