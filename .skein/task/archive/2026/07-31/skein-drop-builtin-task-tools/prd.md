# 移除 skein 插件对 harness 内置 task 工具的用法与拦截 — PRD (主入口)

## 目标
要解决什么 / 用户价值 / 成功长什么样:

- [ ] `plugins/tools/skein` 全仓不再出现 harness 内置 task 工具名 (`TaskCreate` / `TaskList` / `TaskStop` / `TaskUpdate` / `TaskGet` / `TaskOutput` / `TodoWrite`)，无论是调用、授权还是拦截
- [ ] A 类 (调用)：`skein-finisher` 不再持有也不再调用 `TaskList` / `TaskStop`；「finish 前清掉本 task 悬挂的后台 agent」这项要求不丢失，改由 main 在派 finisher 前承担
- [ ] B 类 (拦截)：删除 `TaskCreate` 拦截 hook 全链路 (脚本实现 + 插件注册 + 文档)，skein 从此不干预 harness 建 task
- [ ] skein 侧文档描述能力要求时只写「要达成什么状态」，不具名任何 harness 内置工具 —— 用什么工具达成交给 main 的 harness

## 边界
范围内 / 范围外 (非目标) / 已知约束:

- [ ] 范围内：`plugins/tools/skein/agents/skein-finisher.md`
- [ ] 范围内：`plugins/tools/skein/skills/skein-flow/` 下 `SKILL.md` 与 `references/for-finish.md`、`references/scope-boundary.md`
- [ ] 范围内：`plugins/tools/skein/scripts/hooks.py`、`.claude-plugin/plugin.json`、`docs/skein.md`、`docs/reference.md`
- [ ] 范围外：skein 自有的 task 概念与 `skein.py` 生命周期命令 (`create`/`start`/`finish` 等) 一律不动 —— 本次只清 harness 内置工具，不碰 skein 自己的 task 语义
- [ ] 范围外：`.skein/` 工作区数据、其余 6 个插件、`skills/` 目录
- [ ] 范围外：`docs/reference.md` 里 `subagent-start` / `session-context` 两条与 DISPATCH 不符的陈旧记载，属既有问题，本次不顺手修
- [ ] 约束：finish 阶段的闭环判据不得因此放宽 —— 「悬挂后台 agent 未清 = 未闭环」这条要求保留，只换承担者
- [ ] 约束：删除 `TaskCreate` 拦截后，hooks.py 的 `DISPATCH` 表、模块 docstring、`_CTX` 上方注释中的相关记载需同步清干净，不留悬空引用

## 验收标准
可执行、可核对的完成断言 (逐条):

- [x] `grep -rn -E 'TaskCreate|TaskList|TaskStop|TaskUpdate|TaskGet|TaskOutput|TodoWrite' plugins/tools/skein --include='*.md' --include='*.py' --include='*.json'` 零命中 (排除 `.mypy_cache` / `.ruff_cache`)
- [x] `skein-finisher.md` frontmatter `tools:` 为 `Read, Bash, Grep, Glob`，工作流步骤连续重编号无断号
- [x] `skein-finisher.md` 的返回 JSON 结构与 `dangling` 语义保持可用，仅去掉后台 agent 一项的自清描述
- [x] `skein-flow` 的 finish 阶段文档中，「清悬挂后台 agent」已标为 main 职责且措辞不含任何内置工具名
- [x] `hooks.py` 中 `cmd_task_created` 函数、`DISPATCH` 里的 `task-created` 键、模块 docstring 对应行、`_CTX` 上方注释里的相关句全部删除
- [x] `plugin.json` 中 `TaskCreated` 钩子块已删除，且文件仍是合法 JSON (`python3 -m json.tool` 通过)
- [x] `docs/skein.md` 的 hook 表与 Guards 表、`docs/reference.md` 的 hook 表中相关行已删除
- [x] `python3 plugins/tools/skein/scripts/hooks.py` 无参运行时用法行不再列出 `task-created`
- [x] `skein doctor` 通过 (exit 0)
- [x] 改动已 commit (不 push)

## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-drop-builtin-task-tools`)
