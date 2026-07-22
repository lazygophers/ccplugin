---
name: design-uiux
description: UI/UX 与布局设计——做界面布局/结构/导航/组件/交互的设计决策。触发：做UI/UX/布局/排版/导航/组件/交互/栅格/响应式/图表选型/字体配对。按媒介路由 HTML/Web、原生 App(iOS/Android/桌面)、CLI、TUI。需后端动态系统不适用；配色/主题/色板走姊妹 skill design-color。
---

<!-- 完整触发词（description 已含核心，此处备查）：做UI/UX/布局/排版/结构/导航/信息架构/组件/交互/栅格/间距/响应式/自适应/空状态/表单设计/onboarding/场景适配/行业推理/图表选型/字体配对 -->

# Design-UIUX · UI/UX 与布局设计

一个 skill 专管结构与交互。按媒介落地布局/组件，跨媒介共享 UI/UX 原则。配色/主题在姊妹 skill `design-color`。

## 适用 / 不适用

适用：Web 页面布局 / 原型结构、App 信息架构与导航、CLI 命令结构与参数布局、TUI 面板布局与焦点流转、组件选型与状态设计、交互流程与反馈、场景自适应（响应式 / 平台 / TTY / resize）、空状态 / 表单 / onboarding 设计。

不适用：配色 / 主题 / 色板 / 暗模式色彩——走 `design-color`。需后端的动态系统走代码实现。

## 🔴 核心硬门 · 三方向初稿（100% 必走 · 跳过即失效）

任何会产出新布局 / 交互结构的任务，**无论有无参考、有无品牌名**，第一步必须先出**三个差异化方向的结构初稿**等用户选定，再执行最终版。

- 「就按 Notion 布局做」不豁免——在 Notion 语境内出 3 个差异化结构
- 三方向要真实分化（不同信息架构 / 导航模式 / 密度），不是同款挪位置

### 🛑 失败模式与补救（硬门违反时）

| 触发 | 一线修复 | 兜底 |
|------|---------|------|
| 弱 runtime 无法并行出三版 | 串行逐版输出，每版落盘即给用户 | 单版 + 明确标注「受 runtime 限仅出 1 版，用户可指定补齐另两版方向」 |
| 用户选不定三方向 | 按场景推荐优先级（效率优先→低密度骨架 / 一致性优先→平台原生 / 常见度→主流模式）| 列三方向各自的典型适用场景让用户对号入座 |
| reference 路径不可达 | 降级到 [ui-ux/INDEX](references/ui-ux/INDEX.md) 共用层取原则 | 直接用内置设计原则（层级/对比/对齐/接近/一致/反馈/容错）兜底出结构 |
| WebSearch 事实验证失败 | 标注「未验证」后用保守值继续，禁凭空编 | 用平台官方文档已知安全值（如 iOS 44pt / WCAG 2.1 AA）

## 事实验证先行

涉及具体平台 / 框架 / 规格的断言（如 iOS 44pt 触控目标、WCAG 键盘可达要求），开工前先 `WebSearch` 验证，禁凭训练语料断言。

## 媒介路由表

收到任务先定媒介（多信号叠加按行序），再进对应 INDEX：

| 产物形态 | 媒介 | 二级索引（选择指导） |
|---------|------|------|
| Web 页面 / 原型 / 布局 / 组件结构 | HTML | [html/INDEX](references/html/INDEX.md) |
| 原生 App(iOS / Android / 桌面) 信息架构 / 导航 | App | [app/INDEX](references/app/INDEX.md) |
| 命令行工具命令结构 / 参数布局 | CLI | [cli/INDEX](references/cli/INDEX.md) |
| 终端全屏 TUI 面板布局 / 焦点流转 | TUI | [tui/INDEX](references/tui/INDEX.md) |

每个媒介 INDEX 按三维（**布局 / 场景 / 组件**）分流。

## 无关平台的共用层 · UI/UX 方法论

跨媒介设计纪律，所有 medium 都引用 [ui-ux/INDEX](references/ui-ux/INDEX.md)：

| 主题 | 文件 | 覆盖 |
|------|------|------|
| 设计原则 | [ui-ux/principles](references/ui-ux/principles.md) | 层级 / 对比 / 对齐 / 接近 / 一致 / 反馈 / 容错 |
| 信息架构 | [ui-ux/information-architecture](references/ui-ux/information-architecture.md) | 导航 / 内容优先级 / 心智模型 |
| 交互设计 | [ui-ux/interaction-design](references/ui-ux/interaction-design.md) | 交互模式 / 状态完整性 / 反馈 / 防错 |
| 可用性 / 无障碍 | [ui-ux/usability-a11y](references/ui-ux/usability-a11y.md) | Nielsen 10 / WCAG / 键盘 / 对比 |
| **主流场景设计建议** | [ui-ux/scenarios](references/ui-ux/scenarios.md) | 14 场景（电商/SaaS/BI/落地页/认证/onboarding/搜索/设置/社交/教育/表单/协作/通知）专属 UX 要点 + 常见坑 |
| **行业推理规则** | [ui-ux/industry-rules](references/ui-ux/industry-rules.md) | 100 行业 × 11 大类（科技/金融/医疗/电商/创意/新兴/教育/本地/政务/物流/其他）推荐模式 + 配色字体氛围 + 决策规则 + 反模式 |
| **UX 规则全清单** | [ui-ux/rules](references/ui-ux/rules.md) | 10 类 ~170 条（无障碍/触控/性能/风格/布局/排版色彩/动画/表单/导航/图表）带优先级 CRITICAL→LOW |
| **图表选型决策** | [ui-ux/charts](references/ui-ux/charts.md) | 25 图表类型 × 8 分组（趋势/对比/分布/地理/KPI/层级/金融/多变量）含 a11y 等级 + 数据量阈值 + 库选型 |
| **排版字体配对** | [ui-ux/typography](references/ui-ux/typography.md) | 74 配对 × 6 类（通用SaaS/奢侈编辑/科技数据/创意风格/专业多语言/CJK-RTL）含 Google Fonts 集成 + 权重/行高规则 |

## 布局决策路径

1. **定媒介 + 理解任务流程**：用户要完成什么 → 决定信息架构
2. **三方向初稿门**：出三版差异化结构（标注适合场景 / 优势 / 代价）→ 用户选定
3. **选布局骨架**：按媒介（HTML 栅格 / App 平台导航 / CLI 命令树 / TUI 面板模式）
4. **选组件 + 状态完整性**：default / hover / focus / active / disabled / loading / error / empty 八态
5. **场景自适应**：响应式断点 / 平台主题 / TTY 检测 / resize 重绘
6. **自检**：对照各 medium 文件末尾自检清单，浏览器 / 实际环境看实样，禁凭脑补

## 各媒介布局落地

- HTML → 栅格 / 间距尺度阶 / 响应式断点 / 容器查询（[html/layout](references/html/layout.md) + [scenes](references/html/scenes.md) + [components](references/html/components.md)）
- App → 信息架构 / 导航 / 平台布局 / 手势（[app/layout](references/app/layout.md) + [scenes](references/app/scenes.md) + [components](references/app/components.md)）+ 原生润色规则与预交付清单（[app/polish](references/app/polish.md)）
- CLI → 命令结构 / 命令树 / 参数布局（[cli/layout](references/cli/layout.md) + [scenes](references/cli/scenes.md) + [components](references/cli/components.md)）
- TUI → 框架 / 布局模式 / 栅格 / 焦点流转（[tui/layout](references/tui/layout.md) + [scenes](references/tui/scenes.md) + [components](references/tui/components.md)）

## 姊妹 skill

配色 / 主题 / 色板 / 暗模式色彩 / 数据可视化配色 → `design-color`。本 skill 只管「结构与交互」，颜色不在此处。

## 自检

- [ ] 信息架构清晰（导航 ≤7 项一级）
- [ ] 间距取自固定尺度阶（禁魔法数）
- [ ] 组件八态完整（含空 / 错 / 加载态）
- [ ] 焦点可见（键盘可达）
- [ ] 场景自适应覆盖（响应式 / 平台 / TTY / resize）
- [ ] 视觉层级焦点唯一
- [ ] 禁只靠颜色传信息（加图标 / 文字）
