---
name: skein-flow
description: 强制 task 闭环。复杂/多步/跨文件请求, 或用户显式要求把请求作为 SKEIN task 处理时使用 — 强推 plan→exec→check→finish 全流程, main 作调度器派 subagent 在 worktree 内执行, 禁 inline 直接做
argument-hint: "[任务描述] [--skip]"
arguments: "[任务描述] [--skip]"
model: sonnet
effort: medium
---

把请求**强制作为 SKEIN task 处理**, 除非用户输入 `--skip`，否则禁 inline 直接做 (即使看似简单)。但**不等于一定新建** — 先判**全新任务** vs **对现有 active task 的补充**, 再决定新建/并入

## 执行载体铁律 (最高优先级)

- **「派 agent」= 真实调用 `Agent` 工具, 不是叙述**。每个「派 agent」动作 MUST 在同一回复产生真实 tool_use。禁在无 `Agent` 调用时回传「已派出 / 在做」— 宣称 ≠ 调用 = 幻觉跳步。task/看板/worktree 的「已建」同理必须是真跑过命令的结果。
- **main 默认禁写源码** — 改源码为该 subtask 选合适 agent (无则 `skein-executor`), 跑 check 派 `skein-checker`。仅特别情况例外 (≤3 文件微改 / 上下文密集决策 / 用户显式要求), 且必在 task worktree 内。
- **exec / check 分工, main 作调度器** — exec: 为每个 subtask 选合适 agent (无则 `skein-executor`) 各执行 1 个 (并发上限 2 / 完成即派 / 共享 task worktree); 执行 agent 由 dispatch prompt 硬禁再派 subagent (Recursion Guard, 自己做完 1 个 subtask)。check: 派 `skein-checker` (工具受限, 无 Write/Edit/Agent/Task 的具名 agent)。调度算法详见 `skein-exec` skill, check 详见 `skein-check`。
- **有 task 必有 worktree** — task 在其 worktree 内执行 (`skein start` 自动建), 主工作区零改动; 默认 1 task 1 worktree。finish 后自动销。**多子 git**: 改动跨多个子 git (并列独立 repo 或 submodule) 时, planning 阶段用 `skein create --repos <rel路径,逗号分隔>` 声明目标子 git (root 用 `.`); `start` 为每个声明的子 git 各建 1 worktree+分支, `finish` 各自 commit→merge→销。声明留空 = 单根/原地模式 (原行为)。子 git 集合由 planning 声明, 不靠脚本猜。
- **`skein` 由 main 同步跑** — create/start/finish/archive 是任务记录管理, main 直接跑, 不派 agent、不算实质工作。
- **看板自动刷** — task.json 每次变更 (create/start/subtask/finish) 脚本自动渲染 task.md/task.html, 无需手动跑命令; AI 禁直接编辑 (guard hook 硬阻)。
- **用户交互决策 main 亲做** — `AskUserQuestion` (判新旧不准 / 产物评审 / scope 澄清) subagent 不能与用户对话; subagent 缺信息在返回标 `需要: <问题>` 由 main 转达。
- **文案/格式类变更先给样例确认** — subtask 属**文案** (措辞 / 标签 / 提示语 / 文档表述) 或**格式** (排版 / 展示样式 / 结构布局) 类改动时, main 亲自先给用户「改前→改后」样例 (`AskUserQuestion` 或列对比), 确认后才落地; 逻辑 / bug 修复不受此限。派执行 agent 做此类改动时, dispatch prompt 须注明「先回传样例待 main 确认, 禁直接改」。
- **每个 dispatch prompt 6 字段自包含**: 目标 / 已知 (含 `Active task: <id>` + worktree 路径) / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。缺字段不派。
- **完成即时回传** — 每个 subagent 完成或阻塞, main 立即输出摘要, 禁批量延迟汇总。
- **并发多个 flow 请求禁互相顶掉** — 每个 flow 请求 = 独立 durable task, **收到即先 `skein create` 落盘**再处理。第二个请求进来时**禁中断/覆盖/丢弃**在飞的第一个: planning 阶段本就需 main 同步逐问用户 (brainstorm/grill/AskUserQuestion 不能并行), 故多请求**串行 planning** — 先把当前 task 登记 + 推进到不丢的态 (至少 `create` 落盘), 再处理下一个。已 `create` 未处理完的 task 留 pending, 由 `/skein-exec` 无参续跑, 绝不静默跳过。

## 任务执行流程

plan → exec → check → finish 四步闭环

### plan

- **先查未完成再 durable 登记 (防丢/防并发覆盖/防堆重复 task)** — 收到请求**第一步**先跑一次廉价同步查 `skein list --status open --json` 判归属: 与在列某 task 相关 → **并入补 subtask, 不新建**; 无相关项才 `skein create <slug-id> --name --desc` 落 pending task。此 create 步早于 brainstorm/grill, 故请求即使中途中断或被下一个 flow 顶掉, task 已在盘上, 可 `/skein-exec` 无参续跑, **绝不静默跳过**。`create` 由 skein-plan 步骤 1-2 内部完成; 多个独立 flow 请求各自独立 `create` 独立 id, 互不覆盖 (并发处理见铁律)。**禁不查就 create、禁一直堆新 task**。
- **memory recall (自动召回)** — Skill(skein-memory recall): 派 `skein-memorier` 按任务关键词召回相关 recall 规则, 命中条目注入各 dispatch prompt「已知」段。core 规则已由 SessionStart hook 常驻, 无需召回。委托见 `skein-memory` skill。
- Skill(skein-grill) 确认用户详细需求，确保无遗漏、无偏离用户意图
- Skill(skein-plan --continue) 规划任务、编写 prd; **拆 subtask 并逐个 `subtask add <id> <sid> --agent ...` 登记** (每 subtask 绑定执行 agent, 是 exec 唯一调度真值源)。无 subtask 登记 → `skein start` 硬拒。
- 🛑 ToolCall(AskUserQuestion) 评审产物、确认用户需求 — 未确认禁进 exec (硬门 · STOP, main 亲做)
  - 确认并启动任务
  - 任务需要修改
- `skein start <id>` 激活 (建 worktree; start 仅收 `id`, 无 subtask 硬拒) — 用户确认后 main 同步跑

### exec

- Skill(skein-exec) 执行编排调度: main 作调度器, 动态 DAG 就绪即派 / 完成即派 (并发上限 2)
- **每个已登记 subtask MUST 派 1 个 subagent 异步执行 (硬门)** — 走 skein-exec 的 `claim → 派 Agent → done → claim` 循环, 每 ready subtask 各派 1 个 `Agent` (性质选合适 agent, 无则 `skein-executor`), 改动落 task worktree。**禁 main inline 顺跑 subtask**: 只要 task 有 subtask, 就必须派 subagent, 不得自己一个个做完 (line 15 的 ≤3 文件豁免只针对**整个 task 无 subtask 的微改**, 不是"有 subtask 却跳过派发"的借口)。
- 异步派发后结束回合前 MUST 输出任务清单 (id / 状态 / 摘要 / 进度%); 禁问用户顺序 (顺序归 planning)

### check

- Agent(skein-checker) 跑 lint / type-check / tests / 契约合规 + **一致性核查** (subtask 产物间 / 与 prd 契约有无冲突、重复实现、接口对不上)
- 未过 或 检出冲突 → **同 task 排队修复**: 不改 task 状态 (保持 `进行中`), 在同一 task 内 `subtask add` 修复子任务 (一失败/一冲突一 subtask, `--deps` 挂失败源), 回 exec 派发, 全绿且零冲突才放行
- 详见 `skein-check` skill (验证与修复分离 / 同 task 排队修复不换阶段 / 反复不过第 3 轮做 5 维根因复盘)

### finish

- Skill(skein-finish) 收尾编排门 (check 全绿后): 派 `skein-finisher` 收尾勘察 → 委托 `skein-memory` sediment → 清理悬挂 → `skein finish`。详见 `skein-finish` skill。
- 其中两处记忆自动化 (全流程记忆闭环 = plan recall 召回 + finish sediment 沉淀):
  - **sediment 判定门 (自动沉淀)** — 委托 `skein-memory` sediment: main 把 diff + exec 各 subagent 回传摘要 (含 `SPEC:` 标记) 传给 `skein-memorier`, 由它跑判定门产候选 (core/recall/drop 分层草案) → main 逐项输出 trace + `skein-memory sediment` 自动写盘 (判定门通过即写, 不逐次询问用户)。无增量则跳过 (禁硬凑)。
  - 清理悬挂 (`TaskList`/`TaskStop`) + `skein finish` (commit→merge→archive→销 worktree) 由 skein-finish 编排, main 同步跑。

## 作用域边界 (何时建 task)

| 特征                              | 判定                         |
| --------------------------------- | ---------------------------- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免                         |
| 单文件单处改, ≤20 行且位置已知    | 豁免                         |
| 跨 ≥2 文件 / 单文件多处 / 多步骤  | **必建 task**                |
| 需外部调研 / 产出文档交付         | **必建 task**                |
| 边界模糊                          | **AskUserQuestion 用户裁定** |

**归一 vs 分立 (相关工作优先归一 task 拆 subtask)**: 建 task 前先判新交付物是**某任务的一部分**还是**独立任务** —— 与现有 active task 或本请求内其他交付物**相关** (同目标 / 同模块 / 共享改动面 / 互为前置) → **归一到该 task 拆 subtask** (`subtask add` + `--deps`), 禁为相关工作另开多个 task; 仅**目标独立、无共享改动面、无依赖**才拆多 task。判据是相关性, 非「可独立验收」(subtask 亦可独立验收)。默认倾向归一 (散多 task 丢共享上下文一致性)。判不准 → `AskUserQuestion`。真值源见 `skein-plan` 步骤 1。

**worktree 豁免 (简单改不必上升到 worktree)**: main 按规模自动判 — 命中「单文件单处改 ≤20 行」或「单子 git ≤3 文件且改动集中」这类微改, 无需建 task/worktree, 原地做即可; 用户显式 `--skip` 强制 inline 覆盖自动判定。多子 git 场景同理: 真跨多仓的结构性改动才 `--repos` 声明走多 worktree, 每仓只沾一两行的顺带微调不必为它单开 worktree。

## 完成判定

- 走完 plan→exec→check→finish — **未 archive = 未完成, 禁宣告 Done**。
- finish 前清理悬挂 subagent / 后台任务 (`TaskList`/`TaskStop`), 未关 = 未闭环。
- sediment: 有可复用 learning 才沉淀, 无则跳过 (判定见 `skein-memory`)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                                    | 一线修复                                 | 仍失败兜底                                          |
| --------------------------------------- | ---------------------------------------- | --------------------------------------------------- |
| 判新旧不准 (新建 vs 并入现有 active)    | `AskUserQuestion` 用户裁定               | 用户也不确定 → 默认新建, 保守留旧 task 不动          |
| 相关工作误判成独立 (拆多 task)          | 按相关性收敛: 相关 → 归一 task 拆 subtask (`subtask add`) | 已误建多 task → `skein archive` 多余者, 归一到主 task 补 subtask |
| 某阶段未达出口 (plan 未收敛 / check 未绿) | 停在该阶段, 禁跨阶段推进                  | 反复不过 → 走对应子 skill 兜底 (check 第 3 轮根因复盘) |
| 宣称派 agent 但无 `Agent` tool_use      | 立即在同回合补真实 `Agent` 调用          | 补不出 → 硬错停手, 禁回传「已派出 / 在做」           |
| 有 subtask 却想 inline 顺跑             | 停手, 走 skein-exec `claim→派 Agent` 循环, 每 ready subtask 派 1 subagent | 派不出 → 硬错停手, 禁 main 代跑 subtask              |
| 第二个 flow 进来, 第一个还没 durable    | 先给第一个 `skein create` 落盘再处理第二个 | 都未落盘 → 立即各自 `create`, 未处理者留 pending 待续 |

## 反例 (命中 = 流程错误)

违反上文铁律即流程错误: main 直接改源码 / inline 跳 task / 宣称派 agent 无 tool_use / 无 worktree 改源码 / 直编 `.skein/task.md` / 纯文本代替 AskUserQuestion / exec 阶段问用户顺序 / **有 subtask 却 main inline 顺跑不派 subagent** / **第二个 flow 请求顶掉/中断在飞的第一个 task** / **相关工作拆成多个 task 而非归一 task 拆 subtask**。
