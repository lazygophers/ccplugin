---
name: trellisx-add
description: '➕ 规划级入口 (只规划不执行): 把指定请求纳入 trellis task 的 planning 阶段 —— 判新旧 + task.py create 登记 + 交互式 planning (brainstorm 主导 + grill 硬门1 边问边写), 产出 prd/design/implement 后停在 task.py start 之前, task 留 planning 态, 禁 exec/check/finish。用户想"先看规划再决定执行 / 添加分析规划任务 / 只规划不动手"时用。仅显式调用 (/trellisx-add), 禁 model 自动触发。与 trellisx-flow 边界: flow=强制全闭环 (plan→exec→check→finish), add=只到 planning 停; 执行 pending 规划态 task 走 /go'
when_to_use: '用户显式 /trellisx-add, 或明确表达"只规划不执行 / 先看规划再说 / 先分析设计好, 执行等我确认 / 添加一个分析规划任务"。仅显式触发 (禁自动)。planning 逻辑单一真值源: flow 与 go 均运行时委托本 skill 或复用其产物, 不复制正文'
argument-hint: "[--continue|--exec] <任务描述>"
arguments: [入口选项 (可选), 任务描述]
---

# trellisx-add — 规划级入口 (只规划不执行)

用户**显式调用**本 skill, 要求把其请求纳入 Trellis task 的 **planning 阶段并停下**: 判新旧 + 登记 + 交互式 planning, 产出 `prd.md` / `design.md` / `implement.md` 后**停在 `task.py start` 之前**, task 留 **planning 态**, 交还控制权。**禁 exec / check / finish** —— 那是 `trellisx-flow` (全闭环) 或 `/go` (执行 pending) 的职责。

本 skill 是 trellis **planning 逻辑的单一真值源**: `trellisx-flow` 运行时委托本 skill (`--continue`) 借完 planning 再自接 exec; `/go` 消费本 skill 攒下的 planning 态 task。二者均不复制本 skill 正文。

处理对象 = 用户调用本 skill 时给出的请求 (任务描述 / arguments)。

## 入口参数契约 (决定停/不停)

调用形如 `/trellisx-add [选项] <任务描述>`。**选项位于任务描述之前**, 无法识别为选项的 token 一律并入任务描述, 不报错。

| 调用方 | 选项 | planning 跑完后行为 |
|---|---|---|
| 用户 `/trellisx-add <描述>` | 无 (默认) | **阻塞: 停在 `task.py start` 之前**, task 留 planning 态, 交还控制权给用户 (用户审完自行决定是否 `/go` 或 `/trellisx-flow`) |
| flow 内部委托 | `--continue` (别名 `--exec`) | **不阻塞: 不停**, 返回 planning 产物路径 (`prd.md`/`design.md`/`implement.md`), 由调用方 (flow) 自接 step3 激活续 exec |

- **中文别名** (同义可接): `继续`/`执行` = `--continue` (= `--exec`)。
- 🔴 **「停 / 不停」只是入口层开关 —— planning 逻辑本体零分支** (真复用): 无论有无 `--continue`, 判新旧 + create + brainstorm + grill 硬门1 + 写 prd/design/implement 的正文**完全一致**, 只在 planning 全部产出后, 按本表决定「停并交还」还是「返回产物路径」。**禁在 planning 逻辑里按参数分叉**。

## 调用边界 (重要)

- ✅ **仅显式触发**: 只有用户显式 `/trellisx-add` 或明确表达"只规划不执行 / 先看规划"意图才进入。**禁 model 自动触发** (自动全闭环是 `trellisx-flow` 的双模职责, add 不抢)。
- ⛔ **禁 exec / check / finish**: add 的终点是 planning 态 task。**禁跑 `task.py start` / 禁派 exec subagent / 禁跑 check / 禁 finish**。要执行 → 用户自行 `/go` (执行所有 pending) 或 `/trellisx-flow` (单请求全闭环)。
- ⛔ **仍禁**: 把明显该 inline 的极简请求 (纯查询 / 单文件 ≤20 行) 强行建 task (作用域边界见「硬规」段)。
- 🔗 **与邻居边界**: `trellisx-flow` = 强制全闭环 (plan→exec→check→finish, 双模触发); `/go` = 执行所有 planning 态 pending task; `trellisx-add` = 只到 planning 停 (仅显式)。三者不误抢。

## planning 流程 (判新旧 → 登记 → planning, 到此停)

> **第 0 步 — 解析入参**: 进入流程前, 先从调用参数剥离前置选项 (`--continue`/`--exec` 及中文别名, 见「入口参数契约」段), 确定本次跑完是「停」还是「返回产物」; 剩余 token 即任务描述。

> **贯穿全程: 及时维护 `.trellis/task.md` 看板** —— 下列每步 (create/阶段推进) 完成后, **立即用 `trellisx-workspace` skill 更新 `.trellis/task.md`** 看板表中该任务行 (id/名称/描述/状态/worktree)。看板落后于实际 = 维护失效。

> 载体: **planning 全程 main 同步前台** (brainstorm 交互式, 逐问用户, 不派执行 subagent —— subagent 不能 `AskUserQuestion`); `task.py create` 由 **main 同步跑** (任务记录管理, 非实质工作)。🔴🛑 **"已建 task / 看板已登记"必须是真实跑过 `task.py` / `trellisx-workspace` 的结果, 禁凭空宣称** (宣称 ≠ 调用 = 幻觉跳步)。

### 1. 判新旧 + 登记 (main 编排)

先 `python3 ./.trellis/scripts/task.py current --source` 看有无 active task, **并读 `.trellis/task.md` 看板**对照现有任务全貌 (id/名称/描述/状态), 辅助判断本请求是全新还是匹配某现有任务, 再决定:

- **全新任务** (与 active task 无关, 或无 active task) → `task.py create "<title>" --slug <name>` 新建。多个独立可验收交付 → parent + child (`--parent`); 单一交付 → 单 task。若本 task **依赖其他 pending/现有 task 先完成** (task 级 DAG, 非并行), create 后用 **`trellisx-taskmd.py update <tid> --deps "<前置id>,..."`** 写 task.json `depends_on` + 看板「前置」列 (随 apply 发货, 通用; flow/go 调度据此排序; 无依赖不填)。本仓 task.py 另支持 `create --depends-on` / `set-deps <dir> "a,b"` 语法糖 (仅本仓, 非发货路径)。
- **现有 task 的补充 / 延续** (扩展、修订、补做某 planning 态 task 的一部分) → **不新建顶层 task**: 回到 planning 修订该 task 的 `prd.md` / `implement.md` 并重新规划; 若是可独立验收的子交付, 用 `task.py create --parent <现有 task>` 挂为 child。
- 🔴 **判不准 → 🛑 STOP**: MUST 用 `AskUserQuestion` 问"这是新任务, 还是对 `<现有 task>` 的补充?", **禁自行替用户决定**, 禁纯文本提问代替工具 (用户交互决策点, main 亲做)。

登记后 → **更新 task.md 看板** (新建/更新该任务行)。

### 2. planning (main 同步前台 —— brainstorm 需逐问用户)

分工明确, **禁 main 自行凭空设计**:

- **`trellis-brainstorm` 为主导** —— main **同步**加载, 逐问用户做需求探索 + 方案设计 + 边界收敛, 产出 `prd.md` (复杂任务加 `design.md`)。需求/设计一切以 brainstorm 交互流程为准, 不派 subagent (其不能与用户对话)。
- 🔴 **grill 硬门 1 (PRD 边问边写)**: brainstorm 逐问过程 MUST 协同 `/trellisx-grill` —— grill 轴 A (目标) / B (产出) 当提问引擎, grill 出问 → brainstorm 问用户 → 答完即时更新 PRD → 循环至轴 A/B 双 ✓ (目标封闭 + deliverable 可验收)。**禁写完整 PRD 才调 grill** (本末倒置)。
- **`trellisx-orchestrate` 仅管执行层编排** —— 只负责**实际执行的 subagent 职责划分**、并行组 / 依赖关系、资源互斥, 产出 `implement.md`; **不用它做需求/方案设计**。**spec 加载归 trellisx-orchestrate step 1** (🔴 必做 grep 门, 见该 skill; add 不重复加载)。
- 多交付在 PRD 出 mermaid 调度图显式标并行组 + 依赖箭头。

planning 产物齐 (`prd.md` [+ `design.md`] + `implement.md`) → **到此停**:

- **无 `--continue` (用户直呼)**: **停在 `task.py start` 之前**, task 留 planning 态, 更新 task.md 行 (状态 planning), 交还控制权 —— 回传用户 planning 产物摘要 + "已规划完成, 停在执行前; `/go` 执行所有待办规划, 或 `/trellisx-flow` 单独执行本 task"。**禁 start / exec / check / finish**。
- **有 `--continue`/`--exec` (flow 委托)**: **不停**, 返回 planning 产物路径 (`prd.md`/`design.md`/`implement.md` 绝对路径) 给调用方, 由 flow 自接 step3 激活 (含 grill 硬门2 start 前确认) → exec。

## 硬规 (正向必做)

- 🗂️ **task.py 脚本 main 同步跑** —— `task.py create` 是任务记录管理, main 直接同步执行 (不派 agent、不算实质工作)。add **不跑 `task.py start`** (那是激活/执行, 归 flow/go)。
- 💬 **planning 全程 main 同步前台** —— brainstorm 需逐问用户 (交互式), 不派 subagent、不执行。
- 🔒 **task.md 禁直接 Edit/Write/MultiEdit** —— `.trellis/task.md` 看板**必经 `trellisx-taskmd.py` 脚本操作** (settings.json `permissions.deny` + `guard-taskmd.sh` PreToolUse hook 双保险硬阻)。
- 🧑 **用户交互决策点 main 亲做** —— `AskUserQuestion` (判新旧不准、产物评审、scope 澄清) 必用工具, 禁纯文本代替。
- ✅ **及时维护 task.md 看板** —— 每个节点 (create/阶段推进) 后用 `trellisx-workspace` 更新, 看板滞后视为流程缺陷。

### 作用域边界 (何时建 task)

| 特征 | 判定 |
| --- | --- |
| 纯查询 / 文档阅读 / 问答 (无改动) | 豁免, 不建 task |
| 单文件单处改, ≤20 行且位置已知 | 豁免 |
| 跨 ≥2 文件 / 单文件多处 / 多步骤改 | **必建 task** |
| 需外部调研 (库选型/方案对比) 或产出文档交付 | **必建 task** (调研为 research subtask) |
| 边界模糊 | **MUST AskUserQuestion 由用户裁定** |

## 失败模式 (触发 → 一线修复 → 仍失败兜底)

> 与下方「反例黑名单」区别: 黑名单是**不要做什么**, 本表是 **planning 跑起来卡壳时怎么办**。

| 触发 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 非 trellis 项目 (无 `.trellis/`) | 提示用户先 `/trellisx-apply` 装脚本+hook 初始化 | 用户暂不初始化 → 降级口头给规划框架, 不落 task, 标「apply 后再登记」 |
| 判新旧不准 (是新任务还是补现有) | 🛑 STOP 用 `AskUserQuestion` 让用户裁定 | 用户也拿不准 → 默认建**独立新 task** (可事后 `--parent` 挂靠), 禁静默并入他 task |
| brainstorm 需求探索卡住 / 用户信息太少 | grill 轴 A/B 当提问引擎逐项追问回填 PRD | 用户仍答不清核心目标 → 🛑 STOP 圈定最小可验收 MVP, 超出标「后续迭代」, 禁凭空替用户设计 |
| scope 不收敛 (越谈越大 / 多目标缠绕) | grill 硬门 1 收敛到单一封闭目标 + 可验收 deliverable | 仍发散 → 🛑 STOP 让用户在候选目标间拍板主线, 其余拆为独立 task |
| `task.py create` 执行失败 (路径/权限) | 报错停, 修复后重跑, 禁跳过 | 仍失败 → 明确告知未登记, 禁口头宣称「已建 task」(宣称 ≠ 调用) |

## ⛔ 反例黑名单 (命中任一 = 流程错误, 改方案重来)

| # | 禁做 | 改为 |
|---|---|---|
| 1 | add 跑 `task.py start` / 派 exec subagent / 跑 check / finish | add 只到 planning 停; 执行归 flow / `/go` |
| 2 | planning 逻辑按 `--continue` 参数分叉 | 参数只控入口「停/不停」, planning 本体零分支 (真复用) |
| 3 | model 自动触发 add | add 仅显式; 自动全闭环是 flow 的双模职责 |
| 4 | 写完整 PRD 才调 grill | grill 硬门1 边问边写 (轴 A/B 驱动循环) |
| 5 | main / agent 自行凭空设计需求方案 | `trellis-brainstorm` 主导需求, `trellisx-orchestrate` 仅执行编排 |
| 6 | 把 `task.py create` 派 agent 执行 | main 同步跑 |
| 7 | 纯文本提问代替 `AskUserQuestion` | 用户确认 / 选择必用工具 |
| 8 | 口头宣称"已建 task / 看板已登记"但本回复无对应 tool_use | 先真实调用 `task.py` / `trellisx-workspace` 再回传 (宣称 ≠ 调用) |
| 9 | 把明显该 inline 的极简请求强行建 task | 作用域边界表判 (见「硬规」段) |

## 相关 skill

- `trellisx-flow` — 强制全闭环 (plan→exec→check→finish, 双模触发); 委托本 skill (`--continue`) 借 planning 后自接 exec。
- `/go` (command) — 执行所有 pending (planning 态) task, 消费本 skill 产物。
- `trellisx-grill` — 对抗式工件审查 (硬门1 边问边写, 由本 skill planning 强制驱动)。
- `trellisx-orchestrate` — 执行层编排 (planning 产 `implement.md`)。
- `trellisx-workspace` — task.md 看板维护。
