---
name: skein-redo
description: "SKEIN 断点续跑。session 意外结束后重新调度未完成的 agent, 继续 main 尚未闭环的工作。不等同复位 — running subtask 不强制 fail, 只补派未完成的调度。无参数 = redo 全部 (补派全部孤儿 subtask + 逐个推进 plan task) 并继续按 skein-flow 流程闭环; 有参数 = 只续跑该 task。"
user-invocable: true
argument-hint: "[任务ID] (缺省 = redo 全部并续推 flow)"
arguments: "[任务ID]"
model: sonnet
effort: medium
---

session 意外结束 (崩溃 / 手动中断 / context 满) 后恢复。不是回滚也不是复位 — 而是接上断点继续闭环。

**参数缺省 = redo 全部**: 对全部未完成 task 补派 + 续推, 不是只看某一个; 有 `[任务ID]` 时只处理该 task 链 (含其未完成前置, 见 flow-loop.md 前置链规则)。

1. 查当前有哪些 running subtask / research (孤儿探测入口)
	`! skein subtask list all --status running | jq -r '(.subtasks // []) | if length == 0 then "no subtask" else .[] | [.tid, .sid, .name] | @tsv end'`
	`! skein research list <tid>` (按 task 逐个跑一路; research 任务存 research_tasks[], `subtask list` 只遍历 subtasks[] 不含, 漏跑这路则调研中孤儿全部漏检)
2. 孤儿判据: 条目 running 且派发后**无回传且超过预期时长** (对照 estimate/派发时间) 即判孤儿; running subtask ↔ agent 对应关系无判据, 不依赖 TaskList/AgentList 类查询反查
3. 对判为孤儿的 running subtask/research, 重新 Agent 调度补派 (dispatch hint 照 `skein flow run` 回显)
4. 槽位还有空闲 → 继续按 `skein flow run` 回显派发剩余可调度 subtask (不等孤儿跑完才补位)
5. 查看当前有哪些 plan task
	`! skein list --status plan | jq -r '(.tasks // []) | if length == 0 then "no task" else .[] | [.id, .name] | @tsv end'`
6. 对每一个 plan task 依次走完整 Skill('skein:skein-plan') → confirm → 纳入执行
7. 以上全部接续后, 转入 Skill('skein:skein-flow') 的 exec→check→finish 循环继续闭环, 直到全部 task finish (无参) / 指定 task finish (有参)。转 flow 时, flow 前置的孤儿检测步骤 (检测到孤儿 running subtask 先转 skein-redo) 因刚跑过本流程直接跳过
