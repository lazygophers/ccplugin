---
title: SVG 级联动画选择器用 :nth-of-type 不用 :nth-child (避开 path/text 兄弟污染)
layer: recall
category: frontend
keywords: [frontend,svg,animation,cascade,nth-of-type,nth-child,entrance,stagger,选择器]
source: examples-dag
authored-by: skein-spec
created: 1785078866
status: active
related: [frontend/examples-dag-81]
updated: 1785078866
---

## 触发场景
SVG 节点 (`<g>`) 入场级联动画 (依次淡入) 需按 `<g>` 兄弟顺序写 nth delay, 选择器写错会把 path/text 等非目标兄弟也算进去, 导致 delay 错位。

## 陷阱-正解
**陷阱**: `:nth-child(n)` 数所有兄弟节点 (含 `<path>` / `<text>` / `<defs>` 等混合标签), 节点实际位置错位, 级联节奏乱。
**正解**: `:nth-of-type(n)` 只数同标签 (`<g>`) 兄弟, path/text 不计入索引, 级联按 `<g>` 真实顺序触发。

## 反例表
| 禁 | 改为 |
|---|---|
| `.dag-svg g.node:nth-child(2)` 含 path/text 污染 | `.dag-svg g.node:nth-of-type(2)` |
| 入场全用同一 delay 无级联 | `nth-of-type(n) { animation-delay: calc(n * 60ms) }` stagger |

## 案例
docs/examples/index.html DAG tab 节点入场动画: `.dag-svg g.node:nth-of-type(1){animation-delay:0s}` ... `:nth-of-type(8){animation-delay:.42s}`, 各节点按 `<g>` 顺序错峰 60ms 淡入。同 SVG 内有 `<path>` 边和 `<text>` 标签, 用 nth-of-type 避开。

## 关联
- frontend/examples-dag-81 (DAG 4 态范式 — 同源结构 `<g class="node">`, 入场动画在本规则)
