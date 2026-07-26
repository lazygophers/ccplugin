---
title: Tab 切换重触发 CSS 动画靠 display:none (.hidden) 浏览器自动重置 (零 JS)
layer: recall
category: frontend
keywords: [frontend,css,animation,tab-switch,retrigger,display-none,hidden,reflow,零JS]
source: examples-dag
authored-by: skein-spec
created: 1785078869
status: active
related: [frontend/examples-dag-81]
updated: 1785078869
---

## 触发场景
单页多 tab, 切到某 tab 时希望 CSS 入场动画「重跑」(如节点级联淡入), 切走再切回应能再次触发。不想引入 JS 手动 remove/add class 或 reflow trick。

## 陷阱-正解
**陷阱**: tab 切走只 `visibility:hidden` 或 `opacity:0`, 元素仍在 DOM 树中渲染, CSS 动画「播完即止」, 切回不会重跑。
**正解**: tab 切走给容器加 `.hidden { display: none; }`, 浏览器对 `display:none` 元素的动画会自动重置 (元素脱离渲染树), 切回 (`display` 恢复) 时动画从头播放, 零 JS 重触发。

## 反例表
| 禁 | 改为 |
|---|---|
| `visibility:hidden` 切 tab | `display: none` (`.hidden` class) |
| JS 手动 remove/re-add class 强制 reflow | `.hidden { display: none }` CSS 切换, 浏览器自动重置动画 |
| 动画只播一次永不再触发 | 切回 tab display 恢复, 动画自动重跑 |

## 案例
docs/examples/index.html 多 tab (Timeline/DAG/...) 切换: 切走时 `tab.classList.add('hidden')` → `display:none`; 切回 `classList.remove('hidden')`, DAG 节点级联入场动画自动重跑 (无需 JS 重置 animation)。

## 关联
- frontend/examples-dag-81 (DAG 4 态范式 — tab 切回时节点级联动画依赖此行为)
