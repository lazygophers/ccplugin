# 作用域边界与完成判定

skein-flow 的作用域判定 (何时建 task / 归一 vs 分立 / worktree 豁免) 与完成判定。判定表见主文件「作用域边界」段, 本文件展开细则。

## 归一 vs 分立 (相关工作优先归一 task 拆 subtask)

建 task 前先判新交付物是**某任务的一部分**还是**独立任务** —— 与现有 active task 或本请求内其他交付物**相关** (同目标 / 同模块 / 共享改动面 / 互为前置) → **归一到该 task 拆 subtask** (`subtask add` + `--deps`), 禁为相关工作另开多个 task; 仅**目标独立、无共享改动面、无依赖**才拆多 task。判据是相关性, 非「可独立验收」(subtask 亦可独立验收)。默认倾向归一 (散多 task 丢共享上下文一致性)。判不准 → `AskUserQuestion`。真值源见 `skein-plan` 步骤 1。

## worktree 豁免 (简单改不必上升到 worktree)

main 按规模自动判 — 命中「单文件单处改 ≤20 行」或「单子 git ≤3 文件且改动集中」这类微改, 无需建 task/worktree, 原地做即可; 用户显式 `--skip` 强制 inline 覆盖自动判定。多子 git 场景同理: 真跨多仓的结构性改动才 `--repos` 声明走多 worktree, 每仓只沾一两行的顺带微调不必为它单开 worktree。

## 完成判定

- 走完 plan→exec→check→finish — **未 archive = 未完成, 禁宣告 Done**。
- finish 前清理悬挂 subagent / 后台任务 (`TaskList`/`TaskStop`), 未关 = 未闭环。
- sediment: 有可复用 learning 才沉淀, 无则跳过 (判定见 `skein-memory`)。
