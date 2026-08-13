# trellisx 文档

trellisx 是 **Trellis 增强改造工具**: 跑一次 `trellisx-apply`, 把强推 task / subtask 编排 / worktree 隔离 / plan→exec→check→finish 闭环 / task.md 看板五维度**内化进项目的 `.trellis/` 自身**, 之后由 trellis 原生机制注入这些规则, 不靠 trellisx 运行时 hook。

> 力度边界: 强推 task 与闭环是 **prompt 软约束** (AI 仍有裁量), 不装平台 enforcement hook。需硬强制者自配。

## 快速入口

| 你想… | 看这篇 |
| --- | --- |
| 第一次用, 装上跑起来 | [getting-started.md](getting-started.md) |
| 理解产品定位 / 为什么造 / 验收标准 | [prd.md](prd.md) |
| 理解注入模型 / 架构 / 数据流 / guard hook | [architecture.md](architecture.md) |
| 厘清 task / parent-child / subtask / worktree 概念 | [concepts.md](concepts.md) |
| 查某个 skill 怎么用 | [skills-reference.md](skills-reference.md) |
| 查脚本 CLI | [scripts-reference.md](scripts-reference.md) |
| 查术语定义 | [CONTEXT.md](CONTEXT.md) |
| 查架构决策 + 理由 | [adr/](adr/README.md) |

## 文档地图

| 文档 | 内容 |
| --- | --- |
| [getting-started.md](getting-started.md) | 安装 / apply 改造 / flow 强制闭环 / 日常用法 / FAQ |
| [prd.md](prd.md) | 背景 / 问题 / 目标 / 用户 / 功能需求 / 非目标 / 约束 / 验收 |
| [architecture.md](architecture.md) | 改造工具定位 / apply 5 维度注入模型 / 数据流 / guard hook 事件 / 脚本职责矩阵 |
| [concepts.md](concepts.md) | task / parent-child(任务级动态调度) vs subtask(任务内动态调度, 共享 worktree) / worktree 隔离单位=task / 执行载体 4 层 / 闭环 / 看板 |
| [skills-reference.md](skills-reference.md) | 8 skill + go command 详解 (apply / add / flow / orchestrate / workspace / spec / cleanup / grill / go) |
| [scripts-reference.md](scripts-reference.md) | worktree / finish / taskmd / wt / guard / packages / cleanup 脚本 CLI |
| [CONTEXT.md](CONTEXT.md) | 术语表 (任务结构 / 调度 / 隔离 / 载体 / 闭环 / 看板 / spec / 定位) |
| [adr/](adr/README.md) | 架构决策记录 (调度器=main / child 两层同构 / main 默认禁写 / cortex 解耦 / spec 主动化) |

## 一句话总览

```
早期: trellisx = 外部一堆 command hook 持续拦截/注入 (复杂, 需 reload, 易冲突)
现在: trellisx = 改造工具, 跑一次写进 .trellis (规则内化, trellis 自身机制生效)
```

trellisx 插件本身**无运行时注入 hook**。自动化由 `trellisx-apply` 注入到 **trellis 原生 `.trellis/config.yaml` 生命周期 hook** (`after_create/start/archive/finish`) —— 不依赖 Claude Code 平台 hook, 跨平台生效。另装 `trellisx-guard` 平台 hook 在 trellis 项目内强制执行载体闭环 + 完成清理。
