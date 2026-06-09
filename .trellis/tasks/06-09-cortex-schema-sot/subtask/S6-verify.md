---
id: S6
slug: verify
deliverable: all
parent-task: 06-09-cortex-schema-sot
status: planned
execution-layer: main
depends-on: [S3, S4, S5]
blocks: []
estimated-tokens: 3000
---

# S6 · 联合验证

## 验证 (跑这些, 全过)

```bash
# 1. layout.md 删干净
test ! -f plugins/tools/cortex/docs/layout.md && echo "OK: layout.md gone"
! grep -r 'docs/layout.md' plugins/tools/cortex/ 2>/dev/null && echo "OK: no dangling refs"

# 2. schema-* 单一真相 (新文件存在 + 含权威内容)
test -f plugins/tools/cortex/skills/cortex-schema-knowledge/references/topology.md
test -f plugins/tools/cortex/skills/cortex-schema-knowledge/references/templates.md

# 3. lint/extract 去重 (路径硬列 ≤ 2 容忍, 引用 schema-*)
for f in plugins/tools/cortex/skills/cortex-lint/references/rules.md plugins/tools/cortex/skills/cortex-extract/references/classifier.md; do
  hits=$(grep -cE 'memory/L[0-9]-(core|long|mid|short|inbox)|项目/<host>|领域/<area>' $f || true)
  echo "$f hits=$hits"
  grep -q 'cortex-schema' $f && echo "  ✓ refs schema-*"
done

# 4. 4 SKILL.md frontmatter 体检
for s in cortex-schema-knowledge cortex-schema-memory cortex-lint cortex-extract; do
  python3 -c "
import yaml
fm = yaml.safe_load(open('plugins/tools/cortex/skills/$s/SKILL.md').read().split('---')[1])
desc, wtu = fm['description'], fm['when_to_use']
assert len(desc) <= 512 and len(wtu if isinstance(wtu, str) else '/'.join(wtu)) <= 128
assert '用户说' not in desc and '用户说' not in str(wtu)
assert isinstance(fm['arguments'], str)
print(f'$s: OK desc={len(desc)} wtu={len(wtu if isinstance(wtu, str) else \"/\".join(wtu))}')
"
done

# 5. 脚本行为不变 (smoke)
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ ; echo "validate rc=$?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint rc=$?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract rc=$?"

# 6. 暂存
git add plugins/tools/cortex/ .trellis/tasks/06-09-cortex-schema-sot/
git status --short | head -20
```

## 资源

只读 + 暂存全部.

## 回滚

S6 仅验证. 失败说明 S1-S5 某项不达标, 回该 subtask 修.
