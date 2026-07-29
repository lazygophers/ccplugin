# 修 estimate 硬门导致的 35 个测试失败 — PRD (主入口)

## 目标
- [ ] pytest 从 36 failed / 96 passed 恢复到全绿 (或只剩已知无关项), 让 pytest 重新能当回归门用
- [ ] 根因 (实测 stderr 原文): "feat-x 预计工时未填 — 先 `skein estimate feat-x --set <小时数>` 填实再 confirm" — commit 288056c40 给 confirm 加了 estimate 硬门, 测试 helper 没跟上
## 边界
- 主改点: plugins/tools/skein/scripts/tests/test_statemachine.py:35 附近的 _mk() helper — 在 skein_cli(ws, "confirm", tid) 之前补一行 skein_cli(ws, "estimate", tid, "--set", "1")
- 同型 helper 可能不止一处 — 先 grep tests/ 与 test_skein.py 里所有 "confirm" 调用点, 逐个确认是否需要补 estimate
- 已知另有 1 个失败 test_worktree_disabled.py::test_session_context_hides_worktree_when_disabled 根因不同, 需单独查
- 范围外: 不改 skein.py 的 estimate 硬门本身 (那是有意加的产品行为, 不是 bug)
## 验收标准
- [ ] uv run pytest plugins/tools/skein/scripts/ 输出 failed 数为 0 (或只剩明确说明根因且用户裁定不修的项)
- [ ] 补的是测试 helper 而非放宽 skein.py 的校验 — git diff 中 skein.py 零改动
- [ ] 每个改动点给 file:line + 改前/改后对照
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list test-estimate-gate`)
