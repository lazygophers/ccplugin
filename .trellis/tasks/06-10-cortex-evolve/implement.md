# Implement — cortex-evolve

## Phase A — 建 skill (S1)

- [ ] **[L3] S1** dispatch trellis-implement: 建 skills/cortex-evolve/{SKILL.md, references/{signals,rules,workflow}.md} 按 design.md

## Phase B — wire (S2)

- [ ] **[L1] S2** main: plugin.json skills 6→7 + agent / README / llms 引用

## Phase C — 验证 (S3)

- [ ] **[L1] S3** main: skill 体检 + 6 既有 skill smoke + 暂存

## Phase D — 收尾

- [ ] commit + archive + journal

## S1 Dispatch Prompt

(见 subtask/S1-skill.md)

## S3 验证命令

```bash
d=plugins/tools/cortex/skills/cortex-evolve
test -f $d/SKILL.md && [[ $(wc -l < $d/SKILL.md) -le 60 ]]
for r in signals rules workflow; do test -f $d/references/$r.md; done
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-evolve'
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'], str)
assert fm.get('user-invocable') is True
print('OK')
"
grep -q 'L1.*不主动降\|不主动降.*L1\|L0.*不主动降' $d/references/rules.md
grep -q '金字塔\|pyramid' $d/references/rules.md
grep -q '频率\|frequency' $d/references/signals.md
grep -q '时间\|recency' $d/references/signals.md
grep -q '重要度\|importance' $d/references/signals.md

python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 7
assert './skills/cortex-evolve' in d['skills']
print('plugin.json OK')
"
for f in agents/cortex.md README.md llms.txt; do
  grep -q cortex-evolve plugins/tools/cortex/$f && echo "$f OK"
done

# 既有 skill smoke
bash plugins/tools/cortex/scripts/validate-layout.sh --target plugins/tools/cortex/tests/fixtures/layout-ok/ >/dev/null; echo "validate rc=$?"
bash plugins/tools/cortex/scripts/lint.sh --check --target plugins/tools/cortex/tests/fixtures/lint/ >/dev/null 2>&1; echo "lint rc=$?"
bash plugins/tools/cortex/scripts/extract.sh --dry-run --target plugins/tools/cortex/tests/fixtures/extract/ >/dev/null 2>&1; echo "extract rc=$?"
bash plugins/tools/cortex/scripts/ingest.sh --dry-run --source https://github.com/test/test --target /tmp/cortex-test >/dev/null 2>&1; echo "ingest rc=$?"
bash plugins/tools/cortex/scripts/history-digest.sh --dry-run --source-root plugins/tools/cortex/tests/fixtures/history --target /tmp/cortex-test >/dev/null 2>&1; echo "history rc=$?"
```
