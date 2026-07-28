# Task 状态机

SKEIN task 生命周期的 5 个状态、流转规则、操作命令与合法性约束。
状态常量定义见 `skein.py:48-54`，落盘值为中文。

---

## 5 个状态

| 状态 (中文) | 英文别名 | 阶段 | 占 active 槽 | 有 worktree | 含义 |
|---|---|---|---|---|---|
| **待处理** | pending / planning | plan | 否 | 否 | 刚创建，正在 brainstorm / 规划 subtask / 填 PRD / 出 design，未过用户确认门 |
| **就绪** | ready | ready | 否 | 否 | planning 完成 (prd 齐 + ≥1 subtask) + 用户确认通过，排队等 `skein start` 启动 |
| **进行中** | active | exec | **是** | 是 | 已 start，worktree 已建，subtask 正在被派发执行 |
| **检查中** | check | check | 否 | 是 | 全 subtask done，已 `skein check` 进验证阶段，skein-checker 跑 lint/test/契约 |
| **已完成** | done | finish | 否 | 否 (已销) | 验证全绿 + merge 回主仓 + 销 worktree，闭环结束 |

> **两套语义分离** (skein.py:55-57):
> - `STATUS_ACTIVE = {进行中}` — 占 `max_active` 并发槽的仅进行中
> - `STATUS_INFLIGHT = {进行中, 检查中}` — 已 start 有 worktree、可 finish / del 需销 worktree 的含检查中

---

## 状态流转图

```
                    create
                      ↓
                 ┌──────────┐
                 │  待处理   │  (planning/pending)
                 └────┬─────┘
                      │ confirm (用户确认门)
                      ↓
                 ┌──────────┐
                 │   就绪   │  (ready)
                 └────┬─────┘
                      │ start (占槽+建worktree)
                      ↓
                 ┌──────────┐
        ┌───────→│  进行中  │←──────┐
        │        └────┬─────┘       │
        │             │             │
        │             ↓             │
        │        ┌──────────┐       │
        │        │  检查中  │       │  (检查未过 → 回进行中，
        │        └────┬─────┘       │   加修复 subtask 重派)
        │             │             │
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
| `skein confirm <id>` | 待处理 | 就绪 | ≥1 subtask 登记 + prd 三章节齐 + 无 TODO 占位 | 置 `confirmed` 时间戳 |
| `skein start <id>` | 就绪 | 进行中 | doctor 体检过 + 非满槽 (`max_active`) + deps 全完成 + prd 二次校验 | 建 worktree + 置 `started` 时间戳 |
| `skein check <id>` | 进行中 | 检查中 | (无额外校验，只要状态对) | 置 `checked` 时间戳 |
| `skein finish <id>` | 进行中 / 检查中 | 已完成 | (无 subtask 完成校验，脚本不卡) | merge 回主仓 + 销 worktree + 置 `finished` 时间戳 |
| `skein archive <id>` | 已完成 | (归档) | 已完成 | 移到 `archive/<年>/<月-日>/<id>/` |

> **检查未过回退**: check 阶段发现问题 → **task 保持「进行中」** (不回退状态)，直接同 task `subtask add` 加修复子任务回 exec 重派。再次全绿后重新 `skein check` 进检查中。

---

## 状态合法性约束 (硬约束，脚本硬拒)

以下约束由 `skein.py` 命令层强制执行，违反直接 `SystemExit(1)`：

### 1. 不能跳阶段

| 操作 | 合法源状态 | 跳阶段示例 (非法) |
|---|---|---|
| `confirm` | 仅待处理 | 就绪态再 confirm → 拒 |
| `start` | 仅就绪 | 待处理直接 start → 拒 (须先 confirm) |
| `check` | 仅进行中 | 待处理/就绪 check → 拒 |
| `finish` | 仅进行中 / 检查中 | 待处理/就绪/已完成 finish → 拒 |

### 2. 不能回退 (不可逆)

- 待处理 → 就绪 → 进行中 → 检查中 → 已完成，**单向前进，无回退命令**
- 检查未过 ≠ 状态回退：task 保持进行中，加 subtask 继续跑，不是「回退到待处理」
- 已完成的 task 不可重新激活，要重做就新建 task

### 3. 幂等性边界

| 操作 | 重复调用行为 |
|---|---|
| `create` 同 id | 拒 (id 已占用，含已归档也不可复用) |
| `confirm` 已就绪 | 拒 (只能 confirm 待处理) |
| `start` 已进行中 | 拒 (只能 start 就绪) |
| `finish` 已完成 | 拒 (非在途无法 finish) |
| `archive` 已归档 | 静默返回 0 (幂等) |

### 4. 并发槽约束

- `max_active` (默认 2) 限制同时「进行中」的 task 数
- `start` 时校验：满槽 → 拒，提示先 finish 一个
- 就绪态 task 不占槽，可无限排队

### 5. deps 约束

- `deps` (task 级前置依赖) 只在 `start` 时校验
- `create` / `deps set` / `confirm` **均不阻塞**，pending task 照常规划
- dep 未完成 → start 拒，等 dep finish 后再 start

---

## 看板排序

进行中 > 检查中 > 就绪 > 待处理 > 已完成 (同状态内按 id 稳定排序)
见 `skein.py:60-61` `STATUS_ORDER`。
