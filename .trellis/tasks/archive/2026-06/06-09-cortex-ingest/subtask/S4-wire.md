---
id: S4
slug: wire
deliverable: D6,D8
parent-task: 06-09-cortex-ingest
status: planned
execution-layer: main
depends-on: [S1, S2]
blocks: [S5]
estimated-tokens: 2000
---

# S4 · 改 plugin.json + agent + README + llms.txt

## 产出

- `plugins/tools/cortex/.claude-plugin/plugin.json`: skills 数组添加 `./skills/cortex-ingest` (len 3 → 4)
- `agents/cortex.md`: 相关 skill 表加 cortex-ingest 一行 (触发: import / ingest / 抓取 / build)
- `README.md`: 组件表 + 触发表加 cortex-ingest
- `llms.txt`: skill 列表 3 → 4

## 验证

```bash
python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 4
assert './skills/cortex-ingest' in d['skills']
print('OK')
"
grep -q 'cortex-ingest' plugins/tools/cortex/agents/cortex.md
grep -q 'cortex-ingest' plugins/tools/cortex/README.md
grep -q 'cortex-ingest' plugins/tools/cortex/llms.txt
```

## 执行细节

main 直接 Edit. 不派 sub-agent (小改 4 处).

## 回滚
```bash
git checkout plugins/tools/cortex/.claude-plugin/plugin.json plugins/tools/cortex/agents/cortex.md plugins/tools/cortex/README.md plugins/tools/cortex/llms.txt
```
