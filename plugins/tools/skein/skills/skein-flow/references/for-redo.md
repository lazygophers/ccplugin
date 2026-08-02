# for-redo — redo 阶段作业手册 (断点续跑门)

session 意外结束 (窗口关闭/上下文爆/进程被杀) 后, 被派出去的 subagent 一起消失, 但它们占的槽还记在
盘上: subtask 停在「运行中」, 永不自己完成/失败, 调度器认为满槽, 整个 task 卡死。`redo` 是这个场景
的一键出口: 认领残局、复位死槽、接着往下跑到闭环。**`redo` 落在编排层, 不新增引擎命令** —— 复位动作
全部用现有 `skein subtask` 命令拼, 拼法本文件锁死, 禁自由发挥。

## 触发

`$1=redo <tid> [--plan]` (与 plan/exec/check/finish 并列的第五个首参路由)。`redo` 必须带 `tid` ——
复位是 task 级操作, 不接受全空清空模式。

**不传 tid**: 禁裸报错。扫描全部 task, 筛出「进行中态 (active) 且存在 `status=运行中` subtask」的
task 列成候选清单 (即卡死嫌疑名单), 交使用者从中选一个补 `tid` 重跑; 候选为空 → 明确回「当前无卡死
迹象的 task, 无需 redo」, 不做任何复位动作。

## `--plan` 子参数: 分界点在「进 exec 前」

复位孤儿的动作永远照做 (解卡是刚需, 不因 `--plan` 而跳过)。`--plan` 只影响复位之后的续跑深度:

- **起点归类为规划中** (`待处理`/`调研中`, 见下表): 续规划到收敛即停, **不自动 `claim exec`/`confirm`**。
  这是唯一有意义的拦截点 —— design.md §1 的"只想把规划补收敛, 不想它自动开工", 开工 = confirm 进 exec。
- **起点归类为执行中/验证中/收尾中/已完成**: 规划早在更早阶段收敛过, `--plan` 已经没有可拦的位置,
  行为与不带 `--plan` 时一致 (该复位复位, 该重派重派)。但必须显式告知使用者一句
  「该 task 已过规划阶段, `--plan` 未生效, 按正常 redo 续跑」—— 不能默不作声地照常执行, 让人误以为
  被拦下了却其实没有。

## 🛑 孤儿判定口径 (动手前必须向使用者声明)

**全部「运行中」subtask 一律当孤儿, 不做存活探测/心跳/时长阈值** (2026-08-01 用户裁定)。

- 误判一个其实还活着的 → 代价 = 重跑一个 subtask, 可接受
- 放过一个死槽 → 代价 = 槽永不释放, task 继续卡死, 不可接受
- 两者代价不对称, 故不做"更安全"的候选清单/阈值方案 —— redo 是使用者显式发起的, 他敲这个词的时候
  就知道现场没有 agent 在跑

**代价 (必须讲明, 不能藏)**: **redo 期间禁止有 agent 在跑**。若使用者在有活 agent 时 redo, 会把活的
一起复位, 造成两个 agent 干同一件事、互相覆盖改动。编排层看不见 agent 存活, 这一点无法用代码防, 只能
在动手前把口径亮给使用者, 让他有机会喊停。

## 🛑 复位边界 (动手前必须向使用者声明): redo 不回滚已产出的改动

`redo` 的复位动作只改 subtask **状态** —— 运行中→失败→运行中, 让孤儿槽重新可调度。它**不删除、不撤销**
上一轮 subagent 已经写出的任何文件改动: 已产出的代码/配置留着, 那是上一轮的劳动成果, 且 subtask 重跑
本来就要求幂等 (design.md §6)。

换句话说: **redo 解的是"状态卡死", 不是"回滚重来"**。若使用者的真实意图是丢弃某个 subtask 已产出的
改动、推倒重做, `redo` 不提供这个能力 —— 需要另想办法 (如手工 `git revert`/回退对应文件), 不能靠
`redo` 顺带做到。

## 起点分流: 按 task 当前所处阶段决定续什么

不预设 task 卡在哪一步, 先 `skein status <tid>` 读当前 `status`, 按下表分流:

| task 当前 `status` | 归类 | redo 做什么 |
|---|---|---|
| 待处理 (pending) | 规划中 | 无运行中 subtask 可复位 (未 confirm 无 worktree, 不可能有). 按 [for-plan.md](for-plan.md) 续规划 (brainstorm/PRD/design/工时) 到收敛, 走人审门 `confirm --approved` (吸收原 start 全部职责, 一步直进进行中) |
| 调研中 (research) | 规划中 (调研态) | research subtask 与 exec 同样占 `pools.work` 槽, 可能有孤儿 —— **走下方「复位步骤」**复位后, 按 [for-plan.md](for-plan.md) 续跑调研 subtask 到全 done, `skein plan` 收敛回待处理 |
| 进行中 (active) | 执行中 | **走下方「复位步骤」**, 复位孤儿后按 [for-exec.md](for-exec.md) 正常调度循环续跑到全 subtask done → check |
| 检查中 (check) | 验证中 | check 不设 subtask (task 级一次性动作, 无运行中 subtask 可复位), 直接重派 [for-check.md](for-check.md) `Agent(subagent_type="skein:skein-checker")` |
| 收尾中 (finishing) | 收尾中 | finish 同样不设 subtask, 无运行中 subtask 可复位, 直接重派 [for-finish.md](for-finish.md) `Agent(subagent_type="skein:skein-finisher")` |
| 已完成 (done) | 已闭环 | 报「已闭环, 无事可做」, 不做任何操作, 不重跑 |

`检查中`/`收尾中` 现为状态机里两个独立落盘态 (`skein status <tid>` 直接读得到), 不再需要旧版靠
验收标准 `- [x]` 覆盖率二次判定 "验证中 vs 收尾中" —— 那套判定逻辑随 `finishing` 转换 (design.md §1)
落地已废弃。

## 复位步骤 (执行中态专用, 命令固定, 禁改拼法)

1. **枚举孤儿**: `skein subtask list <tid>` → 筛 `status` 列为 `运行中` 的全部 sid
2. 若第 1 步无任何 `运行中` 项 (边界: task 进行中但当前无占槽 subtask) → 跳过第 3/4 步, 直接进
   [for-exec.md](for-exec.md) 调度循环 (`claim exec`)
3. **逐个复位** (对每个孤儿 sid, 顺序执行):
   ```
   skein subtask fail <tid> <sid> --note "redo 孤儿复位: session 意外退出, 全部运行中一律当孤儿"
   skein subtask start <tid> <sid>
   ```
   引擎状态机无 `运行中→待处理` 直接迁移 (见 [subtask-state-machine.md](subtask-state-machine.md)), 只有
   `运行中→失败→运行中` (失败可重启, `started` 时间戳不覆盖). 这就是"待复位为待处理"在现有命令下唯一
   拼得出的等价路径 —— **本步骤固定, 不得改拼法, 否则每次 redo 拼得不一样**。
   `subtask start` 前置校验含"全局 running 数 < `pools.work`": 孤儿数通常 ≤ 崩溃前的 `pools.work`
   占槽数, 逐个 start 一般不会撞槽; 若撞槽 (罕见), 未 start 成功的项留 `失败` 态, 交给第 4 步的
   `claim exec`/后续 done 释槽后自然被后续调度循环拾起 (仍可 `subtask start`, 源状态含"失败").
4. **回到正常调度循环**: `skein claim exec` 补齐 pending 池待认领项, 之后按 [for-exec.md](for-exec.md)
   常规流程 (main 逐个派 `Agent(subagent_type="skein:skein-executor")`, 完成即 `done`/`fail`, 完成即派补槽)
   续跑到全 subtask done → `skein check` → check 阶段。

## 复位后必报: 被复位清单 (动手后必须回传使用者)

不做交互式确认 (§孤儿判定口径已定过), 但复位后的这份清单是硬性输出, 不能省 —— 是使用者核对有没有
误伤的唯一依据:

```
redo <tid> 已复位以下 subtask (运行中 → 失败 → 运行中, 重新可调度):
- r1: 原运行中, 判定孤儿, 已复位
- r2: 原运行中, 判定孤儿, 已复位
无需复位: r3 (已完成), r4 (待处理)
```

若「复位步骤」第 2 步 (枚举孤儿) 结果为空 → 清单退化为一行:
`redo <tid>: 无运行中 subtask 需复位, 直接续调度。`

非执行中起点 (待处理/检查中/收尾中/已完成) 没有「复位步骤」可跑, 无需输出上述清单, 但仍需回报走的是
起点分流表里的哪一分支 (例如「检查中, 无运行中 subtask 可复位, 直接重派 skein-checker」)。

## 完成判据

- [ ] 已按 task 当前 `status` 落在上表正确分支, 未跳阶段/未退回执行
- [ ] 若走执行中分支: 全部孤儿 sid 已过「复位步骤」(fail→start), 且已 `claim exec` 补位一次
- [ ] 使用者已被告知孤儿判定口径与「redo 期间禁有 agent 在跑」的代价 (动手前)
- [ ] 使用者已收到被复位的 subtask 清单 (动手后), 或非执行中起点的分支说明
- [ ] 若带 `--plan`: 起点为规划中则续规划到收敛即停; 起点为其他阶段则告知「--plan 未生效」后按正常
      redo 续跑
- [ ] 不传 `tid`: 已给出候选清单或「无需 redo」明确结论, 未裸报错
- [ ] task 续跑进入对应阶段后, 移交该阶段自身作业手册, 本文件不重复该阶段流程

## 延伸引用

- [for-plan.md](for-plan.md) / [for-exec.md](for-exec.md) / [for-check.md](for-check.md) / [for-finish.md](for-finish.md) — 复位/分流后移交的各阶段作业手册, 本文件只管"从哪续", 不重复"续什么"的细节
- [subtask-state-machine.md](subtask-state-machine.md) — 复位步骤依据的状态流转单一真值源 (无 `运行中→待处理`, 只有 `运行中→失败→运行中`)
- [task-state-machine.md](task-state-machine.md) — 起点分流依据的 task 5 态单一真值源
- [carrier-rules.md](carrier-rules.md#派发调用形式-照抄-禁自由发挥) — 重派 checker/finisher 时的 `Agent` 调用形式
