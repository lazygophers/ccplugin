---
name: cortex-refactor
description: vault 重构 — rename / merge / split / fold, 默认 dry-run, --apply 才落盘并 backup。仅显式触发 (disable-model-invocation: true)。
argument-hint: "<rename|merge|split|fold> [args...]"
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_list_files_in_dir
---

# cortex-refactor

vault 大动干戈类操作的统一入口。**全部默认 dry-run**, 用户明确 `--apply` 才改盘。

## 子操作

### rename — 改文件名 + 全 vault wikilink 同步

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/refactor/rename.py \
  --vault <path> --from <old-rel> --to <new-rel> [--apply]
```

- 扫全 vault `[[old-stem]]` 与 `![[old-stem]]`, 替换为新 stem
- 不动 alias 字段 (用户决定是否保留)
- backup → `_meta/.cortex-backup/refactor-rename/<ts>/`

### merge — 两页合一

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/refactor/merge.py \
  --vault <path> --from <src> --into <target> [--apply]
```

- `<src>` 内容 (去 frontmatter) 追加到 `<target>` 末尾, 用 H2 分隔
- 全 vault 反链 `[[<src-stem>]]` 重定向到 `<target-stem>`
- `<src>` 移到 `80_archive/` (LYT) 或 `.archive/` (其他 preset)
- 时间戳前缀避免 archive 内重名

### split — 一页按 H2 拆多页

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/refactor/split.py \
  --vault <path> --from <src> [--out-dir <dir>] [--apply]
```

- 每个 H2 节生成一个新页 `<src-stem>--<slug>.md`
- 原页保留, 末尾追加 `> [!info] split into:` callout 列出子页
- 重名不覆盖 (跳过)

### fold — log/ 滚动归档至 folds/

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/refactor/fold.py \
  --vault <path> [--days N] [--apply]
```

- 默认保留近 7 天 log 不动
- 早于 cutoff 的 log 按月聚合到 `folds/YYYY-MM-fold-NNN.md` (NNN 三位序号, 续号)
- 折叠完成后删除原 log 文件 (backup 已存)

## 触发场景

- 用户明确说"重命名 X 到 Y / 合并 A B / 把这页拆开 / 整理日志"
- `/cortex:lint` 命中 `path-naming-violation` / `filename-illegal` 后用户授权修复
- cron weekly 任务调 `fold --days 7 --apply`

## 安全约束

1. 默认 dry-run, 输出 JSON plan
2. `--apply` 前在 `_meta/.cortex-backup/refactor-<op>/<ts>/` 全量 backup 涉及文件
3. **不**自动 git commit (与 `cortex` 整体策略一致, OGit 用户依赖外部备份)
4. rename/merge 永不覆盖已存在的目标
5. 大批量操作建议先 `--apply` 跑一个文件验证, 再扩大范围

## 输出示例 (rename dry-run)

```json
{
  "op": "rename",
  "from": "10_concepts/foo.md",
  "to": "10_concepts/foo-bar.md",
  "files_to_update": [
    {"file": "log/2026-05/10-1430-design.md", "replacements": 2},
    {"file": "60_dashboards/concepts-dashboard.md", "replacements": 1}
  ],
  "applied": false
}
```

用户确认后再加 `--apply` 重跑。
