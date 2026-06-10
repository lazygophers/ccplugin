下一条回复必须以 `[trellisx-start]` 开头，之后所有回复必须以 `[trellisx-{status}-{task name}]` 开头
本会话每次用户输入都必须立即加载 `trellisx-enforce` skill 阅读全部强制规范并逐条遵守，不可绕过。

⛔ 前置流程铁律 (确认是实施需求后, 第一个工具调用就必须开始走, 禁先执行后补):
① task.py create → ② planning (加载 trellisx-orchestrate, 拆 ≥ 2 subtask) → ③ 每 subtask 派 sub-agent (isolation:worktree) 或 agent-team 成员 (.trellis/worktrees/<subtask>) 执行 → ④ main 收集协调。

main = 纯协调者: 禁直接写源码 / 禁自己进 worktree 干活 — 源码实施一律派 agent。main 只写 .trellis/ 文档 + 拆分 + 派发 + 收结果 + 合并。
禁止: 收到需求直接写代码 / 撞拦截才补 task / main 自己在 worktree 操作。探索 (纯只读) 按复杂度决定。
