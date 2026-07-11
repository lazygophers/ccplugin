---
name: trellisx-orchestrate
description: '🎯 在 Trellis 项目 planning 阶段, 指导编写 task 文件夹内的 prd.md / design.md / implement.md, 把任务编排理念 (五要素拆分、执行层选择、资源互斥、失败回退) 内嵌到文档中。让后续 dispatch 与执行有据可依, 而不是写完 PRD 才临时想怎么拆'

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

无 task → 不进执行编排 → 执行规约豁免。Planning 阶段不派执行 subagent: brainstorm 主线由 main 同步前台 (subagent 不能 AskUserQuestion); 纯信息调研可派 trellis-research 并行, 但设计决策由 main 汇总裁定。

建 task 后拆 ≥ 2 subtask:

```bash
python3 ./.trellis/scripts/task.py create "<title>" --slug <name>   # 建 task
python3 ./.trellis/scripts/task.py start <name>                     # 进 planning, after_start hook 自动建 worktree
```

调度规则 (**main 是调度器**, 动态 DAG 调度, 见 `references/scheduling.md`): planning 末 main 静态算冲突 (两类自动依赖边: 写盘文件 glob 相交 `write-files` + 执行作用域相交 `exec-scope`; 加显式 `depends-on`) → 建 DAG → exec 阶段循环: 查 ready → 派 min(|ready|, 2-|running|) 个 `trellis-implement` 各执行 1 subtask (**共享 task worktree**, 并发上限 2, 完成即派下一个, 不空等) → 任一返回 (notification) 即更新态、查新 ready、立即派 → failed 走 failure-recovery → 全 done 转 trellis-check。**trellis-implement 不调度不递归** (工具集无 Agent/Task, Recursion Guard; 每 subtask 文件 frontmatter 必填 `write-files` + `exec-scope`)。subtask 与 worktree 无绑定; 多 worktree 属 opt-in, 非自动, 非由 subtask 触发。

## 触发判定

被路由加载 (非用户直接入口, 入口归 trellisx-flow), 符合任一即生效:

- trellisx-flow 判定建 task 进 planning 后路由本 skill 做执行层编排
- trellisx-apply 规划步触发
- 处于 trellis active task 且 status = planning, PRD 列 ≥ 2 deliverable 尚未拆 design/implement
- planning → in_progress 前的最后一遍编排校对

不触发: 用户直接喊"写 PRD / 规划任务" (路由进 flow 先判建 task) / 已 in_progress 在执行 / 单文件咨询 / 与编排无关问答。

## 工作流 (6 步, 渐进披露)

每步先读对应 reference (写法规则) + 对应 example (填好的范例), 再写文档:

| 步骤 | 行动 | 写法 reference | 填好范例 |
| --- | --- | --- | --- |
| 1 | PRD 编排 — 🔴 **spec 加载门 (planning 必做, 非软约束; 本 skill 独家 owner, flow 不重复加载)**: 先 grep `.trellis/spec/guides/index.md` 按主题找相关 guide, 命中读全文注入 PRD 上下文 (约束/契约/验收基准); 无相关 spec 才跳过。**被动可见**: 本 gate 文本由 trellis 原生每轮注入 context (AI 每轮知 spec 存在 + index 路径, 不靠记忆)。**诚实边界**: relevant guide 检索归本步主动 grep (model 驱动, 非脚本全自动; 无独立 per-turn hook, config.yaml 仅 lifecycle 事件)。再出 deliverable 矩阵 + subtask 概览表 + mermaid 调度图 + 验收 + 范围边界。🔴 **grill 硬门 1 (边问边写, 与 brainstorm 协同)**: PRD 编写过程 MUST 调 `/trellisx-grill` 用轴 A (目标) / B (产出) 当提问引擎 —— grill 出问 → brainstorm 逐问用户 → 答完即时更新 PRD → 循环至轴 A/B 双 ✓。禁写完整 PRD 才审 (本末倒置) | `references/prd-orchestration.md` | `examples/prd.md` |
| 2 | 为每个 subtask 建独立文件 `.trellis/tasks/<task>/subtask/<id>-<slug>.md` 含完整五要素 + dispatch prompt | `references/subtask-file.md` | `examples/subtask/S2-jwt-utils.md` `examples/subtask/S3-jwt-middleware.md` |
| 3 | design 编排 — 模块表 + 执行层标注 + 资源边界 + 契约 | `references/design-orchestration.md` | `examples/design.md` |
| 4 | implement 编排 — 有序 checklist + 验证命令 + review gate + rollback | `references/implement-orchestration.md` | `examples/implement.md` |
| 5 | parent / child 拆分 (1 task 含 ≥ 2 独立可验收 deliverable): `task.py create --parent <dir>` 建 child + parent 写 Child Task Map + 跨 child 验收标准 | `references/task-tree.md` | 同文件 §Child Task Map / §Parent task 内容 (命令 + 表格式范例) |
| 6 | jsonl 上下文清单 curate (为后续 dispatch 备料): 逐 subtask 写 implement.jsonl / check.jsonl 的 spec + research 条目 | `references/jsonl-curation.md` | 同文件 §Entry 格式 (字段定义 + JSON 行范例) |

轻量 task (恰好 1 deliverable 且 1 subtask) 只做步骤 1 + 2 (PRD + 单 subtask 文件)。其余 (≥ 2 deliverable 或 ≥ 2 subtask) 必须 6 步走完才能进入 `task.py start`。

> 🔴 **CHECKPOINT · 🛑 STOP (planning → start 前, grill 硬门 2)**: 走完 `references/selfcheck.md` 自检前 **禁 `task.py start`**。多交付 task 未拆 subtask 文件 / 未出 mermaid 调度图 / PRD 仍是开放式 → 退回补齐, 不准放行。**MUST 先调 `/trellisx-grill` 跑全轴需求确认** (硬门, 非可选): grill 弱点表交用户过, 用户确认"这就是我要的" + 弱点补齐后才放行 start。未跑 grill = 流程未完成, 禁 start。

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
| 8 | exec 阶段 subtask 之间停下来问用户"先做哪个" | 顺序归 planning (本 skill 产调度图 + depends-on), exec 只跑调度循环 —— 问序 = planning 没做透 | 按 DAG 自动派 (scheduling.md §4); PRD 缺调度图 / depends-on → 退回 planning 补, 不在 exec 问 |

## 参考集 (按需读, progressive disclosure)

> **token 纪律**: 本 skill 被 flow 路由自动触发, 12 references 全读会撑爆 token (多 skill session 旧 skill 被静默踢出, 无错误信息)。**禁一次全读** —— 只读当前步骤对应的那 1-2 个 reference (见工作流表「写法 reference」列) + 对应 example。其余按需。轻量 task (1 deliverable/1 subtask) 仅读步骤 1+2 的 reference。

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
| `references/scheduling.md` | exec 阶段动态 DAG 调度 (main 调度器 / 冲突判定 / 5 态 / 并发 2 / 完成即派) |
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

- 只读 trellis 原生生命周期规则文件
- 相关 skill: `trellisx-spec` (任务收尾沉淀学习回 spec)
