# subtask claim --start 参数 + claim/start 文档补充 — PRD (主入口)

## 目标
- [ ] `skein subtask claim <tid>` 加 `--start` 显式参数: 表达"认领即标 running 占槽进执行态" (默认行为不变, 参数作 API 明确表达)。
- [ ] skills (skein-exec / skein-flow) + agent (skein-executor.md) 补 claim/start 分工说明:
  - `subtask claim <tid>` 整批就绪 → 标 running 占槽 (执行态); **不指定 sid** (整批就绪由 DAG 算, 非挑单).
  - `subtask start <tid> <sid>` 单 sid 占槽 (claim 不接受 sid 参数; 指定单 sid 执行用 start, 典型场景 = 失败重派 / 定点补派).
  - `--start` 参数用法.
- [ ] 成功: 翻 skills/agents 能看懂 claim (整批, 不挑 sid) vs start (单 sid) 分工; CLI `--start` 可用.

## 边界
范围内:
- [ ] `scripts/skein.py` subtask claim 子命令加 `--start` 参数 (store_true, 行为=默认 claim 即占槽; 加参数仅为显式语义 + 文档锚点).
- [ ] `skills/skein-exec/SKILL.md` + `skills/skein-exec/references/scheduling-algorithm.md` 补 claim 不指定 sid / start 单 sid / --start 参数说明.
- [ ] `skills/skein-flow/SKILL.md` exec 段落补同样分工说明 (claim 整批 vs start 单 sid).
- [ ] `agents/skein-executor.md` 补: 被派时 subtask 已是 running 态 (claim/start 占槽前置), executor 直接执行不重复占槽.

范围外 (非目标):
- [ ] 不改 claim 默认行为 (仍整批标 running 占槽; --start 不改变行为, 仅显式参数).
- [ ] 不改 _ready / _global_ready 算法.
- [ ] 不改 start 单 sid 路径逻辑.
- [ ] 不改全局 `skein claim` (跨 task) 命令 (本 task 只管 `subtask claim <tid>`).

已知约束:
- [ ] claim 整批标 running + 置 started + 占 max_active 槽 (代码 skein.py:1799-1814, _ready 受槽限 1663).
- [ ] start 单 sid: 检查 pending/failed + 槽限 + 依赖 done (skein.py:1818-1830).
- [ ] 文档现状: scheduling-algo.md:18-20 已讲 claim 标 running / start 单 sid retry, 但没明说"claim 不接受 sid / 指定 sid 用 start" 的分工边界.

## 验收标准
- [x] CLI: skein claim / skein subtask claim <tid> 默认调用 (无参数) 即整批标 running 占槽 (主路径, 默认行为不破).
- [x] CLI: skein claim --dry-run 只读预览就绪批不改态 (与默认 claim 区分).
- [x] skill skein-exec: 含 claim (默认改态占槽) vs claim --dry-run (只读预览) vs subtask start (单 sid 补派) 三命令分工.
- [x] agent skein-executor.md: 含被派时 subtask 已 running 不重复占槽说明.
- [x] python3 skein.py doctor 通过.
- [x] 三文档 (scheduling-algorithm.md / SKILL.md / skein-executor.md) claim 默认行为表述一致, 与 CLI 实际行为 (skein.py:1799-1805) 吻合.
## 索引
- [ ] 详细设计: [design.md](design.md)
- [ ] 调研收敛: [findings.md](findings.md) (仅真调研时生)
- [ ] 任务/子任务/调度: task.json (脚本真值, `skein.py subtask list claim-start-doc`)
