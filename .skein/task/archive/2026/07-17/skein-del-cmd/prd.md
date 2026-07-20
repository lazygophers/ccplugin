# skein del/delete/remove 命令 (删 task + subtask) — PRD

## 目标
skein CLI 加删除命令 (`del` 主名 + `delete`/`rm`/`remove` 别名), 支持:
- `skein del <task-id>` — 删整个 task (task 目录 → trash)
- `skein del <task-id> <subtask-sid>` — 删单 subtask (task.json 移除条目)

## 边界
**内**: skein.py 加 del 命令 (CLI 注册 + handler); task 软删 (移 trash); subtask 移除; active task 先销 worktree+分支; --dry-run 预览
**外**: 不加 --hard 硬删 (用户未选); 不加 restore 命令 (后续 task); 不改 webapp UI (CLI only)
**决策** (用户确认):
- 软删: task 目录移 `.skein/trash/<id>.<YYYYMMDD>/`
- 默认直接删, `--dry-run` 预览不删
- 任意状态可删 (active 先销 worktree+分支再移 trash)
- subtask 删除 = task.json subtasks 数组移除条目 (不进 trash, 不可恢复)

## 验收标准
- [ ] `skein del <pending-task>` → task 目录移 `.skein/trash/<id>.<date>/`, task.json 全局列表移除
- [ ] `skein del <active-task>` → 先销 worktree + 删分支, 再移 trash (active 状态: 进行中/检查中)
- [ ] `skein del <task> <subtask-sid>` → task.json subtasks 移除该条目, 其他 subtask 不动, 看 board 自动刷
- [ ] `skein del <task> --dry-run` → 只打印将删什么, 不动盘
- [ ] `skein del <不存在task>` → 报错 task 不存在, exit 1
- [ ] `skein del <task> <不存在subtask>` → 报错 subtask 不存在, exit 1
- [ ] `delete`/`rm`/`remove` 别名等价 `del`
- [ ] 删除后 `skein list` 不含已删 task; `skein doctor` 无违规
- [ ] help 含 del 命令说明

## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md)
- 任务/子任务/调度: task.json (`skein.py subtask list skein-del-cmd`)
