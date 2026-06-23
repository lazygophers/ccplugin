# task.md 维度字段定义

看板是**单表格, 一行一任务**。每列的 定义 / 取值 / 来源 / 更新时机:

| 字段 | 定义 | 取值 / 格式 | 来源 | 更新时机 |
| --- | --- | --- | --- | --- |
| **ID** | task 目录名 | `MM-DD-slug` | task 目录 / `task.py list` | create 时定, 不变 |
| **名称** | 任务标题 | 短语 | `task.json.title` | create; 改标题时 |
| **描述** | 一句话目的 | ≤ 30 字 | `task.json.description` / prd.md | create; 需求变更时 |
| **状态** | trellis 原生状态 (中文显示) | 规划中 ↔ planning / 进行中 ↔ in_progress / 已完成 ↔ completed | `task.json.status` (英文真值, 映射成中文写入) | start / archive 后 |
| **阶段** | 闭环位置 (中文) | 规划 / 实施 / 检查 / 收尾 | AI 按当前动作判 | 阶段推进时 |
| **进度** | 完成度 | 离散档位 0/40/60/80/100 (见下方进度估算) | AI 按档位定 | 阶段推进时 |
| **worktree** | 隔离工作区 | `.worktrees/<name>` 或 `—` | task.json / worktree hook | start 建 worktree 后 |

## 进度估算 (无子任务树)

按阶段取**离散档位** (按括号判定条件选定值, 禁区间/粗估):
- 规划 → 0%
- 实施 · 刚 start 主体未动 (仅建 worktree) → 40%
- 实施 · 主体已落地待收口 → 60%
- 检查 (派 trellis-check 中) → 80%
- 收尾 (merge + archive 前) → 100%

## Worktree ↔ Task 映射区 (唯一额外 section)

主表外**唯一允许**的额外 section: `## Worktree ↔ Task 映射`。worktree 可能由 subagent
isolation / 手动 `git worktree add` 建, 无对应主表行; 此区显式登记每个活跃 worktree 归属哪个
task。**一行一 worktree, 同 task 可多行 (一对多)**:

| 列 | 定义 | 来源 |
| --- | --- | --- |
| worktree | 隔离工作区路径 (规范化 abspath) | WorktreeCreate hook / task start hook / 手动 map-add |
| task | 映射到的 task ID (未知时为 `?`) | 当前活动 task (WorktreeCreate) / task.py |
| 创建源 | 怎么建的 | `trellisx-start` / `subagent` / `WorktreeCreate` / `-` |

经 `trellisx-taskmd.py map-add/map-remove/map-get/map-list` 维护, AI 勿手编。`lint` 子命令
校验 (主表 7 列 / 映射区 3 列 / 状态合法 / ID 不重复)。

## 一致性规则

- 所有字段真值以 `task.json` 为准; task.md 是投影。冲突 → 以 task.json 重建对应行, 不臆造。
- 字段缺失 (如未建 worktree) → 填 `—`, 不留空。
- 映射区: worktree 销毁即 `map-remove`; task archive 时 `sync archive` 删该 tid 全部映射行。
