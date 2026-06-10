---
id: S1
slug: history-skill
deliverable: D1
parent-task: 06-09-cortex-digest-skills
execution-layer: sub-agent
estimated-tokens: 8000
---

# S1 · 建 cortex-history-digest skill

## 产出

- `skills/cortex-history-digest/SKILL.md` ≤ 60 行
- `skills/cortex-history-digest/references/sources.md` (~/.claude/projects/**/*.jsonl 格式)
- `skills/cortex-history-digest/references/parser.md` (提取学习增量算法)
- `skills/cortex-history-digest/references/routing.md` (路由 L0-L4, 仅全局)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-history-digest
test -f $d/SKILL.md && [[ $(wc -l < $d/SKILL.md) -le 60 ]]
for r in sources parser routing; do test -f $d/references/$r.md; done
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == 'cortex-history-digest'
assert len(fm['description']) <= 512 and len(fm['when_to_use']) <= 128
assert '用户说' not in fm['description'] and '用户说' not in fm['when_to_use']
assert isinstance(fm['arguments'], str) and fm.get('user-invocable') is True
print('OK')
"
```

## Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-digest-skills

## 目标
建 cortex-history-digest skill (SKILL.md ≤ 60 行 + 3 references). 描述从 ~/.claude/projects/**/*.jsonl 提取学习增量 → 全局记忆库. 不写脚本 (S3 处理).

## 已知
- frontmatter (见 design.md):
  name: cortex-history-digest
  description: "Claude Code 会话历史整理 — 扫 ~/.claude/projects/**/*.jsonl 全部 session transcripts, 提取学习增量 (用户校正/决策/踩坑/L0 规则) → 全局记忆库 ~/.cortex/.wiki/memory/. 默认 dry-run JSON plan, --apply 落盘. 与 cortex-extract (L4-inbox 内部) 互补."
  when_to_use: "整理 Claude Code 历史/digest transcripts/沉淀历史会话/扫 ~/.claude/projects/回顾/历史学习增量提取"
  argument-hint: "[--dry-run|--apply] [--target <vault>]"
  arguments: "[--dry-run|--apply] [--target <仓库根>]"
  user-invocable: true
- 路径权威: cortex-schema (引用 ../cortex-schema/references/memory-levels.md)
- 三轴判定: cortex-extract 复用

## SKILL.md 结构
1. frontmatter
2. 1 段总览
3. 路由表 (3 references)
4. 入口命令 (bash scripts/history-digest.sh)
5. 与 cortex-extract 边界 (history-digest 抓 transcripts; extract 整 L4-inbox)
6. 引用 cortex-schema/lint

## references 内容
- sources.md: ~/.claude/projects/ 目录结构 + jsonl message schema (type=user/assistant/tool_use, content=string|array, timestamp); 反例 (非 jsonl 不处理)
- parser.md: 提取算法 "学习增量" (用户校正 "no/wrong/not that" → L0/L1 候选; 决策 "let's use X" → L2/L3; 踩坑 "X failed because" → L2; L0 关键词 "永远/硬性" → L0); jsonl 字段不识别 skip+warn
- routing.md: 目标全部全局 ~/.cortex/.wiki/memory/; 三轴判定复用 cortex-extract; --apply 前必须用户审 (输出前 80 字摘要保护敏感)

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-history-digest/** (新建)
禁改: 其他

## 输出限
- SKILL.md ≤ 60 行
- 各 reference ≤ 220 行

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```
