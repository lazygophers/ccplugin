# 配色 · 二级索引（无关平台）

跨平台 / 跨媒介通用的色彩理论与调色板库。无论 HTML / App / CLI / TUI 都适用。本文件是选择指导——先定问题归属，再查对应文件。

## 选择指导

| 你要解决 | 看哪个文件 |
|---------|-----------|
| 色彩理论（色相 / 明度 / 饱和 / 色环 / 配色法） | [theory.md](theory.md) |
| 现成调色板模板（品牌色阶 / 语义色 / 主题色板，复制即用） | [palette-templates.md](palette-templates.md) |
| 可访问性（对比度 / 色盲安全 / 暗模式） | [accessibility.md](accessibility.md) |
| **主题总清单**（扫全部主题 + 跨平台热门预设 Nord/Dracula/Catppuccin...） | [themes-catalog.md](themes-catalog.md) |
| **配色总清单**（扫全部色板：品牌色阶 / 中性阶 / 语义色 / 命名色板） | [palettes-catalog.md](palettes-catalog.md) |

## 定位

本目录管「跨平台通用的色彩方法论 + 模板」。各媒介的落地产出（CSS 变量 / App token / CLI ANSI / TUI 色域）在对应 medium 的 style 文件：

- HTML 落地 → [../html/style.md](../html/style.md)
- App 落地 → [../app/style.md](../app/style.md)
- CLI 落地 → [../cli/style.md](../cli/style.md)
- TUI 落地 → [../tui/style.md](../tui/style.md)
- UI/UX 原则 / 信息架构 / 交互 / 可用性无障碍 → 姊妹 skill `design-uiux`（本 skill 只管配色）

## 怎么用

配色任务先来本目录定色板（理论 + 模板），再去 medium style 文件落地为该媒介的 token。例：选品牌主色 → 在 palette-templates 选色板 → 在 html/style 写成 `--primary` CSS 变量。

## 跨媒介共享

三方向硬门见顶层 [../../SKILL.md](../../SKILL.md)。
