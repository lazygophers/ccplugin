---
title: SVG 节点详情交互范式 (foreignObject popover + click Modal + 事件委托 + data-node JSON)
layer: recall
category: frontend
keywords: [frontend,svg,foreignobject,popover,modal,dialog,event-delegation,closest,data-node,json-attr,pointer-hit]
source: examples-dag
authored-by: skein-spec
created: 1785080629
status: active
related: [frontend/examples-dag-81,frontend/reconstruct-48,frontend/examples-dag-82]
updated: 1785080629
---

## 触发场景
SVG (DAG/图) 节点需交互查看详情: hover 弹轻量 popover, click 弹完整 Modal。SVG 内嵌 HTML 浮层受限场景, 单 HTML 文档/样例页禁引 JS 框架。

## 陷阱-正解

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

## 适用
- 单 HTML 文档/样例页要嵌 SVG 节点详情交互, 禁引 JS 框架
- 节点数据驱动 (data-* 嵌 JSON), Modal 复用原生 dialog

## 案例
plugins/tools/skein/docs/examples/index.html DAG tab。

## 关联
- [frontend/examples-dag-81] 纯 SVG 4 态范式 (本规则的节点底座)
- [frontend/reconstruct-48] hover popover fixed 定位方案 (本规则 foreignObject 方案的另一选型, 互补)
- [frontend/examples-dag-82] SVG hover scale 必加 transform-box:fill-box
