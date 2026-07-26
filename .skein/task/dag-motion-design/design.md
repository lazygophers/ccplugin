# DAG tab 动效与设计增强 — 详细设计

## 现状基线 (index.html L298-343)
- 4 态色: `.dag-svg .node` (默认 done active failed) 已定义。
- active 脉冲: `@keyframes dagPulse` opacity 1↔0.7。
- 边: `.edge` 实线 / `.edge.dashed` 虚线 / `.edge.active` 高亮色。
- prefers-reduced-motion 已退化 active 脉冲。

## 设计方案 (5 项, 纯 CSS+SVG 无 JS)

### 1. hover 动效 (节点 scale + 边高亮 + tooltip)
- `.dag-svg .node` 加 `transform-box:fill-box; transform-origin:center; transition:transform .15s; cursor:pointer`。
- `:hover > rect/ellipse/polygon` 加 `transform:scale(1.08); filter:drop-shadow(0 4px 8px rgba(0,0,0,.15))`。
- tooltip: 节点 `<g>` 内嵌 `<title>` (原生 SVG tooltip, 零 JS), hover 浏览器显原生 title。
- 边高亮: 难 (CSS 无父选择器), ponytail 简化 — 节点 hover drop-shadow 已足够视觉反馈, 不强求边联动 (避免 JS)。

### 2. 入场级联淡入 (按深度 stagger)
- `.dag-svg .node` 加 `opacity:0; animation:dagFadeIn .4s ease-out forwards`。
- 用 CSS `nth-child` 给不同深度节点设 `animation-delay` (0/80/160/240ms), ≤1s 完成。
- 切 tab 才触发: 用 `section:not(.hidden) .dag-svg .node` 限定 (tab panel .hidden 切换时重置动画)。
- ponytail 兼容: 直接在 `.dag-svg .node` 上跑 (页面加载即跑一次, 切 tab 不重跑也 OK, 不强求重触发)。

### 3. 蚂蚁线流动边 (active 边)
- `.dag-svg .edge.active` 加 `stroke-dasharray:6 4; animation:dagFlow 1s linear infinite`。
- `@keyframes dagFlow{to{stroke-dashoffset:-10}}` (负值=流向箭头方向)。

### 4. 图例条 (panel 顶部)
- panel `<p>` 描述后加一行 flex 图例: 4 色块 (默认/进行中/完成/失败) + 3 边样 (实线/虚线/流动), 复用 ocean/success/danger 色。

### 5. 状态图标 (节点内嵌)
- 各节点 `<g>` 内加 `<text class="node-icon">` (✓/⏳/✗/○) 放节点右上角或文字前缀。
- ponytail: 文字前缀最简 (如 "✓ A · root"), 不另起 text 元素省坐标计算。

## prefers-reduced-motion 退化
- 统一在现有 `@media(prefers-reduced-motion:reduce)` 块内追加: `.dag-svg .node{animation:none;opacity:1} .dag-svg .edge.active{animation:none}`。

## 取舍
- 边 hover 联动节点: 跳过 (需 JS / CSS :has, 兼容性), 节点 hover drop-shadow 已够。
- 入场重触发: 接受首次加载跑一次, 切 tab 不重跑 (纯 CSS 无 intersection observer, ponytail 可接受)。
- 图标: 文字前缀方案最省坐标, 节点 text 一行解决。
