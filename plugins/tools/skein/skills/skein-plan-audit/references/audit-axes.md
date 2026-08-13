# 审计轴 — 8 条逐条定义

每轴产出 `{axis, severity, finding, evidence, suggestion}`。severity 取值 `Blocker` / `Major` / `Minor`。

## 1. 需求真伪

**问**: PRD 写的需求是用户真想要的, 还是 AI 脑补?

**扫描**:
- PRD `目标` / `User Stories` 每条溯源到源诉求 (用户原话 / brainstorm 记录)
- 无源溯回的 → 标 `implied (暗示)` 或 `fabricated (脑补)`
- `implied` 需在 PRD 标注推断依据; `fabricated` 直接 Blocker

**典型反模式**: PRD 写「支持数据导出为 Excel」但用户只说「能导出就行」→ 脑补了格式。

## 2. 边界

**问**: 输入 / 规模 / 并发 / 失败态的边界定了没?

**扫描**:
- PRD `边界` 段是否量化 (非「高并发」「大数据量」等模糊词)
- 失败态有无兜底描述 (超时 / 限流 / 部分失败)
- 规模上限有无数字 (用户数 / 数据量 / QPS)
- 模糊处逐个点名

**严重度**: 核心边界缺失 = Blocker; 次要边界模糊 = Major。

## 3. 假设

**问**: 有哪些没写出来的隐藏假设? 假设错了会崩哪?

**扫描**:
- design.md 的技术选型隐含什么前提 (如「选 Redis」假设了运维能部署)
- subtask DAG 隐含什么执行序假设 (如「st2 假设 st1 的 schema 已稳定」)
- 跨 subtask 的数据 / 接口假设有无 contracts 兜底
- 逐条列出, 标 `假设错了影响范围`

**严重度**: 核心路径上的未验假设 = Blocker; 外围假设 = Major。

## 4. DAG 完整性

**问**: subtask DAG 完整无环? 拆分粒度合理? 并行度够?

**扫描**:
- `depends_on` 有无环 (`skein doctor` 已检测, 但 audit 补语义层)
- 伪依赖: A→B 但 desc 无真实数据 / 接口依赖 → 标 `伪依赖, 建议移除`
- 漏依赖: A 用了 B 产出的 schema 但没挂 deps → 标 `漏依赖`
- 粒度: 单 subtask estimate > 8h → 标 `粒度过粗, 建议拆`
- 并行度: ready 批 < 空闲槽且有 pending → 标 `DAG 过深, 可并行化未并行`

**严重度**: 环 / 漏依赖 = Blocker; 伪依赖 / 粒度过粗 = Major; 可优化 = Minor。

## 5. 验收 (SMARC)

**问**: 每条 AC Specific / Measurable / Achievable / Relevant / Context-bound?

**扫描**:
- 逐条验收标准检查 SMARC 五项
- 命中 wishful 词 (`user-friendly` / `快速` / `好用` / `灵活` / `高效` / `稳定`) → 降级建议: 移到 Open Question
- 缺可执行基准 (无具体数值 / 无可观测行为) → 标 `不可测`

**严重度**: 核心 AC 不可测 = Blocker; 次要 AC = Major。

## 6. drift 一致性

**问**: 产出 (subtask DAG + PRD) 仍服务原始目标?

**扫描**:
- 逐条 subtask 溯源到 PRD `目标` / `User Stories` — 溯不回的标 `drift`
- PRD 多轮追问后原始目标段有无被改写 (应保持不动)
- 新增 AC / subtask 有无偏离原始 intent

**严重度**: 核心 subtask drift = Blocker; 边缘 subtask = Major。

## 7. scope 蔓延

**问**: 每条 subtask 溯源到 said (明说) / implied (暗示) 的源诉求?

**扫描**:
- subtask `name` / `desc` 与 PRD 全文关键词比对
- 无命中的 → 标 `候选蔓延`, 回溯到 said / implied
- 溯不到 → `Out-of-Scope` 建议 (源说「支持 X」, AI 顺手 spec 了 XYZ)
- design.md 的「可能性分支」是否标了触发条件 (未标 = 纯臆想, 砍)

**严重度**: 核心蔓延 = Major; 边缘 = Minor。

## 8. 工时 (estimate)

**问**: estimate 自下而上? 无占位整数? task ≥ Σ subtask?

**扫描**:
- 每个 subtask estimate 是否为占位整数 (`1` / `2` / `8`) 且无 desc 依据 → 标 `疑似拍脑袋`
- task estimate < Σ subtask estimate → 标 `task 工时漏算 plan/check 开销`
- 单 subtask estimate 远超同类 → 标 `偏高, 需说明依据`
- 估了 0 或未填 → Blocker

**严重度**: 未填 = Blocker; 占位 / 拍脑袋 = Major; 偏高无据 = Minor。

---

## 严重度判定速查

| 严重度 | 含义 | 何时标 |
|--------|------|--------|
| **Blocker** | 不修不该 confirm | 核心路径盲点 / 产物缺失 / 不可测的核心 AC |
| **Major** | 应修, 影响规划质量 | 伪依赖 / 边界模糊 / 工时虚估 / 蔓延 |
| **Minor** | 可选改进 | 措辞优化 / 非核心 AC 不可测 / 可并行化 |

每条 finding 必须带:
- `evidence`: 具体文件 + 行号或原文引用
- `suggestion`: 可操作的改进建议 (不是「需要改进」, 而是「把 X 改成 Y」)
