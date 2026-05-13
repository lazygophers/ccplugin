# cortex 知识库 md 强制 tags ≥10

## 目标

知识库内每一个 `.md` 文件 frontmatter `tags:` 字段必须存在且 ≥ 10 个标签。lint 强制 + 模板/seed/skills/agents/commands 全部同步。

## 适用范围

**强制**: `知识库/**/*.md` + `presets/seed/_templates/**/*.md` (含所有模板)

**豁免** (lint whitelist):
- `_meta/**` — 元数据(uri-index/version 等), 非内容
- `仪表盘/**` — runtime 生成块, 非用户内容
- `归档/**` — 历史快照, 不动
- `_assets/**` — 非 md
- `presets/seed/仪表盘/**` — dashboard seed (内容是占位区块, 非知识)

## Lint 规则改造

### `fm-missing-tags` 单规则升级 (不拆新规则)

新行为:
- 字段存在 + 类型 list 且 `len(tags) >= 10` → pass
- 字段不存在 / 非 list / `len(tags) < 10` → warn
- **autofix 必须自动补满 10**, 严禁占位符 (`<待填-N>` / `placeholder/N` 等空语义 tag)
  - 读 frontmatter (title / desc / type / source_url / host / org / repo / when_to_read / score / maturity / lang / created)
  - 读正文 (h1 + h2 + 首 ~500 字)
  - 派生 tags: `topic/<heading-slug>`, `stack/<lang>`, `source/<kind>`, `host/<host>`, `org/<org>`, `lang/<l>`, `created/<YYYY>`, `score/<n>`, `maturity/<l>`, `type/<type>`
  - 去重 + 保序 + 截断到 10..20 (设上限避免无限膨胀)
  - 不足 10 → 从正文 noun-phrase 抽取 (简单 jieba/regex 取 2-4 字中文短语 + 英文驼峰)
  - 仍不足 → autofix 失败, 报 warn 由 AI 补足 (不写占位)

rules.json 描述更新为 "frontmatter tags 字段缺失 / 数量 < 10"。

## 模板同步

`presets/seed/_templates/*.md` 中 frontmatter `tags:` 必须演示 ≥10 占位:

```yaml
tags:
  - <主题分类>
  - <技术栈/工具>
  - <语言/框架>
  - <作者/团队>
  - <版本/状态>
  - <难度/阶段>
  - <关联领域>
  - <来源类型>
  - <可信度>
  - <时间维度>
```

涉及模板:
- `_templates/concept.md`
- `_templates/entity.md`
- `_templates/source.md`
- `_templates/domain.md`
- `_templates/question.md`
- `_templates/dashboard.md` (豁免范围, 但保持示意)
- `_templates/_index.md` (豁免范围)

## Seed `_index.md` 同步

`presets/seed/知识库/**/_index.md` 现状 `tags: []` (豁免)。本任务**不动**(_index 属导航页, 豁免范围)。

但若有非 _index seed md, 全部补到 10 tags。grep 检查后定。

## Skill / Agent / Command 文档同步

涉及文件:
- `skills/cortex-ingest/SKILL.md` — "tags ≥ 3" → "tags ≥ 10" (line 229, 269)
- `commands/ingest.md` — "tags (≥3)" → "tags (≥10)" (line 40)
- `agents/cortex-linker.md` — 第 81 行 "重叠度 ≥2" 是匹配阈值, **不动**
- `skills/cortex-lint/SKILL.md` — 加新规则描述
- `skills/cortex-digest/SKILL.md` — 若提及 tag 数量, 同步
- `.claude/memory/cortex-plugin-2026-05-13.md` — ingest 全局规则 "tags 强制 ≥3" → "≥10" (由 neat-freak 一并改)

## ingest 流程升级

`scripts/cli/ingest_url.py` + `ingest_file.py` 内部 frontmatter 生成逻辑:
- 现状: 自动补 `source/<kind>` + `topic/<domain>` + `stack/<lang>` 共 3 个
- 改: 扩展生成器, 自动补到 ≥10 (含 `score/<n>`, `maturity/<l>`, `lang/<l>`, `created/<YYYY>` 等派生 tag)
- 若派生不够 10, 留 `placeholder/<n>` 占位

## 验收

- `bash ~/.cortex/scripts/lint.sh` 在 vault 跑, 知识库下任意 < 10 tag md 触发 `fm-tags-too-few`
- 所有 `_templates/*.md` (非豁免) `tags:` 列表 ≥ 10 项 (含占位符)
- `grep "tags.*≥.*3" skills/ commands/ docs/` = 0
- python tests 全绿
- `bash ~/.cortex/scripts/ingest_url.sh --url <test>` 生成 md 自动 ≥ 10 tag

## 范围外 (本任务不做)

- 不补历史 vault 内已有 < 10 tag md (用户跑 lint 后自决)
- 不动 `_meta/`, `仪表盘/`, `归档/`, `_assets/` 的 md
- 不强 `tags: []` 升 ≥ 10 (空 list 仍由 fm-missing-tags 报)
