# prd写入强制未勾 — PRD (主入口)

## 目标
- [ ] prd write/add 对目标+验收标准一律落 - [ ]
## 边界
- 不动 fmt (check 标记要保留); 不动 prd check 翻转命令
## 验收标准
- [ ] 输入含 [x] 时 write 后仍为 [ ]
- [ ] prd check 命令仍能翻 [x]
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list skein-prd-nocheck`)
