trellisx: sub-agent 完成。若该 sub-agent 使用 isolation: worktree, main 必须: 1) review worktree diff; 2) 合并到当前分支 (或丢弃); 3) git worktree remove 清理。禁保留已完成 sub-agent 的 worktree 占用磁盘。
