# trellisx ADR (架构决策记录)

> 仅记录难撤销 + 意外 + 真实权衡的决策。概念/边界澄清归 [CONTEXT.md](../CONTEXT.md)。

## 索引

| # | 决策 | 分支 | 状态 |
| --- | --- | --- | --- |
| [0001](0001-scheduler-is-main.md) | 调度器 = main (递归保护) | C | Accepted |
| [0002](0002-child-two-layer-scheduling.md) | child 两层调度器同构 | D | Accepted |
| [0003](0003-main-no-source-write-default.md) | main 写源码默认禁 (opt-out) | E | Accepted |
| [0004](0004-decouple-cortex.md) | trellisx 解耦 cortex (tool 中立) | F | Accepted |
| [0005](0005-spec-proactive-loading.md) | spec 主动加载/更新 (两端自动) | J | Accepted |

## 来源

本批 ADR 源自 2026-06-29 的一次 `/grill-with-docs` 全量设计确认会话 (14 分支 A-N), 经用户事无巨细确认后沉淀。对应 commit: 050c00fb / 23cd0210 / 778cb188 / b7cd3d67 / 6bbbb941 / 0e06ce8f。
