派 sub-agent 未设 isolation:worktree。trellisx 规范: 写盘 sub-agent MUST 带 isolation:worktree (避免脏写 + 失败整树丢弃), 仅纯只读 (探索/调研/审查) 可省。确认此 agent 仅只读? 否则在 Agent 调用加 isolation:worktree 再派。
