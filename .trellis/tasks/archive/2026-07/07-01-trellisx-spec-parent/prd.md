# PRD — trellisx spec 自动化与整理 (parent)

## Goal

trellisx 插件 spec 机制两缺口修复:
1. **sediment 判定可被跳过** — finish 步 sediment 门是 🔴 gate, 但判定过程无强制输出 trace, model 可默默判"全否"跳过沉淀
2. **diagnose 缺整理去重检测** — optimize 模式体检无 guide 间冗余检测 / index 同步检测, 整理能力不全

## 范围 (parent 总览)

痛点 3 (spec 执行时丢失) **本轮 skip**, 留 follow-up。

| Child | 痛点 | 改动 |
|---|---|---|
| [07-01-spec-audit](../07-01-spec-audit/) | 2 整理去重 | trellisx-spec `references/diagnose.md` 加 4 检测项 (冗余/过时/低质量强化/index 同步) |
| [07-01-spec-sediment-trace](../07-01-spec-sediment-trace/) | 1 自动维护 | trellisx-flow finish 步 sediment 判定加强制输出 trace (每项 ✅/❌ 显式) |

两 child **独立可验收**, 无依赖, 可并行。

## 验收 (parent 级)

- 两 child 各自闭环 (check + finish + archive)
- 不破坏 trellisx 现有 spec/orchestrate/flow 行为 (回归)
- sediment 判定 trace + audit 4 检测项 claude -p 可读出

## Open

- 痛点 3 follow-up: spec 执行端 trace 校验 (本轮 skip)
