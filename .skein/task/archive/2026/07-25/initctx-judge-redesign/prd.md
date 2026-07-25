# _INIT_CTX 判定依据重设计 (调研→定方案) — PRD (主入口)

## 目标
- [x] 调研外部项目 (trellisx/matt pocock skills/其他任务编排插件) 的 UserPromptSubmit 判定逻辑 + skein 当前 _INIT_CTX 误判案例, 产出 findings.md 给出重设计方向建议 (判定依据从复杂度→改动类型/或其他)
## 边界
- 范围: 只调研 + 出方案, 不改 hooks.py 代码
- 范围外: 方案定后另起 task 实施
- 已知约束: 调研落 .skein/task/initctx-judge-redesign/research/findings.md
## 验收标准
- [x] findings.md 含: ① 各项目判定逻辑对比表 ② skein 当前误判案例 (>=3 例, 含本会话 0d749f6c) ③ 新判定依据方向建议 (>=2 候选 + 利弊)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list initctx-judge-redesign`)
