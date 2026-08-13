# Optimization Log — 失败/成功编辑记录

> SkillOpt rejected-edit buffer 落地。每次优化轮的 before/after/Δ/结果记录于此，供归因 + 防重复尝试。

## 表头

| 日期 | target skill | 编辑类型 | dim 修改 | before 总分 | after 总分 | Δ | 结果 | judge 共识 | reason / 失败原因 |
|------|-------------|---------|---------|------------|-----------|---|------|-----------|-----------------|

## 记录

| 日期 | target skill | 编辑类型 | dim 修改 | before 总分 | after 总分 | Δ | 结果 | judge 共识 | reason / 失败原因 |
|------|-------------|---------|---------|------------|-----------|---|------|-----------|-----------------|
| 2026-06-26 | skill-optimizer（自评 baseline） | —（基线，无编辑） | — | — | 74.3（均值） | — | baseline | A=84.0 / B=64.6，分歧大（dim8 A=7/B=3） | 首次自验证；2 judge 分歧 → full_test 仲裁。dry_run=100%（无 full_test）⚠️ 评估置信度低 |
| 2026-06-26 | skill-optimizer（自评修复轮） | add/delete/edit | dim1/4/6/8 + 诚实割裂 | 74.3 | —（未重评） | — | applied | 2 judge 共识短板修复 | 4 处修复：optimization-log.md dead link / when_to_use 删路由指令 / Phase 4 CHECKPOINT / accept 准则 gross 标注。未重评（HL-4 收敛） |
| 2026-06-26 | skill-optimizer（full_test 仲裁） | —（仲裁，无编辑） | dim8 | dim8 A=7/B=3 | **dim8=6（仲裁）** | — | arbitration | full_test 子 agent 仲裁取中偏上 | dim8 不是 7（A 高估方法论框架价值）也不是 3（B 忽略 Phase 1 诊断 + held-out test 可迁移价值）。结论：好的诊断 checklist，弱的验证引擎 |
| 2026-06-26 | architecture-design（full_test 产物） | delete 冗余触发词 | dim1（触发簇→dim7） | dim1=5（when_to_use 150>128） | dim1≈8（103<128） | +3.3（dry_run 推演） | applied | full_test 子 agent Phase 1+2 指导 | skill-optimizer 方法论指导的真实 bounded 编辑：when_to_use 150→103 字符，删与 description 重复的 6 个触发词。证明 Phase 1 诊断 + Phase 2 设计有效。⚠️ Δ 为 dry_run 推演未 spawn before/after |

## 自评 baseline 说明（2026-06-26）

skill-optimizer 首次对**自身**跑 9 维评分（dogfooding）：

- **2 独立 judge 盲评**（fresh context，general-purpose subagent）
- Judge A（标准）：**84.0 / 100**
- Judge B（严苛 + 自打脸检查）：**64.6 / 100**
- **均值 74.3**，分歧主要在 dim8 实测表现（A=7 / B=3）

**full_test 仲裁**（2026-06-26）：spawn 独立子 agent 用 skill-optimizer 方法论真优化 architecture-design，验方法论有效性：
- **dim8 仲裁 = 6/10**（A=7 偏乐观 / B=3 过苛 / 取中偏上）
- 真实产出：Phase 1 诊断 + Phase 2 设计指导出 architecture-design 的可验证短板（when_to_use 150>128 + 与 description 触发词重复），bounded 编辑已应用（150→103 字符）
- 判定：**好的诊断 checklist，弱的验证引擎**

**共识短板**（两 judge + full_test 一致）：
1. dim6 资源整合：本文件（optimization-log.md）曾为 dead link → 已创建修复
2. dim8 实测表现：无具体 test prompt 样例 + 本 skill 零自跑实证 → 补 test prompt 样例 + 本条记录即首次自验证 + full_test 仲裁

**Judge B + full_test 致命洞察**：
- 优化器自称 validation-gated，但首次 dogfooding 即 100% dry_run（自指悖论）→ 已写入诚实边界 + 硬规#1 标注「非 darwin 环境必然 dry_run，深度验证 route darwin」
- 诚实边界与操作准则割裂 → 硬规#1 改为二层 gate（gross 分数 + 人审），消解矛盾
- Phase 5 evals.json 空指针 → 改为「绝大多数 skill 无 evals.json 属常态，现场编 test」
- dim8 权重 23% 却无强制 test prompt 编码（可重复性为零 = A/B 分歧根源）→ 建议被优化 skill 内置 test prompt 样例

**dry_run 比例**：dogfooding baseline 100%（2 judge 模拟评分）⚠️；full_test 仲裁中 Phase 1-2 为 full_test 性质（真读真诊断），Phase 3 退化 dry_run（read-only 未 spawn before/after）。按 skill 自身硬规，fine-grained 差异不可信，**dim8=6 仅作 gross 仲裁**。

**本轮 dogfooding 净产出**：
1. skill-optimizer 自身 4 处短板修复 + 4 致命硬伤诚实标注
2. architecture-design 真实改进（when_to_use 150→103，删冗余触发词）—— 证明方法论对真实 skill 有效
3. dim8 仲裁收敛（7 vs 3 → 6）

**未决**：architecture-design 修复的 Δ≈+3.3 为 dry_run 推演，未 spawn before/after 盲评。需 darwin 环境 full_test 才能严格验证。
