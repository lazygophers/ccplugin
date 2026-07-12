---
name: skein-flow
description: 强制 task 闭环。复杂/多步/跨文件请求, 或用户显式要求把请求作为 SKEIN task 处理时使用 — 强推 plan→exec→check→finish 全流程, main 作调度器派 subagent 在 worktree 内执行, 禁 inline 直接做
user-invocable: false
argument-hint: "[任务描述] [--skip]"
arguments: "[任务描述] [--skip]"
model: sonnet
effort: medium
---

把请求**强制作为 SKEIN task 处理**, 除非用户输入 `--skip`，否则禁 inline 直接做 (即使看似简单)。但**不等于一定新建** — 先判**全新任务** vs **对现有 active task 的补充**, 再决定新建/并入

## 执行载体铁律 (最高优先级)

- **「派 agent」= 真实调用 `Agent` 工具, 不是叙述**。每个「派 agent」动作 MUST 在同一回复产生真实 tool_use。禁在无 `Agent` 调用时回传「已派出 / 在做」— 宣称 ≠ 调用 = 幻觉跳步。task/看板/worktree 的「已建」同理必须是真跑过命令的结果。
- **main 默认禁写源码** — 改源码为该 subtask 选合适 agent (无则 `skein-executor`), 跑 check 派 `skein-checker`。仅特别情况例外 (≤3 文件微改 / 上下文密集决策 / 用户显式要求), 且必在 task worktree 内。
- **exec 选合适 agent 执行 / check 派 checker, main 作调度器** — 动态 DAG 为每个 subtask 选合适 agent (按任务性质挑现有 agent, 无合适的用 `skein-executor`) 各执行 1 subtask (并发上限 2, 完成即派), 共享 task worktree; check 派 `skein-checker`。执行 agent 的递归护栏由 dispatch prompt 硬性禁止再派 subagent 承载 (Recursion Guard, 自己动手做完 1 个 subtask); `skein-checker` 仍是工具受限 (无 Write/Edit/Agent/Task) 的具名 agent。调度算法 (双层 DAG / 完成即派循环 / 多 task 并行 / dispatch prompt 携带执行纪律) 详见 `skein-exec` skill; check 详见 `skein-check`。
- **有 task 必有 worktree** — task 在其 worktree 内执行 (`skein.py start` 自动建), 主工作区零改动; 默认 1 task 1 worktree。finish 后自动销。
- **`skein.py` 由 main 同步跑** — create/start/finish/archive 是任务记录管理, main 直接跑, 不派 agent、不算实质工作。
- **看板自动刷** — task.json 每次变更 (create/start/subtask/finish) 脚本自动渲染 task.md/task.html, 无需手动跑命令; AI 禁直接编辑 (guard hook 硬阻)。
- **用户交互决策 main 亲做** — `AskUserQuestion` (判新旧不准 / 产物评审 / scope 澄清) subagent 不能与用户对话; subagent 缺信息在返回标 `需要: <问题>` 由 main 转达。
- **每个 dispatch prompt 6 字段自包含**: 目标 / 已知 (含 `Active task: <id>` + worktree 路径) / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。缺字段不派。
- **完成即时回传** — 每个 subagent 完成或阻塞, main 立即输出摘要, 禁批量延迟汇总。

## 任务执行流程

plan → exec → check → finish 四步闭环

### plan

- `skein.py start <任务 ID> --name <任务名称> --desc <任务描述>` 创建任务
- **memory recall (自动召回)** — Skill(skein-memory recall): 派 `skein-memorier` 按任务关键词召回相关 recall 规则, 命中条目注入各 dispatch prompt「已知」段。core 规则已由 SessionStart hook 常驻, 无需召回。委托见 `skein-memory` skill。
- Skill(skein-grill) 确认用户详细需求，确保无遗漏、无偏离用户意图
- Skill(skein-plan --continue) 规划任务、编写 prd 等内容
- ToolCall(AskUserQuestion) 评审产物、确认用户需求
  - 确认并启动任务
  - 任务需要修改

### exec

- Skill(skein-exec) 执行编排调度: main 作调度器, 动态 DAG 就绪即派 / 完成即派 (并发上限 2)
- Agent(按 subtask 性质选合适 agent, 无则 `skein-executor`) 各执行 1 subtask, 改动落 task worktree
- 异步派发后结束回合前 MUST 输出任务清单 (id / 状态 / 摘要 / 进度%); 禁问用户顺序 (顺序归 planning)

### check

- Agent(skein-checker) 跑 lint / type-check / tests / 契约合规 + **一致性核查** (subtask 产物间 / 与 prd 契约有无冲突、重复实现、接口对不上)
- 未过 或 检出冲突 → **深化拆分**: 不止定点补丁, 回 `skein.py plan` 把冲突根因拆成新 subtask (逐条覆盖每个冲突), 重跑 exec→check 直到全绿且零冲突
- 详见 `skein-check` skill (验证与修复分离 / 一致性冲突 → 深化拆分 / 反复不过第 3 轮做 5 维根因复盘)

### finish

- Skill(skein-finish) 收尾编排门 (check 全绿后): 派 `skein-finisher` 收尾勘察 → 委托 `skein-memory` sediment → 清理悬挂 → `skein.py finish`。详见 `skein-finish` skill。
- 其中两处记忆自动化 (全流程记忆闭环 = plan recall 召回 + finish sediment 沉淀):
  - **sediment 判定门 (自动沉淀)** — 委托 `skein-memory` sediment: `skein-memorier` 读 journal+diff 跑判定门产候选 (core/recall/drop 分层草案) → main 逐项输出 trace + `AskUserQuestion` 审批 + `memory.py sediment` 写盘。无增量则跳过 (禁硬凑)。
  - 清理悬挂 (`TaskList`/`TaskStop`) + `skein.py finish` (commit→merge→archive→销 worktree) 由 skein-finish 编排, main 同步跑。

## 作用域边界 (何时建 task)

| 特征                              | 判定                         |
| --------------------------------- | ---------------------------- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免                         |
| 单文件单处改, ≤20 行且位置已知    | 豁免                         |
| 跨 ≥2 文件 / 单文件多处 / 多步骤  | **必建 task**                |
| 需外部调研 / 产出文档交付         | **必建 task**                |
| 边界模糊                          | **AskUserQuestion 用户裁定** |

## 完成判定

- 走完 plan→exec→check→finish — **未 archive = 未完成, 禁宣告 Done**。
- finish 前清理悬挂 subagent / 后台任务 (`TaskList`/`TaskStop`), 未关 = 未闭环。
- sediment: 有可复用 learning 才沉淀, 无则跳过 (判定见 `skein-memory`)。

## 反例 (命中 = 流程错误)

违反上文铁律即流程错误: main 直接改源码 / inline 跳 task / 宣称派 agent 无 tool_use / 无 worktree 改源码 / 直编 `.skein/task.md` / 纯文本代替 AskUserQuestion / exec 阶段问用户顺序。
