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

作用域边界统一判定 (与 trellisx-flow 共用同一表, 消除冲突):

| 特征 | 判定 |
| --- | --- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task |
| 单文件单处改, ≤20 行且位置已知 | 豁免 |
| 跨 ≥2 文件 / 单文件多处 / 多步骤改 | **必建 task** |
| 需外部调研 (库选型/方案对比) 或产出文档交付 | **必建 task** (调研为 research subtask) |
| 边界模糊 | **MUST AskUserQuestion 由用户裁定** |

无 task → 不进 workflow → 四规范豁免。Planning 阶段也不进 workflow: brainstorm 主线由 main 同步前台 (subagent 不能 AskUserQuestion); 纯信息调研可派 trellis-research 并行, 但设计决策由 main 汇总裁定。

建 task 后拆 ≥ 2 subtask:

```bash
python3 ./.trellis/scripts/task.py create "<title>" --slug <name>   # 建 task
python3 ./.trellis/scripts/task.py start <name>                     # 进 planning, after_start hook 自动建 worktree
```

调度规则 (无依赖即并行, 不留串行余量): 无共享文件且无前后序的 subtask 必须同一消息内并发派 sub-agent (isolation:worktree) / agent-team 成员 (`<git根>/.worktrees/<worktree>`); 有共享文件或前后序的串行。main 写源码**必须在 worktree 内** (单文件 subtask main 直做; 跨文件或可并行的派 agent), 见 `references/task-lifecycle.md`。

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

轻量 task (恰好 1 deliverable 且 1 subtask) 只做步骤 1 + 2 (PRD + 单 subtask 文件)。其余 (≥ 2 deliverable 或 ≥ 2 subtask) 必须 6 步走完才能进入 `task.py start`。

> 🔴 **CHECKPOINT · 🛑 STOP (planning → start 前)**: 走完 `references/selfcheck.md` 自检前 **禁 `task.py start`**。多交付 task 未拆 subtask 文件 / 未出 mermaid 调度图 / PRD 仍是开放式 → 退回补齐, 不准放行。

范例集索引: `examples/README.md` (同一 OAuth2 登录场景贯穿全部文档)。

## 反例黑名单 (禁做)

| # | 反模式 | 为什么禁 | 替代 |
| --- | --- | --- | --- |
| 1 | 开放式 PRD ("实现 X 功能") | 无 deliverable 矩阵 = dispatch 无据可拆 | 列 deliverable 矩阵 + 逐条验收 |
| 2 | 写完 PRD 才临时想怎么拆 | 编排理念没落文档 = 执行阶段重新推导 | 五要素 / 执行层 / 资源互斥就地内嵌 prd/design/implement |
| 3 | 多交付不建 subtask 文件 | dispatch prompt 无源 = sub-agent 缺六要素自包含 | 每 subtask 建独立文件 (步骤 2) |
| 4 | 共享 task 文件并发写 / 同 task 状态并行切换 | 写冲突 + 状态错乱 | 串行化 (立场: 串行优先) |
| 5 | 并行组不标依赖箭头 | 隐藏依赖 → 乱序执行 | mermaid 调度图显式标并行组 + 依赖 |
| 6 | 自检未过强行 `task.py start` | 带病进 in_progress, 返工成本翻倍 | 过 selfcheck gate 才放行 (上方 🔴) |
| 7 | 执行中收到修正指令, main 自己直接改源码 / 口头通知 agent | 与在跑 agent 改动分叉 + 文档与执行脱节 | 先改 PRD 真值文档 → SendMessage 通知在跑 agent 就地纠偏 (`references/progress-communication.md` §中途修正路由) |

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
| `references/progress-communication.md` | coordinator 回传进度时 (每 subtask 完成 / 阻塞); **执行中收到用户新指令做中途修正路由时** (§中途修正路由) |
| `references/task-lifecycle.md` | 任务规划开始 / 阶段切换前 (planning → in_progress → check → sediment → stop) |
| `references/selfcheck.md` | planning → start 前最终自检 |

## 失败处理 (触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 不在 trellis active task / 无 planning 状态 | 提示先 `task.py create` + `start` 进 planning | 非 trellis 项目 → 提示 `trellis init`, 不强行编排 |
| deliverable 边界判不准 (该拆 child 还是单 task) | 按"是否独立可验收"判 (`references/task-tree.md`) | 仍不准 → AskUserQuestion 问用户, 禁自行替决 |
| subtask 资源是否互斥拿不准 | 查 `references/shared-resources.md` 判共享文件/状态 | 拿不准 → 默认串行 (串行优先立场), 不赌并行 |
| selfcheck 未过但想 start | 退回补齐缺项 (subtask 文件/调度图/验收) | 反复不过 → 缩小 MVP 范围重新拆, 不带病 start |
| reference 文件读不到 | 按 SKILL 主体规则就地编排 | 关键 reference 缺失 → 提示用户 skill 安装不全 |

## 引用

- Trellis workflow 全文: `.trellis/workflow.md` (只读, 不写)
- 相关 skill: `trellisx-spec` (任务收尾沉淀学习回 spec)
