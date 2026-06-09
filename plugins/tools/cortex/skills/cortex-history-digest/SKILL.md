---
name: cortex-history-digest
description: "Claude Code 会话历史整理 — 扫 ~/.claude/projects/**/*.jsonl 全部 session transcripts, 提取学习增量 (用户校正/决策/踩坑/L0 规则) → 全局记忆库 ~/.cortex/.wiki/memory/. 默认 dry-run JSON plan, --apply 落盘. 与 cortex-extract (L4-inbox 内部) 互补."
when_to_use: "整理 Claude Code 历史/digest transcripts/沉淀历史会话/扫 ~/.claude/projects/回顾/历史学习增量提取"
argument-hint: "[--dry-run|--apply] [--target <vault>]"
arguments: "[--dry-run|--apply] [--target <仓库根>]"
user-invocable: true
---

# cortex-history-digest

Claude Code 历史 transcripts → 全局记忆库. 扫 `~/.claude/projects/**/*.jsonl` 全部 session 历史, 抽**学习增量** (用户校正 / 关键决策 / 踩坑 / L0 硬性规则), 经三轴判定路由到 `~/.cortex/.wiki/memory/L0-core | L1-long | L2-mid | L3-short`. 默认 dry-run 输出 JSON plan; `--apply` 才落盘 (本 task 范围内仅 dry-run 验证).

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 transcripts 目录结构 + jsonl message schema | `references/sources.md` |
| 查 "学习增量" 识别算法 (用户校正 / 决策 / 踩坑 / L0 关键词) | `references/parser.md` |
| 查路由到 L0-L4 + 三轴复用 + 敏感保护 | `references/routing.md` |

## 入口命令

```bash
bash plugins/tools/cortex/scripts/history-digest.sh --dry-run
bash plugins/tools/cortex/scripts/history-digest.sh --dry-run --source-root ~/.claude/projects --target $HOME/.cortex
bash plugins/tools/cortex/scripts/history-digest.sh --apply   # 需用户审 plan 后再执行
```

默认 `--dry-run` + `target=$HOME/.cortex` + `source-root=$HOME/.claude/projects`. `--since YYYY-MM-DD` 增量过滤 (默认全量).

## 与 cortex-extract 边界

| skill | 数据源 | 落点 |
| --- | --- | --- |
| **cortex-history-digest** (本) | `~/.claude/projects/**/*.jsonl` (Claude Code session 历史) | 仅全局 `~/.cortex/.wiki/memory/` |
| **cortex-extract** | L4-inbox 内已收件 .md 资料 | L0-L4 + 项目/领域 全模块 |

history-digest 从对话流抽取增量, extract 整理已收件文件 — 互补不重叠.

## 路径 + 三轴权威

- 路径段 (L0-core / L1-long / L2-mid / L3-short): `../cortex-schema/references/memory-levels.md`
- 三轴判定 (抗遗忘 / 强度 / 复用面): `../cortex-extract/references/classifier.md` (复用算法, 不重写)
- 落盘前 lint 检查: 调用 `cortex-lint` skill (frontmatter 合规校验)

## 安全

- 默认 dry-run, JSON plan 中正文截前 80 字摘要 (保护敏感数据)
- `--apply` 前必须用户审 plan
- L0 候选 **永远 ask** (即使 --apply, 需 env `CORTEX_EXTRACT_L0_AUTO=accept` 自动批准)
- 不识别字段 skip + warn (transcripts 格式漂移容忍)
