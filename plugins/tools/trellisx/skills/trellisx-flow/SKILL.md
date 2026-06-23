---
name: trellisx-flow
description: 强制以 Trellis task 闭环处理用户指定的请求 (自判新建/并入 → plan→exec→check→finish 全程不跳步)。**仅用户显式主动调用** (/trellisx-flow 或明确要求"强制走 task 处理这个"); **禁止自动 / 被动 / 推断式调用** —— 不要因为某个请求"看起来该建 task"就自动触发本 skill, 那是 apply 注入的 no_task 倾向的职责。
when_to_use: 仅当用户**显式**输入 `/trellisx-flow`、点名本 skill、或明确说"强制以 task 处理这个请求"时调用。其他任何情况 (包括请求看起来复杂/该建 task) 一律**禁止**自动调用本 skill。
user-invocable: true
argument-hint: [task]
arguments: [任务描述]
---

# trellisx-flow — 强制 Trellis task 闭环

用户**显式调用**本 skill, 要求把其指定的请求**强制作为 Trellis task 处理**, 禁止 inline 直接做 (即使看起来简单)。调用本 skill 即「创建同意」信号 —— 跳过"要不要建 task"的询问 (用户已表态: 要)。但 **调用本 skill ≠ "新建 task"** —— 仍须先判这是**全新任务**还是**对现有 active task 的补充/延续**, 再决定新建还是并入。

处理对象 = 用户调用本 skill 时给出的请求 (任务描述 / arguments)。

## 执行载体铁律 (最高优先级)

> **概念分清**: **task** = trellis 任务记录 (由 `task.py create/start/finish/archive` 脚本管理), 由 **main 同步跑**。**实质工作** (改源码 / 跑 check) **编排成一个独立 workflow 执行** (1 task : 1 workflow), 不在 main 上下文里直接做。**runtime 退化标注**: 本规则属 Claude Code runtime-specific —— **Claude Code 用 Workflow 工具编排**; **无 Workflow 工具的平台 → 退回派 subagent 流水线** (`Agent` 工具 + `isolation: worktree`)。是否 `run_in_background` 异步 / 是否并行 **按需自定, 本 skill 不强制**。**注意: worktree 隔离不在「按需」之列 —— exec 阶段 fan-out 的 writer/checker agent 各走 worktree 隔离 (强制, 见步骤 4 + 硬规)。**

- ⛔ **main 禁直接落地实质工作** —— 改源码、跑 check 等**实质产出一律编排进 workflow 执行** (Claude Code: Workflow 工具; 其他平台: 派 subagent 流水线), main 不在自身上下文里直接做。
- 🧩 **exec/check 编排成 1 个独立 workflow (1 task : 1 workflow)** —— **Claude Code**: 用 **Workflow 工具**把本 task 的 exec(+check) 实质工作编排成**一个独立 workflow**; workflow 内 fan-out 的 writer/checker agent 各走 worktree 隔离。**其他平台 (无 Workflow 工具)**: 退回派 subagent 流水线 (`Agent` 工具 + `isolation: worktree`)。
- 🌳 **fan-out agent 必走 worktree 隔离 (强制)** —— 默认 1 task 1 worktree; **仅冲突型并行 subtask** 才各开子 worktree (→ N worktree, finish 经映射合并各子分支)。每个改源码的 agent MUST 在独立 git worktree 内执行 (`Agent` 工具传 `isolation: worktree`, 或先用 `trellisx-workspace` 建 worktree), 主工作区零改动。worktree 是硬性要求, **仅** `run_in_background` 异步 / 并行分组按需自定。
- 💬 **planning 不进 workflow = main 同步走 `trellis-brainstorm`** —— brainstorm 需逐问用户 (交互式), workflow 内 agent 不能 `AskUserQuestion` / 与用户对话, 故 planning 由 **main 同步前台**驱动 brainstorm + orchestrate, 不进 workflow、不派 subagent。
- 🗂️ **task 生命周期脚本由 main 同步跑** —— `task.py create / start / finish / archive` 是任务记录管理, **main 直接同步执行** (不派 agent、不算实质工作); `task.py finish` 后由 `after_finish` hook 自动完成 commit→merge→archive→销 worktree (N 子分支经映射合并)。
- 🧹 **finish 清理 (强制)** —— `task.py finish` 前 MUST 确认本 task 的 workflow 已终止、**无悬挂后台 Workflow/agent 任务** (用 `TaskList` 查残留, `TaskStop` 关闭); 再 finish (hook 合并 N 子分支 + 销毁全部 worktree)。**workflow 未关 / worktree 未销 = 未闭环, 禁宣告 Done**。
- 🧑 **用户交互决策点 main 亲做** —— `AskUserQuestion` (判新旧不准、产物评审、scope 澄清) subagent 不能与用户对话; subagent 缺信息只能在返回里标 `需要: <问题>`, 由 main 转达用户。
- 📦 **每个 dispatch prompt 必须 6 字段自包含**: 目标 / 已知 (含 `Active task: <task.py current 路径>`) / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。缺字段不派。
- 📣 **完成即时回传** —— 每个 subagent 完成或阻塞, main **立即输出摘要回传用户**, 禁批量延迟汇总。
- 🔴🛑 **"派 agent" = 真实调用 `Agent` 工具, 不是叙述 (最易踩, 必守)** —— 每个"派 agent"动作 MUST 在**同一回复**里产生真实的 `Agent` tool_use。**严禁在本回复无 `Agent` 工具调用的情况下, 回传"已派出 / agent 在做"等措辞 —— 宣称 ≠ 调用, 那是幻觉, 等于跳过执行**。同理 task/看板/worktree 的"已建/已登记"必须是真实跑过命令或工具的结果, 禁凭空宣称。
  > **回传前自检**: 任何"agent 已派 / 在跑 / 已建 task / 看板已更新"措辞输出前, 确认本回复**确有对应的 tool_use** (Agent / Bash task.py / trellisx-workspace)。无 → 先发起真实调用, 禁先回传。

## 调用边界 (重要)

- ✅ **仅用户主动**: `/trellisx-flow <描述>` 或用户明确点名。
- ⛔ **禁自动触发**: 不要因为请求"看起来该建 task / 复杂 / 跨文件"就自行调用本 skill。那种"推荐建 task"是 `trellisx-apply` 注入 workflow.md `[workflow-state:no_task]` 的常驻软提示的职责, 不是本 skill。本 skill 只在用户喊它时才动。

## 强制流程 (plan → exec → check → finish, 不可跳步)

> **贯穿全程: 及时维护 `.trellis/task.md` 看板** —— 下列每一步 (create/start/阶段推进/finish) 完成后, **立即用 `trellisx-workspace` skill 更新 `.trellis/task.md`** 看板表中该任务行 (id/名称/状态/阶段/进度/worktree)。看板落后于实际 = 维护失效。

> 载体速查 (runtime-specific): **planning 同步前台, 不进 workflow** (brainstorm 交互); **exec/check 编排成 1 个独立 workflow** —— **Claude Code 用 Workflow 工具**, 其他平台退派 subagent 流水线 (异步/并行按需自定, 不强制); **task.py 脚本 (create/start/finish/archive) main 同步跑**。main 做编排 + 脚本调用 + 交互式 planning + 用户交互决策 + 完成回传 + 看板维护。

1. **判新旧 + 登记** (main 编排) — 先 `python3 ./.trellis/scripts/task.py current --source` 看有无 active task, **并读 `.trellis/task.md` 看板**对照现有任务全貌 (id/名称/描述/状态), 辅助判断本请求是全新还是匹配某现有任务, 再决定:
   - **全新任务** (与 active task 无关, 或无 active task) → `task.py create "<title>" --slug <name>` 新建。多个独立可验收交付 → parent + child (`--parent`); 单一交付 → 单 task。
   - **现有 task 的补充 / 延续** (扩展、修订、补做当前 active task 的一部分) → **不新建顶层 task**: 回到 planning 修订该 task 的 `prd.md` / `implement.md` 并重新规划; 若是可独立验收的子交付, 用 `task.py create --parent <现有 task>` 挂为 child。
   - 🔴 **判不准 → 🛑 STOP**: MUST 用 AskUserQuestion 问"这是新任务, 还是对 `<active task>` 的补充?", **禁自行替用户决定**, 禁纯文本提问代替工具 (此为用户交互决策点, main 亲做)。
   登记后 → **更新 task.md 看板** (新建/更新该任务行)。
2. **planning** (main 同步前台 —— brainstorm 需逐问用户) — 分工明确, **禁 main 自行凭空设计**:
   - **`trellis-brainstorm` 为主导** —— main **同步**加载, 逐问用户做需求探索 + 方案设计 + 边界收敛, 产出 `prd.md` (复杂任务加 `design.md`)。需求/设计一切以 brainstorm 交互流程为准, 不派 subagent (其不能与用户对话)。
   - **`trellisx-orchestrate` 仅管执行层编排** —— 只负责**实际执行的 subagent 职责划分**、并行组 / 依赖关系、资源互斥, 产出 `implement.md`; **不用它做需求/方案设计**。
   - 多交付在 PRD 出 mermaid 调度图显式标并行组 + 依赖箭头。planning 完成 → 进激活。
3. **激活** (main 编排) — 产物**由 main 用 AskUserQuestion 交用户评审** → 通过后 `task.py start` → status=in_progress。→ **更新 task.md 行** (状态 in_progress / 阶段 exec / worktree 路径)。
4. **exec** (编排成 1 个独立 workflow, **worktree 强制隔离**) — 🔴 **Claude Code: 用 Workflow 工具把本 task 的 exec 工作编排成一个独立 workflow** (1 task : 1 workflow), workflow 内 fan-out 的 writer agent 各走 worktree 隔离 —— 默认 1 task 1 worktree, **仅冲突型并行 subtask** 各开子 worktree (→ N worktree)。**其他平台 (无 Workflow 工具): 退回派 subagent** (`Agent` 工具传 `isolation: worktree`, 或先 `trellisx-workspace` 建 worktree)。全部源码改动落 `<git根>/.worktrees/`, 主工作区零改动; **无论单交付还是多交付, 一律 workflow/subagent 写代码, main 禁亲自改源码**。worktree 为硬性要求, **仅**异步 (`run_in_background`) / 并行分组按需自定。每个 agent 完成即回传。→ **更新 task.md 进度**。
5. **check** (同 workflow 内 fan-out / 派 subagent) — workflow 内 checker agent (或退化平台派 subagent) 走 `trellis-check` 质量验证 (spec 合规 / lint / type-check / tests); 未过 → **再 fan-out / 派 agent 修复重检**, 不跳 finish。→ **更新 task.md 阶段 check**。
6. **finish** (main 同步) — check 通过 → **finish 前先确认本 task 的 workflow 已终止 + 无悬挂后台 Workflow/agent 任务** (用 `TaskList` 查残留, `TaskStop` 关闭); 再 main 直接跑 `python3 ./.trellis/scripts/task.py finish`; `after_finish` hook 自动完成 commit→merge→archive→销 worktree (合并 N 子分支, 非派 agent, 非可选)。→ **更新 task.md 行** (状态 completed)。

## 失败模式 (三段式: 触发 → 一线修复 → 仍失败兜底)

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| planning agent 返回标 `需要:` (缺需求/设计输入) | main 用 `AskUserQuestion` 转达, 回填答案重派 agent | 澄清后 scope 仍收不敛 → 🛑 STOP, 让用户直接拍板 MVP 边界 |
| exec agent 失败/报错返回 | 读失败原因, 补 dispatch prompt 已知/缩范围, 重派 | 同一 subtask 连续 2 次失败 → 🛑 STOP 回传用户, 转人工或拆更小 subtask |
| check 反复不过 (≥2 轮) | 派 agent 按 `trellis-check` 报告定点修复重检 | 第 3 轮仍不过 → 🛑 STOP, 加载 `trellis-break-loop` 跳出调试循环 |
| finish 时 worktree 合并冲突 | `after_finish` hook 自动 abort + 报冲突文件清单 | 检 finish 输出有 `trellisx-finish` 冲突告警 → 停, 转手动解, **禁强解 / 禁当成功** |
| 判不准「新建 task」还是「并入现有」 | `AskUserQuestion` 问用户裁定 | 用户必答 (禁自行替用户决定) |
| 非 trellis 项目 (无 `.trellis/`) | 提示用户先 `trellis init` | 用户拒绝 → 退出, 不强行建 task |

## 硬规 (正向必做)

- ✅ **走完 plan→exec→check→finish 闭环** —— **未 archive = 未完成, 禁宣告 Done / 禁结束本轮**。
- 🌳 **exec 必走 worktree 隔离 (强制)** —— 每个写代码 subagent 必须在独立 git worktree 执行 (`isolation: worktree`), 改动落 `<git根>/.worktrees/`, 主工作区零改动; finish 后由 `after_finish` hook 销 worktree。worktree 非可选, 只有异步/并行才按需自定。
- 🧹 **finish 前清理 workflow (强制)** —— `task.py finish` 前 MUST 确认本 task 的 workflow 已终止、无悬挂后台 Workflow/agent 任务 (`TaskList` 查残留, `TaskStop` 关闭); workflow 未关 / worktree 未销 = 未闭环, **禁宣告 Done**。
- ✅ **及时维护 task.md 看板** —— 每个生命周期节点 (create/start/阶段推进/finish) 后用 `trellisx-workspace` 更新 `.trellis/task.md`; 看板滞后视为流程缺陷。

## ⛔ 反例黑名单 (命中任一 = 流程错误, 改方案重来)

| # | 禁做 | 改为 |
|---|---|---|
| 1 | main 直接改源码 / 跑 check | 编排进 1 个独立 workflow 执行 (Claude Code: Workflow 工具; 其他平台: 派 subagent `Agent` 工具) |
| 2 | 把 task.py 脚本派 agent 执行 | `task.py create/start/finish/archive` main 同步跑 |
| 3 | inline 跳过 task (即使请求极简) | 一律走 task 闭环 —— 这是本 skill 全部意义 |
| 4 | check 未过就推进 finish | 先定点修复重检 |
| 5 | check / finish 未走完就宣告 Done | 未 archive (worktree 仍在) = 未闭环 |
| 6 | 自动 / 被动 / 推断式触发本 skill | 仅用户显式调用 (`/trellisx-flow` 或点名) |
| 7 | main / agent 自行凭空设计需求方案 | `trellis-brainstorm` 主导需求, `trellisx-orchestrate` 仅执行编排 |
| 8 | 用 `trellisx-orchestrate` 做需求 / 方案设计 | 它只管 subagent 职责划分 / 并行 / 依赖 |
| 9 | 纯文本提问代替 `AskUserQuestion` | 用户确认 / 选择必用工具 |
| 10 | 批量延迟汇总 agent 进度 | 每个 agent 完成 / 阻塞即时回传 |
| 11 | **口头宣称"已派 agent / 已建 task / 看板已登记"但本回复无对应 tool_use** | **先真实调用** `Agent` / `Bash task.py` / `trellisx-workspace`, 再回传 —— 宣称 ≠ 调用, 凭空宣称 = 幻觉跳步 |
| 12 | exec subagent 直接在主工作区改源码 (无 worktree) | 必走 worktree 隔离 (`isolation: worktree`), 改动落 `<git根>/.worktrees/`, 主工作区零改动 |
| 13 | finish 时留悬挂 workflow / 后台任务未关 | 改为 `TaskList` 查 + `TaskStop` 关后再 finish |

> 与 `trellisx-apply` 的分工: 本 skill 是用户**主动强制建 task**的入口 (喊它才动); apply 注入的 no_task 倾向是**被动推荐建 task**的常驻软提示。两者互补, 不要混用 —— 本 skill 禁自动触发。
