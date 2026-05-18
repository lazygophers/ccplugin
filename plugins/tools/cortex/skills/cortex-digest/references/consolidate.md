# Consolidate — 阶段 5 项目→领域 提炼

> cortex-digest 8 阶段 §5 详细规范。新阶段 (PR digest-deep)。

把 `知识库/项目/<host>/<org>/<repo>/**` 内**通用概念** (跨项目可复用的技术/方法/模式) 抽到 `知识库/领域/<域>/`, 项目层只留**项目专属事实**。

## 输入

- state: `vault/.cortex/state/consolidate.json`
- 扫描范围: `知识库/项目/**/*.md` 中 `processed_files[<rel>].hash` 未命中的
- 既有领域: `知识库/领域/**/*.md` 全量索引 (concept 名 + aliases + content)
- config: `vault/.cortex/config/digest.yaml:domain_aliases`

## 算法

```
for each md in 知识库/项目/**:
  if hash in processed_files: skip
  LLM 深读 md, 输出候选概念列表 [{name, aliases, definition, examples, type: concept|method|pattern|fact}]
  filter: type == fact → 跳 (留项目层)
  for each concept:
    domain = decide_domain(concept)
    既有 = search 知识库/领域/<domain>/ by name + aliases (LLM 语义匹配 + 关键词)
    if 既有 命中:
      patch 既有: append "## 例证 <YYYY-MM-DD>" + 项目 backlink wikilink
      若定义不一致: 落 知识库/收件箱/<date>-矛盾-<concept>.md
    else:
      新建 知识库/领域/<domain>/<concept-slug>.md (用 _templates/knowledge/domain-concept.md)
  写 hash 到 state/consolidate.json
```

## 域名决策 (decide_domain)

优先级:
1. `config/digest.yaml:domain_aliases.<concept_kw>` 强映射命中 → 取映射值
2. concept frontmatter / tags 含 `domain: <x>` → 取 x
3. LLM 自决: 候选域 = `[技术, 创作, 学习, 工作, 生活, 金融, 未分类]` + vault 已存在的 `知识库/领域/<域>/` 目录名

未分类降级: LLM 不确定时归 `未分类/`, 不强分。

## LLM Prompt 模板

```
你是知识整合助手。读以下项目笔记, 抽出**跨项目可复用**的通用概念 (技术/方法/模式), 忽略项目专属事实。

输入:
<md frontmatter + content>

输出 JSON:
{
  "concepts": [
    {
      "name": "<规范化中文名>",
      "aliases": ["<中英 ≥3>"],
      "definition": "<2-3 句>",
      "examples": ["<从原文摘 1-3 例>"],
      "type": "concept|method|pattern",
      "suggested_domain": "技术|创作|..."
    }
  ]
}

规则: type=fact (具体数值/具体人事/项目专有名词) 不输出。
```

## 合并冲突处理

既有 `知识库/领域/<域>/<concept>.md` 定义与新候选**冲突** (LLM 判断: 定义对立 / score 差 ≥ 2 / aliases 完全不交):

1. **不动既有文件**
2. 落 `知识库/收件箱/<YYYY-MM-DD>-矛盾-<concept>.md`, frontmatter:
   ```yaml
   type: conflict
   concept: <name>
   existing: <既有 path>
   new_source: <project md path>
   ```
3. body 列对照表 (既有定义 vs 新定义 + 出处)
4. 统计累加 `consolidate.conflicts_recorded`

## 合并 (非冲突)

既有概念 + 新例证:
1. patch 既有文件: 文末 append `## 例证 <YYYY-MM-DD>` + 项目 backlink (`- 来自 [[<项目相对路径>]]: <一句话摘要>`)
2. 既有 frontmatter `examples_count += 1`
3. 既有 `sources` 数组 append 项目相对路径 (去重)
4. weight bump: `importance += 0.05` (cap 10.0)

## 新建领域条目

模板: `_templates/knowledge/domain-concept.md` (frontmatter 已含 score/confidence/source_credibility/maturity)

填:
- `name` / `aliases` / `tags` (≥3)
- `type: concept` / `domain: <decide_domain>`
- `definition` (body 第一段)
- `examples` body 第二段 (列项目出处 wikilink)
- `sources: [<project rel path>]`
- 初始 score: 5.0 (中性, 后续 enrich/verify 调)

## 输出统计 (合并到 digest JSON `consolidate` 字段)

```json
{
  "scanned": <N>,
  "concepts_extracted": <N>,
  "domain_created": <N>,
  "domain_enriched": <N>,
  "conflicts_recorded": <N>
}
```

## 性能 / 增量

- 单 md 一次 LLM 调用; vault 内项目数 > 100 时数小时是预期
- hash 增量保证未改动文件下次跑跳过
- 失败重试 1 次, 仍失败该文件不写 hash (下次重试)
