# UI/UX · 二级索引（无关平台）

跨平台 / 跨媒介通用的 UI/UX 设计方法论。无论 HTML / App / CLI / TUI 都适用。本文件是选择指导——先定问题归属，再查对应文件。

## 选择指导

| 你要解决 | 看哪个文件 |
|---------|-----------|
| 设计原则（层级 / 对比 / 对齐 / 接近 / 一致 / 反馈 / 容错） | [principles.md](principles.md) |
| 信息架构 / 导航 / 内容优先级 / 用户心智模型 | [information-architecture.md](information-architecture.md) |
| 交互模式 / 状态 / 反馈 / 微交互 / 防错 | [interaction-design.md](interaction-design.md) |
| 可用性启发式（Nielsen 10）/ 无障碍（WCAG / 键盘 / 对比） | [usability-a11y.md](usability-a11y.md) |

## 定位

本目录管「跨平台通用的 UI/UX 纪律」。各媒介专属实现（布局结构、组件库、平台习惯）在对应 medium 目录：

- HTML 实现 → [../html/](../html/INDEX.md)
- App 实现 → [../app/](../app/INDEX.md)
- CLI 实现 → [../cli/](../cli/INDEX.md)
- TUI 实现 → [../tui/](../tui/INDEX.md)
- 配色理论与调色板 → [../color/](../color/INDEX.md)

## 怎么用

设计任务先来本目录定原则与架构，再去 medium 目录定具体实现。例：设计一个设置页——先在 IA 文件定信息架构（分组、层级、搜索），再去 app/components 定具体控件。

## 跨媒介共享

三方向硬门、事实验证见顶层 [../../SKILL.md](../../SKILL.md)。
