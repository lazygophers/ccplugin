---
id: S4
slug: fixture
deliverable: D5
parent-task: 06-09-cortex-digest-skills
execution-layer: main
estimated-tokens: 2000
---

# S4 · 建 fixture

## 产出

`tests/fixtures/history/`:
- `sample-session-1.jsonl` ≥ 5 行 (含用户校正 + L0 候选)
- `sample-session-2.jsonl` ≥ 5 行 (含决策 + 踩坑)

每行 JSON 对象, 字段对齐 Claude Code session 实际格式: `{"type": "user|assistant", "message": {"content": ...}, "timestamp": "..."}` 或精简版.

## 验证
```bash
test -f plugins/tools/cortex/tests/fixtures/history/sample-session-1.jsonl
test -f plugins/tools/cortex/tests/fixtures/history/sample-session-2.jsonl
python3 -c "
import json
for f in ['plugins/tools/cortex/tests/fixtures/history/sample-session-1.jsonl', 'plugins/tools/cortex/tests/fixtures/history/sample-session-2.jsonl']:
    for line in open(f):
        json.loads(line)
print('OK')
"
```

## 执行 main

直接 write fixture 2 文件. 内容含可识别的学习增量短句.
