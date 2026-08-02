# for-exec — exec 阶段作业手册

exec 只管 main 调度编排：claim exec 占槽、派 `skein-executor`、处理回传、失败自愈、全 done 后进入 check。单个 subtask 怎么读需求、怎么改、怎么 done/fail，归 `plugins/tools/skein/agents/skein-executor.md`。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=exec`，或 flow 内 plan 收敛后自动进入。
- **前置**: task 必须已经 `skein confirm` 过人审门并处于「进行中」。
- **出口**: 全部 subtask done 后立即进入 check；exec 不做验收、不勾 PRD。

## main 流程

1. 读当前 open task 队列；待处理且 ready 的 task 先走 confirm，人审门未过则回 plan。
2. 对进行中 task 运行 `skein claim exec`，由命令占槽并把 ready subtask 标 running。
3. 对 claim 返回的每个 subtask，立即派 `Agent(subagent_type="skein:skein-executor")`。
4. dispatch prompt 只传 task id、subtask id、工作目录。详细字段由 executor 自读 `subtask show`。
5. executor 回传 done/fail 后，main 再 claim 下一批；有槽就派，不等整批结束。
6. 所有 subtask done 后，进入 check。

## main 保留职责

- 维护 `pools.work` 并发，不让 pending/failed subtask 绕过 claim 直接派发。
- 转达 executor 返回的 `需要:`；信息不足时不标 done。
- subtask fail 后做自愈决策：重派、补修复 subtask、或停手上报。
- 发现超出当前 task 边界的新问题，另建 task；不塞进当前 task 扩 scope。
- 异步等待时输出在跑任务清单。

## main 完成判据

- [ ] 每个 ready subtask 都已 claim 后真实派发，或已 done/fail。
- [ ] `skein claim exec` 返回空。
- [ ] 无 depends_on 死锁。
- [ ] 全部 subtask done 后已进入 check。
- [ ] 有异步在跑时已输出任务清单。

## 失败模式

| 触发 | 一线处理 | 兜底 |
|---|---|---|
| executor 返回 `需要:` | main 补信息或转达用户后重派 | 信息仍缺则挂起该 subtask |
| subtask fail | 定点重派 ≤2 轮，或补根因修复 subtask | 仍失败则停手走根因复盘 |
| claim 返回空但仍有 pending | 查槽位、depends_on、环 | DAG 问题回 plan 修 |
| 发现 scope 外问题 | 新建 task 排队 | 禁扩当前 task |
