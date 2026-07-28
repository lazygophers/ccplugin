---
title: theme
layer: recall
category: style
keywords: [style,glass,backdrop-blur,半透,暖金shadow,主题统一,popover,modal,样例页,新元件,color,beach,ocean,goldSand,双色平衡,渐变,chip,进度条,theme,status,semantic,done,failed,主题适配,语义色,红线,css,backdrop-filter,webkit,safari,ios,前缀,兼容,兜底,tailwind,whiteSand,wave,gradient,扩阶,样例,dark,mode,localStorage]
status: active
---

## 新 UI 元件先复用 .glass 三件套 (半透底 + backdrop-blur + 暖金 shadow) 与主题统一

### 触发场景
新加 UI 元件 (popover / Modal / card / panel / 浮层) 要与既有 glass 质感主题统一, 避纯白纯色底在已统一 glass 半透的页面里割裂。

### 陷阱-正解
**陷阱**: 新元件直接 `background:#fff` / `#fffefb` 纯不透底, 与页面已 glass 化的 panel / card 质感断层; 或 shadow 用通用冷灰 (`rgba(15,32,51,.12)`) 显得疏离。
**正解**: 新元件第一反应复用 `.glass` utility (`backdrop-filter:blur(10-14px)` + 半透 0.82-0.88 底色 + 暖金/暖灰 shadow), 三件套缺一不可:
- **半透底**: `rgba(255,254,251,0.82)` (light) / `rgba(22,44,66,0.85-0.9)` (dark), 永远禁 `#fff`/`#fffefb` 纯不透
- **backdrop-blur**: `blur(10px)` (popover) / `blur(14px)` (Modal, 略大), 配 `-webkit-backdrop-filter` Safari 兜底 (见姊妹规则)
- **暖金 shadow**: `0 4px 14px rgba(212,176,102,0.18-0.2)` (light) — 用 goldSand 暖金替代冷灰, 与海滩主题对齐; dark 同样用金色调 shadow

### 反例表
| 禁 | 改为 |
|---|---|
| `background:#fffefb` 纯不透底 | `rgba(255,254,251,0.82)` + `backdrop-filter:blur(10px)` |
| `box-shadow:0 4px 12px rgba(15,32,51,0.12)` 冷灰 | `0 4px 14px rgba(212,176,102,0.18)` 暖金 |
| 只在 `.glass` utility 用, 新元件各写一份 | 复用 utility, 或同款三件套手写 |
| Modal 用更冷 shadow 比 popover | Modal shadow 暖金浓度略高 (0.2 vs 0.18) 保持主题一致 |

### 案例
plugins/tools/skein/docs/examples/index.html:367-412 DAG tab `.dag-pop-inner` (popover) + `dialog.dag-modal` (Modal) 同步改 glass: 半透底 0.82/0.85/0.88/0.9 + blur(10px)/blur(14px) + 暖金 shadow 0.18/0.2, 与页面既有 `.glass` 海滩主题统一。

### 关联
- style/reconstruct-40 (glass 令牌派生 — 生产场景走令牌, 样例页走 utility, 互补)
- style/reconstruct-06 (组件色用 var(--token) — 样例页 tailwind.config 命名色阶例外)
- frontend/examples-timeline-antd-79 (单 HTML 样例 Modal <dialog> 范式 — 本规则是其主题化落地)

## 海滩主题双色平衡 (ocean 主色 + goldSand 暖色点睛, 单色冷蓝显单调)

### 触发场景
海滩主题 (ocean + whiteSand + goldSand) 配色元件: 进度条 / chip / 强调点缀。单色 ocean (冷蓝) 平铺会显单调冷感, 需 goldSand (暖金) 破冷平衡。

### 陷阱-正解
**陷阱**: 全用 ocean 单色 (`#429cd1` / `#74b9e8`) 作强调色 (进度条 / chip / active 态), 整体偏冷单调, 与海滩主题 (蓝海+金沙滩双色) 不符。
**正解**: ocean 主色 + goldSand 暖色点睛, 双色平衡:
- **进度条/active 强调**: 用 `linear-gradient(90deg, ocean, goldSand)` 渐变 (`#429cd1 → #d4b066` light / `#74b9e8 → #e6c88b` dark), 单元素内完成蓝→金过渡
- **chip / 标签类**: 直接用 goldSand 系 (`rgba(240,217,160,0.28)` 底 + `#d4b066` 字), 替代默认 ocean, 破冷感
- **静态点 (legend/badge)**: 仍可用 ocean 单色, 渐变留给有"过程感"的元素 (进度条/动效)

### 反例表
| 禁 | 改为 |
|---|---|
| 进度条 `background:#429cd1` 单色冷蓝 | `linear-gradient(90deg,#429cd1,#d4b066)` ocean→goldSand 渐变 |
| chip `background:rgba(116,185,232,0.16)` ocean 系 | `rgba(240,217,160,0.28)` goldSand 系 |
| 全强调色都用 ocean 显冷 | 主 ocean + 点睛 goldSand 双色平衡 |
| 暗模用同一渐变 | dark 模各自调亮 (`#74b9e8 → #e6c88b`) |

### 案例
plugins/tools/skein/docs/examples/index.html:385-389 `.dag-pop-bar > i` 与 :407 `.dag-modal-bar` 进度条 ocean→goldSand 渐变 (light+dark 双套); :405-406 `.dag-modal-chip` goldSand 系替代 ocean。

### 关联
- style/examples-timeline-antd-80 (海滩配色扩阶 — 本规则是其"双色平衡"使用范式)
- style/reconstruct-41 (status 色相语义固定 — 本规则的渐变属"过程感"强调, 不破语义状态色)
- frontend/examples-dag-81 (DAG 4 态范式 — 本规则是 4 态中 active 态的色相处理)

## 主题适配红线: 只改容器质感+强调色, 状态色 (done/failed/active/pending) 不动

### 触发场景
主题适配 (调容器质感 / 强调色 / 配色风格) 时, 既有语义状态色 (done=success / failed=danger / active=进行中 / pending=待执行) 已承载用户认知, 不能在适配中改色相。

### 陷阱-正解
**陷阱**: 主题大改时顺手把 `.done` / `.failed` 也按新主题色 (如 goldSand) 重染, 破坏跨主题/跨页面的状态语义一致性, 用户需重新学习色彩映射。
**正解**: 主题适配操作清单 — 只改两类, 状态色不动:
- **改**: 容器质感 (background 半透 / backdrop-blur / shadow / border-radius) + 强调色 (chip / 进度条 / active 点缀)
- **不改**: 语义状态色 (`.done` / `.failed` / `.active` / `.pending` 的 background/color), 保持 `#48bb78`(success) / `#e53e3e`(danger) 等跨主题固定值

操作前在脑里画一条线: 状态选择器 (`.done`/`.failed`/...) 一律不动, 通用容器/强调选择器 (`.chip`/`.bar`/`.modal`) 自由适配。

### 反例表
| 禁 | 改为 |
|---|---|
| 主题适配顺手 `.done{background:goldSand}` | `.done` 留 `#48bb78` 不动, 只改容器 |
| 状态色随主题换肤 | 状态色相全局固定 (见 reconstruct-41) |
| 改 Modal 容器时连 `.dag-pop-bar.done > i` 也重染 | `.done` / `.failed` 选择器一票否决不动 |

### 案例
plugins/tools/skein/docs/examples/index.html dag-theme-align task: `.dag-pop-bar > i` (默认/active) 改 ocean→goldSand 渐变, 但 `.dag-pop-bar.done > i` 保留 `#48bb78` / `.failed > i` 保留 `#e53e3e`; Modal `.dag-modal-chip` (通用) 改 goldSand, `.dag-modal-bar.done`/`.failed` 不动。

### 关联
- style/reconstruct-41 (status 色相语义固定 — 本规则是其操作层落地: 主题适配时不破语义色)
- style/reconstruct-39 (主题双轨 — 本规则是切轨时的"红线")
- frontend/examples-dag-81 (DAG 4 态范式 — 本规则保护其 4 态色相)

## backdrop-filter 必成对写 -webkit- 前缀 (Safari/iOS 兜底, 否则 glass 失效退纯不透)

### 触发场景
CSS 用 `backdrop-filter: blur(...)` 做 glass 质感 (popover / Modal / card 浮层)。Safari (含 iOS) 内核仍需 `-webkit-backdrop-filter` 前缀才生效, 漏写 Safari 下浮层退化为不透色块, glass 失效。

### 陷阱-正解
**陷阱**: 只写 `backdrop-filter:blur(10px)` 标准属性, Safari 不识别, 浮层变纯不透底, 与其他浏览器视觉效果不一致。
**正解**: 永远成对写, `-webkit-` 前缀在前标准在后:
```css
backdrop-filter:blur(10px);
-webkit-backdrop-filter:blur(10px);
```
(或反过来, 顺序不强约束, 浏览器各取所需)。Safari 18+ 虽已支持无前缀, 但兼容旧版/Safari iOS 仍需保留前缀, 零成本兜底。

### 反例表
| 禁 | 改为 |
|---|---|
| 只写 `backdrop-filter:blur(10px)` | 同时写 `-webkit-backdrop-filter:blur(10px)` |
| 漏前缀, Safari 浮层退化纯不透 | 成对写, 零成本兜底 |
| 假定现代浏览器无需前缀 | 旧 Safari/iOS 仍需, 保留前缀无害 |

### 案例
plugins/tools/skein/docs/examples/index.html:367 `.dag-pop-inner` + :394 `dialog.dag-modal` 同步成对写 `backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);` (Safari 兜底)。

### 关联
- style/reconstruct-40 (glass 令牌派生 — 本规则是其 Safari 兜底细节)
- style/dag-theme-align-86 (新 UI 元件复用 .glass 三件套 — backdrop-filter 是三件套之一, 本规则是其前缀兜底)

## 海滩配色扩阶范式 (ocean 5 阶 + whiteSand/goldSand 拆分 + wave/foam + body 渐变)

### 触发场景
样例页 / 海滩主题要扩色阶, 不能只用单色 ocean + sand 双 token, 需要层次感 + 浪花渐变。

### 陷阱-正解
**陷阱**: 单色 token (ocean/sand) 平铺, 缺层次; 或硬编码具体色值散落各处。
**正解**: 配色按自然语言分族扩阶, 每族 3-5 阶 + 渐变 utility:
- **海蓝 ocean 5 阶**: foam (浪花浅) / shallow (浅海) / mid (近海) / deep (深海) / abyss (海沟)
- **白沙滩 whiteSand 3 色**: pearl / shell / cream (拆自原 sand-pale)
- **金沙滩 goldSand 4 色**: light / mid / deep / sunset (拆自原 sand-gold/dark)
- **浪花渐变 .bg-wave**: `linear-gradient(90deg, foam → shallow)`
- **body 底纹**: `linear-gradient(180deg, pearl 0% → cream 50% → foam 100%)` 体现白沙滩→大海层次
- **暗色 night 3 阶**: deep (夜幕) / base (夜色海) / mid (暗海)

### 反例表
| 禁 | 改为 |
|---|---|
| `sand` 单 token 既表白沙又表金沙 | 拆 `whiteSand` + `goldSand` 各自多阶 |
| 配色硬编码散在 utility | 集中 tailwind.config.theme.extend.colors 一次性定义 |
| body 用纯色背景 | 渐变 `linear-gradient(180deg, …)` 体现层次 |

### 案例
docs/examples/index.html:15-46 (tailwind.config ocean/whiteSand/goldSand/night 定义), :56-66 (.bg-fluid-light/dark body 渐变), :68-70 (.bg-wave utility), :363-412 (色卡 tab 完整展示)。

### 关联
- style/reconstruct-06.md (组件色用 var(--token) 禁硬编码 — 本条是扩阶范式, 互补)
- style/reconstruct-39.md (主题双轨 data-theme 切换 — 本条海滩主题是 light/dark 双模落地)
- style/reconstruct-58.md (oklch 双层派生令牌 — 本条 tailwind.config 直接命名色阶, 不走 CSS 变量派生, 适合样例页非生产场景)

## 主题双轨：两套 CSS + data-theme 切换 + localStorage

### 触发场景
支持浅/暗主题切换。

### 陷阱-正解
**陷阱**：仅一套 CSS，用 JS 改色。
**正解**：两套 CSS 同加载（data-theme 选择器），仅改 data-theme + localStorage 切换。

### 规则
后端同时 link skein.css + skein-dark.css；前端 data-theme + localStorage 持久化；优先级 localStorage > prefers-color-scheme。

## status 色相语义固定（跨主题不变）

### 触发场景
状态染色（待/进行/完成等)。

### 陷阱-正解
**陷阱**：状态色跨主题变。
**正解**：状态色相 (--h-pending/active/done 等) 全局固定，仅 surface 染色与明度换肤。

### 规则
pending=蓝245 / active=橙70 / check=青200 / done=绿150 / failed=红25。
