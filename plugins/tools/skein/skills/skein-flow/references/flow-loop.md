# flow-loop — flow 执行过程唯一真值源

本文件收敛 `/skein-flow` 的执行过程：参数路由、状态硬门、plan→exec→check→finish 循环、redo 断点续跑、失败扭转、自愈、停顿与终止。其他 `references/*.md` 只保留职责边界、命令参数、载体规则或工件写法，不重复流程。

## 0. 参数路由

| `$1` | 阶段 | 行为 |
|---|---|---|
| 全空 | flow · 清空模式 | 不新建 task，取 `skein list --status open --json`，按可推进顺序清空全部未完成 task。无 open task 则报「无待执行 task」。 |
| `flow` / 缺省 / 任务描述 | flow 默认闭环 | 有任务描述先走 plan 建/并入 task；之后自动续 exec→check→finish。 |
| `plan` | 仅规划 | 只推到规划完成态，停在 `skein confirm` 前。 |
| `exec` | 续执行 | 驱动待处理/在途 task 继续闭环到 finish。 |
| `check` | 质量门 | 派 `skein-checker` 验证；失败按本文件「失败扭转」。 |
| `finish` | 收尾门 | check 全绿后派 `skein-finisher` 完成 `skein finish` 和异步 sediment。 |
| `redo <tid> [--plan]` | 断点续跑 | 复位孤儿 running subtask，再按当前状态续跑；`--plan` 只对规划中起点有效。 |

硬规：无参/任务描述不是 `plan`。flow 默认一路做完；只有显式 `plan` 才停在 confirm 前。

## 1. 状态模型

### 1.1 task 状态

| 落盘值 | 展示名 | 阶段 | 池 | 含义 |
|---|---|---|---|---|
| `pending` | 待处理 | plan | 无 | 已 create，PRD/design/subtask/estimate/grill/人审尚未全收敛。 |
| `research` | 调研中 | research | work | research subtask 在跑或待收敛回 plan。 |
| `active` | 进行中 | exec | 无 task 级池 | 已 confirm，worktree 已建，subtask 可经 claim exec 派发。 |
| `check` | 检查中 | check | gate | 全 subtask done 后进入验证。 |
| `finishing` | 收尾中 | finish | gate | check 全绿后占 gate 槽，等待/运行 finisher。 |
| `done` | 已完成 | 完结 | 无 | finish 成功，worktree 已销，闭环结束。 |

状态单向前进：`pending`⇄`research` 例外；`active` 后不退回 `pending`。check 失败不是状态回滚，而是在同 task 内追加修复 subtask，回 exec 前进式修补。

### 1.2 subtask 状态

| 落盘值 | 展示名 | 占 `pools.work` | 含义 |
|---|---|---|---|
| `pending` | 待处理 | 否 | 已登记，等待 depends_on 全 done 和 claim。 |
| `running` | 运行中 | 是 | 已 claim/start，占槽，executor 正在执行。 |
| `done` | 已完成 | 否 | executor 完成并释放槽；正式验收仍归 check。 |
| `failed` | 失败 | 否 | executor 失败并释放槽，可 start 重派或补修复 subtask。 |

## 2. 状态先行硬门

| 硬门 | 先跑 | 禁止 |
|---|---|---|
| task 级 | `skein confirm <tid> --approved`，且批准来自真实用户动作 | 未 confirm 就派 exec。 |
| subtask 级 | `skein claim exec` / `skein subtask start <tid> <sid>` | pending/failed 直接派 executor。 |
| check 级 | 派 `skein-checker`，checker 自跑 `skein check <tid>` | main 在 `active` 态直接跑验证并宣告通过。 |
| finish 级 | `skein finishing <tid>` 后派 `skein-finisher` | 未进入 `finishing` 就跑 finish。 |

借口不是状态命令。「简单」「省一步」「马上就做」不构成豁免。

## 3. 主循环骨架

```text
入口：有任务描述则先 plan 建/并入 task；无参则扫描 open task
while 有可推进 task:
  pending/research:
    跑 plan 或续 research
    规划判据全满后，经真实人审门 confirm
    flow 焦点 task confirm 后直接续 exec；显式 plan 停在 confirm 前
  active:
    claim exec
    对每个 claimed subtask 派 skein-executor
    任一 executor 回传后立刻 done/fail，再 claim 补槽
    全 subtask done 后进入 check
  check:
    派 skein-checker
    PASS 则进入 finishing
    FAIL/冲突/needs_main 则走失败扭转，补修复 subtask 回 exec
  finishing:
    确认本 task 后台 agent 已结束
    派 skein-finisher 跑 skein finish
    成功后异步派 skein-specer 做 sediment / pending-fix maintain
  done:
    回循环头取下一个 open task
无可推进：报「无待执行 task」
```

## 4. plan 过程

1. 拆用户诉求，先查未完成 task；相关工作并入现有 task，不相关才新建。
2. 判 direct-fix / standard / heavy；跨文件、多步、外部调研或文档交付必须走 task。
3. 必要时派 `skein-researcher` 只读调研；结论落 `.skein/task/<id>/research/` 和 `findings.md`。
4. 用 `AskUserQuestion` 做 brainstorm / 关键取舍 / grill 后补齐。
5. 写 PRD 六段、design、subtask DAG、estimate、contracts。
6. subtask DAG 先定共享契约，再并行实现；`subtask add` 必须有 sid/name/desc/estimate/check。
7. 跑 grill 硬门；弱点补齐后才可进入 confirm。
8. `skein confirm --summary` 给用户审；用户批准后才 `skein confirm --approved`。
9. flow 默认焦点 task 通过 confirm 后直接续 exec；显式 `plan` 停在 confirm 前。

plan-ahead 只预备非焦点 pending task 到 confirm 门前，不替非焦点 task 过用户门。

## 5. exec 过程

1. 只对 `active` task 跑 `skein claim exec`。
2. claim 返回即已把 ready subtask 标 `running` 并占 `pools.work` 槽。
3. 每个 claimed subtask 派 `Agent(subagent_type="skein:skein-executor")`；exec 派发只给 tid/sid/工作目录，executor 自读 `subtask show`。
4. executor 回传 done/fail 后，main 只负责记录状态；正式验收勾选留给 check。
5. 任一槽释放立刻再次 `claim exec`，不等整批跑完。
6. `claim exec` 为空但仍有 pending 时，查 depends_on、槽位、DAG 环；必要时回 plan 改 DAG。
7. 全 subtask done 后，进入 check。

## 6. check 过程

1. 确认 task 处于 `active`，派 `skein-checker`。
2. checker 自跑 `skein check <tid>` 进入 `check`，再执行 PRD 验收、subtask checklist、契约、场景测试、一致性核查。
3. checker 回传 `PASS` 且无 `needs_main`：跑 `skein finishing <tid>`，进入 finish。
4. checker 回传 `FAIL` / 冲突 / `needs_main`：走「失败扭转」。
5. 修复 subtask 全 done 后重派 checker；未全绿不得 finish。

## 7. finish 过程

1. 只从 `check` 且全绿 task 进入；先跑 `skein finishing <tid>` 占 gate 槽。
2. main 确认本 task 后台 agent 全部结束；仍有悬挂则禁派 finisher。
3. 派 `skein-finisher`；finisher 勘察 diff、处理悬挂、在仓库根跑 `skein finish <tid>`。
4. `verdict=收尾干净`：视为 task 已 `done`，worktree 已销。
5. `verdict=需处理`：按 dangling/tool_failures/needs_main 清理后重派 finisher；清不掉则停手上报。
6. finish 成功后异步派 `skein-specer` 做 sediment/product amend；检测 `.skein/spec/.pending-fix`，存在则异步跑 maintain auto-fix。
7. 未 finish 闭环不得宣告 Done。

## 8. redo 断点续跑

redo 用于 session 意外结束后清 running 死槽。它只改状态，不删除、不撤销上一轮已产出的文件改动。

动手前必须说明：redo 期间禁止有 agent 在跑；全部 running subtask 一律当孤儿，不做心跳/存活探测/时长阈值。

| 起点状态 | redo 行为 |
|---|---|
| `pending` | 无 running 可复位；续 plan 到收敛。带 `--plan` 时停在 confirm 前。 |
| `research` | 复位 running research subtask；续 research 到 done，再 `skein plan` 回 pending。带 `--plan` 时停在 confirm 前。 |
| `active` | 复位全部 running subtask，再回 exec 调度。 |
| `check` | 无 subtask 可复位；直接重派 `skein-checker`。带 `--plan` 时说明已过规划阶段，参数未生效。 |
| `finishing` | 无 subtask 可复位；直接重派 `skein-finisher`。带 `--plan` 时说明已过规划阶段，参数未生效。 |
| `done` | 报已闭环，无事可做。 |

active 起点复位固定拼法：

```bash
skein subtask fail <tid> <sid> --note "redo 孤儿复位: session 意外退出, 全部运行中一律当孤儿"
skein subtask start <tid> <sid>
```

复位后必须回传被复位清单；无 running subtask 时回传「无运行中 subtask 需复位，直接续调度」。

## 9. 失败扭转

### 9.1 exec 自愈

- subtask fail 后先判断是否在本 task scope 内可修。
- 局部实现 bug：`skein subtask start <tid> <sid>` 定点重派，最多 2 轮。
- 独立根因：追加修复 subtask，`--desc`/`--check` 必含「先复现」；修复 done 后重派原失败 subtask。
- 修复 subtask 也失败、同一 subtask 超 2 轮、或根因超 scope：停手走根因复盘。

### 9.2 check 失败扭转

- check 失败不得直接改状态或 finish。
- 孤立失败：回 planning 思维确认修复方向，补 1 个定点修复 subtask，回 exec。
- 一致性冲突/方案性缺陷：先 root-cause 复盘，再 grill/`AskUserQuestion` 确认方向，补修复 subtask。
- ≥2 轮仍 FAIL：停止盲修，按 5 维根因定位。

### 9.3 根因复盘

按 5 维由外到内定位：需求理解偏差、方案设计缺陷、实现 bug、环境/依赖、测试本身错误。每维给证据；多维命中取最外层。实现/环境/测试问题回 exec 定向修；需求/设计问题停手交用户裁定是否重回 planning 或新建 task。

### 9.4 回退协议

SKEIN 的「回退」是流程扭转，不是状态倒退：task 保持 `active`，通过追加修复 subtask 前进式修补。契约只在 planning 阶段可改；exec/check 发现契约错误，必须经用户裁定后重回 planning 或新建 task。

## 10. 停顿白名单

只有以下情况可以结束本回合等用户：

- plan brainstorm / grill / 人审门需要用户选择。
- check FAIL 后修复方向必须用户裁定。
- subagent 回传 `需要: <问题>`。
- 破坏性或不可逆操作需要显式授权。
- 需求未定、scope 过大、自愈超上限、DAG 死锁、根因超 scope。

用户答完后从停顿点继续，不要求用户重喊命令。

## 11. 禁停顿

- plan 判据全满后问「要不要执行」；flow 焦点 task 直接 confirm 后续 exec。
- 全 subtask done 后问「要不要 check」；直接派 checker。
- check 全绿后问「要不要 finish」；直接 finishing + finisher。
- 一个 task finish 后收工；回循环头继续 open task。
- 派出异步 agent 后就地结束；等回传接着推，并输出在跑清单。
- 借口简单而 inline 跳过 flow。

## 12. 终止条件

- 无就绪、无在途、无待处理可推进 task：报「无待执行 task」。
- 命中停顿白名单：输出问题和当前进度，等待回答。
- 自愈超上限、根因超 scope、DAG 死锁、finish 悬挂清不掉：停手回传。