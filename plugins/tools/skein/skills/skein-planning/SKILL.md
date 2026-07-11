---
name: skein-planning
description: planning 入口 (需求/方案单一真值源)。新建 SKEIN task 做需求梳理时使用 — 判新旧 + create 登记 + brainstorm (交互式) + grill 硬门, 产出 prd.md/implement.md。
argument-hint: "<任务描述>"
arguments: 任务描述 (要做需求梳理/规划的新 task)
---

# skein-planning — planning 入口

**planning 单一真值源**。判新旧 + 登记 + brainstorm + grill, 产出 planning 工件。**全程 main 同步前台** — brainstorm/grill 需逐问用户 (`AskUserQuestion`), subagent 不能与用户对话, 故不派执行 subagent (纯信息调研可派 `skein-researcher` 只读 subagent, 但设计决策 main 汇总裁定)。

`skein-researcher` 的结论持久化在 `.skein/task/<id>/research/` (dispatch 时把该 task id 作为 task-id 传给它)。planning 后续步骤 (brainstorm/PRD) 可复读这些笔记, 不必只靠回传摘要或记忆; task finish 归档时随 task 目录一并归档。

## 入参

- 无参 → 跑完 planning **STOP: 停在 start 前** (等用户直呼激活, 禁自行 start)。
- `--continue` → 跑完 planning **不停**, 返回工件路径 (供 `skein-flow` 自接激活)。

## 策略分档 (轻量路由启发)

判新旧后先给任务定档, 决定 planning 力度 (**仅路由启发, 非新增机器/字段**):

| 档 | 判据 | 走法 |
|---|---|---|
| `direct-fix` | 单点微改, 在作用域边界表豁免范围内 | 不建 task, 直接改 |
| `standard` | 跨文件 / 多步, 单 task 可覆盖 | 常规 plan→exec→check→finish |
| `heavy` | 跨子系统 / 破坏式重构 / 多 task 并行 | 强化 grill + 可能拆多 task + 显式 `depends_on`。破坏式重构 (改契约/删旧路径/全站点一次改齐, 禁垫片) 见 references/breaking-refactor.md |

## 流程

1. **判新旧** — 全新任务 vs 对现有 active task 的补充/延续。不准 → `AskUserQuestion` 用户裁定。并入现有 → 更新其工件, 不新建。
2. **登记** — 全新 → `skein.py create <name> [--desc ..] [--deps ..]`, 得 `<id>` + 工件目录。→ 更新看板。
3. **brainstorm 需求/方案** (main 交互式) — 逐问澄清: 目标 / 用户价值 / 边界 / 非目标 / 验收基准 / 方案取舍。禁 main 自行凭空设计。用 `AskUserQuestion` 拍板关键分歧。
4. **grill 硬门 CHECKPOINT** — 委托 `skein-grill` 全轴对抗校对, 重点确认「用户想法 = PRD 写的」。弱点表交用户过, 补齐后放行。**未跑 grill 禁进 exec**; grill 未完成或弱点表未补齐 → 停在本步, 禁推进。
   - **锁定契约** — grill/brainstorm 里梳理出的不变量 (MUST/禁/边界条件) 由 main 用脚本逐条锁进 task.json (main 同步跑脚本, 不派 agent), 供 check 阶段逐条验证:
     - `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <id> --add "契约文本"` (每条一次)
     - `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <id>` (列出核对)
     - 例: `contract <id> --add "响应体 MUST 保持向后兼容, 禁删字段"`; `contract <id> --add "单文件改动禁超 200 行"`。
5. **产出工件** — 写进 `.skein/task/<id>/`:
   - `prd.md` — 需求: 目标 / 用户价值 / 边界 / 非目标 / 验收基准。
   - `design.md` (可选, 复杂方案) — 架构 / 取舍 / 技术选型。
   - `implement.md` — 实现拆解: subtask 列表 (每个含 write-files glob + exec-scope + depends_on) + **调度图** (mermaid, 供 exec 阶段 DAG)。
6. **返回** — `--continue` → 返回工件路径给调用方; 无参 → 停, 提示用户激活。

## 调度图 (implement.md 必含)

exec 阶段的 DAG 靠这张图。缺失 → exec 无法调度 → 禁进 exec (退回本步补)。mermaid 示例 + subtask 表模板详见 references/dispatch-graph.md。

## 反例

违反上文即流程错误: 凭空设计需求方案 (应 brainstorm 逐问用户) / 派 subagent 做 brainstorm (它不能问用户) / 跳 grill 硬门进 exec / implement.md 缺调度图 / 纯文本代替 AskUserQuestion。
