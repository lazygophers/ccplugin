必须先判断内容是否是当前/现有任务的一部分
如果是，下一条回复必须以 `[trellisx-continue-{task-name}]` 开头，然后去补充、扩展、修改、细化 task 的相关内容，并重新评估调度情况
如果是一个新任务，下一条回复必须以 `[trellisx-new-task]` 开头，启用新的 worktree，然后启用新的 task，走 planning (加载 trellisx-orchestrate skill)，并且在任务结束时，及时关闭并清理 worktree，确保环境干净
除非有特殊说明，否则所有回复必须以 `[trellisx-{status}-{task name}]` 开头