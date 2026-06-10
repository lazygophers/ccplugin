# Implement — cortex-schema 合并 + 样例

## Phase A — 并行建 (S1 // S2)

- [ ] **[L3] S1** dispatch: 建 cortex-schema/SKILL.md + 4 references (topology / knowledge-modules / memory-levels / templates), 从 schema-knowledge/schema-memory 现有 references 合并
- [ ] **[L3] S2** dispatch: 写 cortex-schema/references/examples/ 7 文件 (rule / project / domain / memory-L1/L2/L3 / vault-script)

## Phase B — 并行清理 (S3 // S4)

- [ ] **[L1] S3** main: 删 cortex-schema-knowledge/ + cortex-schema-memory/ + 改 plugin.json (skills 数组 - 2 + 1)
- [ ] **[L3] S4** dispatch: 改全库引用指向 cortex-schema (lint references / extract references / agent / README / llms / _lint __init__.py / e2e-report)

## Phase C — 验证 (S5)

- [ ] **[L1] S5** main 跑全部验证 (按 S5 subtask 文件) + 暂存

## Phase D — 收尾

- [ ] commit + archive + journal
