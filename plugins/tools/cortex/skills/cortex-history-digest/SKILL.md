---
name: cortex-history-digest
description: "Claude Code 会话历史整理 — 扫 ~/.claude/projects/**/*.jsonl 全部 session transcripts, 提取学习增量 (用户校正/决策/踩坑/L0 规则) → 全局记忆库 ~/.cortex/.wiki/memory/. 默认 --apply 落盘 (--dry-run opt-in 仅出 JSON plan 预览). 与 cortex-extract (L4-inbox 内部) 互补."
when_to_use: "整理 Claude Code 历史/digest transcripts/沉淀历史会话/扫 ~/.claude/projects/回顾/历史学习增量提取"
argument-hint: "[--dry-run|--apply] [--target <vault>]"
arguments: "[--dry-run|--apply] [--target <仓库根>]"
user-invocable: true
disable-model-invocation: true
context: fork
agent: cortex-history-worker
---

# cortex-history-digest

Claude Code 历史 transcripts → 全局记忆库. 扫 `~/.claude/projects/**/*.jsonl` 全部 session 历史, 抽**学习增量** (用户校正 / 关键决策 / 踩坑 / L0 硬性规则), 经三轴判定路由到 `~/.cortex/.wiki/memory/L0-core | L1-long | L2-mid | L3-short`. 默认 `--apply` 落盘 (`--dry-run` opt-in 仅出 JSON plan 预览).

> 破坏性提示：默认 `--apply` 会向全局记忆库落盘 (含 L0-core 项直接落盘, 不再 ask)；只想看计划不落盘时显式传 `--dry-run`。

## 后台执行段 (cortex-history-worker 执行)

本段由 `context: fork` 派 `cortex-history-worker` 后台跑：扫 transcripts，抽学习增量，三轴判定路由，默认 `--apply` 直接落盘 (含 L0-core 项自动落盘)，落盘后调用 `cortex-lint` 校 frontmatter 合规。

```bash
bash plugins/tools/cortex/scripts/history-digest.sh
bash plugins/tools/cortex/scripts/history-digest.sh --source-root ~/.claude/projects --target $HOME/.cortex
```

默认 `--apply` + `target=$HOME/.cortex` + `source-root=$HOME/.claude/projects`. `--since YYYY-MM-DD` 增量过滤 (默认全量). worker 把落盘结果 (正文截前 80 字摘要保护敏感数据 / 各条目目标 level) 作为报告返回主会话。

仅预览 (不落盘) 时显式传 `--dry-run`：

```bash
bash plugins/tools/cortex/scripts/history-digest.sh --dry-run
```

## 何时读哪个 reference

| 任务 | 文件 |
| --- | --- |
| 查 transcripts 目录结构 + jsonl message schema | `references/sources.md` |
| 查 "学习增量" 识别算法 (用户校正 / 决策 / 踩坑 / L0 关键词) | `references/parser.md` |
| 查路由到 L0-L4 + 三轴复用 + 敏感保护 | `references/routing.md` |

## 入口命令

```bash
bash plugins/tools/cortex/scripts/history-digest.sh            # 默认 --apply 落盘
bash plugins/tools/cortex/scripts/history-digest.sh --source-root ~/.claude/projects --target $HOME/.cortex
bash plugins/tools/cortex/scripts/history-digest.sh --dry-run  # opt-in 预览, 不落盘
```

默认 `--apply` + `target=$HOME/.cortex` + `source-root=$HOME/.claude/projects`. `--since YYYY-MM-DD` 增量过滤 (默认全量).

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

- 正文落盘前截前 80 字摘要进 plan / 报告 (保护敏感数据); `--dry-run` 仅出 plan 不落盘
- 默认 `--apply` 直接落盘; 需事前审计时显式传 `--dry-run` 预览
- L0 候选默认直接落盘 (不再 ask); env `CORTEX_EXTRACT_L0_AUTO=reject` 可拦核心规则误写
- 不识别字段 skip + warn (transcripts 格式漂移容忍)
