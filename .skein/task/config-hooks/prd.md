# config.yaml 自定义 hooks (阶段钩子 + agent start/stop) — PRD (主入口)

> 禁写具体文件路径与代码片段 (会很快过期) —— 例外: prototype 产出的能精确编码决策的片段 (状态机/schema/type shape) 可内联, 且须注明来自 prototype。

## 目标
要解决什么 / 用户价值 / 成功长什么样:
- [ ] 让用户能在 `.skein/config.yaml` 里声明式挂自定义命令, 无需改插件代码
- [ ] 两类钩子: **阶段钩子** (skein 状态迁移命令的 before/after) + **agent 钩子** (agent 开工/收工)
- [ ] agent 钩子走 **dispatch 参数**实现 (agent 在工作流 step 0 / step 5 自调), 不走 harness hook 机制 —— 原因见边界约束
- [ ] 成功长什么样: 用户在 config.yaml 写几行就能让 `check` 前自动跑 lint、agent 收工自动跑格式化; 无 hooks 配置时零开销零行为变化

## 边界
范围内 / 范围外 (非目标) / 已知约束:
- [ ] 范围内: `_yaml_load` 嵌套支持 / 统一钩子执行器 / 9 个阶段命令接入 / `agent-start`+`agent-stop` 子命令 / 9 个 agent 工作流加两步 / 文档 / 测试
- [ ] 范围外: **改 `plugin.json`** (用户明确排除) —— 故不用 `SubagentStart`/`SubagentStop` harness 事件
- [ ] 范围外: **agent 文件投影到 `.claude/agents/`** (用户明确排除)
- [ ] 范围外: agent frontmatter 写 `hooks:` 字段 —— plugin subagent 的该字段被 harness **静默忽略** (官方文档: 出于安全原因 plugin subagents 不支持 hooks/mcpServers/permissionMode), 写了是误导
- [ ] 约束: 纯 stdlib, 禁引 pyyaml
- [ ] 约束: **配置真值来源唯一** (core 规则) —— hooks 必须在 config.yaml, 不另开配置文件
- [ ] 约束: `subprocess` 必设 timeout/cwd/capture_output (core 规则)
- [ ] 约束: **信任模型** — config.yaml 是用户手写本地文件, 信任级别等同用户在终端敲命令, 故 hook 命令用 shell 执行 (与 Claude Code 自身 hooks 一致)。这不违反「exec 端点禁 shell 注入」那条 core 规则 (信任边界不同: 那条针对网络输入)
- [ ] 约束: **正因上一条, http 配置写端点必须硬排除 `hooks` 键** —— 否则远程可写 shell 命令 = RCE

## User Stories
极其详尽地穷举, 覆盖功能各方面 (含边界情况) —— 穷举本身就是逼出边界情况的机械手段:
1. As a 使用者, 我想在 check 阶段前自动跑 lint, 以便质量问题在进 check 前就暴露
2. As a 使用者, 我想让 before 钩子失败时阻断该阶段, 以便钩子成为真正的质量门而非装饰
3. As a 使用者, 我想让 after 钩子失败只告警不阻断, 因为阶段已完成回滚代价大于收益
4. As a 使用者, 我想用 `continue_on_error` 覆盖上述默认, 以便个别钩子按我的意图处置
5. As a 使用者, 我想给每条钩子设 timeout, 以免钩子挂住卡死整个流程
6. As a 使用者, 我想让钩子默认在 task 工作目录执行, 以便与 agent 的工作目录一致 (最小惊讶)
7. As a 使用者, 我想用 `cwd` 覆盖执行目录, 以便个别钩子在仓库根跑
8. As a 使用者, 我想在钩子里拿到当前 tid/sid, 以便钩子知道自己在为哪个任务工作
9. As a 使用者, 我想通过环境变量而非模板插值拿上下文, 以免命令拼接引入注入面
10. As a 使用者, 我想给指定 agent 配 start/stop 钩子, 以便只对执行器做准备/清理
11. As a 使用者, 我想用 `"*"` 给所有 agent 配统一钩子, 以免逐个重复配
12. As a 使用者, 当具名与通配同时命中时, 我想具名先跑, 因为具体优先于通配符合直觉
13. As a 使用者, 我想让 agent 钩子失败不影响 subtask 成败, 因为我的钩子挂了不该让任务失败
14. As a 使用者, 我想在多条钩子中前一条失败时后续停跑, 以免在错误状态上继续
15. As a 使用者, 我想看到失败钩子的定位前缀 (哪个 scope/when/第几条), 以便一眼知道改哪里
16. As a 使用者, 我想在 config.yaml 没有 hooks 键时一切照旧, 以便升级插件零风险
17. As a 使用者, 我想写错阶段名时立刻收到报错并看到合法值清单, 以免钩子无声失效
18. As a 使用者, 我想写了不支持的 YAML 语法时收到报错并看到行号, 以免配置被静默降级
19. As a 使用者, 我想在钩子里调 skein 命令而不触发无限递归, 以便钩子能查询任务状态
20. As a 维护者, 我想让两类钩子共用同一执行器, 以免两份实现漂移
21. As a 维护者, 我想让无 hooks 配置时不解析深层不 fork 进程, 以免钩子机制拖慢每次状态迁移
22. As a 安全负责人, 我想让 http 配置写端点拒绝写 hooks 键, 以免远程写入 shell 命令造成 RCE
23. As a 使用者, 我想在 doctor 里看到「配了 agent 钩子但从未被触发」的提示, 以便发现 agent 漏跑钩子

## 验收标准
可执行、可核对的完成断言 (逐条):

### YAML 解析
- [ ] `_yaml_load` 支持 ≥4 层嵌套 dict + `- ` list of dict + 标量(str/int/bool) + `#` 注释 + 带引号的键 (如 `"*"` 解析为 `*` 而非 `"*"`)
- [ ] 不支持的语法 (锚点 `&`/`*ref` / 多行 `|`/`>` / 流式 `{}`/`[]` / 多文档 `---`) → **报错并指明行号**, 禁静默降级
- [ ] `_yaml_dump` 能写回嵌套结构且 `_yaml_load(_yaml_dump(d)) == d` (往返一致)
- [ ] 现有扁平配置读写行为**零变化** (全部现有 config 测试仍绿)

### 配置面
- [ ] `hooks` 键进 `CONFIG_DEFAULTS` 默认 `{}`; `config` 无参展示与 `--json` 均能正确呈现嵌套 hooks
- [ ] `config set hooks...` 类操作被拒 (嵌套结构不走 set, 需手改文件), 报错说明清楚
- [ ] **http 配置写端点拒绝 `hooks` 键**, 返回明确错误

### 阶段钩子
- [ ] 支持阶段: `create` / `confirm` / `start` / `check` / `finish` / `archive` / `subtask.start` / `subtask.done` / `subtask.fail`
- [ ] `before` 失败 (非零退出) → **阶段命令退出非零, 阶段不发生**
- [ ] `after` 失败 → 仅 stderr 告警, 阶段结果不变
- [ ] `continue_on_error: true` 使 before 失败不阻断; `false` 使 after 失败阻断
- [ ] 列表内严格串行, 前一条失败即停 (除非该条 `continue_on_error`)
- [ ] 非法阶段名 → 报错并列出全部合法阶段名
- [ ] `timeout` 缺省 60 秒; 超时按失败处置且错误信息含「超时」与秒数
- [ ] `cwd` 缺省 = task 工作目录 (worktree 启用则 worktree, 否则仓库根); 可被 `cwd` 覆盖
- [ ] 输出带 `[hook <scope>.<when>#<N>]` 前缀

### agent 钩子
- [ ] `hooks.py agent-start --agent <name> --tid <tid> --sid <sid>` 执行 `hooks.agent.<name>.start`
- [ ] `agent-stop` 同理执行 `.stop`
- [ ] `"*"` 通配生效; 具名与通配同时命中时**具名先跑**
- [ ] agent 钩子失败 → **只告警不阻断** (返回 0), 不影响 subtask 成败
- [ ] 9 个 agent 的工作流各含 step 0 (agent-start) 与收尾 step (agent-stop, 在 subtask done/fail 之后), Checkpoints 有对应铁律
- [ ] agent frontmatter **不含** `hooks:` 字段 (会被 harness 忽略, 写了是误导)

### env 与安全
- [ ] 注入 `SKEIN_SCOPE` / `SKEIN_WHEN` / `SKEIN_AGENT` / `SKEIN_TID` / `SKEIN_SID` / `SKEIN_TASK_DIR` / `SKEIN_WORKTREE` / `SKEIN_REPO_ROOT` / `SKEIN_IN_HOOK`
- [ ] 上下文**只经 env 传递, 无模板插值** (禁字符串拼接进命令)
- [ ] `SKEIN_IN_HOOK=1` 时嵌套钩子被跳过 (Recursion Guard), 钩子里调 skein 命令不无限递归

### 零开销与兜底
- [ ] 无 `hooks` 键时: 不解析深层结构、不 fork 任何进程、状态迁移命令耗时与改前无显著差异
- [ ] `doctor` 能报「配了 agent 钩子但 `.audit-log` 中从未触发」
- [ ] `uv run pytest plugins/tools/skein/scripts/tests/` 相对本 task 开始时的基线不新增失败

## Testing Decisions
什么算好测试 (只测外部行为不测实现细节) / 测哪些模块 / codebase 内的同类测试先例:
- [ ] **只测外部可观测行为**: 命令退出码 / stdout+stderr 文本 / 钩子进程是否真的跑了 (用钩子写标记文件断言) / 配置往返一致性。禁断言私有方法调用
- [ ] **接缝 = CLI 命令边界**, 用 `tmp_path` 造临时工作区经真实 CLI 子进程跑 —— 复用 `tests/conftest.py` 既有的 `skein_cli`/`ws` fixture, 不新建
- [ ] 钩子命令用 `echo`/`touch`/`exit 1` 这类零依赖 shell, 不依赖 npm/git 等外部工具
- [ ] 先例: `tests/test_config_cli.py` (config CLI 行为) · `tests/test_statemachine.py` (状态迁移经真实 CLI) · `tests/test_spec.py` (tmp_path 直调)
- [ ] `_yaml_load` 的嵌套/报错/往返**单独一个测试文件**, 因为它是本 task 唯一高风险项, 要能独立回归
- [ ] 零开销验证走行为断言 (无 hooks 键时钩子标记文件不存在), 不做性能计时 (不稳定)

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list config-hooks`)
