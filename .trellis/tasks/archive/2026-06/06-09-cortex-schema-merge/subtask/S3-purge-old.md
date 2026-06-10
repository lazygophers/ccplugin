---
id: S3
slug: purge-old
deliverable: D4
parent-task: 06-09-cortex-schema-merge
status: planned
execution-layer: main
depends-on: [S1]
blocks: [S5]
estimated-tokens: 2000
---

# S3 · 删旧 schema 目录 + 改 plugin.json

## 产出

- 删 `skills/cortex-schema-knowledge/`
- 删 `skills/cortex-schema-memory/`
- 改 `plugins/tools/cortex/.claude-plugin/plugin.json`:
  - `skills`: `["./skills/cortex-schema", "./skills/cortex-lint", "./skills/cortex-extract"]`
  - description / keywords 微调 (单数 schema)

## 验证

```bash
test ! -d plugins/tools/cortex/skills/cortex-schema-knowledge
test ! -d plugins/tools/cortex/skills/cortex-schema-memory
python3 -c "
import json
d = json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))
assert len(d['skills']) == 3, d['skills']
assert './skills/cortex-schema' in d['skills']
assert './skills/cortex-lint' in d['skills']
assert './skills/cortex-extract' in d['skills']
print('OK')
"
```

## 资源

写: `plugins/tools/cortex/.claude-plugin/plugin.json`
删: `skills/cortex-schema-{knowledge,memory}/`

## 依赖

S1 必须完成 (cortex-schema 已存在, 否则删旧导致空 skills)

## 执行细节 (main 干)

1. `rm -rf skills/cortex-schema-knowledge/ skills/cortex-schema-memory/`
2. 改 plugin.json: skills 数组 = 3 元素
3. description 可去掉 "L1=long / L2=mid" 等冗余 (整体描述)

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-schema-knowledge/ plugins/tools/cortex/skills/cortex-schema-memory/ plugins/tools/cortex/.claude-plugin/plugin.json
```
