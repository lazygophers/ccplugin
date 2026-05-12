---
name: cortex-refactor
description: vault 重构 — rename/merge/split/fold/migrate-locale, --apply 才落盘 backup。仅显式触发。
argument-hint: "<rename|merge|split|fold|migrate-locale> [args...]"
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_list_files_in_dir
---

# cortex-refactor

vault 大动干戈类操作的统一入口。**全部默认 dry-run**, 用户明确 `--apply` 才改盘。

## 子操作

### rename — 改文件名 + 全 vault wikilink 同步

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/rename.py \
  --vault <path> --from <old-rel> --to <new-rel> [--apply]
```

- 扫全 vault `[[old-stem]]` 与 `![[old-stem]]`, 替换为新 stem
- 不动 alias 字段 (用户决定是否保留)
- backup → `_meta/.cortex-backup/refactor-rename/<ts>/`

### merge — 两页合一

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/merge.py \
  --vault <path> --from <src> --into <target> [--apply]
```

- `<src>` 内容 (去 frontmatter) 追加到 `<target>` 末尾, 用 H2 分隔
- 全 vault 反链 `[[<src-stem>]]` 重定向到 `<target-stem>`
- `<src>` 移到 `80_archive/` (LYT) 或 `.archive/` (其他 preset)
- 时间戳前缀避免 archive 内重名

### split — 一页按 H2 拆多页

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/split.py \
  --vault <path> --from <src> [--out-dir <dir>] [--apply]
```

- 每个 H2 节生成一个新页 `<src-stem>--<slug>.md`
- 原页保留, 末尾追加 `> [!info] split into:` callout 列出子页
- 重名不覆盖 (跳过)

### fold — log/ 滚动归档至 folds/

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/fold.py \
  --vault <path> [--days N] [--apply]
```

- 默认保留近 7 天 log 不动
- 早于 cutoff 的 log 按月聚合到 `folds/YYYY-MM-fold-NNN.md` (NNN 三位序号, 续号)
- 折叠完成后删除原 log 文件 (backup 已存)

### migrate-locale — 切 vault.lang 时一次性 rename 业务目录

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/migrate_locale.py \
  --vault <path> --from <lang> --to <lang> [--apply]
```

- 比对两个 lang 的 `dirs` map, 对每对差异计划 rename
- git repo 走 `git mv` (保留历史), 否则 `os.rename`
- 全 vault wikilink 替换 (path-prefixed)
- 写 `_meta/version.json:.lang = <to>` + `_meta/migrations/<ts>-migrate-locale.json`
- 默认 dry-run, `--apply` 才落盘

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
		{ "file": "log/2026-05/10-1430-design.md", "replacements": 2 },
		{ "file": "60_dashboards/concepts-dashboard.md", "replacements": 1 }
	],
	"applied": false
}
```

dry-run 结束后, **必须调 `AskUserQuestion`** 工具询问: "已扫描 N 个文件 M 处替换, 是否应用?" options: `应用 (--apply 重跑)` / `取消` / `仅看 diff`; 用户选 `应用` 才加 `--apply` 重跑。

L3 写盘授权门: 涉及 ≥3 文件批量改写时, `AskUserQuestion` 问题文案需列出受影响文件路径 (per-batch 单次授权); <3 文件 per-file 逐个授权。

## 新增子命令 (deep refactor)

下列子命令均默认 dry-run, `--apply` 才落盘; 落盘前会 backup 至 `_meta/.cortex-backup/<op>/<ts>/`。

| 子命令          | 签名                                                                                                 | 说明                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| restructure     | `--vault P --from <preset> --to <preset> [--apply]`                                                  | vault 目录预设迁移 (flat/LYT/PARA); 落盘后全 vault wikilink 同步         |
| dedupe          | `--vault P [--scope all\|concepts\|domains\|log] [--threshold 0.85] [--top-k 20] [--apply]`          | 用 TF-IDF cosine 找 ≥ threshold 的候选页对; `--apply` 调 `merge.py` 合并 |
| extract         | `extract_inline.py --vault P --page REL --section H2 --direction extract [--out-path REL] [--apply]` | 抽 H2 节为独立 concept 页, 父页留 `![[child-stem]]`                      |
| inline          | `extract_inline.py --vault P --page REL --child REL --direction inline [--section H2] [--apply]`     | 子页内联回父页, 子页归档, 全 vault wikilink 同步                         |
| graph-rebalance | `graph_rebalance.py --vault P [--hub-threshold 20] [--scope all] [--apply]`                          | 扫 orphan / hub; `--apply` 仅自动补 link_gaps, hub 拆分仅提示            |

调用模板:

```bash
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/restructure.py \
  --vault "$VAULT" --from flat --to LYT
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/dedupe.py \
  --vault "$VAULT" --scope concepts --threshold 0.85
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/extract_inline.py \
  --vault "$VAULT" --page 10_concepts/parent.md --section "Detail" \
  --direction extract
python3 ~/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex/refactor/graph_rebalance.py \
  --vault "$VAULT" --hub-threshold 20
```

所有新子命令输出 JSON, 字段含 `op / applied`, dry-run 字段视子命令而定 (mv_plan/link_plan/candidates/orphans/hubs/link_gaps)。
