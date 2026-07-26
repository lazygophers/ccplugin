---
title: 单 HTML 样例加 tab 范式 (data-tab-target + data-tab + .hidden, switchTab JS 零改)
layer: recall
category: frontend
keywords: [frontend,tab,switchTab,data-tab,data-tab-target,single-html,vanilla-js,样例]
source: examples-timeline-antd
authored-by: skein-spec
created: 1785074369
status: active
related: [task-detail-research-gitignore-72,task-detail-enhance-71]
updated: 1785074369
---

## 触发场景
单 HTML 样例页 (docs/examples/index.html, sample-skein/task.html) 要加多 tab 切换, 不引 JS 框架, 复用 Tailwind utility + 极简 vanilla JS。

## 陷阱-正解
**陷阱**: 各 tab 自己写显示/隐藏逻辑, 或引 petite-vue/vue 等框架做单一切换。
**正解**: 三元件统一架构, 加 tab 仅改 HTML 不动 JS:
- 触发按钮带 `data-tab-target="<id>"` (无 href 不污染路由)
- 内容容器带 `data-tab="<id>"`, 非当前加 Tailwind `.hidden`
- JS 全局一次绑 `.tab-btn` click → 切 `.active` + 切 `[data-tab]` 的 `.hidden`

## 反例表
| 禁 | 改为 |
|---|---|
| `<a href="#colors">` + hashchange 路由 | `<button data-tab-target="colors">` |
| 各 tab 独立 if/else JS 分支 | 单 querySelectorAll 循环, dataset 对比 |
| 切 tab 时忘记重置入场动画 | 切到 panel 时同步重置 `.animate-stagger-in` 的 `animationPlayState='running'` |

## 案例
docs/examples/index.html:345-349 (5 个 `.tab-btn` with `data-tab-target`), :353/:562/:1318/:1423/:1493 (`<section data-tab=... hidden>`), :1845-1865 (15 行 switchTab JS 全复用)。

## 关联
- frontend/task-detail-research-gitignore-72.md (petite-vue DOC_TABS dict 渲染分支顺序 — 不同架构, 本条针对无框架单 HTML)
- frontend/task-detail-enhance-71.md (petite-vue 软刷新保 tab 状态 — 本条架构无此问题, 单 HTML 无软刷新)
