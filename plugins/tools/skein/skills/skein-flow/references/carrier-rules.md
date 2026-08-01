# 执行载体铁律

skein-flow 全流程的载体层强制规则 (最高优先级)。每条都不可妥协, 违反即流程错误 (见主文件「反例」段)。

- **「派 agent」= 真实调用 `Agent` 工具, 不是叙述**。每个「派 agent」动作 MUST 在同一回复产生真实 tool_use。禁在无 `Agent` 调用时回传「已派出 / 在做」— 宣称 ≠ 调用 = 幻觉跳步。task/看板/worktree 的「已建」同理必须是真跑过命令的结果。
- **main 默认禁写源码** — 改源码 exec 一律派 `skein-executor`, 跑 check 派 `skein-checker`。仅特别情况例外 (上下文密集决策 / 用户显式要求), 且必在 task worktree 内。文件数口径见 [scope-boundary.md](scope-boundary.md), 禁另立「≤N 文件」标准。
- **载体一律具名 subagent, 禁 teammate / agent-team** — exec / check / finish 三阶段全部经 `Agent` 工具派具名 subagent, main 独家调度、结果只回传 main。**精确调用形式见下方「派发调用形式」段, 照抄即可**。禁 `SendMessage` 派 teammate, 禁 team 共享任务列表自认领, 禁 `Agent` 带 `team_name`。理由: 调度真值是 `.skein/task.json` 的 DAG + claim 占槽, team 的共享任务列表与之双写冲突; 且 subtask 顺序敏感 + 共享同一 worktree, 命中官方「sequential tasks / same-file edits 用 subagent 更有效」判据。环境层若开着 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, 本条仍是硬约束 — 开关是可用性, 不是许可。
- **exec / check 分工, main 作调度器** — exec: 一律派 `skein-executor` 各执行 1 个 (并发上限 2 / 完成即派 / 共享 task worktree); 递归护栏 (Recursion Guard) 靠 `skein-executor` 工具面剔除 Agent/Task 强制, 非靠 dispatch prompt 文字禁止。check: 派 `skein-checker` (工具受限, 无 Write/Edit/Agent/Task 的具名 agent)。调度算法详见 `skein-flow exec 阶段` skill, check 详见 `skein-flow check 阶段`。
- **有 task 必有 worktree** — task 在其 worktree 内执行 (`skein start` 自动建), 主工作区零改动; 默认 1 task 1 worktree。finish 后自动销。**多子 git**: 改动跨多个子 git (并列独立 repo 或 submodule) 时, planning 阶段用 `skein create <id> --name "X" --desc "Y" --repos <rel路径,逗号分隔>` 声明目标子 git (root 用 `.`); `start` 为每个声明的子 git 各建 1 worktree+分支, `finish` 各自 commit→merge→销。声明留空 = 单根/原地模式 (原行为)。子 git 集合由 planning 声明, 不靠脚本猜。
- **`skein` 由 main 同步跑** — create/start/finish/archive 是任务记录管理, main 直接跑, 不派 agent、不算实质工作。
- **看板自动刷** — task.json 每次变更 (create/start/subtask/finish) 脚本自动渲染 task.md/task.html, 无需手动跑命令; AI 禁直接编辑 (guard hook 硬阻)。
- **用户交互决策 main 亲做** — `AskUserQuestion` (判新旧不准 / 产物评审 / scope 澄清) subagent 不能与用户对话; subagent 缺信息在返回标 `需要: <问题>` 由 main 转达。
- **文案/格式类变更先给样例确认** — subtask 属**文案** (措辞 / 标签 / 提示语 / 文档表述) 或**格式** (排版 / 展示样式 / 结构布局) 类改动时, main 亲自先给用户「改前→改后」样例 (`AskUserQuestion` 或列对比), 确认后才落地; 逻辑 / bug 修复不受此限。派执行 agent 做此类改动时, dispatch prompt 须注明「先回传样例待 main 确认, 禁直接改」。
- **每个 dispatch prompt 6 字段自包含**: 目标 / 已知 (含 `Active task: <id>` + worktree 路径) / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。缺字段不派。**例外: exec 派 `skein-executor` 只给 tid+sid+工作目录三参数** (executor 自读 `subtask show` 补全, 见 [dag-scheduling.md](dag-scheduling.md) §9), 其余阶段 (check/finish) 不受此例外影响。
- **完成即时回传** — 每个 subagent 完成或阻塞, main 立即输出摘要, 禁批量延迟汇总。
- **并发多个 flow 请求禁互相顶掉** — 每个 flow 请求 = 独立 durable task, **收到即先 `skein create` 落盘**再处理。第二个请求进来时**禁中断/覆盖/丢弃**在飞的第一个: planning 阶段本就需 main 同步逐问用户 (brainstorm/grill/AskUserQuestion 不能并行), 故多请求**串行 planning** — 先把当前 task 登记 + 推进到不丢的态 (至少 `create` 落盘), 再处理下一个。已 `create` 未处理完的 task 留 pending, 由 `/skein-flow exec 阶段` 无参续跑, 绝不静默跳过。


## 派发调用形式 (照抄, 禁自由发挥)

三阶段一律用 built-in `Agent` 工具, `subagent_type` 取**带插件前缀的全名**:

| 阶段 | `subagent_type` | 何时 |
|---|---|---|
| exec | `skein:skein-executor` | 每个 ready subtask 一个 |
| check | `skein:skein-checker` | exec 全 done 后 |
| finish | `skein:skein-finisher` | check 全绿后 |
| planning 调研 | `skein:skein-researcher` | research 判定门命中 |
| sediment | `skein:skein-specer` | finish 后异步 fire-and-forget |

```
Agent(
  subagent_type = "skein:skein-executor",     # ← 前缀 skein: 不可省, 省了解析不到
  description   = "exec s3 认证中间件",         # 3-5 词, 进度显示用
  prompt        = "<6 字段自包含 dispatch>",    # 见下方「dispatch prompt 6 字段」
)
```

**禁用参数 / 禁用工具**:
- ❌ `team_name=...` — 传了就是 agent-team, 与 `.skein/task.json` 的 DAG + claim 占槽双写冲突
- ❌ `SendMessage(to=...)` 派 teammate — 同上
- ❌ 裸名 `subagent_type="skein-executor"` (缺 `skein:` 前缀)
- ❌ 只在文字里写「派 skein-executor 执行」而无真实 tool_use — 宣称 ≠ 调用

**并发**: 同一回复里发多个 `Agent` 调用 = 并行执行; 受 `max_active` (缺省 2) 限, 由 main 按 `skein claim exec` 结果决定这一批派几个, 不靠工具侧限流。

## ✅ 正向配方 (命中反面=流程错误)

以下场景与上方 11 条铁律互补, 覆盖铁律未逐条列出的具体反例 (与铁律重复的行已去重不重复列出):

| 场景 | 正确做法 (❌ 反面) |
|---|---|
| 处理请求 | 强制走 task 闭环, 即使看似简单 (❌ inline 跳 task) |
| 改任务状态 | 经 skein CLI 操作 (❌ 直编 `.skein/task.md`) |
| exec 派发顺序 | 按 depends_on DAG 自动排序即派 (❌ exec 阶段问用户顺序) |
| 有 subtask 的 task | 走 claim→派 subagent→done 循环 (❌ main inline 顺跑不派 subagent) |
| 相关工作组织 | 归一 task 拆 subtask (❌ 相关工作拆成多个 task) |
| 进 exec 前置 | 先过 grill 硬门再推进 (❌ 跳 grill 硬门进 exec) |
| 调度图/子任务落盘 | 写进 task.json (❌ 写进 md 文件) |
| subagent 回传后 (exec) | 只 `subtask done/fail` (❌ exec 阶段勾验收 — 归 check) |
| checker 报失败 | 交 `skein-executor` 定点改 (❌ checker 自改码) |
| check 失败 | 走回 planning 重确认: grill 敲定方向 → 同 task `subtask add`, task 保持 `进行中` (❌ 跳确认补 subtask / 改状态 / 另建 task) |
| finisher 职责 | finisher 自主勘察改动+清悬挂+跑 `skein finish`, 不做验收核对 (❌ finisher 核对 subtask 完成度 / 自己改码 / 跑 sediment) |
| sediment 时序 | finish 先闭环, sediment 异步 fire-and-forget 在后 (❌ sediment 阻塞 finish) |
| 宣告 Done | `skein finish` 标记完成后才宣告 Done (❌ 未 finish 闭环即宣告 Done) |
