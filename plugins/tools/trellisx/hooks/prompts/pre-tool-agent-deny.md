⛔ 派写盘 sub-agent 必须带 isolation:worktree (每 subtask 在独立 worktree 内执行, 避免脏写 + 失败整树丢弃)。仅纯只读 agent (探索/调研/审查) 可省。在 Agent 调用加 isolation:worktree 再派。
