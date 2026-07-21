# HTML 媒介 · 二级索引

HTML / Web 媒介的设计方法论入口。本文件是选择指导——先定问题归属，再查对应文件。

## 选择指导

| 你要解决 | 看哪个文件 |
|---------|-----------|
| 选布局骨架 / 间距尺度 / 栅格 / 视觉层级 | [layout.md](layout.md) |
| 适配多场景（亮暗 / 密度 / 响应式 / 触摸 / 动效偏好） | [scenes.md](scenes.md) |
| 选组件 / 组件状态 / token 化 / 可访问性 | [components.md](components.md) |
| 选风格谱系 / 配色色系 / 字体气质 / 可访问对比 | [style.md](style.md) |
| 画架构图 / 流程 / 时序 / 信息图 / 数据图表 | [data-viz.md](data-viz.md) |
| 做封面 / 配图 / 小红书卡片 / 海报 | [image.md](image.md) |
| 做幻灯片 / PDF 报告 / 微信图文 | [slides.md](slides.md) |
| 把 HTML 导出成 PNG / SVG / PDF | [export.md](export.md) |

## HTML 媒介特点

- HTML 是唯一落地产物，其余格式从 HTML 导出（见 [export.md](export.md)）
- 四维（布局 / 场景 / 组件 / 风格）是核心；data-viz / image / slides 是 HTML 特有的输出 genre，复用四维基础
- 纯前端、零后端、CDN 白名单（Tailwind Play / GSAP / D3 / 图标库）

## 跨媒介共享

三方向硬门、事实验证、token 化纪律见顶层 [../../SKILL.md](../../SKILL.md)。
