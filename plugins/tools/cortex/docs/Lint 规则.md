# Lint 规则

本文回答：cortex-lint 的 17 条 规则各自检查什么、哪些能 autofix、`--fix` 行为是什么。
适用读者：跑 `cortex-lint` 看到 errors/warns 想知道含义的用户、写 cron 自动修复的运维。

## 总览

定义文件：`lint/rules.json`。版本 1, 17 条 规则。

| # | id | severity | autofix | 简述 |
|---|----|----|---|------|
| 1 | `fm-missing-type` | error | ✅ | frontmatter 缺 `type` 字段 |
| 2 | `fm-missing-created` | warn | ✅ | frontmatter 缺 `created` 字段 |
| 3 | `dead-wikilink` | error | ❌ | wikilink 指向不存在的页 |
| 4 | `orphan-page` | warn | ❌ | 无入链且无 tag 的孤儿页 |
| 5 | `duplicate-alias` | error | ❌ | alias 跨页冲突 |
| 6 | `hot-too-long` | warn | ✅ | hot.md 超 200 行 |
| 7 | `log-too-long` | warn | ❌ | log 单文件 > 2000 行, 需 fold |
| 8 | `index-missing-section` | warn | ✅ | index.md 未包含某 wiki 顶级子目录 |
| 9 | `title-h1-mismatch` | warn | ✅ | H1 与 frontmatter title 不一致 |
| 10 | `filename-illegal` | error | ❌ | 文件名含非法字符或与 alias 冲突 |
| 11 | `block-id-duplicate` | error | ✅ | block-id 重复 (`^cortex-<sha8>`) |
| 12 | `callout-unknown-type` | warn | ❌ | callout 类型不在 13 类白名单 |
| 13 | `path-naming-violation` | warn | ❌ | 文件路径不符命名规则 (prd §3.2.7) |

autofix 仅 6 条 (rule 1/2/6/8/9/11)。其余需人工或用 `cortex-refactor` 协助。

## 逐条说明

### 1. fm-missing-type (error, autofix)

frontmatter 必须有 `type` 字段, 否则 cortex-search / cortex-save 无法识别。

- **autofix 策略**：根据所在目录推断 — `知识库/领域/` → `concept`, `知识库/项目/` → `entity` 等。

### 2. fm-missing-created (warn, autofix)

`created` 用于 dashboard 排序与 `cortex-fold` 判定。

- **autofix 策略**：用文件系统 mtime 写入 ISO 8601 字符串。

### 3. dead-wikilink (error, **手动**)

wikilink `[[X]]` 找不到对应文件。

- **不自动修复**：可能用户正在打字或刚改名。建议跑 `cortex-refactor rename` 改名时同步反链。

### 4. orphan-page (warn, **手动**)

无入链 (无任何文件链到它) 且无 tag 的页。可能是漂浮的 fleeting note。

- **建议**：给加 tag, 或链入相关 MOC, 或归档到 `80_archive/` (LYT) / `4_archive/` (PARA)。

### 5. duplicate-alias (error, **手动**)

两个文件 frontmatter `aliases` 列表里有重复值, Obsidian 跳转时会歧义。

- **建议**：人工决定哪个保留 alias, 另一个删除或改名。

### 6. hot-too-long (warn, autofix)

`hot.md` 用于 SessionStart 注入, 太长会爆 5KB 上限。

- **autofix 策略**：保留最近 200 行, 多余截到 `folds/hot-archive-YYYYMMDD.md`。

### 7. log-too-long (warn, **手动**)

`log/YYYY-MM/<file>.md` 超 2000 行, 需 fold。

- **建议**：跑 `cortex-fold --apply` 或 `cortex-refactor fold`。

### 8. index-missing-section (warn, autofix)

`index.md` 没有覆盖某个 wiki 顶级子目录 (新加目录后忘了同步)。

- **autofix 策略**：扫 vault 顶层目录, 缺的章节自动追加。

### 9. title-h1-mismatch (warn, autofix)

frontmatter `title: A` 但正文 H1 是 `# B`。

- **autofix 策略**：以 H1 为准覆写 frontmatter (避免改用户正文)。可通过 `lint.prefer_frontmatter` 反转。

### 10. filename-illegal (error, **手动**)

文件名包含 `[/\:*?"<>|]` 等非法字符, 或与某 alias 冲突。

- **建议**：用 `cortex-refactor rename` 修正 (它会自动改反链)。

### 11. block-id-duplicate (error, autofix)

两个段落都用 `^cortex-abc12345`, 跳转歧义。

- **autofix 策略**：保留第一个出现, 其余重新算 sha8 (基于段落原文 + 文件路径)。

### 12. callout-unknown-type (warn, **手动**)

`> [!xxx]` 中 `xxx` 不在 13 类白名单 (见 `模板与美化.md`)。

- **建议**：换成最接近的标准类型 (e.g. `[!hint]` → `[!tip]`)。

### 13. path-naming-violation (warn, **手动**)

文件路径违反命名规则：

- 文件名只用 `[\w一-鿿\-\.]`
- domain 必须 `知识库/来源/代码仓库/<host>/<org>/<repo>/` 三层
- log 必须 `DD-HHMM-<slug>.md`

详见 `知识库结构.md#路径与命名规则`。

## --fix 行为

```bash
# dry-run (默认), 仅报告
python3 lint/run.py --vault /path/to/vault

# 修盘, 自动 backup 原文件到 .cortex-backup/<timestamp>/
python3 lint/run.py --vault /path/to/vault --fix
```

或自然语言：

```text
"wiki audit --fix"
"vault 体检 然后修复"
```

`--fix` 仅对 6 条 autofix 规则生效。其余规则即使加 `--fix` 也只报告。

## 输出格式

```json
{
  "version": 1,
  "vault": "/path/to/vault",
  "summary": {"errors": 2, "warns": 5, "fixed": 3, "skipped": 4},
  "issues": [
    {"rule": "fm-missing-type", "severity": "error", "file": "...", "line": 1, "fixed": true},
    ...
  ]
}
```

## 配置

`~/.cortex/config.json` 的 `lint` 段：

```json
{
  "lint": {
    "ignore": ["dead-wikilink", "orphan-page"],
    "fix_on_save": false
  }
}
```

`ignore` 跳过指定 rule id。`fix_on_save=true` 让 cortex-save 写完立即跑 `lint --fix`。

## 相关文档

- `Skills 详解.md` — cortex-lint 触发短语
- `重构与归档.md` — 复杂修复用 cortex-refactor
- `周期任务.md` — daily lint --fix cron snippet
- `模板与美化.md` — callout 13 类白名单
- `知识库结构.md` — 路径命名规则原文
