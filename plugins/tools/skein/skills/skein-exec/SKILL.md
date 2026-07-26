---
name: skein-exec
description: task exec 阶段执行编排 + /skein-exec 闭环入口。作命令: 有入参→建 task 走闭环 (委托 skein-flow); 无入参→驱动 .skein 既有 ready/active task 走完整闭环直到 finish (start→exec→check→finish, 非只 exec)。作 skill: 被 skein-flow exec 委托, main 按 depends_on DAG 为每个 subtask 选 agent 各执行 1 个, 改动落 task 工作目录 (worktree 或原地仓库根)。
user-invocable: true
argument-hint: "[任务ID]"
arguments: "[任务ID]"
model: haiku
effort: low
---

# skein-exec — 任务闭环入口 + 执行编排调度门

## 入口路由 (作 `/skein-exec` 命令时)

- **有入参 `<task-id>`** → 把请求**强制作为 SKEIN task 处理** (不 inline, 即使看似简单), 调用即「建 task 同意」。判新旧: 全新→新建 / 补充现有 active→并入 (裁定不准用 `AskUserQuestion`) → 加载 `skein-flow` 走**完整闭环** (plan→exec→check→finish, flow 承载, 本 skill 不复制)。
- **无入参 (空)** → 不建新 task, **驱动 `.skein` 内既有 task 走完整闭环直到 finish** (不止 exec):
  1. `skein list --status open --json` (**一次取全部未完成 task 的压缩 JSON, 省 token**): 每项 `{id,status,name,desc,deps,worktree,pct,subs:[done,run,pend,fail],ready}` — `status=进行中/检查中` 即在途 active, `status=就绪 && ready=true` 即可启动 (deps 已清, 可 `skein start`); `status=待处理` = 规划中 (未过 `skein confirm` 用户确认门, 尚未就绪, 不可 start)。不再分别跑 `ready`/`current`/直读 task.json。
  2. 无就绪、无在途 active → 报「无待执行 task」结束。
  3. 有 → 逐个加载 `skein-flow` **走完整闭环** (task 级并发受 `max_active` 默认 2 限, ready 即启 / 完成即启 / 冲突或 `depends_on` 未满足则串行等):
     - **就绪 task** → `skein start` (占 active 槽 + 建 worktree, 就绪→进行中) → 进 exec 调度门 (`claim`→派→`done` 循环)
     - **在途 进行中 task** → 直接进 exec 调度门续跑
     - task **全 subtask done → 自动进 check** (`skein check` 进行中→检查中 → `skein-check` 验证; 未过回 planning 修复重跑) → **check 全绿 → finish** (`skein-finish`: merge + 销 worktree + 标记完成, 检查中→已完成)
  4. **每个 task 必须走到 finish (已完成) 才算完成, 不止于 subtask 全 done**; 全部 task 收束到 finish → 报告闭环完成。
- **前置**: 无 `.skein/` → 先 `skein init` 再继续。

> 下方是 exec 阶段**调度门本体** (被 `skein-flow` exec 委托, 或无入参驱动已 planning task 时进入)。**只管执行编排 (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-plan`)。**

## 调度门 (载体分工)

> **工作目录 (worktree 态自适应)** — 本仓 worktree 隔离启用态: !`skein config --json 2>/dev/null | jq -r '.use_worktree' || echo unknown`。二读约定 (下文"task worktree 内"按此判): `true`=各 subtask 在 **task worktree** 内改、主工作区零改动 (worktree 路径取 `list --json` 的 `worktree` 字段); `false`/`unknown`=**原地在仓库根**改、无隔离 (task `worktree=null`)。真值一律以 task 的 `worktree` 字段为准 (null=原地)。

main 作调度器编排, 改动落各 subtask 工作目录 (worktree 或原地仓库根)、每个 agent 完成即回传。角色分工:

- **claim 默认即改态占槽 (整批标 running), 无需额外参数; --dry-run 才只读预览不改态**。**调度** → main 亲跑 (脚本不能 spawn): `skein claim` (**全局跨 task**, 所有 active task ready subtask 合池竞争同一 `max_parallel` 槽) 算就绪批 + 标 running, main 逐个真实 `Agent` 调用 dispatch。批量推进用 `claim`; 单 task 场景用 `skein subtask claim <tid>` 兼容 (仅该 task 内截断); 只想先看就绪批再决定是否执行, 用 `skein claim --dry-run` (只读预览就绪批, 不改态)。
- **执行** → 派合适 agent (无则 `skein-executor`) 各做 1 subtask, 共享该 task 工作目录 (worktree 或原地仓库根), 不调度不递归 (Recursion Guard)。
- **禁 main 亲改源码** — 实质产出一律派 subagent (仅 ≤3 文件微改等特别情况例外, 且必在该 task 工作目录内)。
- **载体 = 单 subagent (禁 team)** — 每 subtask 派**单 subagent** (一次 `Agent` 调用); agent-teams 已被 skein SessionStart 关闭 (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0`), 需多 agent 协同的活一律拆成独立 subtask 各派单 subagent, 不组 team。
- **及早退出** — 每个载体只做本 subtask、产出即回传**立即退出**, 禁滞留空转 / 轮询等待 / 揽额外活。main 侧 `done` 后即 `claim` 放行下游 (完成即派), 全部 done 立即收束进 check, 禁挂着不结。

## 调度循环 (动态, 完成即派)

```
while skein claim 返回非空:       # 全局跨 task: 所有 active task ready subtask 合池竞争 max_parallel 槽
    对认领到的每个 (task, subtask): 为其选合适 agent (无则 skein-executor) 真实 Agent 调用
    等任一 subagent 返回
    → skein subtask done/fail <tid> <sid> → 回到 skein claim (脚本自动重算就绪, 完成即派)
```
- 单 task 场景兼容: `skein subtask claim <tid>` (仅该 task 内截断, 不跨 task 竞争)。
- **🟢 subtask 调度优先, 空闲才提前 plan (禁干等)** — **优先级: 有可调度 subtask → 一律先 `claim` 派 subtask (尽早完成在飞 task), plan-ahead 是次级填充器**。仅当 `skein claim` 返回空 (满槽 `running==max_parallel` 等回传 / 无就绪 subtask) 时才做 plan-ahead: `skein list --status open --json` 找 **`status=待处理` 且无 subtask (`subs` 全 0) = plan 未完成** 的 task, 加载 `skein-plan --continue` 推到 planning-ready, 使 active 槽一释放即可 (过 `skein confirm` 用户确认门→就绪 后) `skein start`, 流水线不断档。**plan-ahead 必须让位 subtask**: 每步 planning 前/后回探 `claim`, 一旦有 subtask 可派 (subagent 回传腾槽 / 新 ready) 立即放下 planning 回去派 subtask。**严格遵守配置: planning 只推到 `skein confirm`/`start` 门前即停** — plan-ahead 至多把 task 备到 planning-complete 待处理态 (confirm 是用户门, 不自动过); `start` 占 active 槽受 `max_active` 限, 满槽禁 start (脚本会拒), 待 slot 释放 + 用户 confirm 后再 start。无「未 plan 的 pending」→ 回原逻辑 (满槽等回传 / 真无就绪且无 pending 判死锁收束)。
- **🔴 exec 无验收 (完成即 done, 验收全归 check)** — subagent 回传即执行完成, main **只 `done`/`fail`, 禁 exec 阶段勾验收** (`subtask check` 勾验收/checkpoint 核对归 `skein-check` 阶段, 见点3)。`done` = 执行动作完成; subtask 的 `--check` 验收项由 skein-check 统一核对。exec 只判「执行有没有跑完/报错」, 不判「验收过没过」。

- **并行只看 depends_on DAG** — ready = 所有前置 done + 有空闲并发槽。无写文件冲突自算 (发挥 AI 自主性: 有序关系靠 planning 写进 `depends_on`, 不靠脚本猜文件重叠)。
- **并发上限 2 / 完成即派** — 任一返回即 `done` 后再 `claim`, 脚本立刻放行新就绪, 不等一批跑完。
- **返回 `需要:` / 阻塞 → 不计 done** — 该 subtask 未完成, 下游保持未 ready; main 转达用户/补信息后重派, 禁标完成、禁放行下游。
- **🔴 tight feedback loop (先复现再修, ask-matt 同源)** — subtask 失败/报错, **禁直接盲改**: 先建**一条就红的复现命令/最小测试** (one command that goes red on this bug) 固定症状, 再读根因修。无复现 = 修了也无法验证, 是猜。自愈重派前 dispatch prompt MUST 含「先复现」指令: subagent 回传必须含复现命令 + 修复后该命令转绿。验收类 subtask 的 `--check` 含此回归。diagnosing-bugs 同源。
- **subtask 失败 → 自愈闭环 (禁失败即停摆)** — subtask 报错/验收不过, main 读根因**自主修**, 二选一 (均在本 task scope 内): ① 定点小缺陷 → 缩范围**原地重派** `skein subtask start <tid> <失败sid>` (≤2 轮); ② 根因是独立可修单元 → **自主 `skein subtask add <tid> <fix-sid> --name "修复<根因>" --desc "定点修根因" --deps <失败sid的前置>` 插修复 subtask** 定点修根因 → 修复 done 后 `skein subtask start <tid> <失败sid>` 重派失败 subtask。兜底: 修复也失败/累计无进展超上限/根因超 scope → 停回传 (走 skein-check root-cause-protocol 或转人工)。禁跳过该 subtask 放行下游。详见 [scheduling-algorithm.md](references/scheduling-algorithm.md)。
- **exec 中发现独立新问题 → 自主拆新 task, 禁扩当前 scope** — 与上条自愈**互斥分流**: 自愈修的是**本 task scope 内**失败的 subtask (完成原范围); 本条是 subagent 回传暴露**超出本 task 边界**的问题 (新缺陷 / 新需求 / 需单独验收的关联改动), main 自主走 `skein-plan` / `skein create` 登记为**新排队 task** (与当前 task 有先后用 `--deps` 连边, 无则并行; active 集 ≤ 2 自动排队), 禁塞进当前 task 扩范围。当前 task 按原 scope 收束。判据: 修复动作是否属原 subtask 目标 —— 属 → 自愈 (加修复 subtask); 不属 → 拆新 task。

## ⚠️ 两条硬规

- **异步等待 MUST 输出任务清单** — 派出异步任务后、结束本回合前, 输出全景表: 4 列 id/状态/摘要/进度% (状态枚举 进行中/等待中/阻塞), 例 `| st1 | 进行中 | 改 auth 中间件 | 60 |`。同步前台阻塞 / 无在跑任务不触发。
- **exec 阶段禁问用户顺序** — 顺序归 planning (task.json 的子任务 DAG + depends_on)。exec 只跑动态调度循环。task.json 缺子任务 DAG (depends_on) → 退回 planning 补, **不在 exec 问**。

## 调度算法 (双层同构 + dispatch prompt)

subtask 级 + 多 task 级两层同构 (同一套 DAG), subtask 状态经 `skein subtask` 脚本落盘, dispatch prompt 6 字段自包含 (含 Recursion Guard + 读后写硬门)。完整命令表 + 调度 DAG 定义 + worktree 规则 + 多 task 并行 + dispatch prompt 模板见 [references/scheduling-algorithm.md](references/scheduling-algorithm.md)。

## 失败模式 (if-then 三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发                          | 一线修复                                   | 仍失败兜底                                       |
| ----------------------------- | ------------------------------------------ | ------------------------------------------------ |
| subtask 报错 (非阻塞)         | 自愈: 定点小缺陷原地重派 ≤2 轮 / 根因独立则 `subtask add --deps` 插修复 subtask 定点修后重派失败 subtask | 修复也失败/累计无进展超上限/超 scope → 停调度回传 main (走 root-cause-protocol), 禁跳过下游 |
| subagent 返回 `需要:`         | main 转达用户 / 补信息后重派该 subtask     | 信息仍缺 → 该 subtask 挂起, 下游保持未 ready, 禁标 done |
| `claim` 返回空 (满槽 / 无就绪)  | 先找 `待处理` 且无 subtask 的 task 提前 plan (推到 confirm/start 门前) 填空闲 | 无未 plan pending → 满槽等回传; 全 pending 有 subtask 但 `claim` 仍空 → 查 depends_on 死锁 (环) → 停手回 skein-plan 改 DAG, 禁空转轮询 |

## ✅ 正向配方 (命中反面=流程错误)

> 🔒 铁律: main 禁亲改源码 — 实质产出一律派 subagent (仅 ≤3 文件微改例外且必在该 task 工作目录内)。

| 场景                       | 正确做法 (❌ 反面)                                                              |
| -------------------------- | ------------------------------------------------------------------------------ |
| 实质产出                   | 派 subagent 在该 task 工作目录内做 (worktree 或原地仓库根) (❌ main 亲改源码; 仅 ≤3 文件微改例外) |
| subagent 回传后            | 只 `subtask done/fail` (❌ exec 阶段 `subtask check` 勾验收 — 验收/checkpoint 归 skein-check) |
| 就绪 subtask 推进          | 完成即派, 任一返回即 `claim` 放行下游 (❌ 一批跑完才派下一批)                    |
| 并发控制                   | 并发上限 2 (❌ 并发超 2)                                                        |
| subtask 标 `需要:`         | 不计 done, 下游保持未 ready (❌ 计 done 放行下游)                               |
| subtask 间顺序             | 归 planning (task.json 子任务 DAG), 缺 DAG 退回 planning 补 (❌ 在 subtask 间停下问用户顺序) |
| 派出异步任务后             | 回合末输出 4 列全景表 (id/状态/摘要/进度%) (❌ 不输出任务清单)                   |
| 需求 / 方案设计            | 归 skein-plan (❌ 用本 skill 做需求方案设计)                                    |
| 需多 agent 协同            | 拆 subtask 各派单 subagent (❌ 组 subagent-team, 已禁用)                        |
| 载体产出后                 | 及早退出 (❌ 滞留空转不退出)                                                    |
| exec 中发现独立新问题      | 自主拆新排队 task (❌ 塞进当前 task 扩 scope)                                   |
| subtask 失败               | 先自愈 (原地重派或加修复 subtask), 兜底才回传 (❌ 停等人工不自愈)               |
