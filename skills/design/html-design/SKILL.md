---
name: html-design
description: HTML-first 设计工作台——帮用户优化 UI/UX、选前端设计方案与风格、定布局与配色、按场景自适应，并把结果以 HTML 落地后打包导出。覆盖四模式：①UI/UX 界面（App/网页高保真原型、布局、组件设计与选择）②数据可视化（架构图/流程/时序/信息图，HTML→SVG/PNG）③图像设计（封面/配图/卡片/海报，HTML→PNG）④演示排版（HTML 幻灯片、HTML→PDF、HTML→微信）。触发词：做设计/UI/UX/原型/mockup/布局/组件、选风格/配色/色系、画架构图/流程图/信息图、做封面/海报/配图/卡片、做PPT/幻灯片、自适应/响应式、做个好看的HTML页面。需后端的动态系统/生产级 Web App 不适用。
---

# HTML-Design · HTML-first 设计工作台

HTML 是唯一媒介。任何视觉产出先落到 standalone HTML，再按需打包导出为目标格式。不为 PNG / SVG / PDF / 幻灯片 / 微信图文各开独立流程——它们都是 HTML 的下游。

本 skill 的核心价值是**帮用户做设计决策**：选方案、选风格、选配色色系、选布局、选组件，让产物自适应不同场景。

## 适用 / 不适用

适用：UI/UX 高保真原型、布局与组件设计、数据可视化、图像物料、演示排版。

不适用：需后端的动态系统、生产级 Web App、SEO 站点——走代码实现，不是设计产出。

## 核心硬门 · 三方向初稿（100% 必走）

任何会产出新视觉的任务，**无论有无风格参考、有无品牌名**，第一步必须先出**三个差异化方向的真实初稿**等用户选定，再执行最终版。

- 用户说「就按 Apple 风格做」不豁免——在 Apple 语境内出 3 个差异化诠释
- 三方向要真实分化（不同布局骨架 / 不同风格 / 不同配色情绪 / 不同信息密度），不是同款换色
- 弱 runtime（无并行 subagent）→ 串行出三版，禁挂起等待
- 风格词收窄的是解释空间，不豁免选择权

## 事实验证先行

涉及具体产品 / 技术 / 事件的存在性、发布状态、版本号、规格的断言，开工前先 `WebSearch` 验证，禁凭训练语料断言。搜不到或模糊 → 问用户。事实错了后面全歪。

## 模式路由表

收到任务先定模式（多信号叠加按行序）：

| 任务信号 | 模式 | 参考 |
|---------|------|------|
| App / 网页原型、UI 界面、布局、组件、选风格 / 配色 | UI/UX 界面 | [design-styles](references/design-styles.md) · [layout-system](references/layout-system.md) · [component-guide](references/component-guide.md) |
| 架构图 / 流程图 / 时序图 / 信息图 / 数据图 | 数据可视化 | [data-viz](references/data-viz.md) |
| 封面 / 配图 / 卡片 / 海报 / 邀请函 | 图像设计 | [image-design](references/image-design.md) |
| PPT / 幻灯片 / 报告 PDF / 微信图文 | 演示排版 | [slide-deck](references/slide-deck.md) |
| 评审 / 打分 / 找问题 | 任意模式 + §评审 | |

## 共享工作流（所有模式）

1. **定模式 + 收集约束**：受众、品牌色、尺寸、情绪、目标场景（桌面 / 移动 / 印刷 / 社媒）
2. **三方向初稿门**：出三版差异化真实初稿 → 用户选定 → 固化该项目的风格 token
3. **执行选定方向**：standalone HTML（内联或 CDN 白名单，双击可开）
4. **场景自适应**：亮 / 暗模式、密度切换、响应式断点全部在该产物内覆盖（见 [layout-system](references/layout-system.md)）
5. **自检**：浏览器打开看实样，禁凭代码脑补效果
6. **导出**：按目标格式走 [export-pipeline](references/export-pipeline.md)
7. **交付**：HTML 源 + 导出物 + 导出脚本

### 技术红线

- 纯前端，零后端、零构建步骤（或构建结果自包含）
- 外部依赖仅限 CDN 白名单：Tailwind Play CDN / GSAP / D3 / 三方图标库；其余自写
- 单文件优先；确需拆分时同目录 `assets/`
- 中文用系统字体栈，别引私有字体（除非用户提供字体文件）

---

## UI/UX 优化能力（跨模式核心）

这是本 skill 区别于「只会画图」的地方——主动帮用户做设计判断：

### 选前端设计方案

- 先理解任务流程（用户要完成什么），再选布局模式（见 [layout-system](references/layout-system.md) 常见布局模式表）
- 多方案对比时并排出三版，在真实初稿上选，不在抽象描述上选
- 每个方案标注：适合什么场景、优势、代价

### 选风格与配色色系

详见 [design-styles.md](references/design-styles.md)。决策路径：

1. 定语境（受众 / 场景 / 情绪关键词）
2. 从风格谱系（极简 / 暗场 / 杂志 / 玻璃 / Neo-brutalism / Material / 暖色手绘）选三个方向
3. 每方向配一套完整色板（主色 + 辅助 + 中性阶 + 语义色 + 背景），禁只挑单色
4. 配可访问性硬指标（对比度 ≥ 4.5:1、不只靠颜色传信息、暗模式重新调中性阶）
5. 选定后固化 token，全局复用

### 选布局与自适应场景

详见 [layout-system.md](references/layout-system.md)：

- 间距取自固定尺度阶（4 / 8px 基数），禁魔法数
- 移动优先断点：结构随宽度变（列数 / 导航形态 / 侧栏显隐 / 密度）
- 场景切换用 CSS 变量：`[data-theme]`（亮暗）、`[data-density]`（紧凑 / 舒适）、容器查询（组件级自适应）
- 视觉层级：尺寸 > 留白 > 对比 > 位置，焦点唯一

### 选组件与组件设计

详见 [component-guide.md](references/component-guide.md)：

- 选组件先问：用户要完成什么任务？组件状态空间全不全？响应式塌不塌？
- 选型边界（该用 Switch 还是 Checkbox、Segmented 还是下拉、Stepper 还是输入框）
- 状态完整性：default / hover / focus / active / disabled / loading / error / empty 全覆盖
- 组件 token 化：值取自项目 token，换肤 / 密度 / 暗模式一处生效全局生效
- 可访问性基线：键盘可达、focus-visible、aria-label、prefers-reduced-motion

---

## 评审模式

用户要评审 / 打分 / 找问题时，逐维度评 + 给具体改法（不只说「好看 / 不好看」）：

视觉层级 / 对比 / 对齐 / 间距尺度 / 一致性 / 可读性 / 焦点 / 留白 / 响应式塌陷 / 可访问性。

每维度：现状 → 问题 → 具体改法（改哪、改成什么）。
