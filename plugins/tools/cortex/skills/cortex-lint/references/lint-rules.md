# cortex-lint — 18 条规则 + 输出格式

## 规则表 (rules.json)

| # | id | severity | autofix |
|---|---|---|---|
| 1 | fm-missing-type | error | ✓ (按目录推断) |
| 2 | fm-missing-created | warn | ✓ (用 mtime) |
| 3 | dead-wikilink | error | ✗ (建议 cortex-save 创建 stub) |
| 4 | orphan-page | warn | ✗ (人工补 tag/链接) |
| 5 | duplicate-alias | error | ✗ (人工合并) |
| 6 | hot-too-long | warn | ✓ (截断+落 归档/) |
| 7 | log-too-long | warn | ✗ (digest 自动归档) |
| 8 | index-missing-section | warn | ✓ (自动补条目) |
| 9 | title-h1-mismatch | warn | ✓ (以 frontmatter 为准) |
| 10 | filename-illegal | error | ✗ (cortex-refactor rename) |
| 11 | block-id-duplicate | error | ✓ (重哈希) |
| 12 | callout-unknown-type | warn | ✗ (报告) |
| 13 | path-naming-violation | warn | ✗ (cortex-refactor rename) |
| 14 | fm-duplicate-tags | warn | ✓ (保序去重) |
| 15 | fm-banned-tags | warn | ✓ (移除 index/meta/template/_index/stub) |
| 16 | fm-banned-fields | warn | ✓ (移除 preset 等) |
| 17 | fm-missing-tags | warn | ✓ (字段缺失或非 list; autofix 读 fm+正文派生语义 tag, 严禁占位) |
| 18 | path-lang-mismatch | warn | ✗ (vault path segment 不符 vault.lang; 豁免 host/org/repo + ASCII 专名 + frontmatter `path_lang_exempt`; rename 走 cortex-refactor) |

**注**: 21 条规则总数包含本表 18 条 + rule 19 `skill-references-exists` + rule 20 `base-format-yaml` + rule 21 `frontmatter-required-scores` (4 评分字段, 见 `schema-validate.md`)。

模板/示例文件可在 frontmatter 加 `lint-skip: true` 跳过全部检查 (供 `_templates/**/*.md` 使用)。

## 错误/警告分类

- **errors (severity=error)**: rule 1, 3, 5, 10, 11
- **warns (severity=warn)**: rule 2, 4, 6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18

## 输出格式

返回给用户的 markdown 报告:

```
## cortex-lint 报告

vault: <abs path>
files scanned: N
errors: E   warns: W   fixed: F

### errors

| rule | file | line | msg |
| --- | --- | --- | --- |
...

### warns

(同上)
```

按 rule 分组列前 20 条命中。

## --fix 行为

仅对 `autofix:true` 规则改盘 (rule 1/2/6/8/9/11/14/15/16/17)。其他规则需用户手工处理 (cortex-refactor 可协助 rename/merge)。
