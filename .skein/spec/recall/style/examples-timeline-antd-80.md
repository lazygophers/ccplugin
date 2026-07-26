---
title: 海滩配色扩阶范式 (ocean 5 阶 + whiteSand/goldSand 拆分 + wave/foam + body 渐变)
layer: recall
category: style
keywords: [style,color,tailwind,ocean,whiteSand,goldSand,wave,beach,gradient,扩阶,样例]
source: examples-timeline-antd
authored-by: skein-spec
created: 1785074374
status: active
related: [reconstruct-06,reconstruct-39,reconstruct-58]
updated: 1785074374
---

## 触发场景
样例页 / 海滩主题要扩色阶, 不能只用单色 ocean + sand 双 token, 需要层次感 + 浪花渐变。

## 陷阱-正解
**陷阱**: 单色 token (ocean/sand) 平铺, 缺层次; 或硬编码具体色值散落各处。
**正解**: 配色按自然语言分族扩阶, 每族 3-5 阶 + 渐变 utility:
- **海蓝 ocean 5 阶**: foam (浪花浅) / shallow (浅海) / mid (近海) / deep (深海) / abyss (海沟)
- **白沙滩 whiteSand 3 色**: pearl / shell / cream (拆自原 sand-pale)
- **金沙滩 goldSand 4 色**: light / mid / deep / sunset (拆自原 sand-gold/dark)
- **浪花渐变 .bg-wave**: `linear-gradient(90deg, foam → shallow)`
- **body 底纹**: `linear-gradient(180deg, pearl 0% → cream 50% → foam 100%)` 体现白沙滩→大海层次
- **暗色 night 3 阶**: deep (夜幕) / base (夜色海) / mid (暗海)

## 反例表
| 禁 | 改为 |
|---|---|
| `sand` 单 token 既表白沙又表金沙 | 拆 `whiteSand` + `goldSand` 各自多阶 |
| 配色硬编码散在 utility | 集中 tailwind.config.theme.extend.colors 一次性定义 |
| body 用纯色背景 | 渐变 `linear-gradient(180deg, …)` 体现层次 |

## 案例
docs/examples/index.html:15-46 (tailwind.config ocean/whiteSand/goldSand/night 定义), :56-66 (.bg-fluid-light/dark body 渐变), :68-70 (.bg-wave utility), :363-412 (色卡 tab 完整展示)。

## 关联
- style/reconstruct-06.md (组件色用 var(--token) 禁硬编码 — 本条是扩阶范式, 互补)
- style/reconstruct-39.md (主题双轨 data-theme 切换 — 本条海滩主题是 light/dark 双模落地)
- style/reconstruct-58.md (oklch 双层派生令牌 — 本条 tailwind.config 直接命名色阶, 不走 CSS 变量派生, 适合样例页非生产场景)
