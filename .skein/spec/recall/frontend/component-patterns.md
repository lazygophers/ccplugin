---
title: component-patterns
layer: recall
category: frontend
keywords: [frontend,tab,switchTab,data-tab,data-tab-target,single-html,vanilla-js,样例,antd,simulation,dialog,details,appearance-none,tooltip,css-hover,零框架,css,animation,tab-switch,retrigger,display-none,hidden,reflow,零JS]
status: active
---

## 单 HTML 样例加 tab 范式 (data-tab-target + data-tab + .hidden, switchTab JS 零改)

### 触发场景
单 HTML 样例页 (docs/examples/index.html, sample-skein/task.html) 要加多 tab 切换, 不引 JS 框架, 复用 Tailwind utility + 极简 vanilla JS。

### 陷阱-正解
**陷阱**: 各 tab 自己写显示/隐藏逻辑, 或引 petite-vue/vue 等框架做单一切换。
**正解**: 三元件统一架构, 加 tab 仅改 HTML 不动 JS:
- 触发按钮带 `data-tab-target="<id>"` (无 href 不污染路由)
- 内容容器带 `data-tab="<id>"`, 非当前加 Tailwind `.hidden`
- JS 全局一次绑 `.tab-btn` click → 切 `.active` + 切 `[data-tab]` 的 `.hidden`

### 反例表
| 禁 | 改为 |
|---|---|
| `<a href="#colors">` + hashchange 路由 | `<button data-tab-target="colors">` |
| 各 tab 独立 if/else JS 分支 | 单 querySelectorAll 循环, dataset 对比 |
| 切 tab 时忘记重置入场动画 | 切到 panel 时同步重置 `.animate-stagger-in` 的 `animationPlayState='running'` |

### 案例
docs/examples/index.html:345-349 (5 个 `.tab-btn` with `data-tab-target`), :353/:562/:1318/:1423/:1493 (`<section data-tab=... hidden>`), :1845-1865 (15 行 switchTab JS 全复用)。

### 关联
- frontend/task-detail-research-gitignore-72.md (petite-vue DOC_TABS dict 渲染分支顺序 — 不同架构, 本条针对无框架单 HTML)
- frontend/task-detail-enhance-71.md (petite-vue 软刷新保 tab 状态 — 本条架构无此问题, 单 HTML 无软刷新)

## 纯 HTML+Tailwind 模拟 antd 组件库范式 (Modal <dialog> / Menu <details> / Switch appearance:none / Tooltip CSS:hover, 零 JS 框架)

### 触发场景
单 HTML 样例页要模拟 antd 全组件库 (docs/examples/index.html: 6 类 30 组件), 不引 antd/react/vue CDN, 用原生 HTML + Tailwind 实现外观。

### 陷阱-正解
**陷阱**: 引入 antd UMD / react CDN, 单文件膨胀到 MB 级 + 框架运行时。
**正解**: 一对一组件 → 原生 HTML 元素映射, 零框架依赖:

| antd 组件 | 原生解 |
|---|---|
| Modal | `<dialog class="antd-modal">` + `.showModal()` (自带 backdrop + ESC 关闭) |
| Menu 子菜单 | `<details><summary>` (零 JS 展开/收起, `[open]` 状态机原生) |
| Switch | `<input type=checkbox class="antd-switch">` + `appearance:none` 重塑滑块 (`::after` 圆点 + `:checked` translateX) |
| Tooltip | wrapper `.antd-tip-wrap` + 子 `.antd-tip` + 纯 CSS `:hover` 显隐 |
| Spin / Skeleton | `@keyframes antdSpin/shimmer` + utility 类 |
| Message | 顶部 `position:fixed` toast + JS `showAntdMessage()` helper |

### 反例表
| 禁 | 改为 |
|---|---|
| Modal 用 div + 自写 backdrop / ESC 监听 | 原生 `<dialog>` + `::backdrop` 伪元素 |
| Menu 用 ul/li + JS toggle `.open` | `<details>` 原生 `[open]` 状态机 |
| Switch 用 div + JS 切换 class | checkbox + `appearance:none` 纯 CSS 滑块 |
| Tooltip 用 JS 控制显隐 + 定位 | wrapper:hover + 子元素 transform 纯 CSS |

### 规则
- MUST: 单 HTML 样例模拟组件库, 优先原生 HTML 元素 (`<dialog>` / `<details>` / checkbox), 禁引框架 UMD
- MUST: 仅当原生元素语义不匹配时 (Spin/Skeleton 动画 / Message toast), 才补 CSS keyframes + JS helper

### 案例
docs/examples/index.html:256-296 (utility 定义), :847-858 (`<details>` Menu), :1159-1163 (Tooltip `.antd-tip-wrap`), :1233-1316 (`<dialog id="antdModalDemo">`), :1840-1898 (showAntdMessage helper)。

### 关联
- build/reconstruct-44.md (webapp buildless 预构建 dist — 本条更极致, 样例页纯 CDN+单文件)
- build/reconstruct-45.md (petite-vue vendored — 样例页连 vendored 都不引, 全原生)

## Tab 切换重触发 CSS 动画靠 display:none (.hidden) 浏览器自动重置 (零 JS)

### 触发场景
单页多 tab, 切到某 tab 时希望 CSS 入场动画「重跑」(如节点级联淡入), 切走再切回应能再次触发。不想引入 JS 手动 remove/add class 或 reflow trick。

### 陷阱-正解
**陷阱**: tab 切走只 `visibility:hidden` 或 `opacity:0`, 元素仍在 DOM 树中渲染, CSS 动画「播完即止」, 切回不会重跑。
**正解**: tab 切走给容器加 `.hidden { display: none; }`, 浏览器对 `display:none` 元素的动画会自动重置 (元素脱离渲染树), 切回 (`display` 恢复) 时动画从头播放, 零 JS 重触发。

### 反例表
| 禁 | 改为 |
|---|---|
| `visibility:hidden` 切 tab | `display: none` (`.hidden` class) |
| JS 手动 remove/re-add class 强制 reflow | `.hidden { display: none }` CSS 切换, 浏览器自动重置动画 |
| 动画只播一次永不再触发 | 切回 tab display 恢复, 动画自动重跑 |

### 案例
docs/examples/index.html 多 tab (Timeline/DAG/...) 切换: 切走时 `tab.classList.add('hidden')` → `display:none`; 切回 `classList.remove('hidden')`, DAG 节点级联入场动画自动重跑 (无需 JS 重置 animation)。

### 关联
- frontend/examples-dag-81 (DAG 4 态范式 — tab 切回时节点级联动画依赖此行为)
