---
title: 新 UI 元件先复用 .glass 三件套 (半透底 + backdrop-blur + 暖金 shadow) 与主题统一
layer: recall
category: style
keywords: [style,glass,backdrop-blur,半透,暖金shadow,主题统一,popover,modal,样例页,新元件]
source: dag-theme-align
authored-by: skein-spec
created: 1785081475
status: active
related: [reconstruct-40,reconstruct-06,examples-timeline-antd-79]
updated: 1785081475
---

## 触发场景
新加 UI 元件 (popover / Modal / card / panel / 浮层) 要与既有 glass 质感主题统一, 避纯白纯色底在已统一 glass 半透的页面里割裂。

## 陷阱-正解
**陷阱**: 新元件直接 `background:#fff` / `#fffefb` 纯不透底, 与页面已 glass 化的 panel / card 质感断层; 或 shadow 用通用冷灰 (`rgba(15,32,51,.12)`) 显得疏离。
**正解**: 新元件第一反应复用 `.glass` utility (`backdrop-filter:blur(10-14px)` + 半透 0.82-0.88 底色 + 暖金/暖灰 shadow), 三件套缺一不可:
- **半透底**: `rgba(255,254,251,0.82)` (light) / `rgba(22,44,66,0.85-0.9)` (dark), 永远禁 `#fff`/`#fffefb` 纯不透
- **backdrop-blur**: `blur(10px)` (popover) / `blur(14px)` (Modal, 略大), 配 `-webkit-backdrop-filter` Safari 兜底 (见姊妹规则)
- **暖金 shadow**: `0 4px 14px rgba(212,176,102,0.18-0.2)` (light) — 用 goldSand 暖金替代冷灰, 与海滩主题对齐; dark 同样用金色调 shadow

## 反例表
| 禁 | 改为 |
|---|---|
| `background:#fffefb` 纯不透底 | `rgba(255,254,251,0.82)` + `backdrop-filter:blur(10px)` |
| `box-shadow:0 4px 12px rgba(15,32,51,0.12)` 冷灰 | `0 4px 14px rgba(212,176,102,0.18)` 暖金 |
| 只在 `.glass` utility 用, 新元件各写一份 | 复用 utility, 或同款三件套手写 |
| Modal 用更冷 shadow 比 popover | Modal shadow 暖金浓度略高 (0.2 vs 0.18) 保持主题一致 |

## 案例
plugins/tools/skein/docs/examples/index.html:367-412 DAG tab `.dag-pop-inner` (popover) + `dialog.dag-modal` (Modal) 同步改 glass: 半透底 0.82/0.85/0.88/0.9 + blur(10px)/blur(14px) + 暖金 shadow 0.18/0.2, 与页面既有 `.glass` 海滩主题统一。

## 关联
- style/reconstruct-40 (glass 令牌派生 — 生产场景走令牌, 样例页走 utility, 互补)
- style/reconstruct-06 (组件色用 var(--token) — 样例页 tailwind.config 命名色阶例外)
- frontend/examples-timeline-antd-79 (单 HTML 样例 Modal <dialog> 范式 — 本规则是其主题化落地)
