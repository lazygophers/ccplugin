# CLI 媒介 · 二级索引

命令行接口（CLI）设计方法论入口。本文件是选择指导——先定问题归属，再查对应文件。

## 选择指导

| 你要解决 | 看哪个文件 |
|---------|-----------|
| 选命令结构 / 命令树 / 参数布局 | [layout.md](layout.md) |
| 适配多场景（交互/管道/CI/配置优先级） | [scenes.md](scenes.md) |
| 选 flags / args / 输出 / 错误 / 帮助组件 | [components.md](components.md) |
| 选命名风格 / 输出风格 / 错误风格模板 | [style.md](style.md) |

## CLI 媒介特点

- 好的 CLI 像小语言：可猜、可组合、可脚本化、出错说人话
- 遵循 POSIX / GNU 传统 + 现代 UX
- 非交互优先（可脚本化），交互为辅

## 跨媒介共享

三方向硬门、事实验证见顶层 [../../SKILL.md](../../SKILL.md)。

## 无关平台的共用层

- UI/UX 原则 / 信息架构 / 交互 / 可用性无障碍 → [../ui-ux/INDEX.md](../ui-ux/INDEX.md)
- 配色理论 / 调色板模板 / 可访问性 → [../color/INDEX.md](../color/INDEX.md)
