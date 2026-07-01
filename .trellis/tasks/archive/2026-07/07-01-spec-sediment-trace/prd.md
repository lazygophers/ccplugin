# PRD — trellisx-flow sediment 判定 trace 强制 (child)

## Goal

trellisx-flow finish 步的 sediment 判定门, 加**强制输出判定 trace** (5 正向 + 3 排除每项显式 ✅/❌), 防 model 默默判"全否跳过"。判定仍是 model 语义判 (非脚本), 但过程必须显式化。

## What I know

- `trellisx-flow/SKILL.md` 步骤 6 finish: 🔴 sediment 判定门, 5 正向 (新命令式契约/踩坑≥2轮/反复≥2task/跨任务可复用决策/验收基准) + 3 排除 (一次性bug/私有细节/已覆盖)
- 现状: model 按 checklist 判, 但**无强制输出 trace** → 可默默判"全否"跳过沉淀 (痛点 1 根因)
- memory [[trellisx-spec-automation-gate]]: load+sediment 软约束已升 🔴 gate (gate 文本在, 但 trace 输出未强制)
- 审批对象已是"是否**写入**这些变更" (AskUserQuestion 审提案内容), 非抽象"要不要更新" — 此点已对齐

## 方案

finish 步 sediment 判定加 trace 模板, model MUST 输出:

```
sediment 判定 trace
═══════════════════
正向 (任一 ✅ 触发):
  ① 新命令式契约: ❌ (本 task无私有契约) / ✅ (具体: <契约描述>)
  ② 踩坑 ≥2 轮: ❌ / ✅ (具体: <根因>)
  ③ 反复 ≥2 task: ❌ / ✅ (具体: <task list>)
  ④ 跨任务可复用决策: ❌ / ✅ (具体: <决策>)
  ⑤ 验收基准: ❌ / ✅ (具体: <断言>)
排除 (任一 ✅ 不触发):
  - 一次性 bug: ✅/❌
  - 私有实现细节: ✅/❌
  - 已有 spec 覆盖: ✅/❌
判定: <触发 sediment | 全否跳过>
```

未输出此 trace = 流程错误 (加反模式)。

## 范围

- **改**: `plugins/tools/trellisx/skills/trellisx-flow/SKILL.md` 步骤 6 finish (加 trace 模板 + 反模式)
- **不改**: trellisx-spec SKILL sediment 模式本身 (判定逻辑不变, 只强制输出), orchestrate, 其他
- 纯文档改动

## Deliverable

| ID | 交付 | 验收 |
|---|---|---|
| D1 | flow SKILL 步骤 6 加 sediment trace 模板 | grep "判定 trace" 命中 |
| D2 | 反模式黑名单加"未输出 sediment trace" | 反模式表新增 1 行 |
| D3 | 质检: claude -p 读 flow SKILL 问"finish 时 sediment 怎么判" 返回含 trace 模板 | 返回含 5 正向 trace |

## 验收

- finish 步 sediment trace 模板存在
- 反模式含"未输出 trace"
- 现有 sediment 判定逻辑零回归 (5 正向 + 3 排除不变)
- claude -p 可读出 trace 要求
