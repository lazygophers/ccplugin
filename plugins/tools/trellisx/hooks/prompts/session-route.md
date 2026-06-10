下一条回复必须以 `[trellisx-start]` 开头，之后所有回复必须以 `[trellisx-{status}-{task name}]` 开头
本会话每次用户输入都必须立即加载 `trellisx-enforce` skill 阅读全部强制规范并逐条遵守，不可绕过。

⛔ 前置流程铁律 (确认是实施需求后, 第一个工具调用就必须开始走, 禁先执行后补):
确认实施需求 → ① task.py create 建任务 → ② planning (加载 trellisx-orchestrate 写 PRD/design/implement/subtask) → ③ git worktree add 建 worktree → ④ 在 worktree 内执行。
禁止: 收到需求后直接 Read/分析/写代码, 等撞到拦截才回头补 task (打补丁式往回锤)。探索 (纯只读) 按复杂度决定是否建 task。
