---
id: S5
slug: verify
deliverable: all
parent-task: 06-09-cortex-schema-merge
status: planned
execution-layer: main
depends-on: [S1, S2, S3, S4]
blocks: []
estimated-tokens: 2000
---

# S5 · 联合验证

## 验证

```bash
# 1. cortex-schema 存在, 旧 schema 不存在
test -d plugins/tools/cortex/skills/cortex-schema
test ! -d plugins/tools/cortex/skills/cortex-schema-knowledge
test ! -d plugins/tools/cortex/skills/cortex-schema-memory

# 2. plugin.json
python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 3
assert './skills/cortex-schema' in d['skills']
print('plugin.json OK')
"

# 3. SKILL.md frontmatter
python3 -c "
import yaml
fm = yaml.safe_load(open('plugins/tools/cortex/skills/cortex-schema/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-schema'
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'], str)
print('OK')
"
[[ $(wc -l < plugins/tools/cortex/skills/cortex-schema/SKILL.md) -le 60 ]]

# 4. references 齐 + examples ≥ 5
ls plugins/tools/cortex/skills/cortex-schema/references/
count=$(/usr/bin/find plugins/tools/cortex/skills/cortex-schema/references/examples -name '*.md' -type f | wc -l | tr -d ' ')
[[ $count -ge 5 ]] && echo "examples=$count OK"

# 5. 0 旧引用
! grep -rln 'cortex-schema-knowledge\|cortex-schema-memory' plugins/tools/cortex/ && echo "0 dangling refs"

# 6. 其他 skill frontmatter 仍合规
for s in cortex-lint cortex-extract; do
  python3 -c "
import yaml
fm = yaml.safe_load(open('plugins/tools/cortex/skills/$s/SKILL.md').read().split('---')[1])
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
print(f'$s OK')
"
done

# 7. smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate rc=$?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint rc=$?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract rc=$?"

# 8. 暂存
git add plugins/tools/cortex/ .trellis/tasks/06-09-cortex-schema-merge/
```

## 资源

只读 + 暂存.

## 回滚

每子任务独立可回滚.
