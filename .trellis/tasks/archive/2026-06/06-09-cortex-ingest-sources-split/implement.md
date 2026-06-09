# Implement — cortex-ingest sources 拆分

## Phase A — 拆 sources (S1)

- [ ] **[L3] S1** dispatch trellis-implement: 读 references/sources.md, 拆为 sources/{github,gitlab,website,local}.md 4 文件, 各按 design.md 模板; 删原文件

## Phase B — 改引用 (S2)

- [ ] **[L1] S2** main: 改 SKILL.md 路由表 (sources/<type> 4 行 + references/{routing,workflow} 2 行); references/{routing,workflow}.md 内 `sources.md` 引用改 `../sources/<type>.md`

## Phase C — 验证 (S3)

- [ ] **[L1] S3** main: 跑全部验证 + 暂存

## Phase D — 收尾

- [ ] commit + archive + journal

## 验证命令 (S3)

```bash
d=plugins/tools/cortex/skills/cortex-ingest
test -d $d/sources && test ! -f $d/references/sources.md
for s in github gitlab website local; do
  test -f $d/sources/$s.md || echo "MISSING: $s"
  lines=$(wc -l < $d/sources/$s.md 2>/dev/null | tr -d ' ')
  [[ $lines -le 100 ]] || echo "FAIL: $s $lines > 100"
done
[[ $(wc -l < $d/SKILL.md) -le 60 ]] && echo "SKILL ≤ 60"
! grep -rln 'references/sources.md\|`sources.md`' $d/ && echo "0 old refs"
# 6 路由仍工作
for s in 'https://github.com/lazygophers/ccplugin' 'plugins/tools/cortex/tests/fixtures/ingest/local-no-git'; do
  bash plugins/tools/cortex/scripts/ingest.sh --dry-run --source "$s" --target /tmp/cortex-test >/dev/null 2>&1; echo "ingest $s rc=$?"
done
# 其他 skill smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate rc=$?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint rc=$?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract rc=$?"
```
