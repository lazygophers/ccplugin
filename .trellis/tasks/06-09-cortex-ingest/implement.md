# Implement — cortex-ingest

## Phase A — 并行 (S1 // S2 // S3)

- [ ] **[L3] S1** dispatch: 建 cortex-ingest/SKILL.md + references/{sources,routing,workflow}.md
- [ ] **[L3] S2** dispatch: 写 scripts/ingest.sh + scripts/_ingest/ 5 python 模块, 实现识别+路由+dry-run JSON
- [ ] **[L1] S3** main: 建 fixture (inputs.txt + 2 子目录 + 模拟 .git/config)

## Phase B — wire (S4)

- [ ] **[L1] S4** main: 改 plugin.json (skills +1) + agent + README + llms.txt 引用

## Phase C — 验证 (S5)

- [ ] **[L1] S5** main: 跑全部输入路由验证 + 4 skill smoke + 暂存

## Phase D — 收尾

- [ ] commit + archive + journal
