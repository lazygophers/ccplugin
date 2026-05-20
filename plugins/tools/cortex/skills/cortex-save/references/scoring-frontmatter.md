# cortex-save — 评分字段 + frontmatter schema

## 评分字段 (强制 frontmatter, 落档时 AI 自评)

参考权威定义: `skills/cortex-ingest/references/extract.md §3`

### 知识库落档 (kind=concept|domain|log|reflection|source|project)

强制 4 字段, 全 0.0-10.0 浮点:

- `score`: 内容质量 (覆盖度 / 深度 / 准确性)
- `confidence`: AI 对内容的把握度
- `source_credibility`: host 白名单查表 (见 `scripts/cli/lib/remote.py:_HOST_CREDIBILITY`)
- `maturity`: `draft | review | stable | deprecated` enum

### 记忆落档 (kind=memory, 落 `记忆/L0-L4/`)

强制 2 字段:

- `importance`: 重要程度 (核心约束 = 10, 流水账 = 1-3)
- `confidence`: 可信度 (用户明确肯定 = 10, AI 推测 = 4-6, 失败 episode = 0-3)

参考: `skills/cortex-memory/references/scoring.md`

### CLI override

```bash
bash ~/.cortex/scripts/save.sh ... \
  --score=N \
  --confidence=N \
  --source-credibility=N \
  --maturity=stable
```

覆盖 AI 自评。

## Frontmatter 规范 (按目标目录)

save.py 落档时 `_derive_tags` 派生**语义** tag (alias + h1/h2 slug + 中文 2-4 字 + 英文 PascalCase 小写化), 严禁占位符 / 裸时间 (`YYYY[-MM]` 等); hierarchical `xxx/yyy` 不主动派生。

目录级**强制** tags_required (hierarchical 形式如 `type/project`, `host/<x>`, `memory/L1`, `memory/procedural`) 由 **cortex-lint 后续**通过 schema 补齐, 不在 save 阶段填:

- schema 源: `<vault>/_meta/frontmatter-schema.yaml` (fallback `plugin/presets/seed/_templates/frontmatter-schema.yaml`)
- lint rule `frontmatter-schema-violation` 检测缺失 + autofix 按目录 schema `tags_required` 字段补 prefix

```
save.py: 派生语义 tag → 落档
  ↓
cortex-lint --fix: schema-driven 补 tags_required prefix
  ↓
最终 frontmatter
```

## 套模板

读 `<vault>/_templates/<type>.md` (不存在则读 plugin presets `<plugin>/presets/seed/_templates/<type>.md`):

- 替换 `{{TITLE}}` / `{{CREATED}}` / `{{UPDATED}}` (UTC `YYYY-MM-DD`)
- tags 自动加 `[cortex-auto]` 标记
- AI 自评 4 评分字段时, 用启发式: 见 `skills/cortex-ingest/references/extract.md §3.1`
