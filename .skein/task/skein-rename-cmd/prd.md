# skein rename 命令 — PRD (主入口)

## 目标
- [ ] 加 rename 命令重命名 task/subtask 的 id 与 name
## 边界
- 范围内: rename 方法+parser+dispatch+MUTATING+tests
- 范围外: active task 改 id (仅 pending); prd 内脚手架文本重写
## 验收标准
- [ ] rename task name/id + subtask sid/name 各生效且跨引用同步
- [ ] 非 pending 改 id 报错
- [ ] pytest 全绿
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-rename-cmd`)
