---
title: cortex ingest 自动构建知识图谱 — Bases + Canvas + Wikilink 网 + websearch 扩展
status: planning
priority: P2
owner: nico
created: 2026-05-14
---

# 背景

`/cortex:ingest` 跑完后产出 md 但未自动构图。用户跑 Obsidian 时检索体验差 (Graph View 稀疏 / 无 Bases 数据库视图 / 无 Canvas 架构白板)。

要求 ingest **内联**生成以下知识图谱制品 (单步完成, 不另调 agent):

1. Bases 数据库视图 (`.base` 文件, Obsidian ≥ 1.7 原生)
2. Canvas 白板 (架构节点 + 关系连线)
3. Wikilink 网 (子文档互链 + alias + tag)
4. websearch 搜索扩展 (ingest 时主动 WebFetch/WebSearch 补充外部资料)

# 设计

## 1. SKILL.md 新加 §9 知识图谱强制

ingest 完产 md 之后, **同一 skill 内联**生成 4 类制品 (跳一个 = self-check 失败拒交):

### §9.1 Bases 数据库视图

落 `知识库/项目/<host>/<org>/<repo>/_db.base` (Obsidian 1.7+ JSON5 格式), 内含 3 视图:

- **table view**: 全 .md 按 frontmatter (title / type / maturity / score / updated) 表格
- **card view**: 按 type 分组卡片 (concept / domain / log), tag 着色
- **filter views**: 预置过滤 (e.g. `score >= 4`, `maturity == stable`, `tags contains "api"`)

Bases 字段对齐 §3 frontmatter schema, 不再要求 Dataview fallback (用户保底 Obsidian ≥ 1.7)。

### §9.2 Canvas 白板

落 `_assets/canvases/<repo>.canvas` (JSON Canvas 1.0), 5-20 节点 + 连线:

- 节点: `_index.md` (中心) + 主题/{架构,决策,陷阱,依赖,配置,错误码,测试,功能}.md (≥8 主题节点) + 关键模块/.md (前 5)
- 连线: `_index → 主题`, `主题/架构 → 主题/依赖`, `主题/决策 → 主题/陷阱` 等显式因果
- force-directed grid 5 列 400×300

复用 `skills/cortex-canvas/SKILL.md` 排版算法 — ingest 内联调而非派 agent。

### §9.3 Wikilink 网

每个落档 .md **必须**:

- 出链 `[[X]]` ≥ 5 个 (引用兄弟主题 / 模块 / 符号)
- 入链反向被 ≥ 2 个其他 .md 引用 (跨主题穿插, 不是孤岛)
- `aliases:` 字段加全部已知别名 (技术名 + 中文名 + 缩写)
- 末段 `## 相关` 列 ≥ 5 [[wikilink]]

self-check 验: 每 .md `rg '\[\[' <file> | wc -l` ≥ 5, 否则补。

### §9.4 websearch 搜索扩展

ingest 时**主动**跑 WebSearch / WebFetch 补外部资料:

- repo 类: 搜 "<repo-name> issues" / "<repo-name> changelog" / "<repo-name> roadmap" / 官方 docs URL
- 落 `主题/外部资料.md` (frontmatter `source_url` 列全部抓取 URL + 摘要)
- 上限: 5 个外部链接, 防过载
- 失败容忍: WebSearch 不可用静默跳过, 不阻塞 ingest 主体

## 2. commands/ingest.md 步骤 6 self-check 升级

加 §9 4 类验证:

```bash
# 验 Bases
[[ -f "知识库/项目/<host>/<org>/<repo>/_db.base" ]] || 拒交

# 验 Canvas
[[ -f "_assets/canvases/<repo>.canvas" ]] || 拒交

# 验 Wikilink 密度
for md in 知识库/项目/<host>/<org>/<repo>/**/*.md; do
  links=$(rg -c '\[\[' "$md" || echo 0)
  [[ $links -ge 5 ]] || flag "$md"  # 低于 5 出链 → 补
done

# 验 websearch 扩展 (容忍跳过)
[[ -f "知识库/项目/<host>/<org>/<repo>/主题/外部资料.md" ]] || warn "websearch 未补"
```

## 3. agents/cortex-researcher.md 同步

description 加 "ingest 内联产出 Bases + Canvas + Wikilink 网 + websearch 扩展, self-check 4 类齐"。

## 4. 不做

- 不调度独立 cortex-cartographer agent (用户明确"单步完成")
- 不写 Dataview fallback (Obsidian ≥ 1.7 保底)
- 不强制 MOC `_moc.md` 单独文件 (`_index.md` 即 MOC)
- 不改 python CLI (Bases/Canvas 是 AI 落档行为)

# 验收

1. SKILL.md §9 含 4 子节 (.1 Bases / .2 Canvas / .3 Wikilink / .4 websearch)
2. commands/ingest.md self-check 含 4 类验证 bash
3. agents/cortex-researcher.md description 同步
4. GLM 自检识别 "Bases / Canvas / Wikilink ≥5 / websearch 扩展"
5. pytest 314 pass + 9 subtests

# 风险

- Bases JSON5 格式 AI 易写错 → SKILL.md 给最小可工作模板示例 (5 行 `views: [{...}]`)
- Canvas 节点过多导致布局乱 → 限 20 节点上限
- websearch 速率/超时 → 容忍跳过设计, 不阻塞
- Wikilink ≥ 5 在 ≤50 文件小 repo 难达 → 改"按文件数 prorated" (小 repo ≥ 3)
