---
title: worktree-state
category: arch
keywords: [worktree, 状态, 分叉, 快照, 同步, 主仓, 分工, skip]
status: active
inclusion: auto
---

## worktree 与主仓 .skein/ 状态分叉

### 触发场景
派 agent 进 worktree 执行任务时，需要访问 `.skein/` 状态（如 task 定义、状态机状态）。

### 陷阱-正解
**陷阱**：worktree 里的 `.skein/` 是建 worktree 时的快照，而状态推进（如从「就绪」→「进行中」）写在主仓 `.skein/`，两边会静默分叉。具体事故：checker 进 worktree 后读到旧状态（「就绪」），撞上「未处于进行中禁切检查中」的硬门，直接 idle 退出，既没做事也没报错。
**正解**：派 agent 进 worktree 前应确认其 `.skein/` 状态与主仓一致；或 agent 进 worktree 后首先从主仓同步最新状态。

### 铁律
- MUST：建 worktree 前同步主仓状态到 worktree（或工作流文档明确 worktree 使用只读状态快照）
- MUST：agent 进 worktree 后如需读 `.skein/`，先从主仓 pull 最新版本
- MUST：状态推进操作（status 变更）禁在 worktree 中进行，归 main/coordinator 在主仓执行

### 反例表
| 禁 | 改为 |
|---|---|
| worktree 直接读过期的 `.skein/` 状态 | 派发前由 main 完成状态切换，或 agent 进后同步 |
| agent 在 worktree 中修改任务状态 | 状态变更专属 main/coordinator，worktree agent 仅改代码 |
| 状态推进脚本在 worktree 中运行 | 脚本必须在主仓根目录运行 |

### 调试建议
状态分叉往往沉默：看 task 的 status 字段是否与实际执行相符。检查 worktree 内 `.skein/` 修改时间戳，与主仓 `.skein/` 对比。

## worktree 与主仓根 .skein/task/ 各自漂移 — cwd 决定读写哪份, agent 回传 done 不能采信

### 触发场景
agent 在 worktree 里跑完 `subtask done` 后回传「已完成」，main 需要判断能否采信、下一步怎么读状态。

### 机制
`skein` 从进程 **cwd** 解析仓库根，不是从固定路径。worktree 与主仓根各有一份独立的 `.skein/task/`。agent 在 worktree 里跑 `subtask done` 只写 worktree 那份，主仓根读到的仍是旧状态；反过来主仓根的更新也不会自动同步进 worktree。

### 陷阱-正解
**陷阱**：agent 回传「我已 done」后直接采信，不在主仓根核实。曾在同一 session 里因此对错状态两次（不同 subtask），main 自己也因为一时 cwd 落在 worktree 里，读到过一次相反的结论。
**正解**：agent 回传完成后，main 必须在**主仓根**（确认 cwd，不是 worktree）自己核一次实际状态；若发现主仓根未同步，须补跑一次 `subtask done`，不能只凭 agent 的自然语言回传就当作最终真相。

### 关联
- [[worktree 与主仓 .skein/ 状态分叉]] — 同一分叉机制，此条补充 cwd 根因 + 事后核验的具体动作