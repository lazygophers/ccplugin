# flow 模式

**进入本文件后第一动作：先跑 `Bash("skein list --status unfinished --json")` 取现状。拿到 CLI 回显中的已注册 tid 前，禁止任何 Edit/Write；回复前缀中的 tid 必须来自该回显，禁止自造。**

| `$1`                     | 阶段            | 行为                                                                                                                     |
| ------------------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 全空                     | flow · 清空模式 | 不新建 task，取 `Bash("skein list --status unfinished --json")` 回显，按可推进顺序清空全部未完成 task。无未完成 task 则报「无待执行 task」。 |
| `flow` / 缺省 / 任务描述 | flow 默认闭环   | 有任务描述先走 plan 建/并入 task；之后自动续 exec→check→finish。                                                         |
| `plan`                   | 仅规划          | 推到规划完成态，完成 `Bash("skein task confirm <tid> --approved")` 后停，不续 exec。                                                        |
| `exec`                   | 续执行          | 驱动待处理/在途 task 继续闭环到 finish。                                                                                 |
| `check`                  | 质量门          | 派 `skein-checker` 验证；失败按本文件「失败扭转」。                                                                      |
| `finish`                 | 收尾门          | check 全绿后派 `skein-finisher` 完成 `Bash("skein task finish <tid>")` 和异步 sediment。                                                    |

硬规：无参/任务描述 -> flow 闭环模式；只有显式 `plan` 才在 confirm 后停，不续 exec。

**指定 task 有未完成前置 → 纳入前置链一起闭环, 不是拒绝理由**。用户点名执行 task X 但 X 的 `deps` 有未完成项时, 禁停在那报告「X 被前置阻塞」; 正确动作:

1. 沿 `deps` 链取全部未完成前置 task (递归, 直到无未完成前置), 按拓扑序执行。
2. 前置 task 是待处理态 → 先走 plan→confirm→exec 完整闭环; 已是进行中/调研中 → 直接续推进。
3. 前置全部 finish 后, 调度层的依赖门自动放行 X (`Bash("skein claim")` / `Bash("skein flow run")` 即可派活), 无需手动绕门。
4. 并发槽够时前置之间无相互依赖的可并行 (照 `Bash("skein flow run")` 的 hint 派), 不必串行等完。

## CLI 签名速查（本表与 `skein --help` 是同一契约，抄错就是一次白跑）

| 命令 | 易错点 |
| --- | --- |
| `Bash("skein task create <tid> --name <str> --desc <str> [--priority urgent\|high\|normal\|low] [--estimate <小时>]")` | `--priority` 只收这四个英文值，**没有中文档位**；`--estimate` 单位是**小时**（`0.5`=30 分钟，也收 `30m`/`1.5h`） |
| `Bash("skein subtask add <tid> <sid> --name <str> --desc <str> --estimate <小时> [--deps sid1,sid2] [--skills] [--check 'a;b'] [--phase exec\|research]")` | `<sid>` 是**位置参数**不是 `--id`；`sid`/`--name`/`--desc`/`--estimate` 四者缺一即拒；`--check` 分号分隔多条，也可重复传（各段累加） |
| `Bash("skein list --status <plan\|exec\|all\|unfinished\|pending\|...>")` | 顶层命令；`skein task list` 是转发别名，两者等价；`open`/`plan`=待处理阶段，`unfinished`=全部未完成 |
| `Bash("skein task spec <tid> [--desc <str>] [--should <a;b;c>] [--not <a;b;c>] [--acceptance <a;b;c>]")` | TaskSpec 四要素落盘 prd.md frontmatter；列表 `;` 分号分隔；不带参数 = 只读回显；confirm 后锁定 |
| 状态变更 | **没有 `task update --status`**。逐阶段命令：`confirm`（待处理→进行中）/ `research`+`plan`（待处理⇄调研中）/ `check` / `revert`（检查中→待处理）/ `finishing` / `finish`。改字段才用 `task rename\|priority\|estimate\|deps\|repos` |

**`subtask start` 不是开工的入口，`task confirm` 才是**。task 没过 confirm 门（还在待处理），它的 subtask 一律 start 不了 —— 别指望先干活后补审。

**串接 skein 写命令时看回显**——中途失败（如 `create` 成了但 `task spec` 挂了）不会静默：每条命令各自打自己的结果，照着回显重跑失败的那条即可。落盘状态是真值，别为「防半成品」预先把命令拆成一条一回合。

**`subtask done`/`fail` 属于 executor/researcher agent 自跑收尾**——main 串接 Bash 命令时不要把 `subtask done`/`fail` 串进去。executor 完成工作后自行执行 done/fail；main 串接这两条 = 替 agent 补收尾，破坏 agent 自治契约。main 只核对 agent 回传与实际状态是否一致。

## 任务流程框架

无论模式，流程首步固定为：

```text
Bash("skein list --status unfinished --json")  # 流程首步一次性盘点: 未完成 task + 已注册 tid, 之后不再重复跑
```

拿到未完成 task 与已注册 tid 后，才进入对应模式：

```text
Bash("skein task create <tid> --name <任务标题> --desc <任务描述> [--priority ...] [--parent ...] [--deps ...] [--estimate ...]")

# ============================================================
# PLAN 阶段 (含可选 research 循环)
# ============================================================
loop plan:
  # 编写需求文档、设计文档
  Bash("skein task spec <tid> --desc <任务描述> --should <应该做;a;b> --not <不做;a;b> --acceptance <验收;a;b>")
  Bash("skein design seam <tid> --list '接缝一\\n接缝二'")   # 测试接缝段必填, confirm 硬门

  if need_research:
    # 登记研究子任务并发起调研
    for subtask in research_subtasks:
      Bash("skein subtask add <tid> <sid> --name <标题> --desc <描述> --estimate <小时> --phase research [...]")
    Bash("skein task research <tid>")

    # 派发 research agent, 不 sleep 等待 — 每轮 flow tick 检查是否全 done
    loop research_tick:
      out = Bash("skein flow run")
      for hint in out.result.exec.next + out.result.check.next:
        Skills(name='skein-research', subagent_type='skein-researcher', prompt=hint.prompt)  # 异步派发, 不等待
      # 派完后直接查状态, 不 sleep
      if 还有 running/pending 的 research subtask:
        continue research_tick  # agent 还在跑, 下轮 tick 检查
      # 全 done → 收敛回 pending
    Bash("skein task plan <tid>")
    continue plan          # 收敛后带着调研结果重新规划

  # 建执行子任务
  for subtask in exec_subtasks:
    Bash("skein subtask add <tid> <sid> --name <标题> --desc <描述> --estimate <小时> [--deps ...] [--skills ...] [--check 'a;b']")

  if need_grill:
    # 按 skein-grill / ask-matt / grill-me / grill-doc 跑弱点审计
    Skill(name=<可用 grill skill>)
    continue plan          # 补弱点后重跑 plan 循环

  if plan_not_finished:
    continue plan

# 人审门
summary = Bash("skein task confirm <tid> --summary")
options = ["批准（仅规划，不执行）", "有修改意见"] if 模式 == 'plan' else ["批准并继续执行", "有修改意见"]
answer = AskUserQuestion(question=summary, options=options)
if answer 含 "修改意见":
  goto plan loop           # 重新规划
Bash("skein task confirm <tid> --approved")

if 模式 == 'plan':
  exit 0                   # 显式 plan 模式到此为止

# ============================================================
# EXEC 阶段 — 消费 flow run 派发 executor
# (executor 绑定 skill skein:skein-exec, 执行方法论自动随 frontmatter 注入; dispatch prompt 仍是纯 JSON)
# ============================================================
loop exec_tick:
  out = Bash("skein flow run")
  for hint in out.result.exec.next + out.result.check.next:
    Skills(name='skein-exec', subagent_type='skein-executor', prompt=hint.prompt)  # 异步派发, 不等待返回
  # Agent 派发受阻: 重派一次, 仍失败 → subtask fail + report_and_stop
  # 派完后不 sleep / 不轮询 — 直接看 task 状态是否已推进到 check

  status = Bash("skein task status <tid> --json")
  if task.status == "check":
    break exec_tick            # scheduler 在全 subtask done 后自动推 task 到 check
  if 仍有 running/pending subtask 且本轮无新 hint:
    # agent 还在跑, 没有 sleep — 继续下一轮 flow tick 检查是否有新 ready 的 subtask
    continue exec_tick
  # 全 done 但 task 还没到 check (scheduler tick 延迟), 再 tick 一次

# ============================================================
# CHECK 阶段 — 派 checker 验证, 聚合结果
# ============================================================
loop check_tick:
  out = Bash("skein flow run")   # check.next[] 带 checker hint
  for hint in out.result.check.next:
    Agent(subagent_type='skein-checker', prompt=hint.prompt)  # 异步派发, 不等待
  # 派完后看 task 状态是否已推进 (checker 自跑 done 后 scheduler 推 finishing)

  status = Bash("skein task status <tid> --json")
  if task.status == "finishing" or task.status == "done":
    break check_tick           # checker 全 PASS, scheduler 推进到 finishing
  if task.status == "pending":
    # checker FAIL → 已有修复 subtask 被 revert 回 plan, 需重新 confirm + exec
    Bash("skein task confirm <tid> --approved")
    goto exec_tick
  # checker 还在跑, 继续 tick

# ============================================================
# FINISH 阶段 — 派 finisher 完成
# ============================================================
out = Bash("skein flow run")   # 可能带 finishing/finisher hint
for hint in (out.result.exec.next + out.result.check.next):
  Agent(subagent_type='skein-finisher', prompt=hint.prompt)  # skein-finisher

# 确认 task 已 done
status = Bash("skein task status <tid> --json")
if status.done:
  print('任务完成')
else:
  report_and_stop("finish 未完成, 需人工介入")
```

## 主循环骨架

`Bash("skein flow run")` 是一次 scheduler tick：自动认领 ready exec/check，并把 Agent 派发信息放进 `result.exec.next[]` 与 `result.check.next[]`（**顶层 `result` 没有 `next` 键**，两层都要取，任一层都可能有 hint）。只消费 hint 的 `agent`、`tid`、`sid`、`workdir` / `workdirs`、`prompt`；不要从 `skein list` 重建 dispatch，也不要从 `task.worktree` 自行拼接 cwd。

🛑 **Agent 派发只传 `subagent_type` + `prompt`，不传 isolation 参数** —— worktree/cwd 已由 skein CLI 建好并写进 `hint.prompt` 的 `workdir`，agent 按该 workdir 原地干活。`workdir_kind`（`worktree` / `none`）只是信息位，说明 workdir 是 task worktree 还是原地仓库根。

🛑 **executor 只能由 Agent 工具派** —— 禁用 Bash 起任何 `claude` 子进程（`claude -p` / `claude --agent` / `claude agents` 等一律禁），也禁跑 `claude --help` 探参。Agent 派发受阻（被拒 / 回传异常）的唯一处置：重派一次；仍失败则 `Bash("skein subtask fail <tid> <sid> --note 'Agent dispatch blocked: <最短原因>'")` 释放已 claim 的 work 槽 + 回报用户并停下，不自撰替代执行路径，也不由 main 亲自把活干了。此处 `fail` 是 **agent 从未启动**时的调度补偿，不违反「done/fail 由已启动 agent 自跑」契约；等外部修复工具/权限后由后续 flow tick 重派。

真正下发给 agent 的模式开关在 `hint.prompt` 里：它是 scheduler 生成的**单行 JSON**（`tid` / `sid` / `workdir` 或 `workdirs` / `worktree: on\|off` / `repo` / `action`），main 原样转发，不重写不加料。`worktree=on` → 改动只准落在 workdir 内；`worktree=off` → 在仓库根原地改，无隔离。agent 回传同样只允许 JSON。

**`prompt` 是 scheduler 生成的成品串，原样传给 Agent，别自己重写加料** —— 自撰 prompt 有两个实测下场：写太长被 Agent 工具拒，或干脆不派、main 自己把活干了（一场会话 479 次 Edit 全在 main，executor 一次没派）。running subtask 的活归 executor；main 亲做没有 hook 会拦（提醒层已撤），只会让该 subtask 的落盘状态和实际改动对不上。

researcher/executor 完成工作后自行执行 `Bash("skein subtask done <tid> <sid>")`，失败执行 `Bash("skein subtask fail <tid> <sid> --note '<原因>'")`。main 只核对回传、报告和实际状态；报告已存在但 research subtask 仍 pending/running 时报告 mismatch。checker 只验证，scheduler 已推进 task 到 `check` 时安全幂等重跑。finisher 只在绝对仓库根执行 `Bash("skein task finish <tid>")`，不在将被销毁的 task worktree 内执行。多 repo checker 使用 `workdirs[]`。

`--summary` 只属于 `task confirm`；`subtask done` 不接受该选项，也不接受 `--passed`（done 即验收全过）。部分勾选验收走 `Bash("skein subtask check <tid> <sid> --passed <序号|all|none>")`，`--check` 只属于 `subtask add`。

```text
out = Bash("skein flow run")
# next[] 在 result.exec 与 result.check 两层下面，顶层 result 没有 next 键
for hint in out.result.exec.next + out.result.check.next:
  # 只按 hint.agent 派发；使用 hint.workdir 或 hint.workdirs
  # 带 mismatch 的 hint 没有 prompt，跳过并报告，不自撰 prompt 顶上
  # 不 或 task.status 自 或 task.status 自行推导执行目录和 Agent
  # Agent 只传 subagent_type + prompt  call = Skills(name='skein-exec', subagent_type='skein-executor', prompt=hint.prompt)  # 异步派发, 不等待返回
  try:
    async call
  except AgentDispatchBlocked as error:
    # 唯一处置：重派一次；禁 Bash 起 claude 子进程，禁 main 亲做
    retry once
    # 仍失败：agent 未启动，由 main 补 fail 释放已 claim 的槽，然后回报用户并停下
    Bash("skein subtask fail <hint.tid> <hint.sid> --note 'Agent dispatch blocked: <error最短原因>'")
    report_and_stop(error)

# researcher/executor 自行执行 subtask done/fail；main 核对回传与实际状态
# mismatch、FAIL、冲突、在途状态：报告或继续下一次 flow tick，不伪造状态
# 显式 plan 模式在 confirm 后停止；其他模式持续消费后续 tick 的 next[]
```

## 调度原则

- 🛑 **禁 sleep 轮询** — main 禁 `Bash("sleep N")` / `Bash("sleep N && skein ...")` 或定时轮询来等 agent 完成。Agent 工具本身是异步的：派出去后 main 继续下一轮 `Bash("skein flow run")` 或处理其他 task；agent 完成后自跑 done/fail + 异步回传通知 main，下一轮 flow tick 自然看到状态变化。
- **异步通知驱动** — "等待 agent"= 派发后继续做别的，靠 Agent 回传通知推进后续逻辑，而非阻塞 sleep。所有 ready subtask 在一轮 flow run 里全部派出去，不等单个完成。
- 需要和 User 交互的必须在 main 中执行
- 调度需要考虑最终耗时最小化，避免等待过长

## 状态模型

### task 状态

| 落盘值      | 展示名 | 阶段     | 池           | 进入命令                  | 含义                                                          |
| ----------- | ------ | -------- | ------------ | ------------------------- | ------------------------------------------------------------- |
| `pending`   | 待处理 | plan     | 无           | `Bash("skein task create <tid> ...")` / `Bash("skein task plan <tid>")` | 已 create，spec/design/subtask/estimate/grill/人审尚未全收敛。 |
| `research`  | 调研中 | research | work         | `Bash("skein task research <tid>")` | research subtask 在跑；全 done 后 `plan` 收敛回 `pending`。 |
| `active`    | 进行中 | exec     | 无 task 级池 | `Bash("skein task confirm <tid> --approved")` | 已 confirm，worktree 已建，subtask 可经 claim 派发。 |
| `check`     | 检查中 | check    | gate         | `Bash("skein task check <tid>")` | 全 subtask done 后进入验证。 |
| `finishing` | 收尾中 | finish   | gate         | `Bash("skein task finishing <tid>")` | check 全绿后占 gate 槽，等待/运行 finisher。 |
| `done`      | 已完成 | 完结     | 无           | `Bash("skein task finish <tid>")` | finish 成功，worktree 已销，闭环结束；`archive` 移入归档。 |

#### plan

> **Planning 工件写法 (PRD/design/estimate) 见 [skein-plan/references/plan.md](../../skein-plan/references/plan.md)，DAG 拆分调度模型见 [skein-plan/references/dag.md](../../skein-plan/references/dag.md)。本段只保留状态推进与出口规则。**

- 先查未完成 task（`Bash("skein list --status unfinished --json")`），判新诉求是并入现有 task 还是新建；同目标 / 同模块 / 共享改动面 / 互为前置默认并入，只有目标独立且无共享改动面才新建。
- 判 direct-fix / standard / heavy：direct-fix 仅限单文件单处 ≤20 行且位置已知；跨 ≥2 文件、多步、外部调研、文档交付一律建 task。
- 需要调研时，先登记 `Bash("skein subtask add <id> <sid> --name <标题> --desc <描述> --estimate <小时> --phase research")`，再 `Bash("skein task research <id>")`；`skein-researcher` 只读调研，结论落 `.skein/task/<id>/research/` 与 `findings.md`，全 done 后 `Bash("skein task plan <id>")` 收敛回 pending。
- brainstorm / 关键取舍用 `AskUserQuestion`；事实先自查，决策才问用户，禁止把可查事实甩给用户。
- 跑 grill 硬门：按弱点表逐项裁决并补回 spec/design/subtask；有未裁决弱点不得 confirm。
- `Bash("skein task confirm <tid> --summary")` 只给用户审、不改状态；用户明确批准后才 `Bash("skein task confirm <tid> --approved")`，裸 confirm 不作为自动过门手段。
- flow 默认焦点 task 通过 confirm 后直接续 exec；显式 `plan` / `--plan` 路由到 skein-plan skill，confirm 后停，不续 exec。

#### 周期 / 无人值守场景（cron、`/loop`、CI）

- **别每轮从零 planning**：先 `Bash("skein list --status all --json")` 找上一轮同 intent 的 task（**含已完成的**），用 `Bash("skein task create <新tid> --like <上一轮tid> --name <标题> --desc <描述>")` 克隆 spec/design/subtask 骨架，只改本轮真正不同的部分。不这么做的后果实测过：同一个巡检 intent 堆出 5 个内容雷同的 task。
- **别拿 `--approved` 冒充人审**：无人值守没有用户可问，`--approved` 就是伪造。走 `Bash("skein task confirm <tid> --unattended")`（需用户预先 `Bash("skein config set confirm.unattended true")` 授权一次），`confirmed_by` 会记 `unattended` 留痕。
- 参考 [skein-plan/references/dag.md](../../skein-plan/references/dag.md) 设计task/subtask 的编排以确保依赖关系得到满足、任务调度最高效

## check 过程 — 双 checker 并行

check 阶段可派两个 checker **并行**（各自独立 context，互不污染）：

| checker | 职责 | 返回 |
|---------|------|------|
| **skein-checker**（现有） | 验收标准 / 一致性 (skein-spec analyze) | JSON verdict |
| **skein-code-reviewer**（双轴 diff 审查） | Standards (repo 规范 + Fowler smell baseline) + Spec (diff 对齐 originating spec) | JSON verdict |

两个 checker 并行跑，各自回传 JSON。main 聚合：

- **任一 FAIL** → 补修复 subtask，回流 exec
- **全 PASS** → 放行 finishing
- **skein-code-reviewer 为可选** — 无 spec 来源或 diff 为空时跳过，不阻塞 skein-checker

## finish 过程

- 检测 `.skein/spec/.pending-fix`，存在则异步跑 maintain auto-fix（同样 fire-and-forget）。
- 未 finish 闭环不得宣告 Done。

### subtask 状态

| 落盘值    | 展示名 | 占 `pools.work` | 进入命令                  | 含义                                              |
| --------- | ------ | --------------- | ------------------------- | ------------------------------------------------- |
| `pending` | 待处理 | 否              | `Bash("skein subtask add <tid> <sid> ...")` | 已登记，等待 depends_on 全 done 和 claim。 |
| `running` | 运行中 | 是              | `Bash("skein subtask start <tid> <sid>")` | 已认领占槽，executor/researcher 正在执行。 |
| `done`    | 已完成 | 否              | `Bash("skein subtask done <tid> <sid>")` | 执行完成并释放槽；正式验收仍归 check。 |
| `failed`  | 失败   | 否              | `Bash("skein subtask fail <tid> <sid> --note '<原因>'")` | 执行失败并释放槽，可 start 重派或补修复 subtask。 |

## 作用域边界

skein-flow 的作用域判定 (何时建 task / 归一 vs 分立 / worktree 豁免) 与完成判定 —— 本文件是这三项的单一真值源。

### 归一 vs 分立 (相关工作优先归一 task 拆 subtask)

建 task 前先判新交付物是**某任务的一部分**还是**独立任务** —— 与现有 active task 或本请求内其他交付物**相关** (同目标 / 同模块 / 共享改动面 / 互为前置) → **归一到该 task 拆 subtask** (`subtask add` + `--deps`), 禁为相关工作另开多个 task; 仅**目标独立、无共享改动面、无依赖**才拆多 task。判据是相关性, 非「可独立验收」(subtask 亦可独立验收)。默认倾向归一 (散多 task 丢共享上下文一致性)。判不准 → AI 自行裁定 (默认归一), 仅极不确定才 `AskUserQuestion`。

## 终止条件

- 无就绪、无在途、无待处理可推进 task：报「无待执行 task」。
- 命中停顿白名单：输出问题和当前进度，等待回答。
- 自愈超上限、根因超 scope、DAG 死锁、finish 悬挂清不掉：停手回传。
- 走完 plan→exec→check→finish — **未 finish 闭环(标记完成) = 未完成, 禁宣告 Done**。
- finish 阶段前 main 需确认本 task 派出的后台 agent 均已结束, 未关 = 未闭环。
- sediment: 有可复用 learning 才沉淀, 无则跳过 (判定见 `skein-spec`)。
