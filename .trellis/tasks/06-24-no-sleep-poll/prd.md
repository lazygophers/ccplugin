# PRD — 禁 workflow sleep 轮询: 明确异步语义

## 背景 / 问题

trellisx 升级 Claude Code Workflow 执行 exec 时, AI 自发出现反模式:

```
Bash(sleep 120 && echo done)
```

根因: AI 把**异步** Workflow 当同步等待。Claude Code `Workflow` 工具本就异步 (调用即返回 task ID, 完成时 `<task-notification>` 自动回调)。正确做法 = 调用后**结束本回合**, 等 notification 再继续 finish 清理。

触发点: trellisx-flow finish 段要求 "finish 前确认 workflow 已终止 (TaskList 查 / TaskStop 关)", 但**未禁 sleep/轮询**, AI 为"等 workflow 跑完"就脑补 sleep 阻塞 main。

确认: 整个 trellisx (skills/scripts/README) 无任何 `sleep` 指令 —— 是文档缺约束导致 AI 钻空, 非 trellisx 主动要求。

## 目标

在 trellisx 文档补硬规: **Workflow 异步, 禁 `sleep`/轮询阻塞 main; 调用即结束回合, notification 回来再继续 finish**。

## 范围 (待 exec 阶段确认精确行)

- `skills/trellisx-flow/SKILL.md` — workflow 骨架段 (L55-93) + finish 段 (L95) + 失败模式表
- `skills/trellisx-apply/references/workflow-injection.md` — 注入用户项目 `.trellis/workflow.md` 的 in_progress / finish snippet (这是 AI 实际执行时读的产物, 必须同步加约束)
- 其余出现 "Workflow / 后台 Task / finish 清理" 语义处按需补一句

## 验收标准

1. flow SKILL.md + workflow-injection.md 注入 snippet 均含明确约束: Workflow 异步 / 禁 sleep 轮询 / 调用即结束回合等 notification
2. 措辞锚定行为 (禁 `sleep`、禁轮询 main 阻塞), 不只泛泛说"异步"
3. 经 CLAUDE.md 规定的 `claude -p` 验证: AI 能正确识别"禁 sleep 等待 workflow"语义
4. 不破坏既有 marker / 标签结构

## 非目标

- 不改 workflow 骨架的 phase/parallel/retry 逻辑
- 不改 scripts (sleep 问题是文档层, 非脚本层)
