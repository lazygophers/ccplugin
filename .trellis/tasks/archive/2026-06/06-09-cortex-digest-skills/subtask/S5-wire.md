---
id: S5
slug: wire
deliverable: D6
parent-task: 06-09-cortex-digest-skills
execution-layer: main
depends-on: [S1, S2]
estimated-tokens: 2000
---

# S5 · plugin.json + agent + README + llms 引用

## 产出

- plugin.json skills 数组 +2 (cortex-history-digest + cortex-context-digest) → len 6; keywords 补 history/digest/context/sediment
- agents/cortex.md: 相关 skill 表 +2 行
- README.md: 组件表 +2 行 + 触发表 +2 行
- llms.txt: skill 列表 4→6 + 目录树补充

## 验证
```bash
python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 6
for s in ['./skills/cortex-history-digest', './skills/cortex-context-digest']:
  assert s in d['skills']
print('OK')
"
for f in agents/cortex.md README.md llms.txt; do
  grep -q 'history-digest' plugins/tools/cortex/$f && grep -q 'context-digest' plugins/tools/cortex/$f && echo "$f OK"
done
```
