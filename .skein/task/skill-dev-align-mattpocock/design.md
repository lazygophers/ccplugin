# 优化 skill-dev 全部 skill 对齐 mattpocock/skills — 详细设计

## 1. mattpocock 范式核心 (照抄骨架)

来源: research/mattpocock-skills-patterns.md + philosophy.md

### 1.1 信息层级三阶梯
1. **In-skill steps** — 有序动作, 每步以**完成准则** (checkable + exhaustive) 结束
2. **In-skill reference** — 按需查阅的定义/规则/事实
3. **Disclosed reference** — 推到 sibling `.md`, 经 context pointer 按需加载

### 1.2 body 结构节拍 (有则按此序)
1. 可选 `# H1`
2. **一句话职责声明** (defining constraint)
3. 可选 `## Process` / 编号步骤, 每步带 `**Done when:**` 或 `[ ]` 完成准则
4. inline 模板 `<name>` 自定义标签围栏
5. 可选 `## Failure modes` (仅特征性失误)
6. 可选 `## Out of scope`

### 1.3 negation 规则
- 默认**正向表述** (state target behaviour so banned one never spoken)
- 反例仅作**硬护栏** (无法正向表述时), 且配正例
- "Rejected framings" 段命名被拒术语 + 原因 (合规反例写法)

### 1.4 报告模板三种发行
- inline `<template>` 围栏 (本任务选此)
- sibling copy-me 文件 (大型结构化产物)
- inline config JSON/bash (小片段)

### 1.5 评分/验证 (Matt 无数字)
- 完成准则 (checkable + exhaustive)
- "prove the rules bite" (pass → 注入违规 → 确认 fail → revert → 确认 pass)
- "It's working if" 可观测信号
- 3-value badge (Strong/Worth exploring/Speculative)

## 2. 本任务裁决 (grill 收敛)

| 冲突点 | 裁决 |
|---|---|
| 数字评分 vs 完成准则 | **混合**: rubric 量化保留 + 完成准则作底线锚点 |
| 反例 vs negation 末选 | **默认正向**, 仅必要场景保留反例 (纯正向优先) |
| optimize-any 迁移 | 拆进 skill-dev/plugin-dev 流程 B |
| 报告模板形态 | inline `<report-template>` 围栏 |
| 收敛机制 | rubric 加**方向轴 + 理想值**列 |
| 完成范围 | 全量改造 |

## 3. rubric 方向轴设计 (核心创新 — 对齐需求#5)

每个评分维度加 3 列:

| 维度 | 分 (1-10) | 方向 | 理想值 | 完成准则底线 |
|---|---|---|---|---|

- **方向**: ↑ (越高越好) 或 ↓ (越低越好, 如冗余度)
- **理想值**: 该维度的目标值 (如触发准确=10, 冗余度=8+)
- **完成准则底线**: checkable + exhaustive 的最低可判定锚点 (未达=该维未完成)

**收敛机制**: ratchet 不仅看总分 Δ>0, 还看是否沿方向轴走 (退步维度即使总分涨也标记警示)。触顶停 (连续 2 轮 Δ<2) + 膨胀护栏 (>原×1.5 拒提交) 保留。

## 4. 各 skill 改造方案

### 4.1 skill-dev (skill/agent 创建+优化方法论)
- **流程 A 创建**: 加 inline `<creation-report-template>` 围栏 (定位/骨架/frontmatter/调研/验证 各段)
- **流程 B 优化**: 加 inline `<optimization-report-template>` 围栏 (before/after 9维分+Δ+方向轴+留/滚清单)
- **dimensions.md**: 9 维 rubric 加方向轴 + 理想值 + 完成准则底线列
- **反例段**: 默认正向, 反模式黑名单改为 "Rejected framings" (命名被拒模式+原因+正例)
- **传递要求**: 流程 A Phase 4 / 流程 B Phase 2 加 "目标 skill 默认正向表述, 仅必要场景反例配正例"

### 4.2 plugin-dev (插件创建+优化)
- **流程 A**: 加 inline `<plugin-creation-report-template>`
- **流程 B**: 加 inline `<plugin-optimization-report-template>` + 吸收 optimize-any 的 validation-gate 循环纪律 (评分→单变量→ratchet→触顶)
- **optimize-rubric.md**: 8 维加方向轴 + 理想值 + 完成准则底线
- **反例段**: 改 Rejected framings
- **传递要求**: 同 skill-dev

### 4.3 optimize-any (移除)
- 6 维通用评分 (scoring-matrix.md) → 拆: 通用维度思想融入 skill-dev dimensions.md (skill/agent 适配) + plugin-dev optimize-rubric.md (插件适配)
- validation-gate 循环纪律 (validation-gate.md) → 拆: skill-dev workflow.md (已有, 补强) + plugin-dev 流程 B (新吸收)
- 删整目录 `skills/skill-dev/optimize-any/`

### 4.4 README.md
- 移除 optimize-any 引用

## 5. 评分机制汇总 (交付物)

完成后输出独立汇总 (对话内 + 可选落盘), 含:
- skill-dev: 9 维 rubric + 方向轴 + 理想值 + 完成准则底线
- plugin-dev: 8 维 rubric + 同上
- 共享收敛机制: ratchet + 触顶停 + 膨胀护栏 + 方向轴校验
- 各 skill 评分适用场景 (何时用哪个)

## 6. 执行策略

4 subtask, DAG:
- s1 (skill-dev 改造) + s2 (plugin-dev 改造) 并行 (无依赖)
- s3 (optimize-any 移除 + README) 依赖 s1+s2 (内容先拆完再删源)
- s4 (评分机制汇总 + 质量门全跑) 依赖 s1+s2+s3

并发上限 2: s1/s2 并行, s3/s4 串行。
