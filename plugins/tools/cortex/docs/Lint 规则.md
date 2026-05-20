# Lint 规则

本文回答：cortex-lint 的 30 条 规则各自检查什么、哪些能 autofix、`--fix` 行为是什么。
适用读者：跑 `cortex-lint` 看到 errors/warns 想知道含义的用户、写 cron 自动修复的运维。

## 总览

定义文件：`scripts/lint/rules.json`。版本 1, 30 条 规则。

**范围**: 全部规则作用于 知识库 **知识库 (vault)** — 即 `~/.cortex/config.json:.vault` 指向的目录。不影响 全局 全局配置 / 当前目录 / 记忆层 记忆层。

| # | id | severity | autofix | 简述 |
|---|----|----|---|------|
| 1 | `fm-missing-type` | error | ✅ | frontmatter 缺 `type` 字段 |
| 2 | `fm-missing-created` | warn | ✅ | frontmatter 缺 `created` 字段 |
| 3 | `fm-duplicate-tags` | warn | ✅ | frontmatter tags 列表内重复 |
| 4 | `fm-banned-tags` | warn | ✅ | tags 含结构/模板/类型/时间标记 (`index/meta/template/_index/stub` + `type/* template/* created/* date/* time/* year/month/week/day/quarter/*` + 裸 `YYYY[-MM[-DD]]/YYYY-Q[1-4]/YYYY-W##`) |
| 5 | `fm-banned-fields` | warn | ✅ | frontmatter 含废弃字段 (如 `preset`), autofix pop |
| 6 | `fm-missing-tags` | warn | ✅ | tags 字段缺失或非 list; autofix 从正文派生语义 tag (严禁占位符/模板/类型/时间式) |
| 7 | `dead-wikilink` | error | ✅ | wikilink 指向不存在的页 |
| 8 | `orphan-page` | warn | ✅ | 无入链且无 tag 的孤儿页 |
| 9 | `duplicate-alias` | error | ✅ | alias 跨页冲突 |
| 10 | `hot-too-long` | warn | ✅ | hot.md 超 200 行 |
| 11 | `index-missing-section` | warn | ✅ | index.md 未包含某 知识库 顶级子目录 |
| 12 | `title-h1-mismatch` | warn | ✅ | H1 与 frontmatter title 不一致 |
| 13 | `filename-illegal` | error | ❌ | 文件名含非法字符或与 alias 冲突 |
| 14 | `block-id-duplicate` | error | ✅ | block-id 重复 (`^cortex-<sha8>`) |
| 15 | `callout-unknown-type` | warn | ✅ | callout 类型不在 13 类白名单 |
| 16 | `path-naming-violation` | warn | ✅ | 业务目录命名应来自 vault.lang 的 dirs map |
| 17 | `i18n-frontmatter-lang-mismatch` | warn | ❌ | 页 frontmatter lang 与 `_meta/version.json:.lang` 不一致 |
| 18 | `i18n-path-not-in-locale` | warn | ✅ | 业务目录名不在 vault.lang 的 dirs map; autofix slug-safe rename |
| 19 | `vault-structure-violation` | error | ✅ | vault 根/子目录含非 schema 允许的文件; autofix mv 到 `~/.cache/cortex/lint-backup` |
| 20 | `vault-misaligned` | warn | ✅ | vault 内 plugin-managed 文件 (seed/_meta/_templates) 偏离源, 强制覆盖头部, `TEMPLATE_END` 后用户内容保留 |
| 21 | `repo-path-deprecated` | warn | ✅ | `知识库/来源/代码仓库/<host>/<org>/<repo>/` 废弃, mv 到 `知识库/项目/<host>/<org>/<repo>/` |
| 22 | `reflection-path-deprecated` | warn | ✅ | `知识库/反思/` 废弃, mv 到 `知识库/收件箱/` |
| 23 | `question-fleeting-path-deprecated` | warn | ✅ | `知识库/问题/` 与 `知识库/临时/` 废弃, mv 到 `知识库/收件箱/` |
| 24 | `entity-concept-path-deprecated` | warn | ❌ | `知识库/实体/` 与 `知识库/概念/` 废弃, 应迁到 `知识库/领域/<域>/<kebab>.md` (需 AI 选域, lint 不自决) |
| 25 | `journal-multi-freq-deprecated` | warn | ✅ | `知识库/日记/{周/月/年}/` 废弃, mv 到 `归档/日记/<YYYY-QN>.md` 季度桶 |
| 26 | `source-non-repo-path-deprecated` | warn | ✅ | `知识库/来源/{网页/论文/书籍}/` 废弃, mv 到 `知识库/收件箱/` |
| 27 | `path-lang-mismatch` | warn | ❌ | vault path segment 不符 vault.lang (豁免 host/org/repo + ASCII 专名 + `path_lang_exempt`) |
| 28 | `skill-references-exists` | warn | ❌ | SKILL.md / AGENT.md 引用 `references/<x>.md` 目标必须存在 |
| 29 | `base-format-yaml` | warn | ❌ | `.base` 文件必须顶层 YAML object, 禁 markdown header / 禁 Dataview DQL |
| 30 | `frontmatter-required-scores` | warn | ✅ | 知识库 .md 必含 4 评分字段, 记忆 .md 必含 2 评分字段, 0.0-10.0 浮点 |

autofix 24 条; 6 条 (rule 13/17/24/27/28/29) 不 autofix, 需人工或用 `cortex-refactor` 协助。

### rule 23: frontmatter-required-scores

**触发**: 知识库 `.md` (项目/领域/日记, 排除 收件箱) 缺 `score` / `confidence` / `source_credibility` / `maturity` 任一; 记忆 `.md` (L0-L4) 缺 `importance` / `confidence` 任一; 或值类型/范围越界 (非 float 0.0-10.0, maturity 非 4 enum)。

**校验**: 全 0.0-10.0 浮点 (越界 clamp); `maturity` enum: `draft|review|stable|deprecated`。

**Autofix**: 缺字段 → 加 stub `0.0` (maturity → `draft`); 类型错 → coerce float; 越界 → clamp。

**修复方案 (推荐, 历史 vault)**: 跑一次性 `bash ~/.cortex/scripts/migrate.sh --to=v2`, 自动处理旧 `score: 1-5 整数` → `0-10 浮点 × 2.0` 及缺字段加 stub, 比 lint autofix 智能 (含 patterns.md confidence 0-1 → 0-10 迁移)。

**不变量**:
- `score` / `confidence` / `source_credibility`: float [0, 10]
- `maturity`: enum
- `importance`: float [0, 10] (仅记忆)
- 跳过: `仪表盘/` / `归档/` / `.obsidian/` / `.trash/` / `_meta/` / `_templates/` / `_assets/` / `知识库/收件箱/`

### rule 22: base-format-yaml

**触发**: `.base` 文件 (`知识库/项目/<host>/<org>/<repo>/_db.base` 等)。跳过 `.obsidian/` / `归档/` / `.trash/`。

**校验**:

1. 首行禁 markdown header (`#` / `##`)
2. 禁 Dataview DQL 行首关键字 (TABLE / LIST / TASK / FROM / WHERE / SORT / GROUP BY / FLATTEN) — Bases ≠ Dataview
3. YAML 必须成功解析
4. 顶层必须是 object (dict), 不能是 list / string / None
5. 顶层至少含 1 个 Bases schema 字段 (`filters` / `views` / `formulas` / `properties`)

**修复**: AI 重新落档时遵守 `skills/cortex-ingest/references/knowledge-graph.md §9.1` 模板; 或用户主动调 `bash ~/.cortex/scripts/ingest_remote.sh <项目 url>` 重 ingest 项目覆盖。

**不 autofix**: 用户 `.base` 数据敏感, 不直接 patch。lint 仅报警, 用户自行重 ingest 或人工修改。

## 逐条说明

### 1. fm-missing-type (error, autofix)

frontmatter 必须有 `type` 字段, 否则 cortex-search / cortex-save 无法识别。

- **autofix 策略**：根据所在目录推断 — `知识库/领域/` → `concept`, `知识库/项目/` → `entity` 等。

### 2. fm-missing-created (warn, autofix)

`created` 用于 dashboard 排序与 `` 判定。

- **autofix 策略**：用文件系统 mtime 写入 ISO 8601 字符串。

### 3. dead-wikilink (error, **手动**)

wikilink `[[X]]` 找不到对应文件。

- **不自动修复**：可能用户正在打字或刚改名。建议跑 `cortex-refactor rename` 改名时同步反链。

### 4. orphan-page (warn, **手动**)

无入链 (无任何文件链到它) 且无 tag 的页。可能是漂浮的 fleeting note。

- **建议**：给加 tag, 或链入相关概念页, 或归档到 `80_archive/` (LYT) / `4_archive/` (PARA)。

### 5. duplicate-alias (error, **手动**)

两个文件 frontmatter `aliases` 列表里有重复值, Obsidian 跳转时会歧义。

- **建议**：人工决定哪个保留 alias, 另一个删除或改名。

### 6. hot-too-long (warn, autofix)

`hot.md` 用于 SessionStart 注入, 太长会爆 5KB 上限。


### 7. log-too-long (warn, **手动**)

`log/YYYY-MM/<file>.md` 超 2000 行, 需 fold。


### 8. index-missing-section (warn, autofix)

`index.md` 没有覆盖某个 知识库 顶级子目录 (新加目录后忘了同步)。

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
- project/domain 必须 `知识库/项目/<host>/<org>/<repo>/` 三层 (local 时 host=local, org=basename)
- log 必须 `DD-HHMM-<slug>.md`

详见 `知识库结构.md#路径与命名规则`。

### 14. repo-path-deprecated (warn, **自动**)

`知识库/来源/代码仓库/<host>/<org>/<repo>/` 路径已废弃, autofix 自动 mv 到 `知识库/项目/<host>/<org>/<repo>/`, 并补全/修正 frontmatter (`type: domain` → `type: project`, 补 `host/org/repo` 字段)。

### 15. reflection-path-deprecated (warn, **自动**)

`知识库/反思/<rest>` 路径已废弃 (反思现作日记一项)。autofix 自动 mv 到 `知识库/收件箱/<basename>.md` (待 digest 重分配), 并在 frontmatter 追加 `was_path: 知识库/反思/<rest>` 用于追溯。

### 16. question-fleeting-path-deprecated (warn, **自动**)

`知识库/问题/<rest>` 与 `知识库/临时/<rest>` 路径已废弃。autofix 自动 mv 到 `知识库/收件箱/<basename>.md`, frontmatter 追加 `was_path`。

### 17. entity-concept-path-deprecated (warn, **自动**)

`知识库/实体/<rest>` 与 `知识库/概念/<rest>` 路径已废弃, 应迁到 `知识库/领域/<域>/<kebab>.md`。autofix 自动 mv 到 `知识库/领域/未分类/<basename>.md` (lint 时无 AI 上下文, 默认走未分类兜底), 并在 frontmatter 追加 `was_path:` 字段。后续 AI 可调 `cortex_refactor` 把已迁文件从 `未分类/` 改判到 6 域之一 (创作/学习/工作/技术/生活/金融)。

> autofix 后 post-cleanup 会 rmdir 空的 `知识库/实体/`、`知识库/概念/`、`知识库/来源/`、`知识库/反思/`、`知识库/问题/`、`知识库/临时/`、`知识库/日记/{周,月,年}/` 等已迁空的废弃根目录, 防止再次写入。

### 18. journal-multi-freq-deprecated (warn, **自动**)

`知识库/日记/{周|月|年}/<rest>` 路径已废弃 (仅日维度保留)。autofix 自动 mv 到 `归档/日记/<YYYY-QN>.md` 季度桶 (从 frontmatter `date:` 或文件名推算季度, 同季度合并到同一文件)。

### 19. source-non-repo-path-deprecated (warn, **自动**)

`知识库/来源/{网页|论文|书籍}/<rest>` 路径已废弃 (非 repo 来源统一落收件箱)。autofix 自动 mv 到 `知识库/收件箱/<host>-<slug>.md` (从 frontmatter `source.url` 或路径抽 host), 待 digest 分发到 `项目/<repo>/笔记/` 或 `领域/<域>/`。

### 20. path-lang-mismatch (warn, **手动**)

vault path segment (目录名 / 文件名) 不符 `_meta/version.json:.lang` 指定的 vault 主语言。

**检测逻辑** (逐 segment, 取 `vault.lang`, 默认 `zh-CN`):

- `zh-*`: segment 应含 CJK 字符 (`一-鿿`); 全 ASCII 段 (`^[A-Za-z0-9._\-]+$`) → flag
- `en`: segment 不含 CJK / Kana → 通过; 含 → flag
- `ja`: segment 含 Hiragana/Katakana/Kanji → 通过; 全 ASCII → flag

**豁免清单**:

- 顶层基础设施: `_meta` / `_templates` / `_assets` / `locales` / `.obsidian` / `.trash` / `.git` / `记忆` / `归档` / `仪表盘` (英文等价 `memory` / `archive` / `dashboard`)
- `知识库/项目/<host>/<org>/<repo>/` 前 5 段 (host / org / repo 由 git remote 决定, 不强制 lang 对齐); 英文 vault 等价 `kb/projects/<host>/<org>/<repo>/`
- ASCII 专名 stem: `README` / `LICENSE` / `CHANGELOG` / `CONTRIBUTING` / `pyproject` / `package` / `Cargo` / `go.mod` / `tsconfig` / `Makefile` / `Dockerfile` / `_index` / `index` / `hot` 等
- frontmatter `path_lang_exempt: true` (手动豁免单文件)

**修复指引**: 不 autofix (rename 涉及 wikilink 联动)。走 `cortex-refactor rename` 重命名, 同步更新反链; 或在 frontmatter 加 `path_lang_exempt: true` 标记本页为专名页。

**示例** (zh-CN vault):

- `知识库/项目/github.com/lazygophers/ccplugin/笔记/架构.md` ✅ (前 5 段豁免, 文件名含 CJK)
- `知识库/项目/github.com/lazygophers/ccplugin/architecture.md` ⚠ flag (`architecture.md` 全 ASCII, 非豁免 stem)
- `知识库/项目/github.com/lazygophers/ccplugin/README.md` ✅ (ASCII 专名豁免)
- `知识库/领域/技术/笔记/algorithm.md` ⚠ flag (建议 `算法.md` 或加 `path_lang_exempt: true`)

## --fix 行为

```bash
# dry-run (默认), 仅报告
python3 lint/run.py --vault /path/to/vault

# 修盘, 自动 backup 原文件到 .cortex-backup/<timestamp>/
python3 lint/run.py --vault /path/to/vault --fix
```

或自然语言：

```text
"知识库 audit --fix"
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
