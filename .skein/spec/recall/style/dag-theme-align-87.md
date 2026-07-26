---
title: 海滩主题双色平衡 (ocean 主色 + goldSand 暖色点睛, 单色冷蓝显单调)
layer: recall
category: style
keywords: [style,color,beach,ocean,goldSand,双色平衡,渐变,chip,进度条,样例页]
source: dag-theme-align
authored-by: skein-spec
created: 1785081488
status: active
related: [examples-timeline-antd-80,reconstruct-41,examples-dag-81]
updated: 1785081488
---

## 触发场景
海滩主题 (ocean + whiteSand + goldSand) 配色元件: 进度条 / chip / 强调点缀。单色 ocean (冷蓝) 平铺会显单调冷感, 需 goldSand (暖金) 破冷平衡。

## 陷阱-正解
**陷阱**: 全用 ocean 单色 (`#429cd1` / `#74b9e8`) 作强调色 (进度条 / chip / active 态), 整体偏冷单调, 与海滩主题 (蓝海+金沙滩双色) 不符。
**正解**: ocean 主色 + goldSand 暖色点睛, 双色平衡:
- **进度条/active 强调**: 用 `linear-gradient(90deg, ocean, goldSand)` 渐变 (`#429cd1 → #d4b066` light / `#74b9e8 → #e6c88b` dark), 单元素内完成蓝→金过渡
- **chip / 标签类**: 直接用 goldSand 系 (`rgba(240,217,160,0.28)` 底 + `#d4b066` 字), 替代默认 ocean, 破冷感
- **静态点 (legend/badge)**: 仍可用 ocean 单色, 渐变留给有"过程感"的元素 (进度条/动效)

## 反例表
| 禁 | 改为 |
|---|---|
| 进度条 `background:#429cd1` 单色冷蓝 | `linear-gradient(90deg,#429cd1,#d4b066)` ocean→goldSand 渐变 |
| chip `background:rgba(116,185,232,0.16)` ocean 系 | `rgba(240,217,160,0.28)` goldSand 系 |
| 全强调色都用 ocean 显冷 | 主 ocean + 点睛 goldSand 双色平衡 |
| 暗模用同一渐变 | dark 模各自调亮 (`#74b9e8 → #e6c88b`) |

## 案例
plugins/tools/skein/docs/examples/index.html:385-389 `.dag-pop-bar > i` 与 :407 `.dag-modal-bar` 进度条 ocean→goldSand 渐变 (light+dark 双套); :405-406 `.dag-modal-chip` goldSand 系替代 ocean。

## 关联
- style/examples-timeline-antd-80 (海滩配色扩阶 — 本规则是其"双色平衡"使用范式)
- style/reconstruct-41 (status 色相语义固定 — 本规则的渐变属"过程感"强调, 不破语义状态色)
- frontend/examples-dag-81 (DAG 4 态范式 — 本规则是 4 态中 active 态的色相处理)
