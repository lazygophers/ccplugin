# exec/check/finish 下沉到 agent + 剥离 subtask agent 绑定 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] subtask 不再绑定 agent — 删 `--agent` 参数与 task.json `agent` 字段, exec 一律用 `skein-executor`
- [ ] exec/check/finish 三阶段作业内容下沉到对应 agent md, flow 只留「调用哪个 agent + 入参」
- [ ] agent md 内写明具体 skein 命令 (非抽象描述), 省 dispatch prompt token
- [ ] 新增 `skein subtask show <tid> <sid>` — agent 自读 subtask 详细要求, 不靠 main 在 prompt 转抄

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `plugins/tools/skein/` 下 scripts/skein.py、agents/{executor,checker,finisher}.md、skills/skein-flow/{SKILL.md,references/}、assets/webapp、docs/、README.md
- [ ] 范围外: trellisx 插件 (独立实现, 口径自持); 其余六个 agent 职责不动
- [ ] 保留边界 (用户已裁定, 不下沉):
  - `claim` 占槽留 main (max_active 并发上限靠它)
  - executor 缺信息仍标 `需要:` 回传 main 转达用户 (subagent 无 AskUser)
  - check 失败后的 grill/AskUserQuestion 方向确认 + 补修复 subtask + 重派 留 main
  - sediment/auto-fix 派 `skein-specer` 留 main (Agent 工具 + 递归护栏)
- [ ] 已下沉授权 (用户已裁定):
  - executor: 自跑 `subtask done/fail`、读 + **直接写** spec
  - checker: 自跑 `skein check <id>` 状态切换 + 全部验证 + `skein prd check` 验收回写
  - finisher: 加 `TaskList`/`TaskStop` 工具清悬挂 + **在仓库根**跑 `skein finish <id>` (避免自销 worktree)
  - dispatch prompt 瘦为 `tid + sid + 工作目录` 三参数, 其余全由 agent 自读 (`subtask show`) + agent md 自带; 废除「6 字段自包含 prompt」在 exec 派发处的转抄要求
  - `--skills` 字段保留 (executor 自读后自行加载对应 skill)
- [ ] 已知约束: 本次改的就是 skein-flow 自身, 边改边用有自引用风险 — 改动落盘后当前会话不重载 skill

## 验收标准
可执行、可核对的完成断言 (逐条):
- [ ] `skein subtask add` 不再接受 `--agent`; `--help` 无该参数; 新建 subtask 的 task.json 无 `agent` 键
- [ ] `skein doctor` 不再把缺 `agent` 判为错 (必填集 = sid/name/desc/estimate)
- [ ] `skein subtask show <tid> <sid>` 输出该 subtask 全字段 (name/desc/status/estimate/deps/skills/验收/note), 不存在的 sid 报错退出
- [ ] 看板 task.md、webapp、web API 出参不再含 agent 列/字段
- [ ] `skein-executor.md` 含具体命令行: `skein subtask show`、`skein subtask done/fail`、`skein-spec recall` 与写盘
- [ ] `skein-checker.md` 含 check 全流程具体命令 (`skein check`/`skein prd read`/`skein subtask list`/`skein contract`/`skein prd check`)
- [ ] `skein-finisher.md` 含 finish 全流程具体命令 (git diff/status、TaskList/TaskStop、仓库根 `skein finish`), tools 加 TaskList/TaskStop
- [ ] `for-exec.md`/`for-check.md`/`for-finish.md` 瘦为「触发 + 派哪个 agent + 入参 + main 保留项」, 作业细节不重复
- [ ] SKILL.md 三阶段段落同步瘦身, 与 references 无重复真值源
- [ ] pytest 全绿 + webapp 3 个 check.mjs 全绿
- [ ] 全仓无 stale 引用 (`--agent`、`s.agent`、「按 subtask 关联 agent dispatch」表述)

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list agent-sink`)
