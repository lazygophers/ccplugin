# finish 剥离核对 — PRD (主入口)

## 目标
- [ ] finish 只负责收尾工作 (merge/销wt/标记/异步spec)
## 边界
- 不动 check 逻辑; 只改 finish 三处
## 验收标准
- [ ] finisher 去 subtask 完成度核对
- [ ] finish SKILL 去验收/subtask 退回门
- [ ] mmd finish 节点去完成度检查
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-finish-scope`)
