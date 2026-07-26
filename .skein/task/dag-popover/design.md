# DAG 节点 hover popover + click Modal 浮窗 — 详细设计

## 难点: SVG 内 popover 被 viewBox 裁切
SVG `<g>` 内放 HTML popover 不可行 (SVG 不渲染 HTML 子节点, 且 overflow 裁切)。
方案: **HTML overlay** — DAG panel 外层加 `<div class="dag-overlay">` 绝对定位, popover 是 HTML 元素, JS 监听 SVG 节点 mouseenter/click, 算节点屏幕坐标 → 定位 overlay popover/modal。
但 ponytail: 零 JS 优先。

## 方案 A (推荐, 混合): popover 纯 CSS + Modal 极小 JS
- **popover (纯 CSS)**: 每个 `<g class="node">` 内紧跟一个 `<foreignObject>` (SVG 原生支持嵌入 HTML), hover 显 foreignObject 内的 HTML popover。foreignObject 突破 SVG 渲染限制可放 HTML。
  - 但 foreignObject 定位受 SVG 坐标系, 节点密集时 popover 会重叠相邻节点 (SVG 无 z-index 概念, 后绘制盖前)。
  - ponytail 兜底: foreignObject popover 限定小尺寸 (160x90), 显精简字段 (名称+状态+进度), 详细字段留 Modal。
- **Modal (极小 JS)**: 节点 `<g data-node-id="A" data-details="...">` 加 data 属性, 全局 1 个 `<dialog id="dag-modal">`, JS (~15 行) 监听节点 click → 读 data → 填 dialog → showModal()。复用现有 Modal CSS 范式 (L256)。

## 方案 B (备选, 全 JS): overlay 定位
HTML overlay div + JS 跟踪 hover/click + 算坐标。更灵活但 JS 重 (~40 行), ponytail 不取除非 A 有硬伤。

## 取舍: 选方案 A
- popover 用 foreignObject 纯 CSS hover (无 JS), 尺寸限 160x90 显精简 (名称+状态徽标+进度条)。
- Modal 用原生 dialog + ~15 行 JS (showModal/close + 填字段), 全量字段 (名称/状态/上下游/描述/进度)。
- 节点 data-* 属性存全量字段 JSON (供 Modal 读), popover 用 SVG 内 static text (不动态)。
- 4 态示例值写死 (done 耗时 2h / active 进度 67% / failed 失败原因 / 默认 待执行)。

## 实现细节
1. 节点结构改造: `<g class="node <state>" data-node='{"name":"A","status":"done","deps":["root"],"next":["B","C"],"desc":"...","progress":100,"elapsed":"2h"}'>`。
2. foreignObject popover (节点内, 纯 CSS hover):
   ```html
   <foreignObject x="..." y="..." width="160" height="90" class="dag-popover">
     <div xmlns="http://www.w3.org/1999/xhtml" class="dag-pop-inner">名称+状态+进度</div>
   </foreignObject>
   ```
   CSS: `.dag-svg .dag-popover{opacity:0;pointer-events:none;transition:opacity .15s} .dag-svg .node:hover .dag-popover{opacity:1}`。
3. Modal: panel 末尾 1 个 `<dialog id="dag-modal">` + JS 事件委托 (panel click → 命中 .node → 读 data-node → 填 modal DOM → showModal)。
4. 4 态字段示例值表 (design 末附)。

## prefers-reduced-motion
popover opacity transition 在 reduced-motion 下保留 (非动画, 是过渡, 无害)。Modal 无动画。
