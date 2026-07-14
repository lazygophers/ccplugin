# 名词说明

SKEIN 全部术语一处查清。按主题分组, 每条一句话说清「是什么」+「谁管它」。

## 任务模型

| 名词 | 是什么 |
| --- | --- |
| **task** | 一条闭环任务记录, 存 `.skein/task/<id>/`, 由 `skein.py` 管理。id 为**可读描述性 slug** (kebab-case, 如 `order-create-api`), 人工传入, 兼作分支名 + 目录名; 禁 `t01` 这类字母+数字代号 (脚本硬拒), 含归档不可复用。 |
| **subtask** | 单个 task 内的执行单元, 存 per-task task.json 的 `subtasks[]`, id 形如 `s1`。每个关联一个 `agent` (省略默认 `skein-executor`) + 0-n 个 `skills`, main 据此 dispatch 执行。 |
| **闭环** | `plan → exec → check → finish` 四阶段, 不可跳步。**未 archive = 未完成**。 |
| **active 集** | 同 session 内所有 `进行中` 的 task。上限 `max_active` (默认 2)。无 task 级 focus — 无未完成前置的 task 皆可并行, 命令 (finish 等) 必带 id。 |
| **状态流转** | task: `待处理 → 进行中 → 已完成` (已完成移入 archive/)；`检查中` 为 check 阶段中间态。subtask: `待处理 → 运行中 → 已完成/失败`。状态中文落盘。 |

## 调度

| 名词 | 是什么 |
| --- | --- |
| **DAG** | 有向无环图, 描述工作单元的执行顺序。SKEIN 双层同构 (task 级 + subtask 级)。 |
| **depends_on / deps** | 显式前置边: subtask `--deps` / task `--deps`。被依赖者未完成前, 依赖者不 ready。**并行只看这张显式依赖 DAG** — 无写文件冲突自算 (真正有序的关系靠 planning 写进 `depends_on`, 不靠脚本猜写文件重叠)。 |
| **ready (就绪)** | 待处理 + 依赖 (`depends_on`) 全已完成 + 有空闲槽。`subtask ready` 只读预览。 |
| **claim (认领)** | `subtask claim` 一次性算就绪批 + 整批标 running, 返回给 main 逐个派 agent。脚本一步到位, 免 main 逐个 start。 |
| **完成即派** | 任一 agent 返回即 `done` 后再 `claim`, 脚本立刻放行新就绪, 不空等一批跑完。 |
| **并发上限** | `max_parallel` (默认 2) — 同时在跑的 subagent ≤ 此值。`claim` 内按剩余槽截断。 |
| **完成百分比** | subtask 完成度 = 已过验收/总验收 (`subtask check --passed` 勾选驱动, 存 `验收done[]`); `done` 强制 100%。看板逐 subtask 渲染进度条, task 综合完成率 = 各 subtask 均值。 |

## worktree

| 名词 | 是什么 |
| --- | --- |
| **worktree 隔离** | 每 task 一个 git worktree (存 `.worktrees/`), 所有改动落此, 主工作区零改动。**多子 git** (`create --repos`): worktree 落**各子仓内部** `<repo>/.worktrees/`, 非根仓根; 子仓各自补 `.gitignore` 忽略。**git 非强制**: cwd 非 git 仓库时 (如微服务/前后端分离, 子目录各自独立仓) 降级为原地执行 —— 无 worktree、无分支、finish 不合并, 其余生命周期 (create/start/finish/archive/看板/依赖门) 照常。 |
| **1 task 1 worktree** | 默认拓扑: 一 task 一 worktree, 其内 subtask 共享 (subtask 不绑定 worktree)。多 worktree 允许但 opt-in。 |
| **finish 合并** | finish 时 commit → merge 回主 → 销 worktree → archive。冲突自动 abort。 |
| **archive (归档)** | 丢弃 task: 销 worktree/分支, **不 merge**, 移入 `task/archive/<年>/<月-日>/<id>/`。 |

## 规则记忆 (差异化核心)

| 名词 | 是什么 |
| --- | --- |
| **spec** | 规则记忆库, 存 `.skein/spec/`。对标 trellis 的单文件 spec, 但 SKEIN 分两层×类目。 |
| **core (核心层)** | 常驻注入的硬规, 每 session 由 SessionStart hook 注入。有字符预算, 超了降级到 recall。 |
| **recall (召回层)** | 按需语义召回的规则, `memory.py recall <query>` 粗筛命中行, model 再读全文定用否。 |
| **类目 (category)** | 层内按物理子目录分类 (git/test/arch/build/style/domain/ops/misc...), 自由建。 |
| **sediment (沉淀)** | 把本 task 的 learning 写盘成规则。finish 前经**判定门**判 → core / recall / drop。 |

## 契约与记录

| 名词 | 是什么 |
| --- | --- |
| **contract (契约)** | planning 锁定的不可回退不变量, 存 task.json `contracts[]`。check 阶段逐条验证。 |
| **看板 (board)** | `.skein/task.md` (顶层) + per-task task.md, 经脚本渲染, **AI 禁直接读写** (guard 硬阻)。 |

## 角色与载体

| 名词 | 是什么 |
| --- | --- |
| **main (调度器)** | 主对话 agent。跑 task 生命周期脚本 + 编排派 agent + 用户交互 + 完成回传。默认禁写源码。 |
| **执行者 (executor)** | worktree 内写 1 个 subtask 代码的 agent。**不是具名 agent** — main 按 subtask 性质选一个合适的现有 agent (无合适的用 `skein-executor`); 改哪些文件由其在 worktree 内自主决定, 完成前对照 planning 登记的验收标准 checklist 逐条自检; 执行纪律 (递归护栏 + 读后写硬门 + 验收标准自检 + 输出格式) 经 dispatch prompt 硬性注入。 |
| **skein-checker** | 验证 agent, 只读跑 lint/type/test/契约合规。`model: sonnet + effort: medium`。 |
| **skein-researcher** | 调研 agent, planning 选型对比 + bootstrap 扫既有约定, 过程笔记落 `research/`, 收敛结论进 `findings.md`。 |
| **Recursion Guard** | 防 agent 自派 subagent 递归爆炸。具名 agent (checker/researcher) 靠工具集不含 Agent/Task 兜住; 执行者 (skein-executor 等有 Agent/Task) 靠 dispatch prompt 硬性禁止再派承载。 |

## 脚本管理的文件 (AI 禁读写)

四个 json/md 全由 `skein.py` 维护, AI 只经命令 stdout 取态 (`current`/`list`/`board`/`subtask list`/`ready`):

| 文件 | 内容 |
| --- | --- |
| `.skein/task.json` | 顶层状态汇总 `{tasks:[{id,status,deps,worktree}]}` (全部未归档 task) |
| `.skein/task.md` | 顶层看板 (task.json 渲染) |
| `.skein/task/<id>/task.json` | 单 task 记录 + subtask DAG (`subtasks[]`) |
| `.skein/task/<id>/task.md` | 单 task 子任务看板 |

planning 工件 (`prd.md` 主入口 / `design.md` 详细设计 / `findings.md` 调研收敛 / `research/` 过程) 不在此列, AI 可读写。子任务 + 调度 DAG 归 task.json (脚本真值)。
