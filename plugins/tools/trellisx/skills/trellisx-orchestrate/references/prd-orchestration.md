# PRD 编排

`prd.md` = team 章程。**保留 trellis 原生骨架** (Goal / What I already know / Assumptions / Open Questions / Requirements / Acceptance Criteria / Definition of Done / Out of Scope / Technical Notes), **插入 trellisx 编排增强** (Deliverable 矩阵 / Subtask 拆分 / mermaid 调度图)。禁开放式描述。填好范例见 `examples/prd.md`。

## 必备结构 (trellis 原生 + trellisx 增强)

```markdown
# <task-title>

## Goal
<一句话, 动词 + 对象 + 可验证结果>

## What I already know
### 现状
<已知文件位置 / 现有实现 / 约束>
### 调研结论
<research/*.md 引用 + 关键结论>

## Assumptions (temporary)
<本 task 成立的前提假设, 后续可能被推翻>

## Open Questions
<尚未定的点; 无则写 "无 (范围已明确)">

## Deliverable 矩阵    ← trellisx 增强

| ID | 交付物 | 类型 | 独立验收 | 优先级 |
| --- | --- | --- | --- | --- |
| D1 | <名称> | diff / 报告 / 配置 / UI | <可机器或人工验证, 一句话> | P0 |

## Requirements
<编号需求, 每条标所属 deliverable; 禁技术方案 / 代码 (那些去 design)>

## Subtask 拆分    ← trellisx 增强

每个 subtask **必须**有独立文件 `.trellis/tasks/<task>/subtask/<id>-<slug>.md` (见 `subtask-file.md`)。本节仅概览。

| ID | Subtask | 所属 Deliverable | 边界 (改动 / 读取范围) | 简要说明 | 详情文件 |
| --- | --- | --- | --- | --- | --- |
| S1 | <动词+对象> | D1 | `packages/api/src/auth/**` | <≤ 30 字概述> | `subtask/S1-<slug>.md` |

### Subtask 调度图    ← trellisx 增强

\`\`\`mermaid
flowchart LR
    S1[S1 · 概述] --> S2[S2 · 概述]
    S1 --> S3[S3 · 概述]
    S2 --> G1{{G1 · D1 验收}}
    classDef parallel fill:#e0f7fa,stroke:#006064;
    classDef serial fill:#fff3e0,stroke:#e65100;
    class S2,S3 parallel
    class S1 serial
\`\`\`

图必含: 全部 subtask 节点 (ID + 概述) / 依赖箭头 / 并行串行视觉区分 (classDef) / review gate 菱形节点 `G1{{Gate}}`。

## Acceptance Criteria
- [ ] 全部 P0 deliverable 独立验收通过 (命令 / 文件存在 / 输出对比)
- [ ] 跨 deliverable 一致性 (列具体检查项)

## Definition of Done
- 全部 Requirements 实现 + Acceptance Criteria 勾选
- 变更自动暂存
- task worktree 已合并 + 移除 (环境干净)
- bump .version (若用户可见功能变更)

## Out of Scope
<显式列禁区, 防 "顺手优化" 漂移>

## Technical Notes
### 文件位置
<关键文件路径>
### 灰度 / 回滚
<feature flag / 回滚策略, 详细去 design>
### 验证命令
\`\`\`bash
<可执行验证命令>
\`\`\`
```

## trellis 原生 vs trellisx 增强

| section | 来源 | 说明 |
| --- | --- | --- |
| Goal / What I already know / Assumptions / Open Questions | trellis 原生 | brainstorm 阶段产出, 勿删 |
| Requirements / Acceptance Criteria / Definition of Done | trellis 原生 | 需求与验收契约 |
| Out of Scope / Technical Notes | trellis 原生 | 边界 + 落地提示 |
| **Deliverable 矩阵** | trellisx 增强 | 多交付物拆分起点 |
| **Subtask 拆分 + 调度图** | trellisx 增强 | 编排核心, 驱动 subtask 文件 + dispatch |

## 写 PRD 的硬规

1. **目标必须包含可验证的结果对象**, 禁 "实现 / 完成 / 优化" 这类不可证伪动词单独使用; 必带"…后 X 行为变为 Y / 文件 Z 存在 / 输出符合 W"。

2. **每个 deliverable 必须独立可验收**, 验收方式必须是命令 / 文件存在性 / 输出对比 / 截图。禁"看起来对"。

3. **禁把 design / implement 内容塞进 PRD**: 不写技术方案、不写文件改动清单、不写代码片段。这些去 design / implement。

4. **out of scope 必填**, 防止"顺手优化"导致任务漂移。

5. **保留 trellis 原生 section**: brainstorm 已写的 Goal / What I already know / Assumptions / Open Questions 不删不改骨架, 仅在其后插入 trellisx 增强 (Deliverable 矩阵 / Subtask 拆分 / 调度图)。禁用自定义中文 section 替换原生英文骨架 (破坏 trellis 工具链识别)。

6. **Definition of Done 必含 worktree 清理**: task 结束前 worktree 合并 + 移除。

## Multi-deliverable 判定

> PRD 列 ≥ 2 个 deliverable 且每个都能独立交付 → **MUST** 走 parent/child task tree (见 `task-tree.md`), 不许塞进单 PRD。

单 PRD 内塞多 deliverable 后患:
- 验收难以独立
- subtask 拆分边界混乱
- 局部回滚不可行

