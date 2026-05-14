# cortex-ingest — 知识图谱 4 制品 (Bases / Canvas / Wikilink / websearch)

> SKILL.md §9 (知识图谱强制) 的详细规范。ingest 内联产, 跳一类 = self-check 失败拒交。

---

## 9. 知识图谱强制 (ingest 内联产, 跳一类 = self-check 失败拒交)

落档 .md 之后, **同一 skill 内联**再产 4 类制品 (不另调 agent, 单步完成):

---

## 9.1 Bases 数据库视图 (`_db.base`)

落 `知识库/项目/<host>/<org>/<repo>/_db.base` (Obsidian 1.7+ 原生 YAML 格式)。

### 硬契约 (lint rule 20: base-format-yaml)

**禁忌** (违反 = lint warn):

1. **不是 markdown 文件** — 首行**禁** `#` / `##` 标题, 整个文件**禁**任何 markdown 语法 (header / table / list bullet / code fence)。即使扩展名 `.base` 也不是 .md。
2. **不是 Dataview DQL** — 严禁 `TABLE` / `LIST` / `TASK` / `FROM` / `WHERE` / `SORT` / `GROUP BY` / `FLATTEN` 行首关键字。Bases ≠ Dataview, 两套插件语法。
3. **顶层必须 YAML object** — `yaml.safe_load(content)` 必须返回 `dict`, 不能是 list / string / None。
4. **顶层至少含 1 个 Bases schema 字段** — `filters` / `views` / `formulas` / `properties` 任一。

### 最小可工作模板

```yaml
filters:
  and:
    - file.ext == "md"
views:
  - type: table
    name: all
    order: [file.name, type, maturity, score, updated]
  - type: card
    name: by-type
    groupBy: type
    columns: [title, tags, score]
  - type: table
    name: stable-high
    filters:
      and:
        - maturity == "stable"
        - score >= 4
    order: [score, updated]
```

字段对齐 `references/extract.md` §3 frontmatter schema (type / title / desc / created / updated / tags / source_url / version / when_to_read / score / maturity)。**不写 Dataview fallback** (用户保底 Obsidian ≥ 1.7)。

### 自检 (AI 落档后必跑)

```bash
python3 -c "import yaml; d = yaml.safe_load(open('<path>')); assert isinstance(d, dict), '.base 必须 YAML object'; assert any(k in d for k in ('filters','views','formulas','properties')), '.base 必须含 Bases schema 字段'; print('ok')"
```

不通过 = 重写。lint rule 20 (`base-format-yaml`) 跑同样校验。

---

## 9.2 Canvas 白板 (`_assets/canvases/<repo>.canvas`)

落 JSON Canvas 1.0 格式, **5-20 节点**(上限 20 防布局乱) + 显式因果连线:

- **节点**: `_index.md` (中心) + 主题/{架构,决策,陷阱,依赖,配置,错误码,测试,功能}.md (≥8 主题) + 关键模块/.md (前 5)
- **连线**: `_index → 各主题`, `主题/架构 → 主题/依赖`, `主题/决策 → 主题/陷阱`, `主题/配置 → 主题/错误码` 等显式因果
- **布局**: force-directed grid 5 列, 节点 400×300, x = (i%5)*420, y = (i/5)*320

最小模板 (省略 nodes 数组):

```json
{
  "nodes": [
    {"id": "idx", "type": "file", "file": "知识库/项目/<h>/<o>/<r>/_index.md", "x": 0, "y": 0, "width": 400, "height": 300},
    {"id": "arch", "type": "file", "file": "...主题/架构.md", "x": 420, "y": 0, "width": 400, "height": 300}
  ],
  "edges": [
    {"id": "e1", "fromNode": "idx", "toNode": "arch", "label": "覆盖"}
  ]
}
```

复用 `skills/cortex-canvas/SKILL.md` 排版算法 — **ingest 内联调而非派 agent**。

---

## 9.3 Wikilink 网 (每 .md 强制)

每个落档 .md **必须**:

- **出链** `[[X]]` ≥ 5 个 (引用兄弟主题 / 模块 / 符号; 小 repo R ≤ 50 prorated ≥ 3)
- **入链** 反向被 ≥ 2 个其他 .md 引用 (跨主题穿插, 不孤岛)
- `aliases:` frontmatter 字段加全部已知别名 (技术名 + 中文名 + 缩写)
- 末段 `## 相关` 列 ≥ 5 [[wikilink]] (小 repo prorated ≥ 3)

self-check 验密度: `rg -c '\[\[' <file>` ≥ 5 (小 repo ≥ 3), 否则补再测。

---

## 9.4 websearch 搜索扩展 (主动跑 WebSearch/WebFetch)

ingest 时**主动**搜外部资料补 vault:

- **repo 类**: 搜 `"<repo-name> issues"` / `"<repo-name> changelog"` / `"<repo-name> roadmap"` / 官方 docs URL
- **落档**: `主题/外部资料.md`, frontmatter `source_url:` 列全部抓取 URL + 每条摘要 2-3 行
- **上限**: 5 个外部链接, 防过载
- **失败容忍**: WebSearch 不可用静默跳过, **不阻塞 ingest 主体**; self-check 仅 warn 不拒交
