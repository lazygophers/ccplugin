---
id: S3
slug: history-script
deliverable: D3
parent-task: 06-09-cortex-digest-skills
execution-layer: sub-agent
estimated-tokens: 12000
---

# S3 · 写 history-digest.sh + _history_digest/

## 产出

- `scripts/history-digest.sh` ≤ 80 行
- `scripts/_history_digest/__init__.py` (dataclass / regex)
- `scripts/_history_digest/scanner.py` (扫 jsonl 文件)
- `scripts/_history_digest/parser.py` (jsonl 行 → 消息对象)
- `scripts/_history_digest/extractor.py` (识别学习增量)
- `scripts/_history_digest/router.py` (路由到 L0-L4, 全部全局)
- `scripts/_history_digest/runner.py` (argparse + main, 输出 JSON plan)

## 验证

```bash
bash plugins/tools/cortex/scripts/history-digest.sh --help
# fixture
bash plugins/tools/cortex/scripts/history-digest.sh --dry-run --source-root plugins/tools/cortex/tests/fixtures/history --target /tmp/cortex-test 2>/dev/null | python3 -c "
import json, sys
d = json.loads(sys.stdin.read())
print('plan-len=', len(d.get('plan', [])))
assert len(d['plan']) >= 1
"
```

## Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-digest-skills

## 目标
写 scripts/history-digest.sh + scripts/_history_digest/ python 模块. 实现扫 jsonl 历史 + 提取学习增量 + 路由 + dry-run JSON plan. 本 task 范围不做实际写盘 (apply 标 "需 main").

## 已知
- 默认 source-root = $HOME/.claude/projects/
- 默认 target = $HOME/.cortex (写盘到 ~/.cortex/.wiki/memory/)
- 路径权威: cortex-schema/references/memory-levels.md (5 级映射)
- 三轴判定 (复用 cortex-extract 模式): 时效 / 强度 / 复用面

## 入口
```
history-digest.sh [--dry-run|--apply] [--target <vault>] [--source-root <claude-projects>] [--since <YYYY-MM-DD>] [--help]
  默认 --dry-run + target=$HOME/.cortex + source-root=$HOME/.claude/projects
```

## planner JSON 输出
```json
{
  "mode": "dry-run",
  "source_root": "...",
  "target": "...",
  "plan": [
    {
      "session_file": "<jsonl path>",
      "line_no": <int>,
      "kind": "user-correction|decision|tip|L0-rule",
      "summary": "前 80 字摘要",
      "target_path": "memory/L<n>-<suffix>",
      "target_filename": "<slug>.md",
      "reason": "..."
    }
  ]
}
```

## extractor 启发式
- 用户消息含 "no/wrong/not that/不对/不是/别这样" → user-correction → L1/L2 候选
- 用户消息含 "always/永远/never/严禁/硬性" → L0 候选 (ask)
- assistant 消息含决策语 ("let's use X / 我们选 Y / 决定 Z") → L2/L3 候选
- 含 "failed/error because/踩坑/坑" → 踩坑笔记 → L2

## 模块边界
- scanner: rglob jsonl → 文件清单
- parser: 每行 json.loads + 字段抽取 (type, content, timestamp); 不识别字段 skip + warn
- extractor: 消息 → 学习增量条目 (kind/summary)
- router: 增量 → target_path + level (调 memory-levels 映射, 全部全局)
- runner: argparse + 拼装 plan + 输出 JSON

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/scripts/history-digest.sh + plugins/tools/cortex/scripts/_history_digest/** (新建)
禁改: 其他

## 输出限
- history-digest.sh ≤ 80 行
- 每 .py ≤ 200 行

## 失败处理
- jsonl 解析错误 → skip 该行 + warn stderr
- source-root 不存在 → exit 1

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```
