---
title: svg-dag
layer: recall
category: frontend
keywords: [frontend,svg,dag,node,state,marker,defs,opacity,pulse,transform-box-compat,hover,scale,transform-box,fill-box,transform-origin,center,animation,cascade,nth-of-type,nth-child,entrance,stagger,选择器,foreignobject,popover,modal,dialog,event-delegation,closest,data-node,json-attr,pointer-hit]
status: active
---

## DAG 组件纯 SVG 4 态范式 (g.node<state> + 群组选择器 + defs marker 复用 + opacity 脉冲)

### 触发场景
单 HTML 文档/样例页要嵌 DAG (有向无环图) 视觉, 禁引 JS 框架, 用纯 SVG + CSS 群组降级选择器驱动 4 态色彩 (待执行 / 已完成 / 进行中 / 失败)。

### 陷阱-正解
**陷阱**: 各节点单独写 inline 样式 / 用 transform scale 做进行中脉冲 (transform-box 浏览器兼容性差, 部分内核定位漂移) / 各 SVG 各画一份箭头 marker。
**正解**:
- 节点统一 `<g class="node <state>">` 包形状 (rect/ellipse/polygon 通用) + text, 形状选择器写 `.dag-svg .node > rect, .node > ellipse, .node > polygon` 三件套群组降级, 一个 class 切全局态
- 箭头 marker 全 panel 复用: 文件级单一 `<defs><marker id="dag-arrow">` 定义, 各 path `marker-end="url(#dag-arrow)"` 引用; active 边单独 `id="dag-arrow-active"` 配色
- 进行中态脉冲用 `@keyframes dagPulse{0%,100%{opacity:1}50%{opacity:.7}}` 替代 transform scale, 避 transform-box 兼容坑
- 暗模独立写一遍选择器 (无 color-mix polyfill 时), `prefers-reduced-motion:reduce` 关动画

### 反例表
| 禁 | 改为 |
|---|---|
| 各节点 inline `fill="#..."` 硬编码 | class 驱动, CSS 群组降级选择器 |
| transform: scale 做脉冲 | opacity 0.7↔1 脉冲 (兼容性稳) |
| 每个 SVG 各定义 marker | 文件级 `<defs>` 单一 marker, 全 panel url(#id) 引用 |
| 形状只支持 rect | 群组选择器并列 rect/ellipse/polygon 三件套 |

### 案例
docs/examples/index.html:296-340 完整 CSS 块 (4 态色彩 + dagPulse keyframes + dark 模式 + reduced-motion); :1456/:1882-1890 双 defs marker; :1911-1970 多 panel path 共享 `marker-end="url(#dag-arrow)"`; :1916-1937 `<g class="node done/active/无">` 结构。

### 关联
- frontend/reconstruct-48 (hover popover 状态机 — DAG 节点悬浮浮层配套)
- arch/reconstruct-50 (后端算数据 / 前端呈现 — DAG 数据后端算好下发)

## SVG hover scale 必加 transform-box:fill-box (否则飞向 viewBox 原点)

### 触发场景
SVG `<g class="node">` 形状 (rect/ellipse/polygon) hover `transform: scale(1.05)` 时, 默认 transform-origin 在 viewBox (0,0), 缩放会从画布原点「飞」到鼠标位置远处; 需让缩放从形状自身几何中心出发。

### 陷阱-正解
**陷阱**: `transform-origin: center` 在 SVG shape 上无效 (默认按 user space 的 viewBox 原点算, 不是形状 bbox 中心), scale 时形状飞向 viewBox (0,0)。
**正解**: 加 `transform-box: fill-box;` 让 transform 坐标系落在形状自身 bounding box, 此时 `transform-origin: center` 才指向形状几何中心。

### 反例表
| 禁 | 改为 |
|---|---|
| `.node:hover rect { transform: scale(1.05); transform-origin: center; }` 形状飞走 | 加 `transform-box: fill-box` |
| `transform-origin: 50% 50%` (无 fill-box) 仍按 viewBox 算 | `transform-box: fill-box` + `transform-origin: center` |

### 案例
docs/examples/index.html DAG tab `.dag-svg g.node:hover > rect` 选择器, 加 `transform-box: fill-box; transform: scale(1.05); transform-origin: center;` 后 hover 缩放稳定锚在节点中心。同时 `:hover` 抬出 drop-shadow filter 强化反馈。

### 关联
- frontend/examples-dag-81 (DAG 4 态范式 — 本规则补充 81 避坑表中 transform-box 的另一面: pulse 用 opacity, hover scale 必须用 fill-box)

## SVG 级联动画选择器用 :nth-of-type 不用 :nth-child (避开 path/text 兄弟污染)

### 触发场景
SVG 节点 (`<g>`) 入场级联动画 (依次淡入) 需按 `<g>` 兄弟顺序写 nth delay, 选择器写错会把 path/text 等非目标兄弟也算进去, 导致 delay 错位。

### 陷阱-正解
**陷阱**: `:nth-child(n)` 数所有兄弟节点 (含 `<path>` / `<text>` / `<defs>` 等混合标签), 节点实际位置错位, 级联节奏乱。
**正解**: `:nth-of-type(n)` 只数同标签 (`<g>`) 兄弟, path/text 不计入索引, 级联按 `<g>` 真实顺序触发。

### 反例表
| 禁 | 改为 |
|---|---|
| `.dag-svg g.node:nth-child(2)` 含 path/text 污染 | `.dag-svg g.node:nth-of-type(2)` |
| 入场全用同一 delay 无级联 | `nth-of-type(n) { animation-delay: calc(n * 60ms) }` stagger |

### 案例
docs/examples/index.html DAG tab 节点入场动画: `.dag-svg g.node:nth-of-type(1){animation-delay:0s}` ... `:nth-of-type(8){animation-delay:.42s}`, 各节点按 `<g>` 顺序错峰 60ms 淡入。同 SVG 内有 `<path>` 边和 `<text>` 标签, 用 nth-of-type 避开。

### 关联
- frontend/examples-dag-81 (DAG 4 态范式 — 同源结构 `<g class="node">`, 入场动画在本规则)

## SVG 节点详情交互范式 (foreignObject popover + click Modal + 事件委托 + data-node JSON)

### 触发场景
SVG (DAG/图) 节点需交互查看详情: hover 弹轻量 popover, click 弹完整 Modal。SVG 内嵌 HTML 浮层受限场景, 单 HTML 文档/样例页禁引 JS 框架。

### 陷阱-正解

**陷阱①**: SVG `<text>` / 自定义浮层样式受限, 富 HTML (按钮/列表) 在 SVG 内渲染错乱。
**正解**: 用 `<foreignObject>` 在 SVG 内嵌一个 HTML 子树 (div+CSS), 突破 SVG 渲染限制; 父 `<g>` 设 `overflow:visible` 防裁切, foreignObject 用 width/height 控浮层尺寸。
```svg
<g class="node" style="overflow:visible">
  <rect .../>
  <foreignObject x=".." y=".." width="220" height="120" class="popover">
    <div xmlns="http://www.w3.org/1999/xhtml" class="popover-body">...</div>
  </foreignObject>
</g>
```

**陷阱②**: popover 坐标硬编码, 节点贴顶/右边时浮层出 viewBox 被裁。
**正解**: 居中对齐节点中心 (`x = node_center_x - popover_width/2`); 垂直上方优先 (`y = node_top - popover_height - gap`), 上方溢出 viewBox 改下方; 左右溢出同理夹回。

**陷阱③**: 节点详情 JSON 嵌 HTML data-* 属性, 双引号撞 HTML 属性引号。
**正解**: `data-node='{"k":"v"}'` — 外层 HTML 属性用单引号, JSON 内全用双引号; 中文直接写无需转义; 读时 `JSON.parse(el.dataset.node)`。

**陷阱④**: 每个节点各加 click 监听, 节点多时浪费内存, 动态增删还要重绑。
**正解**: 事件委托 — 父 panel 挂一次 click, `e.target.closest('.node')` 找命中节点, `JSON.parse(...)` 取数据; `<dialog>` 原生 Modal (`showModal()` + ESC/backdrop 关闭), ~15 行 JS 全搞定。
```js
panel.addEventListener('click', e => {
  const node = e.target.closest('.node'); if (!node) return;
  const data = JSON.parse(node.dataset.node);
  // fill <dialog> fields...
  dlg.showModal();
});
```

**陷阱⑤**: click 落在 `<g>` 内 `<rect>` / `<text>` 子元素, `e.target` 是子元素而非 `<g>`, 取不到 dataset。
**正解**: `e.target.closest('.node')` 自下而上兜底找最近 `.node` 祖先, 不依赖事件冒泡到 g; SVG 子元素 click 不冒泡时也命中。

### 适用
- 单 HTML 文档/样例页要嵌 SVG 节点详情交互, 禁引 JS 框架
- 节点数据驱动 (data-* 嵌 JSON), Modal 复用原生 dialog

### 案例
plugins/tools/skein/docs/examples/index.html DAG tab。

### 关联
- [frontend/examples-dag-81] 纯 SVG 4 态范式 (本规则的节点底座)
- [frontend/reconstruct-48] hover popover fixed 定位方案 (本规则 foreignObject 方案的另一选型, 互补)
- [frontend/examples-dag-82] SVG hover scale 必加 transform-box:fill-box
