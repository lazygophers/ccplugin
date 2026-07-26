---
title: backdrop-filter 必成对写 -webkit- 前缀 (Safari/iOS 兜底, 否则 glass 失效退纯不透)
layer: recall
category: style
keywords: [style,css,backdrop-filter,webkit,safari,ios,前缀,glass,兼容,兜底]
source: dag-theme-align
authored-by: skein-spec
created: 1785081513
status: active
related: [reconstruct-40,dag-theme-align-86]
updated: 1785081513
---

## 触发场景
CSS 用 `backdrop-filter: blur(...)` 做 glass 质感 (popover / Modal / card 浮层)。Safari (含 iOS) 内核仍需 `-webkit-backdrop-filter` 前缀才生效, 漏写 Safari 下浮层退化为不透色块, glass 失效。

## 陷阱-正解
**陷阱**: 只写 `backdrop-filter:blur(10px)` 标准属性, Safari 不识别, 浮层变纯不透底, 与其他浏览器视觉效果不一致。
**正解**: 永远成对写, `-webkit-` 前缀在前标准在后:
```css
backdrop-filter:blur(10px);
-webkit-backdrop-filter:blur(10px);
```
(或反过来, 顺序不强约束, 浏览器各取所需)。Safari 18+ 虽已支持无前缀, 但兼容旧版/Safari iOS 仍需保留前缀, 零成本兜底。

## 反例表
| 禁 | 改为 |
|---|---|
| 只写 `backdrop-filter:blur(10px)` | 同时写 `-webkit-backdrop-filter:blur(10px)` |
| 漏前缀, Safari 浮层退化纯不透 | 成对写, 零成本兜底 |
| 假定现代浏览器无需前缀 | 旧 Safari/iOS 仍需, 保留前缀无害 |

## 案例
plugins/tools/skein/docs/examples/index.html:367 `.dag-pop-inner` + :394 `dialog.dag-modal` 同步成对写 `backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);` (Safari 兜底)。

## 关联
- style/reconstruct-40 (glass 令牌派生 — 本规则是其 Safari 兜底细节)
- style/dag-theme-align-86 (新 UI 元件复用 .glass 三件套 — backdrop-filter 是三件套之一, 本规则是其前缀兜底)
