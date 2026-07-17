# 执行载体铁律

skein-flow 全流程的载体层强制规则 (最高优先级)。每条都不可妥协, 违反即流程错误 (见主文件「反例」段)。

- **「派 agent」= 真实调用 `Agent` 工具, 不是叙述**。每个「派 agent」动作 MUST 在同一回复产生真实 tool_use。禁在无 `Agent` 调用时回传「已派出 / 在做」— 宣称 ≠ 调用 = 幻觉跳步。task/看板/worktree 的「已建」同理必须是真跑过命令的结果。
- **main 默认禁写源码** — 改源码为该 subtask 选合适 agent (无则 `skein-executor`), 跑 check 派 `skein-checker`。仅特别情况例外 (≤3 文件微改 / 上下文密集决策 / 用户显式要求), 且必在 task worktree 内。
- **exec / check 分工, main 作调度器** — exec: 为每个 subtask 选合适 agent (无则 `skein-executor`) 各执行 1 个 (并发上限 2 / 完成即派 / 共享 task worktree); 执行 agent 由 dispatch prompt 硬禁再派 subagent (Recursion Guard, 自己做完 1 个 subtask)。check: 派 `skein-checker` (工具受限, 无 Write/Edit/Agent/Task 的具名 agent)。调度算法详见 `skein-exec` skill, check 详见 `skein-check`。
- **有 task 必有 worktree** — task 在其 worktree 内执行 (`skein start` 自动建), 主工作区零改动; 默认 1 task 1 worktree。finish 后自动销。**多子 git**: 改动跨多个子 git (并列独立 repo 或 submodule) 时, planning 阶段用 `skein create --repos <rel路径,逗号分隔>` 声明目标子 git (root 用 `.`); `start` 为每个声明的子 git 各建 1 worktree+分支, `finish` 各自 commit→merge→销。声明留空 = 单根/原地模式 (原行为)。子 git 集合由 planning 声明, 不靠脚本猜。
- **`skein` 由 main 同步跑** — create/start/finish/archive 是任务记录管理, main 直接跑, 不派 agent、不算实质工作。
- **看板自动刷** — task.json 每次变更 (create/start/subtask/finish) 脚本自动渲染 task.md/task.html, 无需手动跑命令; AI 禁直接编辑 (guard hook 硬阻)。
- **用户交互决策 main 亲做** — `AskUserQuestion` (判新旧不准 / 产物评审 / scope 澄清) subagent 不能与用户对话; subagent 缺信息在返回标 `需要: <问题>` 由 main 转达。
- **文案/格式类变更先给样例确认** — subtask 属**文案** (措辞 / 标签 / 提示语 / 文档表述) 或**格式** (排版 / 展示样式 / 结构布局) 类改动时, main 亲自先给用户「改前→改后」样例 (`AskUserQuestion` 或列对比), 确认后才落地; 逻辑 / bug 修复不受此限。派执行 agent 做此类改动时, dispatch prompt 须注明「先回传样例待 main 确认, 禁直接改」。
- **每个 dispatch prompt 6 字段自包含**: 目标 / 已知 (含 `Active task: <id>` + worktree 路径) / 工作目录与范围 / 输出格式 / 验收标准 / 失败处理。缺字段不派。
- **完成即时回传** — 每个 subagent 完成或阻塞, main 立即输出摘要, 禁批量延迟汇总。
- **并发多个 flow 请求禁互相顶掉** — 每个 flow 请求 = 独立 durable task, **收到即先 `skein create` 落盘**再处理。第二个请求进来时**禁中断/覆盖/丢弃**在飞的第一个: planning 阶段本就需 main 同步逐问用户 (brainstorm/grill/AskUserQuestion 不能并行), 故多请求**串行 planning** — 先把当前 task 登记 + 推进到不丢的态 (至少 `create` 落盘), 再处理下一个。已 `create` 未处理完的 task 留 pending, 由 `/skein-exec` 无参续跑, 绝不静默跳过。
