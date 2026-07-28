# design — for-consumer 聚合文件结构

## for-xxx.md 内容规范

每个 for-xxx.md = 该 consumer 所需全部流程规则的**聚合正文**（自包含），从对应原子文件提取。原则:

- **简短规则（<60 行）直接全文搬入**（如 state-before-action 93行、subtask-state-machine 141行、task-state-machine 122行、rollback-protocol 166行、worktree-convention 217行、priority-scale 176行）。
- **冗长规则（dag-scheduling 260行）提炼该 consumer 真正用到的条款** + 末尾"深详见 ../skein-workflow/references/dag-scheduling.md §N"。例: for-exec 只需 §2就绪判定 + §5完成即派 + §6plan-ahead + §7自愈；for-flow 需全貌概览。
- **subtask-operations（238行）按 consumer 取相关节**: for-exec 取§3自愈, for-check 取§4修复, for-plan 取§1新增+§2并入。
- for-xxx.md 顶部放一行「单一真值源: 改规则改原子文件 + 同步本聚合文件」警示。

## 各 for 文件预估行数

| 文件 | 聚合来源 | 预估行 |
|---|---|---|
| for-flow.md | state-before-action(全93) + task/subtask-state-machine(精简~80) + dag-scheduling(概览~40) + subtask-ops(全场景摘要~50) + worktree(精简~40) + rollback(全166) | ~470 |
| for-plan.md | task-state-machine(全122) + subtask-state-machine(全141) + subtask-ops(§1新增§2并入~80) + dag(§1依赖模型§3布局~50) | ~390 |
| for-exec.md | worktree(精简~50) + state-before-action(硬门2~30) + dag(§2§5§6§7~100) + subtask-ops(§3自愈~60) + subtask-state-machine(精简~40) | ~280 |
| for-check.md | state-before-action(硬门3~25) + worktree(精简~40) + rollback(全166) + subtask-ops(§4~50) | ~280 |
| for-finish.md | worktree(精简~60) | ~60 |

## consumer SKILL.md 改动

每个 consumer SKILL.md:
1. 删除内联复述的规则正文段落（如 skein-flow:16-26 state-before-action 全文复述、:38 DAG 引用句、:41 rollback 引用句）。
2. 替换为一行: `本阶段流程规则（状态机/调度/操作/worktree/回退）聚合见 ../skein-workflow/references/for-flow.md`。
3. 保留 consumer 自有逻辑（闭环步骤、场景路由、失败模式表等），只动"引用 skein-workflow 规则"的部分。

## 路径修复

所有 `skein-workflow/references/xxx.md` → `../skein-workflow/references/xxx.md`（从 consumer 目录出发的正确相对路径）。

## 缓存考量

- consumer SKILL.md 删复述后变薄且稳定 → 该层 prompt cache 命中率提升。
- for-xxx.md 经 AI 主动 Read 注入（tool result），不进 SKILL.md cache 前缀 → 故 for-xxx.md 须精炼（已按 consumer 裁剪，非整本抄）。
- 原子文件改动频率低（规则稳定），for-xxx.md 同步更新即可。

## 验证

每个改完的 consumer SKILL.md 跑 claude -p 质量门（CLAUDE.md 规范），确认 AI 仍能正确识别流程规则、引用路径可达。

## grill 裁决回写 (2026-07-27)

1. **consumer 范围**: 只 for-{flow,exec,check,plan,finish} 五个。grill/research/spec/setup 不动(保留声明性引用句, 它们不实际读规则正文)。
2. **priority-scale**: 塞进 for-exec.md(调度顺序相关, exec 实际会用)。从 skein-workflow/SKILL.md 索引表标注归属。
3. **交叉引用路径**: for-xxx.md 与原子文件同目录(skein-workflow/references/), 原子文件间引用(./xxx.md)与跨 skill 引用(../../skein-xxx/...)保持不变, 天然正确。
4. **验收 (s3)**: claude -p 质量门(每 consumer) + grep 死链双检(无旧 skein-workflow/references/xxx.md 路径残留) + 一致性双检(for-xxx 规则正文与原子文件一致)。
5. **漂移防护**: 双警示标注 — 每个 for-xxx.md 顶部加「⚠️ 单一真值源: 改规则改原子文件 + 同步本文件」; 每个被聚合的原子文件顶部加「改我须同步 for-{consumers}.md」。
