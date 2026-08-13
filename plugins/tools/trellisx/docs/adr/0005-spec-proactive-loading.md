# ADR 0005 · spec 主动加载/更新 (两端自动)

- 状态: Accepted (2026-06-29)
- 分支: J (spec 主动化 + grill 贯穿 plan)
- 相关 commit: 6bbbb941

## 背景 (Context)

`trellisx-spec` 原为**被动** skill: 用户主动调 (`/trellisx-spec`), 或任务收尾手动跑 sediment 模式。

问题: 任务开始时 AI 不主动读 `.trellis/spec/` 指导 (易忽略既有契约); 收尾时易跳过 spec 沉淀 (非平凡规则丢失)。

## 决策 (Decision)

**spec 两端自动 (软约束)**:
- **planning (任务开始)**: 自动 grep `.trellis/spec/` 按主题找相关 guide, 命中则注入 PRD 上下文 (约束/契约/验收基准); 无相关则跳过
- **finish (任务收尾前)**: 自动判本 task 有无 spec 增量需求 (非平凡契约 / 踩坑 / 反复犯错规则), 有则走 sediment (提案→审批→写盘), 无则跳过

**软约束**: AI 执行 ("如需"判定), 非新 hook 硬拦。无相关 spec 不强加载, 无增量不强 sediment。

**sediment ≠ cortex**: sediment 沉淀到 `.trellis/spec/` (命令式契约), 非 cortex 知识库 (见 [ADR 0004](0004-decouple-cortex.md))。

## 后果 (Consequences)

- ✅ spec 从被动→主动 (planning 有上下文指导, finish 有沉淀闭环)
- ✅ spec 与 task 生命周期双向绑定 (入: planning 加载; 出: finish 沉淀)
- ✅ 软约束不强拦 (避免无 spec 时噪音)
- ⚠️ 依赖 AI 自觉执行 ("如需" 判定有裁量空间)
- ⚠️ sediment 仍走 AskUserQuestion 审批门 (main 直做, 非 subagent)

## 备选 (Alternatives)

| 方案 | 否决理由 |
| --- | --- |
| 纯被动 (用户主动调) | 易忘; planning 缺上下文; finish 易跳沉淀 |
| 硬 hook 强制加载/沉淀 | 噪音 (无 spec 时仍触发); sediment 审批门需 AskUserQuestion, hook 跑不了 |

## 同批: grill 贯穿 plan

grill 从 "planning→start 前置审查" 扩为 **贯穿 plan 前/中/后** (帮确认/审查/拆解需求)。grill 对象从固定 5 类扩为动态全产物。
