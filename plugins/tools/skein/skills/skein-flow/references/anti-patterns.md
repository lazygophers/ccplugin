# ⛔ 反例 (命中 = 流程错误)

| 禁 | 改为 |
|---|---|
| main 直接改源码 / 跑 check (非特别例外) | 派 subagent 在 worktree 内 |
| 把 skein.py 派 agent 执行 | main 同步跑 |
| inline 跳过 task | 一律走闭环 (本 skill 全部意义) |
| 极简请求 (纯查询 / 单文件 ≤20 行) 强建 task | 该 inline 的 inline |
| check 未过推进 finish / 未 archive 宣告 Done | 先修复重检 / 未闭环 |
| 口头宣称「已派 agent / 已建 task」但无 tool_use | 先真实调用再回传 |
| exec subagent 在主工作区改源码 (无 worktree) | 必在 task worktree |
| 直接 Edit/Write `.skein/task.md` | 经 `skein.py board` |
| 纯文本提问代替 `AskUserQuestion` | 用工具 |
| exec 阶段问用户「先做哪个」 | 顺序归 planning |
| sediment 判定未输出 trace | 逐项 ✅/❌ 输出 |
