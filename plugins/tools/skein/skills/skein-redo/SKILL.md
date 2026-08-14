---
name: skein-redo
description: "SKEIN 断点续跑。session 意外结束后重新调度未完成的 agent, 继续 main 尚未闭环的工作。不等同复位 — running subtask 不强制 fail, 只补派未完成的调度。"
user-invocable: true
argument-hint: "[任务ID]"
arguments: "[任务ID]"
model: sonnet
effort: medium
---

session 意外结束 (崩溃 / 手动中断 / context 满) 后恢复。不是回滚也不是复位 — 而是接上断点继续闭环：

1. 查当前有哪些 running subtask
	`! skein subtask list all --status running | jq -r '(.subtasks // []) | if length == 0 then "no subtask" else .[] | [.tid, .sid .name] | @tsv end'`
2. TaskList、AgentList 等方式查询正在运行的 Task、Agent 的状态
3. 重新使用 Agent 调度正在进行中的但是没有实际 Task、Agent 的 subtask
4. 如果 Agent 槽位有空闲，继续调度，use with Skill('skein:skein-flow')
5. 查看当前有哪些 plan task
	`! skein task list --status plan | jq -r '(.tasks // []) | if length == 0 then "no task" else .[] | [.id .name] | @tsv end'`
6. 对每一个 plan task 依次完成完整的 Skill('skein:skein-plan')
