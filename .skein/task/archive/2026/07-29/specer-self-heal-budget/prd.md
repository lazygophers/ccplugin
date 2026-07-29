# specer 所有写 mode 末尾统一体检修超预算 — PRD (主入口)

## 目标
- [ ] skein-specer.md 改: sediment/reconstruct/prune 三写 mode 末尾统一加「跑 spec.py maintain --apply 就地体检修超预算 + 清 .pending-fix」, 不依赖 Stop hook auto-fix 二次派
- [ ] auto-fix mode (mode 4) 保留 — Stop hook 写 .pending-fix 仍兼容, 但 sediment/reconstruct/prune 自愈后 .pending-fix 应已被清/不产生
- [ ] 成功: specer 任一写 mode 跑完, core 不超 budget (或 maintain --apply 修不掉的才 needs_main)
## 边界
- [ ] plugins/tools/skein/agents/skein-specer.md 单文件改
- [ ] 不改 spec.py / skein.py (CLI 已支持 maintain --apply)
- [ ] 不改 Stop hook
## 验收标准
- [x] skein-specer.md sediment mode 含「写盘+reindex 后跑 maintain --apply 就地修超预算」
- [x] reconstruct/maintain mode 同样末尾 maintain --apply
- [x] prune mode 同样末尾 maintain --apply
- [x] auto-fix mode 保留 (Stop hook 兼容)
- [x] maintain --apply 失败/修不掉 (如断链) 入 needs_main, 不静默
- [x] python3 skein.py doctor 通过
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list specer-self-heal-budget`)
