# task.md 维度字段定义

看板是**单表格, 一行一任务**。5 列, 每列的 定义 / 取值 / 来源 / 更新时机:

| 字段 | 定义 | 取值 / 格式 | 来源 | 更新时机 |
| --- | --- | --- | --- | --- |
| **ID** | task 目录名 | `MM-DD-slug` | task 目录 / `task.py list` | create 时定, 不变 |
| **名称** | 任务标题 | 短语 | `task.json.title` | create; 改标题时 |
| **描述** | 一句话目的 | ≤ 30 字 | `task.json.description` / prd.md | create; 需求变更时 |
| **状态** | 生命周期阶段 (合并原"状态"+"阶段") | 规划中 / 实施中 / 检查中 / 收尾 / 已完成 / 已归档 | hook sync 写基础态 (规划中/实施中/已完成/已归档); AI update 细化 (实施中/检查中/收尾) | start / 阶段推进 / archive 后 |
| **worktree** | 隔离工作区 | `.worktrees/<name>` 或 `—` | task.json / worktree hook | start 建 worktree 后 |

## 状态列取值 (生命周期阶段)

状态列承载闭环阶段, 取值及其含义:

| 状态 (中文) | 含义 | 谁写 | 对应 task.json status |
| --- | --- | --- | --- |
| 规划中 | 规划中 (写 prd/design/implement) | hook sync | planning |
| 实施中 | 实施中 | hook sync / AI | in_progress |
| 检查中 | 质量验证中 (派 trellis-check) | AI update | in_progress |
| 收尾 | 已通过 check, merge+archive 前 | AI update | in_progress |
| 已完成 | 已归档 | hook sync (archive) | completed |
| 已归档 | 已归档 (lint 允许) | hook sync | archived |

**冲突规则**: hook sync 写基础态; 若 AI 已写细分 (实施中/检查中/收尾) 且 task 仍 in_progress, hook sync 不覆 AI 细分。

## Worktree ↔ Task 映射区 (唯一额外 section)

主表外**唯一允许**的额外 section: `## Worktree ↔ Task 映射`。worktree 可能由 subagent
isolation / 手动 `git worktree add` 建, 无对应主表行; 此区显式登记每个活跃 worktree 归属哪个
task。**一行一 worktree, 同 task 可多行 (一对多)**:

| 列 | 定义 | 来源 |
| --- | --- | --- |
| worktree | 隔离工作区路径 (规范化 abspath) | WorktreeCreate hook / task start hook / 手动 map-add |
| task | 映射到的 task ID (未知时为 `?`) | 当前活动 task (WorktreeCreate) / task.py |
| 创建源 | 怎么建的 | `trellisx-start` / `subagent` / `WorktreeCreate` / `-` |

经 `trellisx-taskmd.py map-add/map-remove/map-get/map-list` 维护 (guard hook 调用), AI 勿手编。
`lint` 子命令校验 (主表 5 列 / 映射区 3 列 / 状态合法 / ID 不重复)。

## 一致性规则

- 所有字段真值以 `task.json` 为准; task.md 是投影。冲突 → 以 task.json 重建对应行, 不臆造。
- 字段缺失 (如未建 worktree) → 填 `—`, 不留空。
- 映射区: worktree 销毁即 `map-remove`; task archive 时 `sync archive` 删该 tid 全部映射行。
