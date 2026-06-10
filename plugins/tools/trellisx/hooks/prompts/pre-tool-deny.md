⛔ 停止。main 禁止直接写源码 — 源码实施必须派 agent 在 worktree 内执行。

正确流程: ① task.py create → ② planning (加载 trellisx-orchestrate, 拆 ≥ 2 subtask) → ③ 每 subtask 派 sub-agent (isolation:worktree) 或 agent-team 成员 (.trellis/worktrees/<subtask>) 执行 → ④ main 收集结果协调。

禁止: main 自己写源码 / 自己进 worktree 干活 / 打补丁式往回锤。纯探索 (只读) 不受限。main 写 .trellis/ 文档不受限。
