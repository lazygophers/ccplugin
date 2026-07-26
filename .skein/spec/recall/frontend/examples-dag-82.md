---
title: SVG hover scale 必加 transform-box:fill-box (否则飞向 viewBox 原点)
layer: recall
category: frontend
keywords: [frontend,svg,hover,scale,transform-box,fill-box,transform-origin,center]
source: examples-dag
authored-by: skein-spec
created: 1785078861
status: active
related: [frontend/examples-dag-81]
updated: 1785078861
---

## 触发场景
SVG `<g class="node">` 形状 (rect/ellipse/polygon) hover `transform: scale(1.05)` 时, 默认 transform-origin 在 viewBox (0,0), 缩放会从画布原点「飞」到鼠标位置远处; 需让缩放从形状自身几何中心出发。

## 陷阱-正解
**陷阱**: `transform-origin: center` 在 SVG shape 上无效 (默认按 user space 的 viewBox 原点算, 不是形状 bbox 中心), scale 时形状飞向 viewBox (0,0)。
**正解**: 加 `transform-box: fill-box;` 让 transform 坐标系落在形状自身 bounding box, 此时 `transform-origin: center` 才指向形状几何中心。

## 反例表
| 禁 | 改为 |
|---|---|
| `.node:hover rect { transform: scale(1.05); transform-origin: center; }` 形状飞走 | 加 `transform-box: fill-box` |
| `transform-origin: 50% 50%` (无 fill-box) 仍按 viewBox 算 | `transform-box: fill-box` + `transform-origin: center` |

## 案例
docs/examples/index.html DAG tab `.dag-svg g.node:hover > rect` 选择器, 加 `transform-box: fill-box; transform: scale(1.05); transform-origin: center;` 后 hover 缩放稳定锚在节点中心。同时 `:hover` 抬出 drop-shadow filter 强化反馈。

## 关联
- frontend/examples-dag-81 (DAG 4 态范式 — 本规则补充 81 避坑表中 transform-box 的另一面: pulse 用 opacity, hover scale 必须用 fill-box)
