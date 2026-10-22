# subagent 没有 Skill 工具：派单 prompt 别让它调 Skill，把 skill 内容路径抄进去

派 subagent 干需要某个 skill 知识的活，prompt 里不要写「先调 Skill(xxx)」——
subagent 工具集里没有 Skill，它只会回一句「调不了，我用别的方式替代」，白耗
一轮。要的是 skill 的知识就直接给：SKILL.md 的绝对路径让它 Read，或把关键
结论抄进 prompt（本仓惯例：`.scratch/research/` 里的调研报告路径 + 一句「这是
唯一数据格式依据」）。

顺带写明票面文件的去向：ticket 在主仓 `.scratch/<feature>/issues/`（gitignored），
worktree 里的 agent 改主仓票面直接改、无需 commit。

出处：2026-10-22 watchtower session，ticket 02 agent 回报「本 subagent 无 Skill
工具，Skill(plugin-authoring) 调不了；用它的同一参照替代」——派单 prompt（transcript
d5852c1b L816）写了「开工先调 Skill(plugin-authoring)」，浪费一轮往返；同 session
ticket 01/04 的派单改成抄报告路径后无此问题。
