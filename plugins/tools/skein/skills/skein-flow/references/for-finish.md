# for-finish — finish 阶段作业手册

finish 是 check 全绿后的收尾门。main 只负责确认可派、派 `skein-finisher`、读结果、处理失败、派异步 spec 收尾。勘察改动和执行 `skein finish` 归 `plugins/tools/skein/agents/skein-finisher.md`。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=finish`，或 flow 内 check 全绿后自动进入。
- **前置**: check 阶段完成判据全绿。
- **禁止**: 未 finish 闭环不得宣告 Done。finish 不重做验收。

## main 流程

1. 确认本 task 派出的后台 agent 都已结束；未结束则等待或停手。
2. 派 `Agent(subagent_type="skein:skein-finisher")`，prompt 只给 task id + 工作目录。
3. 读取 finisher JSON 回传。
4. `verdict=收尾干净`：视为 `skein finish` 已成功，进入 spec 收尾。
5. `verdict=需处理`：按 `dangling` / `tool_failures` / `needs_main` 处理后重派 finisher，或停手上报。
6. finish 成功后异步派 `skein-specer` 做 sediment / product amend。
7. 检测 `.skein/spec/.pending-fix`；存在则异步派 `skein-specer` 跑 `skein-spec maintain --apply`。

## main 完成判据

- [ ] finisher 已真实派发并回传。
- [ ] finisher verdict=收尾干净。
- [ ] `skein finish` 已成功，task 已标 done。
- [ ] sediment / product amend 已异步派出。
- [ ] `.pending-fix` 已检测；有则 auto-fix 已异步派出。

## 失败模式

| 触发 | 一线处理 | 兜底 |
|---|---|---|
| 后台 agent 未结束 | 等待或人工中止 | 禁派 finisher |
| finisher 报悬挂残留 | main 清理后重派 | 清不掉则停手上报 |
| `skein finish` merge 冲突 | 读冲突文件，手动解后重派 | 解不开则保留现场上报 |
| finisher 报无改动 | main 核实是否误派 | 误派则停手排查上游 |
| spec 收尾失败 | 记录为异步失败，不回滚 finish | 后续单独修 spec |
