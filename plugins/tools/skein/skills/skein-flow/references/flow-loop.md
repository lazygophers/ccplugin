# flow 模式

| `$1`                     | 阶段            | 行为                                                                                                                     |
| ------------------------ | --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 全空                     | flow · 清空模式 | 不新建 task，取 `skein list --status open --json`，按可推进顺序清空全部未完成 task。无 open task 则报「无待执行 task」。 |
| `flow` / 缺省 / 任务描述 | flow 默认闭环   | 有任务描述先走 plan 建/并入 task；之后自动续 exec→check→finish。                                                         |
| `plan`                   | 仅规划          | 只推到规划完成态，停在 `skein confirm` 前。                                                                              |
| `exec`                   | 续执行          | 驱动待处理/在途 task 继续闭环到 finish。                                                                                 |
| `check`                  | 质量门          | 派 `skein-checker` 验证；失败按本文件「失败扭转」。                                                                      |
| `finish`                 | 收尾门          | check 全绿后派 `skein-finisher` 完成 `skein finish` 和异步 sediment。                                                    |

硬规：无参/任务描述 -> flow 闭环闭环模式；只有显式 `plan` 才停在 confirm 前。

## 作用域边界

skein-flow 的作用域判定 (何时建 task / 归一 vs 分立 / worktree 豁免) 与完成判定 —— 本文件是这三项的单一真值源。

### 归一 vs 分立 (相关工作优先归一 task 拆 subtask)

建 task 前先判新交付物是**某任务的一部分**还是**独立任务** —— 与现有 active task 或本请求内其他交付物**相关** (同目标 / 同模块 / 共享改动面 / 互为前置) → **归一到该 task 拆 subtask** (`subtask add` + `--deps`), 禁为相关工作另开多个 task; 仅**目标独立、无共享改动面、无依赖**才拆多 task。判据是相关性, 非「可独立验收」(subtask 亦可独立验收)。默认倾向归一 (散多 task 丢共享上下文一致性)。判不准 → AI 自行裁定 (默认归一), 仅极不确定才 `AskUserQuestion`。

### worktree 豁免 (简单改不必上升到 worktree)

**🔒 本节是「何时建 task」文件数阈值的单一真值源** — 与之表述不一致的其他措辞 (如「≤3 文件微改例外」) 均以此处口径为准, 禁另立标准。

**唯一豁免口径: 单文件单处改 ≤20 行且位置已知** — 命中才无需建 task/worktree, 原地做即可; 用户显式 `--skip` 强制 inline 覆盖自动判定。**跨 ≥2 文件一律必建 task**, 无论文件数多寡、改动是否「集中」—— 不设「≤3 文件且集中」这类例外 (「集中」判断主观, 易被 AI 自降级借口绕过 flow)。多子 git 场景同理: 真跨多仓的结构性改动才 `--repos` 声明走多 worktree; 但若某仓只沾一两行的顺带微调仍属「跨 ≥2 文件」范畴, 同样必建 task, 不因「顺带」豁免。

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

worktree：由 config `worktree.enabled` 决定（默认 false）。启用时 confirm 建 task worktree（多子 git 落各仓 `<repo>/.worktrees/skein-<id>`），finish 合并后销毁；禁用则全程原地在仓库根做。派 agent 时把工作目录直接写进 dispatch，agent 不自己探测。

状态单向前进：`pending`⇄`research` 例外；`active` 后不退回 `pending`。check 失败不是状态回滚，而是在同 task 内追加修复 subtask，回 exec 前进式修补。

### subtask 状态

| 落盘值    | 展示名 | 占 `pools.work` | 进入命令                  | 含义                                              |
| --------- | ------ | --------------- | ------------------------- | ------------------------------------------------- |
| `pending` | 待处理 | 否              | `subtask add`             | 已登记，等待 depends_on 全 done 和 claim。        |
| `running` | 运行中 | 是              | `claim` / `subtask start` | 已认领占槽，executor/researcher 正在执行。        |
| `done`    | 已完成 | 否              | `subtask done`            | 执行完成并释放槽；正式验收仍归 check。            |
| `failed`  | 失败   | 否              | `subtask fail`            | 执行失败并释放槽，可 start 重派或补修复 subtask。 |

验收勾选用 `subtask check <tid> <sid>`（不改状态）。池：`pools.work` 只数 running subtask，`pools.gate` 数 `check`/`finishing` task。参数与更多子命令查 `skein --help` / `skein subtask --help`，不在文档里重抄。

## 状态先行硬门

| 硬门       | 先跑                                                     | 禁止                                        |
| ---------- | -------------------------------------------------------- | ------------------------------------------- |
| task 级    | `skein confirm <tid> --approved`，且批准来自真实用户动作 | 未 confirm 就派 exec。                      |
| subtask 级 | `skein claim` / `skein subtask start <tid> <sid>`        | pending/failed 直接派 executor/researcher。 |
| check 级   | `skein claim` 收进 `check` 后派 `skein-checker`          | main 在 `active` 态直接跑验证并宣告通过。   |
| finish 级  | `skein claim` 收进 `finishing` 后派 `skein-finisher`     | 未进入 `finishing` 就跑 finish。            |

状态先行是铁律：动手前必须先让对应 `skein` 状态命令成功落盘，能过脚本状态门才算合法。借口不是状态命令，「简单」「省一步」「马上就做」不构成豁免。

## 主循环骨架

```text
Bash("skein claim")                                   # 一次 claim, 两路认领: ready subtask 标 running;
                                                      # 全 done 的 active→check, 全 done 的 check→finishing
for task in Bash("skein list --status open --json"):  # 认领后按 task 状态分派
  wd = task.worktree or repo_root
  if task.status == "research":
    for st in task.subtasks where st.status == "running" and st.phase == "research":
      async Agent("skein:skein-researcher", {"tid": task.id, "sid": st.sid, "workdir": wd})
  elif task.status == "active":
    for st in task.subtasks where st.status == "running":
      async Agent("skein:skein-executor",   {"tid": task.id, "sid": st.sid, "workdir": wd})
  elif task.status == "check":
    async Agent("skein:skein-checker",      {"tid": task.id, "sid": None, "workdir": wd})
  elif task.status == "finishing":
    async Agent("skein:skein-finisher",     {"tid": task.id, "sid": None, "workdir": wd})
    async Agent("skein:skein-specer",       {"tid": task.id, "sid": None, "workdir": wd, "mode": "sediment"})

for task in Bash("skein list --status pending --json"):   # pending 三分路, 无一路问用户
  if task.ready:                     confirm(task)        # 判据已勾满 → 直接 confirm 进 active
  elif 缺 plan 产物(prd 未填/无 subtask): 补 plan 收敛(填 prd + 加 subtask + estimate) → confirm
  else:                              pass                 # 前置未清 (depends_on 未 done), 暂缓
```

骨架是 flow 每一轮的唯一驱动，硬规：

- 每轮先跑一次 `skein claim`（不带 phase）——它只做**状态推进**：ready subtask 标 `running`，全 done 的 `active` task 进 `check`，全 done 的 `check` task 进 `finishing`。**claim 不告诉你派谁**。
- 派哪个 agent 由 main 按 **task 状态**判定，映射固定：`research` → `skein-researcher`；`active` → `skein-executor`；`check` → `skein-checker`；`finishing` → `skein-finisher` + `skein-specer`。exec 路遍历该 task 下 claim 刚标成 `running` 的 subtask，一个 subtask 派一个 agent。
- 入参就是各 agent 文件「入参格式 (JSON)」那一行：`tid` / `sid` / `workdir` 三个公共字段（task 级 agent 的 `sid` 传 `null`），其余按 agent 各自扩展（researcher 加 `query`+`mode`，specer 加 `mode`，recaller 加 `query`+`src`，clean 加 `retain_days`）。`workdir` 见 task 状态中的 worktree 说明（worktree 启用则 task worktree，否则仓库根）。
- 全部 agent 一律 async 派出即结束回合，不等回传串行卡住。
- claim 与派发结束后再扫 `skein list --status pending` 调度 plan，不与上面的派发抢顺序。

### 派发载体

`subagent_type` 必须带插件前缀：`skein:skein-executor` / `skein-checker` / `skein-finisher` / `skein-researcher` / `skein-specer`。裸名无效。

- 「派 agent」= 真实 `Agent` tool_use。无 tool_use 禁说已派。禁 teammate / agent-team / `SendMessage` 派 teammate / `team_name`。
- main 默认禁写源码：改源码派 executor，验证派 checker，收尾派 finisher。`skein` CLI 由 main 同步跑（create/confirm/subtask/finish/archive 是记录管理，不派 agent）。
- **claim 路径派的四个 agent（executor / researcher / checker / finisher，加同轮 specer）只给上面那行 JSON**，不写六字段 prompt —— 详情各自从 `skein subtask show` / `skein prd read` / git diff 读，转述一律以落盘为准。
- 非 claim 路径派的 agent（recaller、手动调研的 researcher、dedup、clean、setup）dispatch prompt 六字段自包含：目标 / 已知（含 `Active task: <id>` 与工作目录）/ 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。
- 用户交互决策归 main 用 `AskUserQuestion`；subagent 缺信息回传 `需要: <问题>`，main 转达。
- subagent 完成或阻塞，main 立即回传摘要，禁批量延迟汇总。
- 看板由脚本自动刷，禁直接编辑 task.md / task.html。
- 文案/格式类变更先给样例确认；逻辑/bug 修复不受此限。
- 并发多个 flow 请求不得互相覆盖：先登记 durable task，再串行处理需要用户交互的 planning。

## plan 过程

- 拆用户诉求，先查未完成 task；相关工作并入现有 task，不相关才新建。
- 判 direct-fix / standard / heavy；跨文件、多步、外部调研或文档交付必须走 task。
- 必要时派 `skein-researcher` 只读调研；结论落 `.skein/task/<id>/research/` 和 `findings.md`。
- 用 `AskUserQuestion` 做 brainstorm / 关键取舍 / grill 后补齐。
- 写 PRD 七段、design、subtask DAG、estimate、contracts。
- subtask DAG 先定共享契约，再并行实现；`subtask add` 必须有 sid/name/desc/estimate/check。
- 跑 grill 硬门；弱点补齐后才可进入 confirm。
- `skein confirm --summary` 给用户审；用户批准后才 `skein confirm --approved`。
- flow 默认焦点 task 通过 confirm 后直接续 exec；显式 `plan` 停在 confirm 前。

plan-ahead 只预备非焦点 pending task 到 confirm 门前，不替非焦点 task 过用户门。

## exec 过程

- 认领走主循环的 `skein claim`（只想单跑 exec 一路时用 `skein claim exec`）。
- claim 返回即已把 ready subtask 标 `running` 并占 `pools.work` 槽。
- 每个 claimed subtask 按 task 状态派：`research` 态派 `skein:skein-researcher`，`active` 态派 `skein:skein-executor`；入参只给 `tid`/`sid`/`workdir`，agent 自读 `subtask show`。
- executor/researcher 回传 done/fail 后，main 只负责记录状态；正式验收勾选留给 check。
- 任一槽释放立刻回循环头再 claim，不等整批跑完。
- claim 为空但仍有 pending 时，查 depends_on、槽位、DAG 环；必要时回 plan 改 DAG。
- 全 subtask done 后，进入 check。

ready 判定、排序权重、双池与 claim 命令族见 [dag.md](dag.md)。

## check 过程

- `skein claim` 把全 subtask done 的 `active` task 推进 `check`；main 见 `check` 态即派 `skein:skein-checker`。
- checker 自跑 `skein check <tid>`（已在 `check` 则幂等），再执行 PRD 验收、subtask checklist、契约、场景测试、一致性核查。
- checker 回传 `PASS` 且无 `needs_main`：跑 `skein finishing <tid>`，进入 finish。
- checker 回传 `FAIL` / 冲突 / `needs_main`：走「失败扭转」。
- 修复 subtask 全 done 后重派 checker；未全绿不得 finish。

## finish 过程

- 只从 `check` 且全绿 task 进入；`skein claim` 已把它收进 `finishing` 占好 gate 槽（单独推时用 `skein finishing <tid>`）。
- main 确认本 task 后台 agent 全部结束；仍有悬挂则禁派 finisher。
- 派 `skein-finisher`；finisher 勘察 diff、处理悬挂、在仓库根跑 `skein finish <tid>`。同轮异步并发派 `skein-specer` 做 sediment / product amend，两者互不等待。
- `verdict=收尾干净`：视为 task 已 `done`，worktree 已销。
- `verdict=需处理`：按 dangling/tool_failures/needs_main 清理后重派 finisher；清不掉则停手上报。
- 检测 `.skein/spec/.pending-fix`，存在则异步跑 maintain auto-fix（同样 fire-and-forget）。
- 未 finish 闭环不得宣告 Done。

### sediment + amend 判定门

finish 后由 `skein-specer` 异步跑的两个动作，完全复用 `skein-spec` skill，**禁新造沉淀机制**。语法细节不在这里重复，见 [skein-spec SKILL.md](../../skein-spec/SKILL.md) 与 [sediment-workflow.md](../../skein-spec/references/sediment-workflow.md) 的 amend vs sediment 抉择树。

#### fire-and-forget

main 派完 skein-specer **不等回传即结束回合**，finish 已闭环。禁为等回传延后 `skein finish`。回传到达后 main 只补 output trace，判定结果不影响 finish 的闭环性。

#### 动作一：sediment（规则/决策沉淀）

skein-specer 读 diff + 各 subagent 回传摘要（含 `SPEC:` 标记），跑 `skein-spec sediment` 判定门后**自主写盘 + reindex，不逐次问用户**。

无可沉淀增量（一次性 bug / 私有细节 / 已有规则覆盖）→ 自判 drop 跳过，**禁硬凑**。

plan 阶段沉淀的决策（grill/design 推出但本轮 check 未验证）落 `--status proposed`，供 `skein-spec analyze` 的置信度检查识别；常规已验证决策走默认 `active`。

#### 动作二：amend（product wiki 回写候选）

跑 `skein-spec finish-candidates <tid>`，三路降级：

- diff 改动文件反查 anchors 命中既有 product 页 → 该页即候选 → `amend` 改写。
- 无命中 → `skein-spec recall --src product` 以 prd 关键词找弱候选。
- 仍无 → 报「无候选，可能是新功能域，建议新建」，**禁摊派到不相关的既有页**，可按需 `sediment --namespace product` 新建。

## 失败扭转

### exec 自愈

- subtask fail 后先判断是否在本 task scope 内可修。
- 局部实现 bug：`skein subtask start <tid> <sid>` 定点重派，最多 2 轮。
- 独立根因：追加修复 subtask，`--desc`/`--check` 必含「先复现」；修复 done 后重派原失败 subtask。
- 修复 subtask 也失败、同一 subtask 超 2 轮、或根因超 scope：停手走根因复盘。

### check 失败扭转

- check 失败不得直接改状态或 finish。
- 孤立失败：回 planning 思维确认修复方向，补 1 个定点修复 subtask，回 exec。
- 一致性冲突/方案性缺陷：先 root-cause 复盘，再 grill/`AskUserQuestion` 确认方向，补修复 subtask。
- ≥2 轮仍 FAIL：停止盲修，按 5 维根因定位。

### 根因复盘

按 5 维由外到内定位：需求理解偏差、方案设计缺陷、实现 bug、环境/依赖、测试本身错误。每维给证据；多维命中取最外层。实现/环境/测试问题回 exec 定向修；需求/设计问题停手交用户裁定是否重回 planning 或新建 task。

报告模板：

```md
## 根因复盘

- 失败摘要：<最短可复现症状>
- 已尝试修复：<轮次 + 结果>
- 维度证据：
  - 需求理解偏差：<证据或排除理由>
  - 方案设计缺陷：<证据或排除理由>
  - 实现 bug：<证据或排除理由>
  - 环境或依赖：<证据或排除理由>
  - 测试本身错误：<证据或排除理由>
- root cause：<维度 + 一句话根因>
- 本次修：<定向修复建议>
- 同类防：<可复用契约；无则写无>
- 建议出口：<回 exec / 用户裁定回 planning / 新建 task>
```

每维都要给证据或排除理由，不能只查实现层。教训能写成可验证契约就走 `skein-spec sediment`，一次性问题跳过，不写流水账。

### 回退协议

SKEIN 的「回退」是流程扭转，不是状态倒退：task 保持 `active`，通过追加修复 subtask 前进式修补。

- 原失败 subtask 历史保留，不删除毁迹。
- 能小修不大修，能定点修不重拆 task。
- 契约只在 planning 阶段可改；exec/check 发现契约错误，必须经用户裁定后重回 planning 或新建 task。
- 孤立失败（实现 bug / 环境 / 测试错）走 exec 自愈和 check 失败扭转就地修；一致性冲突加根因复盘；方案性缺陷与需求理解偏差一律停手交用户裁定，不自行改 PRD 或 design 后继续跑。

## 停顿白名单

只有以下情况可以结束本回合等用户：

- plan brainstorm / grill / 人审门需要用户选择。
- check FAIL 后修复方向必须用户裁定。
- subagent 回传 `需要: <问题>`。
- 破坏性或不可逆操作需要显式授权。
- 需求未定、scope 过大、自愈超上限、DAG 死锁、根因超 scope。

用户答完后从停顿点继续，不要求用户重喊命令。

## 禁停顿

- plan 判据全满后问「要不要执行」；flow 焦点 task 直接 confirm 后续 exec。
- 全 subtask done 后问「要不要 check」；直接派 checker。
- check 全绿后问「要不要 finish」；直接 finishing + finisher。
- 一个 task finish 后收工；回循环头继续 open task。
- 派出异步 agent 后就地结束；等回传接着推，并输出在跑清单。
- 借口简单而 inline 跳过 flow。

## 终止条件

- 无就绪、无在途、无待处理可推进 task：报「无待执行 task」。
- 命中停顿白名单：输出问题和当前进度，等待回答。
- 自愈超上限、根因超 scope、DAG 死锁、finish 悬挂清不掉：停手回传。

### 完成判定

- 走完 plan→exec→check→finish — **未 finish 闭环(标记完成) = 未完成, 禁宣告 Done**。
- finish 阶段前 main 需确认本 task 派出的后台 agent 均已结束, 未关 = 未闭环。
- sediment: 有可复用 learning 才沉淀, 无则跳过 (判定见 `skein-spec`)。
