---
title: 主题适配红线: 只改容器质感+强调色, 状态色 (done/failed/active/pending) 不动
layer: recall
category: style
keywords: [style,theme,status,semantic,done,failed,主题适配,语义色,红线,样例页]
source: dag-theme-align
authored-by: skein-spec
created: 1785081502
status: active
related: [reconstruct-41,reconstruct-39,examples-dag-81]
updated: 1785081502
---

## 触发场景
主题适配 (调容器质感 / 强调色 / 配色风格) 时, 既有语义状态色 (done=success / failed=danger / active=进行中 / pending=待执行) 已承载用户认知, 不能在适配中改色相。

## 陷阱-正解
**陷阱**: 主题大改时顺手把 `.done` / `.failed` 也按新主题色 (如 goldSand) 重染, 破坏跨主题/跨页面的状态语义一致性, 用户需重新学习色彩映射。
**正解**: 主题适配操作清单 — 只改两类, 状态色不动:
- **改**: 容器质感 (background 半透 / backdrop-blur / shadow / border-radius) + 强调色 (chip / 进度条 / active 点缀)
- **不改**: 语义状态色 (`.done` / `.failed` / `.active` / `.pending` 的 background/color), 保持 `#48bb78`(success) / `#e53e3e`(danger) 等跨主题固定值

操作前在脑里画一条线: 状态选择器 (`.done`/`.failed`/...) 一律不动, 通用容器/强调选择器 (`.chip`/`.bar`/`.modal`) 自由适配。

## 反例表
| 禁 | 改为 |
|---|---|
| 主题适配顺手 `.done{background:goldSand}` | `.done` 留 `#48bb78` 不动, 只改容器 |
| 状态色随主题换肤 | 状态色相全局固定 (见 reconstruct-41) |
| 改 Modal 容器时连 `.dag-pop-bar.done > i` 也重染 | `.done` / `.failed` 选择器一票否决不动 |

## 案例
plugins/tools/skein/docs/examples/index.html dag-theme-align task: `.dag-pop-bar > i` (默认/active) 改 ocean→goldSand 渐变, 但 `.dag-pop-bar.done > i` 保留 `#48bb78` / `.failed > i` 保留 `#e53e3e`; Modal `.dag-modal-chip` (通用) 改 goldSand, `.dag-modal-bar.done`/`.failed` 不动。

## 关联
- style/reconstruct-41 (status 色相语义固定 — 本规则是其操作层落地: 主题适配时不破语义色)
- style/reconstruct-39 (主题双轨 — 本规则是切轨时的"红线")
- frontend/examples-dag-81 (DAG 4 态范式 — 本规则保护其 4 态色相)
