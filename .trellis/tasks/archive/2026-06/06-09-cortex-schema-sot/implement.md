# Implement — cortex schema 单一真相源整合

## Phase A — schema 吸收 (S1 // S2 并行)

- [ ] **[L3] S1** dispatch trellis-implement: schema-knowledge 吸收 layout.md 三模块/同构/脚本用途/开放扩展/顶层布局/frontmatter 字段表/各 type 模板. 新增 references/{topology,templates}.md.
- [ ] **[L3] S2** dispatch trellis-implement: schema-memory 吸收 layout.md 5 级物理树 + 遗忘曲线速查; 从 lint R6 迁来 level↔dir 映射表.

## Phase B — 去重 + 清理 (S3 // S4 // S5 并行)

依赖: Phase A 全完 (引用方需要知道 schema-* 已含权威源).

- [ ] **[L3] S3** dispatch: lint references 去重 (rules.md R3/R4/R6 路径段改引用)
- [ ] **[L3] S4** dispatch: extract references 去重 (classifier.md 路由路径改引用)
- [ ] **[L1] S5** main 做: 删 docs/layout.md + 改 agents/cortex.md + README + llms.txt + validate-layout.sh 注释引用 schema-*

## Phase C — 验证 (S6, 串行)

- [ ] **[L1] S6** main 跑验证:
  ```bash
  test ! -f plugins/tools/cortex/docs/layout.md
  ! grep -r "docs/layout.md" plugins/tools/cortex/ || echo "FAIL: dangling ref"
  ! grep -E "memory/L[0-9]-(core|long|mid|short|inbox)" plugins/tools/cortex/skills/cortex-lint/references/rules.md || echo "WARN: lint still hardlists paths"
  ! grep -E "项目/<host>|领域/<area>" plugins/tools/cortex/skills/cortex-extract/references/classifier.md || echo "WARN: extract still hardlists"
  bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/
  bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ ; echo "rc=$?"
  bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null
  ```
- [ ] frontmatter 体检 (4 SKILL.md description ≤ 512 / wtu ≤ 128 / 无 "用户说")
- [ ] git add 暂存

## Phase D — 收尾

- [ ] commit
- [ ] archive + journal

## Rollback

```bash
git checkout plugins/tools/cortex/skills/cortex-{schema-*,lint,extract}/ plugins/tools/cortex/agents/ plugins/tools/cortex/README.md plugins/tools/cortex/llms.txt plugins/tools/cortex/scripts/validate-layout.sh
# 恢复 layout.md
git checkout HEAD~ -- plugins/tools/cortex/docs/layout.md
```
