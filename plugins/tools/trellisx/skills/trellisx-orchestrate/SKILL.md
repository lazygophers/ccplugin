---
name: trellisx-orchestrate
description: 在 Trellis 项目 planning 阶段, 指导编写 task 文件夹内的 prd.md / design.md / implement.md, 把任务编排理念 (五要素拆分、执行层选择、资源互斥、失败回退) 内嵌到文档中。让后续 dispatch 与执行有据可依, 而不是写完 PRD 才临时想怎么拆。
when_to_use: trellis active task planning 阶段编写 / 完善 prd / design / implement; 任务规划 / 拆 deliverable / 拆 subtask / 写验收标准时。短语 "写 PRD" "规划任务" "拆任务" "完善 implement" "设计任务"。
user-invocable: false
---

# trellisx-orchestrate — Trellis 任务规划与文档编排

在 trellis active task 的 **planning 阶段**, 把任务编排理念内嵌到 `prd.md` / `design.md` / `implement.md`。Dispatch 与执行阶段直接读这些文档落地, 避免"写完 PRD 才临时想怎么拆"。

## 立场

| 立场 | 说明 |
| --- | --- |
| 编排即文档 | 五要素 / 执行层 / 资源互斥不是临时口头约定, 必须写进 PRD / design / implement |
| 拒绝模糊 PRD | PRD 必须列 deliverable 矩阵 + 验收, 禁开放式"实现 X 功能" |
| 自包含 | 全部规则就地内嵌, 不引外部 |
| 串行优先 | 共享 task 文件写入 / 同一 active task 状态切换必须串行 |

## 何时强制建 trellis task

| 类型 | 是否建 task |
| --- | --- |
| 探索 (纯只读: 读/查/搜/分析) | 按复杂度决定 (简单可不建; 复杂调研建 task 承载) |
| 实施 (写盘/改文件/任何落盘工作) | **无条件强制建 task**, 走 planning 全流程, 不看 subtask 数 |

判定靠不准时倾向建 task。建 task 后拆 ≥ 2 subtask, 异步调度 sub-agent (isolation:worktree) / agent-team 成员 (<git根>/.worktrees/<worktree>) 尽可能并行执行; main 可直接写源码但**必须在 worktree 内** (简单 subtask main 直做, 复杂/并行派 agent), 见 `references/task-lifecycle.md`。

## 触发判定

主会话符合任一即加载:

- 处于 trellis active task 且 status = planning
- 用户要求 "写 / 完善 / 改 / 拆" PRD / design / implement / deliverable / subtask
- 当前 task 仅 PRD 存在但 prd 列 ≥ 2 deliverable 尚未拆 design/implement
- 准备从 planning → in_progress 前的最后一遍编排校对

不触发: 已 in_progress 在执行 / 单文件咨询 / 与编排无关问答。

## 工作流 (6 步, 渐进披露)

每步先读对应 reference (写法规则) + 对应 example (填好的范例), 再写文档:

| 步骤 | 行动 | 写法 reference | 填好范例 |
| --- | --- | --- | --- |
| 1 | PRD 编排 — deliverable 矩阵 + subtask 概览表 + mermaid 调度图 + 验收 + 范围边界 | `references/prd-orchestration.md` | `examples/prd.md` |
| 2 | 为每个 subtask 建独立文件 `.trellis/tasks/<task>/subtask/<id>-<slug>.md` 含完整五要素 + dispatch prompt | `references/subtask-file.md` | `examples/subtask/S2-jwt-utils.md` `examples/subtask/S3-jwt-middleware.md` |
| 3 | design 编排 — 模块表 + 执行层标注 + 资源边界 + 契约 | `references/design-orchestration.md` | `examples/design.md` |
| 4 | implement 编排 — 有序 checklist + 验证命令 + review gate + rollback | `references/implement-orchestration.md` | `examples/implement.md` |
| 5 | parent / child 拆分 (1 task 含 ≥ 2 独立可验收 deliverable) | `references/task-tree.md` | — |
| 6 | jsonl 上下文清单 curate (为后续 dispatch 备料) | `references/jsonl-curation.md` | — |

轻量 task (单 deliverable + 单 subtask) 可仅做步骤 1 + 2 (PRD + 单 subtask 文件)。复杂 task 必须 6 步走完才能进入 `task.py start`。

范例集索引: `examples/README.md` (同一 OAuth2 登录场景贯穿全部文档)。

## 参考集 (按需读)

| 文件 | 何时读 |
| --- | --- |
| `references/prd-orchestration.md` | 写 / 改 PRD 时 |
| `references/subtask-file.md` | 创建 / 改 / 删 subtask 文件时 |
| `references/design-orchestration.md` | 写 / 改 design 时 |
| `references/implement-orchestration.md` | 写 / 改 implement 时 |
| `references/task-tree.md` | 多 deliverable 拆 parent/child 时 |
| `references/jsonl-curation.md` | dispatch 前最后一步 |
| `references/five-elements.md` | 拆任何 subtask / checklist 项时 (基础参考) |
| `references/layer-selection.md` | implement 标注执行层时 + trellis 复杂度判定 coordinator |
| `references/shared-resources.md` | 标注资源互斥 / 并行决策时 |
| `references/progress-communication.md` | coordinator 回传进度时 (每 subtask 完成 / 阻塞) |
| `references/task-lifecycle.md` | 任务规划开始 / 阶段切换前 (planning → in_progress → check → sediment → stop) |
| `references/selfcheck.md` | planning → start 前最终自检 |

## 引用

- Trellis workflow 全文: `.trellis/workflow.md` (只读, 不写)
- 相关 skill: `trellisx-spec` (任务收尾沉淀学习回 spec)
