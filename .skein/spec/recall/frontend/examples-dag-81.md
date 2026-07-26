---
title: DAG 组件纯 SVG 4 态范式 (g.node<state> + 群组选择器 + defs marker 复用 + opacity 脉冲)
layer: recall
category: frontend
keywords: [frontend,svg,dag,node,state,marker,defs,opacity,pulse,transform-box-compat]
source: examples-dag
authored-by: skein-spec
created: 1785077939
status: active
related: [frontend/reconstruct-48,arch/reconstruct-50]
updated: 1785077939
---

## 触发场景
单 HTML 文档/样例页要嵌 DAG (有向无环图) 视觉, 禁引 JS 框架, 用纯 SVG + CSS 群组降级选择器驱动 4 态色彩 (待执行 / 已完成 / 进行中 / 失败)。

## 陷阱-正解
**陷阱**: 各节点单独写 inline 样式 / 用 transform scale 做进行中脉冲 (transform-box 浏览器兼容性差, 部分内核定位漂移) / 各 SVG 各画一份箭头 marker。
**正解**:
- 节点统一 `<g class="node <state>">` 包形状 (rect/ellipse/polygon 通用) + text, 形状选择器写 `.dag-svg .node > rect, .node > ellipse, .node > polygon` 三件套群组降级, 一个 class 切全局态
- 箭头 marker 全 panel 复用: 文件级单一 `<defs><marker id="dag-arrow">` 定义, 各 path `marker-end="url(#dag-arrow)"` 引用; active 边单独 `id="dag-arrow-active"` 配色
- 进行中态脉冲用 `@keyframes dagPulse{0%,100%{opacity:1}50%{opacity:.7}}` 替代 transform scale, 避 transform-box 兼容坑
- 暗模独立写一遍选择器 (无 color-mix polyfill 时), `prefers-reduced-motion:reduce` 关动画

## 反例表
| 禁 | 改为 |
|---|---|
| 各节点 inline `fill="#..."` 硬编码 | class 驱动, CSS 群组降级选择器 |
| transform: scale 做脉冲 | opacity 0.7↔1 脉冲 (兼容性稳) |
| 每个 SVG 各定义 marker | 文件级 `<defs>` 单一 marker, 全 panel url(#id) 引用 |
| 形状只支持 rect | 群组选择器并列 rect/ellipse/polygon 三件套 |

## 案例
docs/examples/index.html:296-340 完整 CSS 块 (4 态色彩 + dagPulse keyframes + dark 模式 + reduced-motion); :1456/:1882-1890 双 defs marker; :1911-1970 多 panel path 共享 `marker-end="url(#dag-arrow)"`; :1916-1937 `<g class="node done/active/无">` 结构。

## 关联
- frontend/reconstruct-48 (hover popover 状态机 — DAG 节点悬浮浮层配套)
- arch/reconstruct-50 (后端算数据 / 前端呈现 — DAG 数据后端算好下发)
