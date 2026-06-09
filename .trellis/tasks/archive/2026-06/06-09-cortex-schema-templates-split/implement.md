# Implement — cortex-schema 模板按变体拆分

## Phase A — 拆 templates (S1)

- [ ] **[L3] S1** dispatch trellis-implement: 读 `references/templates.md`, 按 design.md 拆分映射建 11 新文件 (10 type + 1 `_fields.md`), 删原 templates.md

## Phase B — 改引用 (S2)

- [ ] **[L1] S2** main: 改 SKILL.md 路由表; references/{topology,knowledge-modules,memory-levels}.md 内 `templates.md` 引用改 `../templates/<path>.md`

## Phase C — 验证 (S3)

- [ ] **[L1] S3** main: 跑验证 + 暂存

## Phase D — 收尾

- [ ] commit + archive + journal

## 验证命令 (S3)

```bash
d=plugins/tools/cortex/skills/cortex-schema
test ! -f $d/references/templates.md && echo "✓ old gone"
count=$(/usr/bin/find $d/templates -name '*.md' -type f | wc -l | tr -d ' ')
[[ $count -eq 11 ]] && echo "✓ templates=11"
test -d $d/templates/memory && test -d $d/templates/project
for f in memory/L0-rule memory/L1-long memory/L2-mid memory/L3-short memory/L4-inbox project/github project/gitlab project/website domain vault-script _fields; do
  test -f $d/templates/$f.md || echo "MISSING: $f"
done
# 每文件 ≤ 50 行
for f in $d/templates/**/*.md $d/templates/*.md; do
  lines=$(wc -l < "$f" 2>/dev/null | tr -d ' ')
  [[ $lines -le 50 ]] || echo "FAIL: $f $lines > 50"
done
# 无旧引用
! grep -rln 'references/templates.md\|`templates.md`' $d/ && echo "✓ 0 old refs"
# SKILL.md ≤ 60
[[ $(wc -l < $d/SKILL.md) -le 60 ]] && echo "✓ SKILL.md ≤ 60"
# smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate rc=$?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint rc=$?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract rc=$?"
```

## Rollback

```bash
git checkout plugins/tools/cortex/skills/cortex-schema/
```
