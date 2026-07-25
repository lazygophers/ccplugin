# plan 阶段完成判据标注 — PRD (主入口)

## 目标
- [x] 在 skein-plan SKILL.md 流程末尾 (步骤 7 后) 加 '## ✅ plan 阶段完成判据' section, 列 4 条勾满才转 exec 的判据 (task 已 create / prd 已填完 / subtask 已规划 / 设计方案已定或 main 豁免)
## 边界
范围内 / 范围外 (非目标) / 已知约束:
- 仅 skein-plan SKILL.md 一处; skein-flow plan 段加一行指针指向 skein-plan 判据段
## 验收标准
可执行、可核对的完成断言 (逐条):
- [x] skein-plan SKILL.md 含 '## ✅ plan 阶段完成判据' section 含 4 条 checklist
- [x] skein-flow SKILL.md plan 段指向 skein-plan 判据段
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list plan-done-criteria`)
