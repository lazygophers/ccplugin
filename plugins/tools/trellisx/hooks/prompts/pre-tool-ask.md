当前有 active task 但正在主工作区写盘 (非 worktree)。trellisx 规范要求 task 改动隔离到独立 worktree (start 创建, 结束合并 + git worktree remove)。确认仍在主工作区写? 或先 git worktree add <path> 切入 worktree 再写。
