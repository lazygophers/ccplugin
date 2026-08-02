# for-check — check 阶段作业手册

check 是 exec 完成后、finish 前的质量门。main 只负责编排：派 `skein-checker`、读结果、失败后组织修复循环、全绿后放行 finish。验证细节归 `plugins/tools/skein/agents/skein-checker.md`。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=check`，或 flow 内 exec 全 subtask done 后自动进入。
- **前置**: task 必须处于「进行中」；状态切换 `skein check <id>` 由 `skein-checker` 自跑。
- **禁止**: exec / check / finish 阶段禁改 `design.md`。check 发现方案性冲突，回 planning 二次进入后再改。

## main 流程

1. 确认 task 处于「进行中」。
2. 派 `Agent(subagent_type="skein:skein-checker")`，prompt 只给 task id + 工作目录。
3. 读取 checker JSON 回传。
4. `verdict=PASS` 且无需 main 介入：进入 finish。
5. `verdict=FAIL | 冲突` 或存在 `needs_main`：回 planning 思维重审，必要时用 `AskUserQuestion`/grill 确认修复方向，再补修复 subtask 回 exec。
6. 修复 subtask 全 done 后，重派 checker。未全绿继续循环。

## main 完成判据

- [ ] checker 已真实派发并回传。
- [ ] checker verdict=PASS。
- [ ] checker 已处理验收回写；未回写项已列入 `needs_main`。
- [ ] FAIL/冲突 已先确认修复方向，再补修复 subtask。
- [ ] 全绿后只放行 finish，不在 check 宣告 Done。

## 失败模式

| 触发 | 一线处理 | 兜底 |
|---|---|---|
| checker 工具失败 | 按 `tool_failures` 定位，修环境或重派一次 | 仍失败则停手回传 |
| 孤立失败 | 回 planning 确认修复方向，补 1 个定点修复 subtask | 反复不过则走根因复盘 |
| 一致性冲突 / 方案性缺陷 | 回 planning 修 PRD/design/契约，再补修复 subtask | 冲突未全覆盖禁 finish |
| 修复 ≥2 轮仍 FAIL | 停止堆 subtask，按 root-cause-protocol 复盘 | 超出 task scope 则转人工 |
