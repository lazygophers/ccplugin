---
name: skein-plan
description: "planning 入口 + 单一真值源 (用户可显式调用 /skein-plan, 也被 skein-flow 委托): 新建 SKEIN task 做需求梳理 — 判新旧 + create 登记 + brainstorm (交互式) + grill 硬门, 产出 prd.md 主入口 + design.md 详细设计 + 调度落 task.json。无参 = 跑完停在 start 前 (只规划不执行); --continue = 不停返回工件路径 (供 flow 自接激活)"
user-invocable: true
argument-hint: "<任务描述>"
arguments: "<任务描述>"
model: opus
effort: high
---

# skein-plan — planning 入口 + 单一真值源

**planning 单一真值源**。判新旧 + 登记 + brainstorm + grill, 产出 planning 工件。**全程 main 同步前台** — brainstorm/grill 需逐问用户 (`AskUserQuestion`), subagent 不能与用户对话, 故不派执行 subagent (纯信息调研可派 `skein-researcher` 只读 subagent, 但设计决策 main 汇总裁定)。

`skein-researcher` 的结论持久化在 `.skein/task/<id>/research/` (dispatch 时把该 task id 作为 task-id 传给它)。planning 后续步骤 (brainstorm/PRD) 可复读这些笔记, 不必只靠回传摘要或记忆; task finish 归档时随 task 目录一并归档。

## 入参 (决定是否停在 start 前)

- **无参** (用户直呼 `/skein-plan`) → 跑完 planning **停在 start 前**, task 留 planning 态, 交还控制权。**禁 `skein.py start` / 禁 exec / check / finish** — 执行归 `skein-flow` / `/skein-exec`。
- `--continue` (skein-flow 委托) → 跑完 planning **不停**, 返回工件路径 (供 `skein-flow` 自接激活)。

## 策略分档 (轻量路由启发)

判新旧后先给任务定档, 决定 planning 力度 (**仅路由启发, 非新增机器/字段**):

| 档           | 判据                                 | 走法                                                                                                                                   |
| ------------ | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `direct-fix` | 单点微改, 在作用域边界表豁免范围内   | 不建 task, 直接改                                                                                                                      |
| `standard`   | 跨文件 / 多步, 单 task 可覆盖        | 常规 plan→exec→check→finish                                                                                                            |
| `heavy`      | 跨子系统 / 破坏式重构 / 多 task 并行 | 强化 grill + 可能拆多 task + 显式 `depends_on`。破坏式重构 (改契约/删旧路径/全站点一次改齐, 禁垫片) 见 references/breaking-refactor.md |

### 作用域边界 (何时建 task)

| 特征                              | 判定                            |
| --------------------------------- | ------------------------------- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task                 |
| 单文件单处改, ≤20 行且位置已知    | 豁免                            |
| 跨 ≥2 文件 / 单文件多处 / 多步骤  | **必建 task**                   |
| 需外部调研 / 产出文档交付         | **必建 task** (调研走 research) |
| 边界模糊                          | **AskUserQuestion 用户裁定**    |

## 流程

1. **判新旧** — 全新任务 vs 对现有 active task 的补充/延续。不准 → `AskUserQuestion` 用户裁定。并入现有 → 更新其工件, 不新建。
2. **登记** — 全新 → `skein.py create <id> [--desc ..] [--deps ..] [--estimate <分钟>]`, `<id>` 须为**可读描述性 slug** (kebab-case, 如 `order-create-api` / `user-auth`; 兼作分支名 + 目录名), **禁 `t01`/`t2` 这类字母+数字代号** (脚本硬拒)。得工件目录。`--estimate` = **AI 执行预期耗时** (非人类工时), planning 判力度时估, 供 task.html 显示 预期 vs 实际。subtask 同理可带 `--estimate`。(`create` 自动刷看板)
3. **brainstorm 需求/方案** (main 交互式) — 逐问澄清: 目标 / 用户价值 / 边界 / 非目标 / 验收基准 / 方案取舍。禁 main 自行凭空设计。用 `AskUserQuestion` 拍板关键分歧。
4. **grill 硬门 (未过禁进 exec)** — 委托 `skein-grill` 全轴对抗校对, 重点确认「用户想法 = PRD 写的」。弱点表交用户过, 补齐后放行。**未跑 grill 禁进 exec**; grill 未完成或弱点表未补齐 → 停在本步, 禁推进。
   - **锁定契约** — grill/brainstorm 里梳理出的不变量 (MUST/禁/边界条件) 由 main 用脚本逐条锁进 task.json (main 同步跑脚本, 不派 agent), 供 check 阶段逐条验证:
     - `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <id> --add "契约文本"` (每条一次)
     - `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py contract <id>` (列出核对)
     - 例: `contract <id> --add "响应体 MUST 保持向后兼容, 禁删字段"`; `contract <id> --add "单文件改动禁超 200 行"`。
5. **产出工件** — `create` 已落 prd/design/findings 三脚手架 (骨架标题, 本步填正文); 调度落 task.json (脚本):
   - `prd.md` (主入口) — 分章节: **目标 / 边界 / 验收标准 / 索引** (链 design/findings/task.json)。每章节自带 `- [ ] TODO`, 填完逐个勾掉; 未勾清 = planning 未收敛。
   - `design.md` — 详细设计: 架构 / 数据流 / 取舍 / 技术选型 (**不含调度图**, 调度归 task.json)。
   - `findings.md` (需调研时) — 深度调研的收敛结论 + 依据/引用; 过程笔记存 `research/` (researcher 写)。
   - **子任务 + 调度 DAG** — subtask 拆分 (每个含 depends_on + 验收 checklist) 逐条 `skein.py subtask add <id> <sid> --name --agent [--deps --check]` 落进 task.json。**这是 exec 唯一调度真值源**, 不写 mermaid 图文件。
6. **返回** — `--continue` → 返回工件路径给调用方; 无参 → 停在 start 前, 提示用户 `/skein-exec <task>` 或 `/skein-flow` 激活。

## 调度 = task.json 子任务 DAG

exec 阶段的 DAG 靠 task.json 的 `subtasks[].depends_on` (经 `skein.py subtask add --deps` 登记), **非文件里的 mermaid 图**。planning 未登记任何 subtask → `skein.py start` 硬拒 (无从调度)。subtask 拆分 + 依赖登记模板详见 references/dispatch-graph.md。

## 反例

违反上文即流程错误: 凭空设计需求方案 (应 brainstorm 逐问用户) / 派 subagent 做 brainstorm (它不能问用户) / 跳 grill 硬门进 exec / **把调度图/子任务写进 md 文件而非 task.json** / start 前未 `subtask add` 任何子任务 / 纯文本代替 AskUserQuestion / **无参调用却跑了 `skein.py start` 或 exec/check/finish** (无参只到 planning 停, 执行归 flow/go)。
