# Task 状态机

SKEIN task 生命周期的 7 个状态、流转规则、操作命令与合法性约束。
状态落盘值为中文，`skein status <id>` 可查当前态。

---

## 7 个状态

| 状态 (中文) | 英文别名 | 阶段 | 占 work 槽 | 占 gate 槽 | 有 worktree | 含义 |
|---|---|---|---|---|---|---|
| **待处理** | pending / planning | plan | 否 | 否 | 否 | 刚创建，正在 brainstorm / 规划 subtask / 填 PRD / 出 design，未过用户确认门 |
| **调研中** | research | research | 否 | 否 | 否 | 已 `research` 发起调研，≥1 个 phase=research 的 subtask 在跑，尚未收敛回规划 |
| **进行中** | active | exec | **是** | 否 | 是 | 已 `confirm`(吸收原 start)，worktree 已建，subtask 正在被派发执行 |
| **检查中** | check | check | 否 | **是** | 是 | 全 subtask done，已 `skein check` 进验证阶段，skein-checker 跑 lint/test/契约 |
| **收尾中** | finishing | finishing | 否 | **是** | 是 | 已 `skein finishing` 占 gate 槽，main 派出的 skein-finisher 正在跑 `finish` |
| **已完成** | done | finish | 否 | 否 | 否 (已销) | 验证全绿 + merge 回主仓 + 销 worktree，闭环结束 |

> `就绪` 中间态已删 — 人审通过的下一秒就该开工，`confirm` 一步直接推进「进行中」(design.md §1)。

> **两个池**：
> - `pools.work` (默认 2) — 占槽态 `{进行中}`
> - `pools.gate` (默认 2) — 占槽态 `{检查中, 收尾中}`，两池互不干扰 (work 满仍可 check)

---

## 状态流转图

```
                    create
                      ↓
                 ┌──────────┐
        ┌───────→│  待处理   │  (pending)
        │        └────┬─────┘
        │ plan         │ research (发起调研)
        │              ↓
        │        ┌──────────┐
        └────────│  调研中   │  (research)
                  └──────────┘
                      │  (待处理)
                      │ confirm (用户确认门, 吸收 start: 占 work 槽 + 建 worktree)
                      ↓
                 ┌──────────┐
        ┌───────→│  进行中  │←──────┐
        │        └────┬─────┘       │
        │             │ check       │
        │             ↓             │
        │        ┌──────────┐       │
        │        │  检查中  │       │  (检查未过 → 回进行中，
        │        └────┬─────┘       │   加修复 subtask 重派)
        │             │ finishing   │
        │             │ (占 gate 槽)│
        │             ↓             │
        │        ┌──────────┐       │
        │        │  收尾中  │       │
        │        └────┬─────┘       │
        └─────────────┼─────────────┘
                      │ finish (merge+销worktree)
                      ↓
                 ┌──────────┐
                 │  已完成   │  (done)
                 └──────────┘
                      │ archive
                      ↓
                  归档目录
```

---

## 状态切换命令

| 命令 | 源状态 | 目标状态 | 前置校验 | 副作用 |
|---|---|---|---|---|
| `skein create <id>` | (无) | 待处理 | id 合法 (kebab-case slug)、未占用 | 建 task 目录 + prd/design 脚手架 |
| `skein research <id>` | 待处理 | 调研中 | 至少一个 phase=research 的 subtask | (无额外副作用，只改状态) |
| `skein plan <id>` | 调研中 | 待处理 | research subtask 全 done | 收敛调研回规划 |
| `skein confirm <id>` | 待处理 | 进行中 | ≥1 subtask 登记 + prd 三章节齐 + 无 TODO 占位 + 预计工时 + **用户审核** (看板点「确认规划」, 或 `--summary` → `AskUserQuestion` → `--approved`) + doctor 体检过 + deps 全完成 | 置 `confirmed` + `confirmed_by=user` + 建 worktree + 置 `started` 时间戳 (吸收原 `start`)。调研中 task 直接 confirm 会被拒，须先 `plan` |
| `skein check <id>` | 进行中 | 检查中 | (无额外校验，只要状态对) | 置 `checked` 时间戳 |
| `skein finishing <id>` | 检查中 | 收尾中 | gate 池有空槽 (`pools.gate`) | 占 gate 槽，main 收到后派 skein-finisher |
| `skein finish <id>` | **仅收尾中** | 已完成 | (无 subtask 完成校验，脚本不卡)；**`kind=supertask` 例外**：`parent` 指向它的 child task 须全部已完成，否则拒 | merge 回主仓 + 销 worktree + 置 `finished` 时间戳，释放 gate 槽 |
| `skein archive <id>` | 已完成 | (归档) | 已完成 | 移到 `archive/<年>/<月-日>/<id>/` |

> **检查未过回退**: check 阶段发现问题 → **task 保持「进行中」** (不回退状态)，直接同 task `subtask add` 加修复子任务回 exec 重派。再次全绿后重新 `skein check` 进检查中。

---

## 状态合法性约束 (硬约束，脚本硬拒)

以下约束由 `skein` 命令强制执行，违反直接 `SystemExit(1)`：

### 1. 不能跳阶段

| 操作 | 合法源状态 | 跳阶段示例 (非法) |
|---|---|---|
| `research` | 仅待处理 | 调研中/进行中再 research → 拒 |
| `plan` | 仅调研中 | 待处理 plan → 拒 (无需, 已在待处理) |
| `confirm` | 仅待处理 | 调研中直接 confirm → 拒 (须先 plan 收敛)；进行中再 confirm → 拒 |
| `check` | 仅进行中 | 待处理/调研中/检查中 check → 拒 |
| `finishing` | 仅检查中 | 进行中/收尾中 finishing → 拒 |
| `finish` | **仅收尾中** | 进行中/检查中直接 finish → 拒 (须先 check + finishing) |

### 2. 不能回退 (不可逆)

- 待处理 ⇄ 调研中 (仅这一对可往返)；待处理 → 进行中 → 检查中 → 收尾中 → 已完成，其余单向前进，无回退命令
- 检查未过 ≠ 状态回退：task 保持进行中，加 subtask 继续跑，不是「回退到待处理」
- 已完成的 task 不可重新激活，要重做就新建 task

### 3. 幂等性边界

| 操作 | 重复调用行为 |
|---|---|
| `create` 同 id | 拒 (id 已占用，含已归档也不可复用) |
| `confirm` 已进行中 | 拒 (只能 confirm 待处理) |
| `finishing` 已收尾中 | 拒 (只能对检查中收尾) |
| `finish` 已完成 | 拒 (仅收尾中可 finish) |
| `archive` 已归档 | 静默返回 0 (幂等) |

### 4. 并发槽约束 (两池独立)

- `pools.work` (默认 2) 限制同时「进行中」的 task 数；`confirm` 时校验，满槽 → 拒
- `pools.gate` (默认 2) 限制同时「检查中 + 收尾中」的 task 数；`finishing` 时校验，满槽 → 拒
- 两池互不干扰：work 满仍可 `check` (check 本身不占槽，只是进 gate 池候选)

### 5. deps 约束

- `deps` (task 级前置依赖) 只在 `confirm` 时校验
- `create` / `deps set` **均不阻塞**，pending task 照常规划
- dep 未完成 → confirm 拒，等 dep finish 后再 confirm

---

## 看板排序

进行中 > 检查中 > 收尾中 > 调研中 > 待处理 > 已完成 (同状态内按 id 稳定排序)
`skein list` / `skein board` 按此序输出。
