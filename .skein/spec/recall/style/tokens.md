---
title: tokens
layer: recall
category: style
keywords: [style,color,token,variable,css,glass,effect,oklch,theme]
status: active
---

## 组件色一律用 var(--token)，禁硬编码

### 触发场景
编写新组件或修改样式，需要配色。

### 陷阱-正解
**陷阱**：硬编码色值 `color: #3498db`。
**正解**：用派生令牌 `color: var(--accent)` 或语义色。

### 规则
允许唯一例外：彩底白字 `#fff` 与 body 底纹锚点。

### 关联
style/oklch-token-derivation (F-STYLE-1)

## glass 令牌派生 + backdrop-filter

### 触发场景
玻璃质感面板。

### 陷阱-正解
**陷阱**：硬编码 glass 样式。
**正解**：glass 令牌派生 (--glass-bg/brd/shadow 等)；配 backdrop-filter blur+saturate。

### 规则
仅 webapp 专属（board 无 glass 层）。

## oklch 双层派生令牌（seed + 锚点 → 语义色）

### 铁律

- MUST：:root seed 定义 `--h` (色相) / `--c-neutral` (中性染色) / `--h-accent` (accent 色相) + `--l-*` 锚点
- MUST：派生令牌 `--bg / --card / --fg / --head / --muted / --brd / --line / --accent / --st-pending/active/check/done/failed`
- MUST：状态色相 `--h-pending/active/check/done/failed` 全局固定不变（跨主题）
- MUST：组件只引派生名（var(--bg)），不硬编码色值
- MUST：两 app 同构 board/base.css:13-40 与 webapp/src/input.css:17-62 逐条对齐

### 反例表

| 禁 | 改为 |
|---|---|
| 组件用 `#3498db` 硬编码 | 用 `var(--accent)` 派生令牌 |
| 换肤修改组件 CSS | 仅改 seed + 锚点 |
