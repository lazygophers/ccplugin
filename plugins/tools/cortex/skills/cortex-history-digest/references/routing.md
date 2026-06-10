# routing — 候选 → 全局记忆库路由

> history-digest 落点**恒为全局** `~/.cortex/.wiki/memory/`. 不写项目/领域模块 (与 cortex-extract 区分: extract 走 L4-inbox 已收件资料, 含项目/领域; history-digest 走 transcripts 增量, 仅 memory).

## 目标根

```
$target/.wiki/memory/
├── L0-core/        硬性规则 (永远 ask)
├── L1-long/        长期 (用户校正 / 高强度决策)
├── L2-mid/         中期 (决策 / 踩坑 / 默认复用面 ≥ 3 候选)
└── L3-short/       短期 (默认入口; 单次决策 / 弱信号)
```

`$target` 默认 `$HOME/.cortex`, 由 `--target` 覆盖. **路径段权威**: `../../cortex-schema/references/memory-levels.md` (history-digest 不重写路径段定义).

## 候选 → 层级映射

```
候选.suggested_level (来自 parser 信号词) 
  ↓
经三轴判定 (../../cortex-extract/references/classifier.md 算法)
  ↓
最终目标目录 + 是否附 promote 标
```

| parser kind | 默认 suggested_level | 经三轴可能升级到 |
| --- | --- | --- |
| L0-rule | L0-core | L0-core (固定; 永远 ask) |
| user-correction | L1-long | L1-long / L0-core (若含"硬性"等 L0 关键词) |
| decision | L2-mid / L3-short | L2-mid → L1-long (复用 ≥ 5 + weight ≥ 0.8) |
| tip | L2-mid | L2-mid → L1-long (复用 ≥ 5) |

## 文件命名

```
$target/.wiki/memory/<level>/history-<YYYYMMDD>-<id12>.md
```

- `YYYYMMDD` = 候选 timestamp 的日期
- `id12` = candidate.id (sha256 前 12 位)
- 后缀强制 `.md` (符合 cortex-schema)

文件 frontmatter (落盘时):

```yaml
---
created: <ISO 8601>
source: history-digest
session_file: <jsonl path>
session_id: <uuid>
project_slug: <slug>
kind: user-correction|decision|tip|L0-rule
weight: 0.0-1.0
occurrences: <int>      # 复用面计数
trigger_keywords: [...]
---
```

正文 = 完整原文 (非 80 字摘要 — 摘要只用于 dry-run plan).

## dry-run JSON plan schema

```json
{
  "version": 1,
  "generated_at": "ISO 8601",
  "source_root": "/home/x/.claude/projects",
  "target": "/home/x/.cortex",
  "since": null,
  "stats": {
    "files_scanned": 12,
    "lines_parsed": 4321,
    "candidates": 8,
    "warnings": 3
  },
  "candidates": [
    {
      "id": "...",
      "kind": "user-correction",
      "suggested_level": "L1-long",
      "target_path": "/home/x/.cortex/.wiki/memory/L1-long/history-20250609-abc123.md",
      "text_excerpt": "...前 80 字...",
      "weight": 0.7,
      "occurrences": 1,
      "promote_marks": [],
      "needs_user_review": true,
      "source": {
        "session_file": "/home/x/.claude/projects/.../<uuid>.jsonl",
        "session_id": "...",
        "timestamp": "..."
      }
    }
  ],
  "warnings": [
    {"file": "...", "line": 42, "error": "json parse failed"}
  ]
}
```

## --apply 行为 (本 task 范围仅文档, 不实现)

1. 对每个候选, 若 `kind == L0-rule` → 必须 user accept (env `CORTEX_EXTRACT_L0_AUTO` 控制; 默认 ask 阻断)
2. 写文件到 `target_path` (frontmatter + 正文)
3. 落盘前调 `cortex-lint` 校验 frontmatter 合规
4. 更新 cursor (后续 task 引入)
5. 输出 apply 报告 (创建数 / 跳过数 / 失败数)

## 敏感数据保护

| 防护 | 实现 |
| --- | --- |
| dry-run plan 不暴露完整对话 | `text_excerpt` 严格 80 字截断 |
| --apply 前必须用户审 | runner 输出 plan 后停, 等待 `--apply` 二次调用 |
| L0 永远 ask | 即使 --apply, env `CORTEX_EXTRACT_L0_AUTO=ask` (默认) 仍阻断 |
| 不在 plan 中显示 cwd / token / 凭证 | parser 过滤含 `sk-/ghp_/Bearer /password` 等高敏特征的候选 (skip + warn) |

## 与 cortex-extract / cortex-save 边界

| skill | 数据源 | 落点 |
| --- | --- | --- |
| cortex-history-digest (本) | transcripts | 仅 memory (L0-L3) |
| cortex-extract | L4-inbox .md 文件 | L0-L4 + 项目 + 领域 |
| cortex-save | 单次快速存 (用户主动调) | 由用户指定层级 |

history-digest **不写 L4-inbox** (它直接路由到 L0-L3, 跳过 inbox 暂存), 因 transcripts 已经是过滤后的增量, 无需再过收件箱.
