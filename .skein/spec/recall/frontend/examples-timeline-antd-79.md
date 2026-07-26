---
title: 纯 HTML+Tailwind 模拟 antd 组件库范式 (Modal <dialog> / Menu <details> / Switch appearance:none / Tooltip CSS:hover, 零 JS 框架)
layer: recall
category: frontend
keywords: [frontend,antd,simulation,dialog,details,appearance-none,tooltip,css-hover,single-html,零框架]
source: examples-timeline-antd
authored-by: skein-spec
created: 1785074372
status: active
related: [reconstruct-44,reconstruct-45]
updated: 1785074372
---

## 触发场景
单 HTML 样例页要模拟 antd 全组件库 (docs/examples/index.html: 6 类 30 组件), 不引 antd/react/vue CDN, 用原生 HTML + Tailwind 实现外观。

## 陷阱-正解
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

## 反例表
| 禁 | 改为 |
|---|---|
| Modal 用 div + 自写 backdrop / ESC 监听 | 原生 `<dialog>` + `::backdrop` 伪元素 |
| Menu 用 ul/li + JS toggle `.open` | `<details>` 原生 `[open]` 状态机 |
| Switch 用 div + JS 切换 class | checkbox + `appearance:none` 纯 CSS 滑块 |
| Tooltip 用 JS 控制显隐 + 定位 | wrapper:hover + 子元素 transform 纯 CSS |

## 规则
- MUST: 单 HTML 样例模拟组件库, 优先原生 HTML 元素 (`<dialog>` / `<details>` / checkbox), 禁引框架 UMD
- MUST: 仅当原生元素语义不匹配时 (Spin/Skeleton 动画 / Message toast), 才补 CSS keyframes + JS helper

## 案例
docs/examples/index.html:256-296 (utility 定义), :847-858 (`<details>` Menu), :1159-1163 (Tooltip `.antd-tip-wrap`), :1233-1316 (`<dialog id="antdModalDemo">`), :1840-1898 (showAntdMessage helper)。

## 关联
- build/reconstruct-44.md (webapp buildless 预构建 dist — 本条更极致, 样例页纯 CDN+单文件)
- build/reconstruct-45.md (petite-vue vendored — 样例页连 vendored 都不引, 全原生)
