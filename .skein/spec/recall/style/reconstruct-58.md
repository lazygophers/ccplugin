---
title: oklch 双层派生令牌（seed + 锚点 → 语义色）
layer: recall
category: style
keywords: [style,color,oklch,token,theme]
source: reconstruct
authored-by: skein-spec
created: 1784346892
status: active
related: []
updated: 1784346892
---

---
title: oklch 双层派生令牌（seed + 锚点 → 语义色）
layer: core
category: style
keywords: [style,color,oklch,token,theme]
source: reconstruct
authored-by: skein-spec
created: 1784346448
status: active
related: []
updated: 1784346448
---

## 铁律

- MUST：:root seed 定义 `--h` (色相) / `--c-neutral` (中性染色) / `--h-accent` (accent 色相) + `--l-*` 锚点
- MUST：派生令牌 `--bg / --card / --fg / --head / --muted / --brd / --line / --accent / --st-pending/active/check/done/failed`
- MUST：状态色相 `--h-pending/active/check/done/failed` 全局固定不变（跨主题）
- MUST：组件只引派生名（var(--bg)），不硬编码色值
- MUST：两 app 同构 board/base.css:13-40 与 webapp/src/input.css:17-62 逐条对齐

## 反例表

| 禁 | 改为 |
|---|---|
| 组件用 `#3498db` 硬编码 | 用 `var(--accent)` 派生令牌 |
| 换肤修改组件 CSS | 仅改 seed + 锚点 |
