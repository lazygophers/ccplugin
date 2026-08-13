# 主题总清单（Themes Catalog）

一处扫全部现成主题。两类：**A 各媒介内置主题**（已带 token，复制即用）+ **B 跨平台热门主题预设**（社区经典，跨媒介通用）。

> 选主题流程：① 本表扫气质定候选 → ② 点详情拿 token → ③ 去 medium style 落地为该媒介格式。

## A · 各媒介内置主题

| # | 主题 | 媒介 | 气质 | primary | accent | 详情 |
|---|------|------|------|---------|--------|------|
| 1 | 极简留白 Minimal Light | HTML | 性冷淡、大留白、黑主 | `#111111` | `#3b82f6` | [html/style](../html/style.md#模板-1--极简留白minimal-light) |
| 2 | 深空暗场 Deep Space | HTML | GitHub / 开发者 | `#58a6ff` | `#bc8cff` | [html/style](../html/style.md#模板-2--深空暗场deep-space) |
| 3 | 杂志编辑 Editorial | HTML | 报刊衬线、墨色红强调 | `#8b1e1e` | `#1a1a1a` | [html/style](../html/style.md#模板-3--杂志编辑editorial) |
| 4 | 玻璃拟物 Glassmorphism | HTML | 半透明模糊、柔渐变 | `#6366f1` | `#ec4899` | [html/style](../html/style.md#模板-4--玻璃拟物glassmorphism) |
| 5 | Neo-Brutalism 新野兽派 | HTML | 高饱和、粗黑边、硬阴影 | `#7c3aed` | `#ec4899` | [html/style](../html/style.md#模板-5--neo-brutalism新野兽派) |
| 6 | Material 平面 | HTML | Google 企业规范、层级阴影 | `#1976d2` | `#ff9800` | [html/style](../html/style.md#模板-6--material-平面企业规范) |
| 7 | 暖色手绘 Warm Hand-drawn | HTML | 暖橙圆角、亲切 | `#ea580c` | `#0891b2` | [html/style](../html/style.md#模板-7--暖色手绘warm-hand-drawn) |
| 8 | Apple HIG 风 | App | iOS 原生、系统色 | `#007AFF` | `#5856D6` | [app/style](../app/style.md#模板-1--apple-hig-风ios) |
| 9 | Material 3 风 | App | Android 原生、紫调 | `#6750A4` | `#7D5260` | [app/style](../app/style.md#模板-2--material-3-风android) |
| 10 | 桌面 Fluent / Neutral | App | Win 桌面、紧凑 | `#005FB8` | `#0078D4` | [app/style](../app/style.md#模板-3--桌面-fluent--neutral-风) |
| 11 | 消费活力风 | App | 电商 / 社交、高饱和红 | `#FF4D4F` | `#FA8C16` | [app/style](../app/style.md#模板-4--消费活力风跨平台电商--社交) |
| 12 | 极简原生风 | App | 跨平台、黑主克制 | `#111111` | `#3B82F6` | [app/style](../app/style.md#模板-5--极简原生风跨平台) |
| 13 | 极简 Unix 风 | CLI | 安静可组合、无色 | — | — | [cli/style](../cli/style.md#模板-1--极简-unix-风严肃开发者) |
| 14 | 彩色友好风 | CLI | npm/cargo、emoji 图标 | 绿/红/黄/蓝 | `⚙✔✖ℹ⚠` | [cli/style](../cli/style.md#模板-2--彩色友好风现代-cli如-npm--cargo) |
| 15 | 结构化表格风 | CLI | docker/kubectl、表格主 | — | — | [cli/style](../cli/style.md#模板-3--结构化表格风数据型工具如-docker--kubectl) |
| 16 | 向导对话风 | CLI | onboarding/init、交互引导 | — | — | [cli/style](../cli/style.md#模板-4--向导对话风onboarding--init-类) |
| 17 | Gruvbox 暖色 | TUI | 经典 vim、复古暖 | `#fe8019` | `#d3869b` | [tui/style](../tui/style.md#模板-1--gruvbox-暖色经典-vim-风) |
| 18 | Tokyo Night 冷色 | TUI | 现代编辑器、深低饱和 | `#7aa2f7` | `#bb9af7` | [tui/style](../tui/style.md#模板-2--tokyo-night-冷色现代编辑器风) |
| 19 | Solarized | TUI | 科学配色、色盲友好 | `#268bd2` | `#6c71c4` | [tui/style](../tui/style.md#模板-3--solarized科学配色色盲友好) |
| 20 | 极简单色 | TUI | 16 色安全、最大兼容 | cyan | reverse | [tui/style](../tui/style.md#模板-4--极简单色最大兼容16-色安全) |

## B · 跨平台热门主题预设

社区经典，跨 HTML / App / TUI 通用。每条带全 token，按媒介落地：HTML→CSS 变量、App→平台 token、TUI→按真彩/256/16 降级（见 [../tui/style.md](../tui/style.md) 色域降级表）。

### B1 · Nord — 北极冷调

```
bg:#242933  bg-subtle:#2E3440  card:#3B4252
text:#ECEFF4  text-muted:#D8DEE9  border:#4C566A
primary:#88C0D0  accent:#88C0D0
frost:#8FBCBB  #81A1C1  #5E81AC
success:#A3BE8C  warning:#EBCB8B  error:#BF616A  info:#81A1C1
```
气质：冷、克制、低对比。适合编辑器 / 长文阅读 / 数据工具。

### B2 · Dracula — 暗色高饱和

```
bg:#282A36  bg-subtle:#21222C  card:#44475A
text:#F8F8F2  text-muted:#BDBDBD  border:#6272A4
primary:#BD93F9  accent:#FF79C6
success:#50FA7B  warning:#F1FA8C  error:#FF5555  info:#8BE9FD
```
气质：深紫底、高饱和荧光。适合开发者工具 / 代码展示。

### B3 · Catppuccin Mocha — 柔和暖暗（最流行）

```
bg:#1E1E2E  bg-subtle:#181825  card:#313244
text:#CDD6F4  text-muted:#A6ADC8  border:#45475A
primary:#CBA6F7  accent:#F5C2E7  secondary:#89B4FA
rose:#F5E0DC  flamingo:#F2CDCD  pink:#F5C2E7  mauve:#CBA6F7  red:#F38BA8
maroon:#EBA0AC  peach:#FAB387  yellow:#F9E2AF  green:#A6E3A1
teal:#94E2D5  sky:#89DCEB  sapphire:#74C7EC  blue:#89B4FA  lavender:#B4BEFE
```
气质：柔、暖、低饱和多彩。适合现代产品 / 任何场景默认。

### B4 · Catppuccin Latte — 柔和亮色

```
bg:#EFF1F5  bg-subtle:#E6E9EF  card:#CCD0DA
text:#4C4F69  text-muted:#6C6F85  border:#BCC0CC
primary:#8839EF  accent:#EA76CB
mauve:#8839EF  red:#D20F39  green:#40A02B  yellow:#DF8E1D
blue:#1E66F5  peach:#FE640B  teal:#179299  sky:#04A5E5  lavender:#7287FD
```
气质：Mocha 的亮态镜像。适合亮模式产品。

### B5 · One Dark — Atom 经典

```
bg:#282C34  bg-subtle:#21252B  card:#2C313A
text:#ABB2BF  text-muted:#5C6370  border:#3E4451
primary:#61AFEF  accent:#C678DD
success:#98C379  warning:#E5C07B  error:#E06C75  info:#56B6C2
```
气质：平衡、通用、不刺眼。适合编辑器 / IDE 风。

### B6 · Rosé Pine — 玫瑰木暖暗

```
bg:#191724  bg-subtle:#1f1d2e  card:#26233a
text:#e0def4  text-muted:#908caa  border:#403d52
primary:#c4a7e7  accent:#ebbcba
success:#9ccfd8  warning:#f6c177  error:#eb6f92  info:#31748f
rose:#ebbcba  pine:#31748f  foam:#9ccfd8  iris:#c4a7e7
```
气质：文艺、玫瑰调、有质感。适合内容站 / 品牌 / 杂志。

### B7 · GitHub Light — 浅色文档

```
bg:#ffffff  bg-subtle:#f6f8fa  card:#ffffff
text:#24292f  text-muted:#57606a  border:#d0d7de
primary:#0969da  accent:#8250df
success:#1a7f37  warning:#9a6700  error:#cf222e  info:#0969da
```
气质：GitHub 风、清爽、可信。适合文档 / 技术站。

### B8 · GitHub Dark — 深色文档

```
bg:#0d1117  bg-subtle:#161b22  card:#161b22
text:#e6edf3  text-muted:#8b949e  border:#30363d
primary:#58a6ff  accent:#bc8cff
success:#3fb950  warning:#d29922  error:#f85149  info:#58a6ff
```
气质：深空暗场原型。适合开发者文档 / 数据看板。

### B9 · Monokai — 经典荧光

```
bg:#272822  bg-subtle:#1e1f1c  card:#3e3d32
text:#f8f8f2  text-muted:#75715e  border:#49483e
primary:#a6e22e  accent:#fd971f
success:#a6e22e  warning:#e6db74  error:#f92672  info:#66d9ef
purple:#ae81ff  pink:#f92672
```
气质：荧光、高对比、辨识度强。适合代码展示 / 强调场景。

### B10 · Night Owl — 深蓝夜色

```
bg:#011627  bg-subtle:#0a2942  card:#082a45
text:#d6deeb  text-muted:#8badc4  border:#2a3b54
primary:#7fdbff  accent:#c792ea
success:#22da6e  warning:#ffeb95  error:#ef5350  info:#7fdbff
yellow:#addb67  orange:#f78c6c  purple:#c792ea
```
气质：深蓝、冷静、护眼。适合夜间长用 / 数据密集。

### B11 · Synthwave '84 — 霓虹复古

```
bg:#241b2f  bg-subtle:#1a1721  card:#2a2139
text:#f92aad... → 实际 text:#b6b0c9  text-muted:#8480bb  border:#34294f
primary:#ff7edb  accent:#fe4450
success:#72f1b8  warning:#fede5d  error:#fe4450  info:#03edf6
cyan:#36f9f6  yellow:#fede5d  pink:#ff7edb  purple:#ff7edb
```
气质：赛博朋克、霓虹粉紫。适合潮牌 / 创意 / 落地页。

### B12 · Everforest — 自然森林绿

```
bg:#2d353b  bg-subtle:#232a2e  card:#343f44
text:#d3c6aa  text-muted:#9da9a0  border:#475258
primary:#a7c080  accent:#dbbc7f
success:#a7c080  warning:#dbbc7f  error:#e67e80  info:#7fbbb3
red:#e67e80  orange:#e69875  yellow:#dbbc7f  green:#a7c080  aqua:#7fbbb3  blue:#a7c080  purple:#d699b6
```
气质：自然、护眼、绿调。适合长阅读 / 健康产品。

### B13 · Gruvbox Light — Gruvbox 亮态

```
bg:#fbf1c7  bg-subtle:#f2e5bc  card:#ebdbb2
text:#3c3836  text-muted:#7c6f64  border:#d5c4a1
primary:#af3a03  accent:#427b58
success:#79740e  warning:#b57614  error:#9d0006  info:#076678
```
气质：复古暖亮。 Gruvbox 暗态见 A-17。

## 主题选择速查

| 场景 | 推荐 |
|------|------|
| 开发者工具 / 文档 | B7 GitHub Light / B8 GitHub Dark / 2 深空暗场 |
| 现代 SaaS 产品 | B3 Catppuccin Mocha / B4 Latte / 1 极简留白 |
| 内容站 / 杂志 / 品牌 | B6 Rosé Pine / 3 杂志编辑 |
| 电商 / 消费 / 活力 | 5 Neo-Brutalism / 11 消费活力风 |
| 教育 / 儿童 / 亲切 | 7 暖色手绘 |
| 编辑器 / IDE 风 | B5 One Dark / B2 Dracula / B1 Nord |
| 代码展示 / 强调 | B9 Monokai / B11 Synthwave |
| 长阅读 / 护眼 | B12 Everforest / B10 Night Owl |
| iOS 原生 | 8 Apple HIG |
| Android 原生 | 9 Material 3 |
| Windows 桌面 | 10 Fluent |
| CLI 现代风 | 14 彩色友好 |
| CLI 严肃 / 可组合 | 13 极简 Unix |
| TUI 经典 | 17 Gruvbox / 18 Tokyo Night / 19 Solarized |

## 跨媒介落地

主题选好后，去对应 medium 的 style 落地：

- HTML → CSS 变量贴 `:root`（见 [../html/style.md](../html/style.md)）
- App → 平台 token（见 [../app/style.md](../app/style.md)）
- CLI → ANSI 色码（见 [../cli/style.md](../cli/style.md) 彩色语义表）
- TUI → 真彩 hex，降级 256/16（见 [../tui/style.md](../tui/style.md) 色域降级表）

配色理论 + 品牌色阶生成 → [palette-templates.md](palette-templates.md)。
