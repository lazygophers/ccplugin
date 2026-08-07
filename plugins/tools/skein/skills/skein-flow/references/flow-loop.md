# flow 模式

| `$1`                     | 阶段            | 行为                                                                                                                     |
| ------------------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 全空                     | flow · 清空模式 | 不新建 task，取 `skein list --status open --json`，按可推进顺序清空全部未完成 task。无 open task 则报「无待执行 task」。 |
| `flow` / 缺省 / 任务描述 | flow 默认闭环   | 有任务描述先走 plan 建/并入 task；之后自动续 exec→check→finish。                                                         |
| `plan`                   | 仅规划          | 推到规划完成态，完成 `skein task confirm --approved` 后停，不续 exec。                                                        |
| `exec`                   | 续执行          | 驱动待处理/在途 task 继续闭环到 finish。                                                                                 |
| `check`                  | 质量门          | 派 `skein-checker` 验证；失败按本文件「失败扭转」。                                                                      |
| `finish`                 | 收尾门          | check 全绿后派 `skein-finisher` 完成 `skein task finish` 和异步 sediment。                                                    |

硬规：无参/任务描述 -> flow 闭环模式；只有显式 `plan` 才在 confirm 后停，不续 exec。

## CLI 签名速查（本表与 `skein --help` 是同一契约，抄错就是一次白跑）

| 命令 | 易错点 |
| --- | --- |
| `skein task create <tid> --name <str> --desc <str> [--priority urgent\|high\|normal\|low] [--estimate <小时>]` | `--priority` 只收这四个英文值，**没有中文档位**；`--estimate` 单位是**小时**（`0.5`=30 分钟，也收 `30m`/`1.5h`） |
| `skein subtask add <tid> <sid> --name <str> --desc <str> --estimate <小时> [--deps sid1,sid2] [--skills] [--check] [--phase exec\|research]` | `<sid>` 是**位置参数**不是 `--id`；`sid`/`--name`/`--desc`/`--estimate` 四者缺一即拒 |
| `skein prd write <tid> --type <段名> --list <条目>` | `--type` **单数**，一次只写一段；段名 `goal\|scope\|stories\|acceptance\|verification\|testing` |
| `skein list --status <open\|all\|pending\|...>` | 顶层命令；`skein task list` 是转发别名，两者等价 |

**禁把多条 skein 写成 `&&` 长链** —— 中途失败会留下半成品 task（`create` 成功但 `prd write` 失败 → 重跑撞 `id 已占用`，只能换 id，留孤儿）。分开发，每条看回显。

## 任务流程框架

```
Bash(skein task create <tid> --name <任务标题> --desc <任务描述> [--priority urgent|high|normal|low] [--parent 父任务ID] [--deps 依赖任务ID] [--estimate <小时>])

PLAN:
def research():
  # 建 research 子任务
  for subtask in research_subtasks:
    Bash(skein subtask add <tid> <sid> --name <subtask标题> --desc <subtask描述> --estimate <小时> --phase research [--deps 依赖sid] [--skills 技能列表])
  Bash(skein task research <tid>)

  Wait(research subtask done) # 等待主循环调度
  Agent(sub_agent='skein:skein-specer', prompt='sediment', context=fork, task=<tid>, step='research')
  Bash(skein task plan <tid>)

# 编写需求文档、设计文档等
for 任务规划:
  # prd 六段逐段写 (--type 单数, 一次一段); design 无 CLI, 直接编辑文件
  for seg in [goal, scope, stories, acceptance, verification, testing]:
    Bash(skein prd write <tid> --type <seg> --list <该段条目,支持多个>)
  Write(.skein/task/<tid>/design.md)   # 测试接缝段必须填实, confirm 会硬门校验

  if need_research:
    research()
    continue

  # 建子任务 (sid 位置参数 + estimate 必填)
  for task in subtasks:
    Bash(skein subtask add <tid> <sid> --name <task标题> --desc <task描述> --estimate <小时> [--deps 依赖sid] [--skills 技能列表])

  if need_grill:
    if exist_skill("ask-matt"):
      Skill(name="ask-matt", prompt="使用 AskUserQuestion 询问")
    elif exist_skill("grill-me"):
      Skill(name="grill-me", prompt="使用 AskUserQuestion 询问")
    elif exist_skill("grill-doc"):
      Skill(name="grill-doc", prompt="使用 AskUserQuestion 询问")
    else:
      Skill(name="skein-grill")
    continue

  if plan_finished:
    break

summary = Bash(skein task confirm <tid> --summary)
if AskUserQuestion(summary) != '确认':
  goto Plan(分析失败原因，并重新规划任务)
else:
  Bash(skein task confirm <tid> --approved)

if 模式 == 'plan':
  exit 0

Wait(subtask done) # 等待主循环调度
Bash(skein task check <tid>)

if Wait(check done) != 'pass': # 等待主循环调度
  goto Plan(分析失败原因，并重新规划任务)
else:
  Bash(skein task finish <tid>)

Agent(sub_agent='skein:skein-specer', prompt='sediment', context=fork, task=<tid>, step='finish')
Wait(finish done) # 等待主循环调度

print('任务完成')
```

## 主循环骨架

`skein claim` 的回显里有 `next: [{agent, tid, sid}]` —— **认领只改状态，推进靠你按 `next` 派 agent**。
拿到 `checked: [X]` 就该立刻派 `skein-checker X`，**不要轮询 `skein list` 等状态自己变**（等不到，那是活锁）。

```text
Bash("skein claim")                                   # 一次 claim, 两路认领: ready subtask 标 running;
                                                      # 全 done 的 active→check, 全 done 的 check→finishing
                                                      # 回显 next[] 直接给出该派的 agent + tid/sid
for task in Bash("skein list --status open --json"):  # 认领后按 task 状态分派
  wd = task.worktree or repo_root
  if task.status == "research":
    for st in task.subtasks where st.status == "running" and st.phase == "research":
      async Agent(sub_agent="skein:skein-researcher", tid=task.id, sid=st.sid, workdir=wd)
  elif task.status == "active":
    for st in task.subtasks where st.status == "running":
      async Agent(sub_agent="skein:skein-executor", tid=task.id, sid=st.sid, workdir=wd)
  elif task.status == "check":
    async Agent(sub_agent="skein:skein-checker", tid=task.id, sid=None, workdir=wd)
  elif task.status == "finishing":
    async Agent(sub_agent="skein:skein-finisher", tid=task.id, sid=None, workdir=wd)

for task in Bash("skein list --status pending --json"):   # pending 三分路, 非焦点只完成 plan, 不续 exec
  if task.ready:                     confirm(task)        # 判据已勾满 → 完成 confirm, plan 闭合
    Bash(skein task confirm <task.id> --approved)
  else:
    Plan(task)
```

## 调度原则

- 尽可能的确保使用 Agent 异步化调度，避免阻塞主循环
- 需要和 User 交互的必须在 main 中执行
- 调度需要考虑最终耗时最小化，避免等待过长

## 状态模型

### task 状态

| 落盘值      | 展示名 | 阶段     | 池           | 进入命令                  | 含义                                                          |
| ----------- | ------ | -------- | ------------ | ------------------------- | ------------------------------------------------------------- |
| `pending`   | 待处理 | plan     | 无           | `create` / `plan`         | 已 create，PRD/design/subtask/estimate/grill/人审尚未全收敛。 |
| `research`  | 调研中 | research | work         | `research`                | research subtask 在跑；全 done 后 `plan` 收敛回 `pending`。   |
| `active`    | 进行中 | exec     | 无 task 级池 | `confirm --approved`      | 已 confirm，worktree 已建，subtask 可经 claim 派发。          |
| `check`     | 检查中 | check    | gate         | `claim`（或 `check`）     | 全 subtask done 后进入验证。                                  |
| `finishing` | 收尾中 | finish   | gate         | `claim`（或 `finishing`） | check 全绿后占 gate 槽，等待/运行 finisher。                  |
| `done`      | 已完成 | 完结     | 无           | `finish`                  | finish 成功，worktree 已销，闭环结束；`archive` 移入归档。    |

#### plan

- 先查未完成 task，判新诉求是并入现有 task 还是新建；同目标 / 同模块 / 共享改动面 / 互为前置默认并入，只有目标独立且无共享改动面才新建。
- 判 direct-fix / standard / heavy：direct-fix 仅限单文件单处 ≤20 行且位置已知；跨 ≥2 文件、多步、外部调研、文档交付一律建 task。
- 需要调研时，先登记 `--phase research` subtask，再 `skein task research <id>`；`skein-researcher` 只读调研，结论落 `.skein/task/<id>/research/` 与 `findings.md`，全 done 后 `skein task plan <id>` 收敛回 pending。
- brainstorm / 关键取舍用 `AskUserQuestion`；事实先自查，决策才问用户，禁止把可查事实甩给用户。
- 写齐 planning 工件：PRD 七段无 TODO、design 与测试接缝、subtask DAG/check/estimate、task estimate、contracts。
- 跑 grill 硬门：按弱点表逐项裁决并补回 PRD/design/contracts/subtask；有未裁决弱点不得 confirm。
- `skein task confirm --summary` 只给用户审、不改状态；用户明确批准后才 `skein task confirm --approved`，裸 `skein task confirm` 不作为自动过门手段。
- flow 默认焦点 task 通过 confirm 后直接续 exec；显式 `plan` 完成 confirm 后停，不续 exec。

#### 周期 / 无人值守场景（cron、`/loop`、CI）

- **别每轮从零 planning**：先 `skein list --status all --json` 找上一轮同 intent 的 task（**含已完成的**），用 `skein task create <新tid> --like <上一轮tid>` 克隆 prd/design/subtask 骨架，只改本轮真正不同的部分。不这么做的后果实测过：同一个巡检 intent 堆出 5 个内容雷同的 task。
- **别拿 `--approved` 冒充人审**：无人值守没有用户可问，`--approved` 就是伪造。走 `skein task confirm <tid> --unattended`（需用户预先 `skein config set confirm.unattended true` 授权一次），`confirmed_by` 会记 `unattended` 留痕。
- 参考 [dag.md](dag.md) 设计task/subtask 的编排以确保依赖关系得到满足、任务调度最高效

## finish 过程

- 检测 `.skein/spec/.pending-fix`，存在则异步跑 maintain auto-fix（同样 fire-and-forget）。
- 未 finish 闭环不得宣告 Done。

### subtask 状态

| 落盘值    | 展示名 | 占 `pools.work` | 进入命令                  | 含义                                              |
| --------- | ------ | --------------- | ------------------------- | ------------------------------------------------- |
| `pending` | 待处理 | 否              | `subtask add`             | 已登记，等待 depends_on 全 done 和 claim。        |
| `running` | 运行中 | 是              | `claim` / `subtask start` | 已认领占槽，executor/researcher 正在执行。        |
| `done`    | 已完成 | 否              | `subtask done`            | 执行完成并释放槽；正式验收仍归 check。            |
| `failed`  | 失败   | 否              | `subtask fail`            | 执行失败并释放槽，可 start 重派或补修复 subtask。 |

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
