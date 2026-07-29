# 清理 max_parallel 幽灵配置名 (skein-flow 目录外 9 处) — PRD (主入口)

## 目标
- [ ] 清掉 max_parallel 这个幽灵配置名 — 代码从不读它 (CONFIG_DEFAULTS skein.py:167 只有 max_active, 读取处 :229 同), 但配置/文档/样例里到处是它, 用户按文档设了以为生效实则被忽略
- [ ] 统一为唯一真名 max_active, 消除「设了不生效」的静默陷阱
## 边界
- 范围内 11 处 (全扩展名 grep 复核, 非上次估的 9 处):
- 幽灵配置键 2: .skein/config.yaml:9, plugins/tools/skein/docs/examples/sample-skein/config.yaml:2
- 文档 5: docs/reference.md:63, docs/skein.md:101/185/193, docs/examples/index.html:1749
- skill 1: skills/skein-setup/SKILL.md:42
- 测试注释 2: scripts/test_skein.py:215, scripts/tests/test_dag.py:8
- spec 2: .skein/spec/recall/planning/discipline.md:16, .skein/spec/recall/impl/claim.md:18
- 范围外: .skein/task/archive/ 下全部历史归档 (2026/07-17/cross-task-parallel-sched 等) — 历史记录禁改写
- 范围外: .skein/task.json 里 id 为 max-parallel-cleanup 的 task 自身 (那是 task id 不是配置名)
- 约束: config.yaml 里两处的值均为 2, 与 max_active 一致, 删键无行为变化 — 只删不改 max_active 的值
- 约束: spec 两处需等并行的 skein-specer agent (正在跑 maintain --apply) 完成后才能动, 避免写冲突
## 验收标准
- [ ] 全仓 grep -rn "max_parallel\|maxParallel\|max-parallel" 排除 .git/ 与 .skein/task/archive/ 后, 仅剩 .skein/task.json 的 task id 一处 (那是本 task 自己的 id)
- [ ] .skein/config.yaml 与 docs/examples/sample-skein/config.yaml 的 max_parallel 键已删, max_active 值未变 (均为 2)
- [ ] python3 -m pytest plugins/tools/skein/scripts/tests/ 全绿 (改的是注释, 不该影响)
- [ ] skein CLI 仍可正常读配置: python3 skein.py list 无报错
- [ ] 文档改后语义正确 — 不是简单替换字符串, 而是确认该处描述的确实是 max_active 的语义 (subtask 并发上限)
## 索引
- 详细设计: [design.md](design.md)
- 调研收敛: [findings.md](findings.md) (仅真调研时生)
- 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list max-parallel-cleanup`)
