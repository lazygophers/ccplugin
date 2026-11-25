# subagent 没有 Skill 工具：派单 prompt 别让它调 Skill，把 skill 内容路径抄进去

派 subagent 干需要某个 skill 知识的活，prompt 里不要写「先调 Skill(xxx)」——
subagent 工具集里没有 Skill，它只会回一句「调不了，我用别的方式替代」，白耗
一轮。要的是 skill 的知识就直接给：SKILL.md 的绝对路径让它 Read，或把关键
结论抄进 prompt（本仓惯例：`.scratch/research/` 里的调研报告路径 + 一句「这是
唯一数据格式依据」）。

顺带写明票面文件的去向：ticket 在主仓 `.scratch/<feature>/issues/`（gitignored），
worktree 里的 agent 改主仓票面直接改、无需 commit。
