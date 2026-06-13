# task.md 维度字段定义

看板是**单表格, 一行一任务**。每列的 定义 / 取值 / 来源 / 更新时机:

| 字段 | 定义 | 取值 / 格式 | 来源 | 更新时机 |
| --- | --- | --- | --- | --- |
| **ID** | task 目录名 | `MM-DD-slug` | task 目录 / `task.py list` | create 时定, 不变 |
| **名称** | 任务标题 | 短语 | `task.json.title` | create; 改标题时 |
| **描述** | 一句话目的 | ≤ 30 字 | `task.json.description` / prd.md | create; 需求变更时 |
| **状态** | trellis 原生状态 (中文显示) | 规划中 ↔ planning / 进行中 ↔ in_progress / 已完成 ↔ completed | `task.json.status` (英文真值, 映射成中文写入) | start / archive 后 |
| **阶段** | 闭环位置 (中文) | 规划 / 实施 / 检查 / 收尾 | AI 按当前动作判 | 阶段推进时 |
| **进度** | 完成度 | 百分比 (按阶段估) | AI 估 | 阶段推进时 |
| **worktree** | 隔离工作区 | `.worktrees/<name>` 或 `—` | task.json / worktree hook | start 建 worktree 后 |

## 进度估算 (无子任务树)

按阶段近似:
- 规划 → 0%
- 实施 → 进行中 (可填 30–70% 粗估)
- 检查 → ~80%
- 收尾 → 100%

## 一致性规则

- 所有字段真值以 `task.json` 为准; task.md 是投影。冲突 → 以 task.json 重建对应行, 不臆造。
- 字段缺失 (如未建 worktree) → 填 `—`, 不留空。
