下一条回复必须以 `[trellisx-start]` 开头

⚠️ 强制任务门禁 (本会话每次实施动作前自检, 不可绕过):
- 动手写代码 / 改文件 / 系统搜索后准备改动前, 必须先判断任务复杂度
- 多步骤 / 多文件 / 多独立目标 / 需调度 (subtask ≥ 2) → 禁直接动手, 必须先建 trellis task 走 planning (加载 `trellisx-orchestrate` skill)
- 仅单步单文件且无独立子目标 (subtask ≤ 1) → 可 main 直做
- 判定靠不准倾向建 task。"任务看起来不复杂"不是绕过理由 — 按是否拆得出 ≥ 2 个独立可验收 subtask 判定
- 一个 prompt 内含 ≥ 2 个独立问题 / 目标 = 必建 task (可拆 parent + child)
- 已绕过 task 开始实施后才发现复杂 → 立即停, 补建 task 重走 planning

路由:
- 任务编排 (subtask 拆分 / 选执行层 / dispatch prompt / 进度通讯 / 生命周期 / 失败回退 / 状态更新) 走 `trellisx-orchestrate` skill
- spec 演化 (init / optimize / sediment) 走 `trellisx-spec` skill
- task.py start 即创 worktree, 结束合并 + 移除确保环境干净
- 非 trellis 编排场景按 CLAUDE.md 通用规则
