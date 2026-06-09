# Design — cortex-history-digest + cortex-context-digest

## skill 1: cortex-history-digest

```
skills/cortex-history-digest/
├── SKILL.md (≤ 60 行)
└── references/
    ├── sources.md       transcripts 格式 (~/.claude/projects/**/*.jsonl, message schema)
    ├── parser.md        提取算法 (识别"学习增量" - 用户校正/决策/踩坑/规则)
    └── routing.md       路由到 L0-L4 (复用 cortex-extract 三轴; 仅全局 ~/.cortex/.wiki/memory/)
```

frontmatter:
```yaml
---
name: cortex-history-digest
description: "Claude Code 会话历史整理 — 扫 ~/.claude/projects/**/*.jsonl 全部 session transcripts, 提取学习增量 (用户校正/决策/踩坑/L0 规则) → 全局记忆库 ~/.cortex/.wiki/memory/. 默认 dry-run JSON plan, --apply 落盘. 与 cortex-extract (L4-inbox 内部) 互补."
when_to_use: "整理 Claude Code 历史/digest transcripts/沉淀历史会话/扫 ~/.claude/projects/回顾/历史学习增量提取"
argument-hint: "[--dry-run|--apply] [--target <vault>]"
arguments: "[--dry-run|--apply] [--target <仓库根>]"
user-invocable: true
---
```

## skill 2: cortex-context-digest

```
skills/cortex-context-digest/
├── SKILL.md (≤ 60 行)
└── references/
    ├── scope.md         全局 vs 项目级 自动判定 + --scope 显式覆盖
    └── triggers.md      识别什么值得 digest (决策/选型/踩坑/规则)
```

无独立脚本 — skill 步骤指导 main 会话执行: Read 当前任务上下文 → 判定 scope → 调 cortex-extract / cortex-save 落盘.

frontmatter:
```yaml
---
name: cortex-context-digest
description: "整理当前会话上下文 → 记忆库. 自动判定全局 (L0 关键词/跨项目语义) vs 项目级 (默认/含 repo 特定); 用户可 --scope global|project 显式覆盖. 复用 cortex-extract 三轴 + cortex-schema 路径. 任务收尾或显式 'digest 上下文/沉淀' 触发."
when_to_use: "整理上下文/沉淀本次会话/digest context/任务收尾沉淀/把决策落记忆库/全局还是项目级判定"
argument-hint: "[--scope global|project] [--dry-run|--apply]"
arguments: "[--scope 全局|项目] [--dry-run|--apply]"
user-invocable: true
---
```

## scope 自动判定 (context-digest)

```
判定规则 (优先序):
1. 用户显式 --scope global → 全局
2. 用户显式 --scope project → 项目级
3. 自动: 含 L0 触发词 (永远/硬性/never/严禁/绝不) → 全局
4. 自动: 内容引用当前 repo 名/路径/具体文件 → 项目级
5. 自动: 跨项目通用 (e.g. shell 通用规则, AI 协作规范) → 全局
6. 兜底 → 项目级 (保守)
```

## scripts/history-digest.sh + _history_digest/

```
_history_digest/
├── __init__.py       共享 dataclass / regex
├── scanner.py        扫 ~/.claude/projects/**/*.jsonl
├── parser.py         每条 jsonl 行 → 消息对象 (type/role/content)
├── extractor.py      识别学习增量 (user-correction / decision / tip)
├── router.py         路由到 L0-L4 (复用三轴判定; 调 cortex-extract router 或独立简化版)
└── runner.py         argparse + main
```

history-digest.sh 入口:
```
history-digest.sh [--dry-run|--apply] [--target <vault>] [--source-root <claude-projects>] [--since <YYYY-MM-DD>] [--help]
  默认 --dry-run + target=$HOME/.cortex + source-root=$HOME/.claude/projects
  --since 增量 (默认全量, 后续 task 可加游标)
```

## context-digest 无脚本 — skill 步骤

SKILL.md 描述 main 会话执行步骤:
1. Read 当前 active task 上下文 (.trellis/tasks/<current>/journal-N.md + prd/design/implement)
2. Read 最近用户指令 (会话最近 N 轮)
3. 识别"学习增量" (用户校正/决策/选型/踩坑)
4. 对每个增量跑 scope 判定 (见 references/scope.md)
5. 调 cortex-extract --dry-run 输出 plan (用 schema 路径)
6. 用户审 plan → --apply

## 资源边界

| Subtask | 写资源 | 并行 |
| --- | --- | --- |
| S1 | `skills/cortex-history-digest/**` | 与 S2/S3/S4 |
| S2 | `skills/cortex-context-digest/**` | 与 S1/S3/S4 |
| S3 | `scripts/history-digest.sh` + `scripts/_history_digest/**` | 与 S1/S2/S4 |
| S4 | `tests/fixtures/history/**` | 与 S1/S2/S3 |
| S5 | plugin.json / agent / README / llms | 依赖 S1+S2 |
| S6 | 只读 | 收口 |

## fixture (S4)

```
tests/fixtures/history/
├── sample-session-1.jsonl       Claude Code session 节选 (含用户校正 + L0 候选)
└── sample-session-2.jsonl       含决策 + 踩坑
```

每文件 ≥ 5 条 jsonl 行, 真实 schema (type=user/assistant, content=string/array).

## 验证契约 (S6)

- 2 skill 完整 (SKILL.md + references; frontmatter 合规)
- history-digest.sh --dry-run --source-root tests/fixtures/history/ → JSON plan 含 ≥ 1 候选
- plugin.json skills len == 6
- 4 既有 skill smoke 同前
- 0 "用户说" 残留

## Rollback

```bash
git checkout plugins/tools/cortex/
rm -rf plugins/tools/cortex/skills/cortex-{history,context}-digest/ plugins/tools/cortex/scripts/history-digest.sh plugins/tools/cortex/scripts/_history_digest/ plugins/tools/cortex/tests/fixtures/history/
```
