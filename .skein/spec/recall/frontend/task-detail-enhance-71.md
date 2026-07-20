---
title: petite-vue 无实例句柄读状态 → DOM 抽模式
layer: recall
category: frontend
keywords: [petite-vue,dom,state,extract,soft-refresh,scroll]
source: task-detail-enhance
authored-by: skein-spec
created: 1784546614
status: active
related: []
updated: 1784546614
---

## 触发场景
软刷新 (innerHTML swap) petite-vue 响应式组件，需保存 tab/滚动状态。

## 陷阱-正解
**陷阱**：依赖 petite-vue 实例句柄读状态 (如 app.$data.tab)，但 vendored petite-vue 无对外钩子。
**正解**：重挂前从旧 DOM 抽取 data-cur-tab 属性 + window.scrollY，重挂后回填。

## 规则
- MUST：软刷新保状态用 DOM 抽取，不依赖 petite-vue 实例句柄
- MUST：重挂前从 mount.querySelector("[data-cur-tab]") 抽当前 tab
- MUST：重挂前保存 window.scrollY
- MUST：createApp() 时注入 savedTab 作为初始 tab
- MUST：重挂后 requestAnimationFrame(() => window.scrollTo(0, savedScroll))

## 反例表
| 禁 | 改为 |
|---|---|
| 依赖 app.$data.tab 读状态 | 从 DOM 抽 data-cur-tab 属性 |
| 软刷新不保存滚动位 | 保存 window.scrollY 并重挂后回填 |
| 直接 createApp() 无初参 | 注入 savedTab 作为初始 tab |
| 不等 DOM 布局完成就 scrollTo | 用 requestAnimationFrame 等 DOM 完成 |

## 案例
task.js:359-435 (保 tab/滚动)，board-render.js:376-401 (保滚动位)。

## 关联
- petite-vue 先 await 拉数据，再 createApp (frontend/reconstruct-05.md)
- innerHTML 软刷新保滚动位 (frontend/reconstruct-49.md)
