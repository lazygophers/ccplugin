---
name: design-color
description: 主题与配色设计 skill——帮用户做颜色搭配的优化、调整与设计决策。按产出媒介路由色彩落地：HTML/Web（CSS 变量）、原生 App（平台 token）、CLI（ANSI 色码）、TUI（真彩/256/16 降级）。帮选配色色系、调色板、主题风格、品牌色阶、暗模式、语义色，保证可访问性（对比度 / 色盲安全）。触发词：选配色/配色色系/调色/主题/色板/品牌色/暗模式/暗色/亮色/对比度/色盲/配色调优/改颜色/换主题/调色板/token。需后端的动态系统不适用。UI/UX 布局/组件/交互设计走姊妹 skill design-uiux。
---

# Design-Color · 主题与配色设计

一个 skill 专管色彩。按媒介落地色板，跨媒介共享色彩理论与可访问性。布局/组件/交互在姊妹 skill `design-uiux`。

## 适用 / 不适用

适用：Web 页面 / 原型配色、App 平台配色（iOS/Android/桌面）、CLI 彩色输出、TUI 主题、品牌色系设计、暗模式适配、数据可视化配色、对比度/色盲修复。

不适用：布局结构调整、组件选型、交互流程——走 `design-uiux`。需后端的动态系统走代码实现。

## 🔴 核心硬门 · 三方向初稿（100% 必走 · 跳过即失效）

任何会产出新视觉色彩的任务，**无论有无风格参考、有无品牌名**，第一步必须先出**三个差异化方向的色彩初稿**（每方向配完整色板：主色 + 辅助 + 中性阶 + 语义色 + 背景）等用户选定，再执行最终版。

- 「就按 Material 配色」不豁免——在 Material 语境内出 3 个差异化色板
- 三方向要真实分化（不同色相 / 饱和度 / 气质），不是同款换明度

### 🛑 失败模式与补救（硬门违反时）

| 触发 | 一线修复 | 兜底 |
|------|---------|------|
| 弱 runtime 无法并行出三版 | 串行逐版输出，每版落盘即给用户 | 单版 + 标注「受 runtime 限仅出 1 版」 |
| 用户选不定三方向 | 按语境推荐（信任→蓝系 / 活力→暖橙系 / 创新→紫系 / 自然→绿系） | 列三方向典型适用品牌气质让用户对号入座 |
| 配色决策缺语境信号 | 追问受众 / 场景 / 情绪 / 品牌调性四要素 | 默认中性蓝灰专业风，标注「默认值，可调整」 |
| 对比度验证工具不可用 | 用 WCAG 已知安全组合（深底浅字 / 避免黄白） | 标注「对比度待实测」并给出保守建议值 |
| WebSearch 事实验证失败 | 标注「未验证」后用保守值继续 | 用平台官方已知色值（如 iOS systemBlue #0A84FF） |

## 事实验证先行

涉及具体产品 / 平台 / 规格的断言（如 iOS systemBlue 色值、WCAG 版本要求），开工前先 `WebSearch` 验证，禁凭训练语料断言。

## 媒介路由表

收到任务先定媒介（多信号叠加按行序），再进对应 style 文件落地色彩：

| 产物形态 | 媒介 | 二级索引（选择指导） |
|---------|------|------|
| Web 页面 / 原型 / 可视化 / 幻灯片配色 | HTML | [html/INDEX](references/html/INDEX.md) |
| 原生 App(iOS / Android / 桌面) 配色 | App | [app/INDEX](references/app/INDEX.md) |
| 命令行工具彩色输出 / 风格 | CLI | [cli/INDEX](references/cli/INDEX.md) |
| 终端全屏 TUI 主题 / 色域降级 | TUI | [tui/INDEX](references/tui/INDEX.md) |

每个媒介 INDEX 指向该媒介的 `style.md`（现成主题模板 + 配色 token，复制即用）。

## 无关平台的共用层 · 色彩方法论

跨媒介色彩纪律，所有 medium 都引用 [color/INDEX](references/color/INDEX.md)：

| 主题 | 文件 | 覆盖 |
|------|------|------|
| 色彩理论 | [color/theory](references/color/theory.md) | 色相 / 明度 / 饱和 / 色环 / 配色法 |
| **主题总清单** | [color/themes-catalog](references/color/themes-catalog.md) | 20 内置主题 + 13 跨平台热门预设（Nord/Dracula/Catppuccin/OneDark/RoséPine/GitHub/Monokai...）全 token |
| **配色总清单** | [color/palettes-catalog](references/color/palettes-catalog.md) | 品牌色阶×6 + 中性阶×3 + 语义色 + Okabe-Ito + 4 命名色板 |
| 调色板模板 | [color/palette-templates](references/color/palette-templates.md) | 色阶生成 / 暗模式派生 / 自定义扩阶 |
| 可访问性 | [color/accessibility](references/color/accessibility.md) | 对比度 / 色盲安全 / 暗模式硬指标 |
| **UI 风格总清单** | [color/styles-catalog](references/color/styles-catalog.md) | 67 风格（49 通用 + 8 落地页 + 10 BI）含主色/亮暗模式/性能/a11y/移动/转化全属性 |

## 配色决策路径

1. **定语境**：受众 / 场景 / 情绪（信任→蓝、活力→橙、创新→紫，见 theory.md 语义）
2. **三方向初稿门**：从风格谱系出三套色板 → 用户选定
3. **配完整色板**：主色（1）+ 辅助（1-2）+ 中性阶（5-7）+ 语义色（4）+ 背景（2-3）
4. **可访问性硬指标**：对比度 ≥ 4.5:1（正文）/ ≥ 3:1（大字）；禁只靠颜色传信息；暗模式重调中性阶降饱和提对比
5. **固化 token**：按媒介落地（CSS 变量 / App token / ANSI / 真彩 hex）
6. **场景自适应**：亮/暗切换、色域降级（TUI）、TTY 关色（CLI）

## 各媒介色彩落地

- HTML → CSS 变量贴 `:root`（[html/style](references/html/style.md) 7 套主题模板）
- App → 平台 token（[app/style](references/app/style.md) 5 套含平台覆盖速查 iOS/iPadOS/watchOS/tvOS/Android/WearOS）
- CLI → ANSI 色码 + 语义前缀（[cli/style](references/cli/style.md) 含 shell 兼容速查）
- TUI → 真彩 hex，降级 256/16（[tui/style](references/tui/style.md) 含终端兼容速查 + 4 主题模板）

## 姊妹 skill

布局 / 组件 / 交互 / 信息架构 / 场景自适应的结构性问题 → `design-uiux`。本 skill 只管「颜色」，结构问题不在此处。

## 自检

- [ ] 色板含主色 + 辅助 + 中性阶 + 语义色
- [ ] 对比度达标（亮 / 暗，正文 ≥ 4.5:1）
- [ ] 禁只靠颜色传信息（加图标 / 文字冗余）
- [ ] 色盲安全（数据可视化用 Okabe-Ito）
- [ ] token 化，换肤一处生效
- [ ] 暗模式中性阶重调（降饱和、提对比、深蓝灰底非纯黑）
