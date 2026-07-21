---
name: design
description: 跨媒介设计 skill——帮用户做 UI/UX 与接口设计决策，按产出媒介路由：HTML/Web、原生 App(iOS/Android/桌面)、CLI 命令行、TUI 终端 UI。帮选方案、风格、配色色系、布局、组件、交互模式，让产物自适应不同场景，产出高保真原型或实现指引。触发词：做设计/UI/UX/原型/mockup/布局/组件、选风格/配色/色系、做App/iOS/Android/桌面应用、做CLI/命令行工具/命令设计、做TUI/终端界面、画架构图/信息图、做封面/海报/幻灯片、自适应/响应式。需后端的动态系统/生产级服务不适用。
---

# Design · 跨媒介设计

一个 skill，四种媒介。先判产物是什么媒介，再进对应方法论；跨媒介共享设计纪律（三方向硬门、事实验证、token 化、自检）。

## 适用 / 不适用

适用：Web 页面 / 原型 / 可视化 / 图像 / 幻灯片（HTML 媒介）、原生 App、命令行工具、终端全屏 UI。

不适用：需后端的动态系统、生产级服务、SEO 站点——走代码实现。

## 核心硬门 · 三方向初稿（100% 必走）

任何会产出新视觉 / 接口的任务，**无论有无风格参考、有无品牌名**，第一步必须先出**三个差异化方向的真实初稿**等用户选定，再执行最终版。

- 「就按 Apple 风格做」不豁免——在 Apple 语境内出 3 个差异化诠释
- 三方向要真实分化（不同结构 / 风格 / 配色 / 信息密度），不是同款换色
- 弱 runtime（无并行 subagent）→ 串行出三版，禁挂起等待
- 风格词收窄的是解释空间，不豁免选择权

## 事实验证先行

涉及具体产品 / 技术 / 事件的存在性、发布状态、版本号、规格的断言，开工前先 `WebSearch` 验证，禁凭训练语料断言。搜不到或模糊 → 问用户。事实错了后面全歪。

## 媒介路由表

收到任务先定媒介（多信号叠加按行序）：

| 产物形态 | 媒介 | 参考 |
|---------|------|------|
| Web 页面 / 原型 / 布局 / 组件 / 数据可视化 / 图像 / 幻灯片 | HTML | [html/styles](references/html/styles.md) · [layout](references/html/layout.md) · [components](references/html/components.md) · [data-viz](references/html/data-viz.md) · [image](references/html/image.md) · [slides](references/html/slides.md) · [export](references/html/export.md) |
| 原生 App(iOS / Android / 桌面) | App | [app-medium](references/app-medium.md) |
| 命令行工具(`./tool <command>`) | CLI | [cli-medium](references/cli-medium.md) |
| 终端全屏交互应用(TUI) | TUI | [tui-medium](references/tui-medium.md) |
| 评审 / 打分 / 找问题 | 任意媒介 + §评审 | |

边界：

- 网页内跑的 App mockup → HTML 媒介（HTML 出原型）
- 跨平台框架(Flutter / RN / Electron) App 设计 → App 媒介
- 命令行工具带交互向导但仍命令式 → CLI 媒介
- 终端里全屏多面板 GUI → TUI 媒介

---

## UI/UX 优化能力（跨媒介核心）

本 skill 的核心价值是帮用户做设计判断，不是「只会画图」：

### 选方案

- 先理解任务流程（用户要完成什么），再选布局 / 结构模式
- 多方案并排出三版，在真实初稿上选，不在抽象描述上选
- 每方案标注：适合什么场景、优势、代价

### 选风格与配色色系

HTML 媒介详见 [html/styles.md](references/html/styles.md)。决策路径：定语境（受众 / 场景 / 情绪）→ 从风格谱系选三方向 → 每方向配完整色板（主色 + 辅助 + 中性阶 + 语义色 + 背景）→ 可访问性硬指标（对比度 ≥ 4.5:1、不只靠颜色传信息、暗模式重调中性阶）→ 固化 token。App / TUI 媒介各自适配平台色域约束（见对应 medium 文件）。

### 选布局与场景自适应

HTML 媒介详见 [html/layout.md](references/html/layout.md)。共通纪律：间距取自固定尺度阶（禁魔法数）、移动优先断点（结构随宽度变）、场景切换用 CSS 变量或平台机制（亮暗 / 密度 / 焦点）、视觉层级焦点唯一。App 适配平台导航习惯，TUI 适配字符格栅与 resize，CLI 适配参数与输出分层。

### 选组件与交互

HTML 见 [html/components.md](references/html/components.md)，App 见 [app-medium.md](references/app-medium.md) 组件与手势段，TUI 见 [tui-medium.md](references/tui-medium.md) 组件与焦点段，CLI 见 [cli-medium.md](references/cli-medium.md) 参数与输出段。共通：选型先问「用户要完成什么任务」、状态完整性（default / hover / focus / active / disabled / loading / error / empty）、token 化、可访问性基线。

### 自适应不同场景

- HTML：亮 / 暗模式、密度切换、响应式断点、容器查询（[layout.md](references/html/layout.md)）
- App：系统主题跟随、横竖屏、平板分栏、动态字体（[app-medium.md](references/app-medium.md)）
- CLI：TTY 检测关色 / 关进度、配置五层优先级链、非交互降级（[cli-medium.md](references/cli-medium.md)）
- TUI：色域检测降级（真彩→256→16）、resize 重绘、亮暗主题（[tui-medium.md](references/tui-medium.md)）

---

## 共享工作流（所有媒介）

1. **定媒介 + 收集约束**：受众、品牌色、尺寸、情绪、目标场景
2. **三方向初稿门**：出三版差异化真实初稿 → 用户选定 → 固化项目 token
3. **执行选定方向**：按媒介产出（HTML standalone / App 原型或标注 / CLI 命令规格 / TUI 布局与键位表）
4. **场景自适应**：在该产物内覆盖对应媒介的多场景切换
5. **自检**：对照各 medium 文件末尾自检清单，浏览器 / 实际环境看实样，禁凭脑补
6. **导出 / 交付**：HTML 媒介走 [html/export.md](references/html/export.md)；其余媒介产出即成品

### 技术红线（HTML 媒介）

- 纯前端，零后端、零构建步骤（或构建结果自包含）
- 外部依赖仅限 CDN 白名单：Tailwind Play CDN / GSAP / D3 / 三方图标库；其余自写
- 单文件优先；确需拆分时同目录 `assets/`
- 中文用系统字体栈，别引私有字体（除非用户提供字体文件）

---

## 评审模式

用户要评审 / 打分 / 找问题时，逐维度评 + 给具体改法（不只说「好看 / 不好看」）：

视觉层级 / 对比 / 对齐 / 间距尺度 / 一致性 / 可读性 / 焦点 / 留白 / 响应式或自适应塌陷 / 可访问性。

每维度：现状 → 问题 → 具体改法（改哪、改成什么）。
