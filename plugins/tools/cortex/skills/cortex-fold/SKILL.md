---
name: cortex-fold
description: 把 log/ 旧条目按月滚动归档至 folds/YYYY-MM-fold-NNN.md, 默认保留近 7 天, --apply 才落盘并 backup。Triggers on "fold logs", "归档日志", "整理日志".
allowed-tools: Bash Read Write Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_list_files_in_dir
---

# cortex-fold

把陈旧的 log 条目滚动归档到 `folds/`, 控制 log/ 目录大小。

## 触发场景

- 用户说"整理一下 log / fold logs / 归档日志"
- cron weekly 任务自动调用
- `cortex-lint` 命中 `log-too-long` 时建议触发

## 行为

调 `${CLAUDE_PLUGIN_ROOT}/refactor/fold.py`:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/refactor/fold.py \
  --vault <path> [--days N] [--apply]
```

- `--days N` (默认 7): 保留最近 N 天 log 不动
- 早于 cutoff 的按月聚合到 `folds/YYYY-MM-fold-NNN.md`
- NNN 三位续号, 已存在的 fold 文件不动
- frontmatter 自动填 `type: fold` + `created/updated`
- 每个原 log 在 fold 内以 `## from [[<stem>]]` 起头, wikilink 保持可达
- backup → `_meta/.cortex-backup/refactor-fold/<ts>/`
- 折叠完成后删除原 log 文件 (用户可从 backup 恢复)

## 命名规则 (与 prd §3.2.7 一致)

- 路径: `folds/YYYY-MM-fold-NNN.md`
- NNN: 三位数字, 从 001 起递增
- 同月可有多个 fold (不同次操作累积)

## 安全

- 默认 dry-run, 输出 JSON plan (列出每月哪些文件将被折叠)
- `--apply` 前 backup 全部待折叠的源文件
- 已经在 folds/ 的文件不再二次折叠
- 永不修改 hot.md / index.md

## 输出示例 (dry-run)

```json
{
  "op": "fold",
  "buckets": [
    {"month": "2026-04", "files": ["log/2026-04/01-1430-x.md", ...],
     "fold_target": "folds/2026-04-fold-002.md", "count": 23}
  ],
  "applied": false,
  "cutoff_days": 7
}
```

## 与其他 skill 协作

- `cortex-lint` rule#7 (log-too-long) 命中后建议 cortex-fold
- `cortex-search` 在 fold 中检索时, wikilink `[[<stem>]]` 仍可解析到 fold 内段落 (依赖 block-id)
