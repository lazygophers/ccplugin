---
id: S5
slug: verify
deliverable: all
parent-task: 06-09-cortex-ingest
status: planned
execution-layer: main
depends-on: [S1, S2, S3, S4]
blocks: []
estimated-tokens: 3000
---

# S5 · 联合验证 + 暂存

## 验证

```bash
# 1. cortex-ingest skill 结构
d=plugins/tools/cortex/skills/cortex-ingest
test -f $d/SKILL.md && [[ $(wc -l < $d/SKILL.md) -le 60 ]]
for r in sources routing workflow; do test -f $d/references/$r.md || echo "MISSING: $r"; done

# 2. frontmatter
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-ingest'
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'], str)
assert fm.get('user-invocable') is True
print('OK')
"

# 3. ingest.sh 路由 6 输入全过
for src in \
  'https://github.com/lazygophers/ccplugin:项目/github.com/lazygophers/ccplugin' \
  'https://gitlab.com/gitlab-org/gitlab:项目/gitlab.com/gitlab-org/gitlab' \
  'https://docs.python.org/3/library/argparse.html:项目/docs.python.org/_/3' \
  'git@github.com:tokio-rs/tokio.git:项目/github.com/tokio-rs/tokio'; do
  source="${src%%:项目*}"
  expect="项目${src##*:项目}"
  out=$(bash plugins/tools/cortex/scripts/ingest.sh --dry-run --source "$source" --target /tmp/cortex-test 2>/dev/null | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['plan'][0]['target_path'])")
  [[ "$out" == "$expect" ]] && echo "✓ $source" || echo "✗ $source got $out want $expect"
done

# local 输入
out=$(bash plugins/tools/cortex/scripts/ingest.sh --dry-run --source plugins/tools/cortex/tests/fixtures/ingest/local-no-git --target /tmp/cortex-test | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['plan'][0]['target_path'])")
[[ "$out" == "项目/local/local-no-git" ]] && echo "✓ local-no-git" || echo "✗ local-no-git got $out"

out=$(bash plugins/tools/cortex/scripts/ingest.sh --dry-run --source plugins/tools/cortex/tests/fixtures/ingest/local-with-git-remote --target /tmp/cortex-test | python3 -c "import json,sys; print(json.loads(sys.stdin.read())['plan'][0]['target_path'])")
[[ "$out" == "项目/github.com/foo/bar" ]] && echo "✓ local-with-git-remote → github" || echo "✗ local-with-git-remote got $out"

# 4. plugin.json + 引用
python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 4 and './skills/cortex-ingest' in d['skills']
print('plugin.json OK')
"
grep -q cortex-ingest plugins/tools/cortex/agents/cortex.md && echo "agent OK"
grep -q cortex-ingest plugins/tools/cortex/README.md && echo "README OK"
grep -q cortex-ingest plugins/tools/cortex/llms.txt && echo "llms OK"

# 5. 其他 skill smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate rc=$?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint rc=$?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract rc=$?"

git add plugins/tools/cortex/ .trellis/tasks/06-09-cortex-ingest/
```

## 资源
只读 + 暂存.
