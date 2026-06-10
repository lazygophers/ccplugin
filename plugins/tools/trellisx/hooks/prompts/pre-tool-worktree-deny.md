⛔ 有 active task, 但本次写盘目标在主工作区 (非 worktree)。task 改动必须隔离到 worktree。

正确做法: ① git worktree add <worktree 路径> (若未建) → ② 写盘目标改为 <worktree 路径>/... 内的文件 → ③ 完成后合并回当前分支 + git worktree remove 清理。
禁止直接写主工作区源码。
