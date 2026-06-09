---
id: S6
slug: verify
deliverable: all
parent-task: 06-09-cortex-digest-skills
execution-layer: main
depends-on: [S1, S2, S3, S4, S5]
estimated-tokens: 3000
---

# S6 · 联合验证 + 暂存

## 验证

```bash
# 1. 2 skill 结构
for s in cortex-history-digest cortex-context-digest; do
  d=plugins/tools/cortex/skills/$s
  test -f $d/SKILL.md && [[ $(wc -l < $d/SKILL.md) -le 60 ]] && echo "✓ $s SKILL.md"
  python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == '$s'
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'], str)
assert fm.get('user-invocable') is True
"
done

# 2. plugin.json
python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 6
print('skills=', d['skills'])
"

# 3. history-digest 脚本
bash plugins/tools/cortex/scripts/history-digest.sh --help >/dev/null && echo "history --help OK"
bash plugins/tools/cortex/scripts/history-digest.sh --dry-run --source-root plugins/tools/cortex/tests/fixtures/history --target /tmp/cortex-test 2>/dev/null | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print('history plan-len=', len(d.get('plan', [])))
assert len(d['plan']) >= 1, 'no learning increments found'
"

# 4. 4 既有 skill smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate rc=$?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint rc=$?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract rc=$?"
bash plugins/tools/cortex/scripts/ingest.sh --dry-run --source https://github.com/test/test --target /tmp/cortex-test >/dev/null 2>&1; echo "ingest rc=$?"

git add plugins/tools/cortex/ .trellis/tasks/06-09-cortex-digest-skills/
```
