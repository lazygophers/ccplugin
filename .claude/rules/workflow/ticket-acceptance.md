# 验收 agent 完工的票：逐个 [x] 追证据，agent 自报的勾选不算数

implementer agent 回报「票完成」后，主对话验收固定四步，缺一不可：

1. **逐个 `[x]` 核证据**：grep 票面勾选，每个勾选必须在 agent 回报里找到对应的
   实跑输出（命令原文 + 结果数字）。回报里没有实跑输出支撑的勾选一律当未验：
   改回 `[ ]` 加尾注，或 SendMessage 让 agent 补验后再勾。
2. **重跑测试**：在 worktree 里重跑票面测试命令（如 `node --test …`），以输出里
   `# pass / # fail` 的数字为准，不信回报里的数字。
3. **核 commit 范围**：`git log <base>..<branch> --oneline` + `git show --stat`，
   改动文件严格等于票面；越界的打回。
4. **核票面状态**：grep `Status:` 确认 agent 真改了（含 `## Comments` 尾注），
   没改就自己改——但只补状态行，勾选仍按第 1 步处理。

agent 不会主动区分「验过」和「验不了但勾了」；spec 轴审查的价值就在抓这个，
别等到 code-review 才发现。

出处：2026-10-22 watchtower session 两次被抓：ticket 03 把「从 marketplace 安装
并确认装出副本可用」勾成 [x]，实测只覆盖模块加载与解析器，pane 核心功能未验
（code-review Spec 轴审查发现，fixer 把第 13 项改回 `[ ]` + 尾注）；ticket 01 漏做
票面第 4 条验收（locateTranscript），靠主对话验收 grep 抓出（transcript d5852c1b
L738）。四步走全的 ticket 04 无返工。
