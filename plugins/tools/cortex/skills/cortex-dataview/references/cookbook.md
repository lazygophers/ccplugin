# cookbook — cortex vault 8 个实用 DQL

按 cortex vault 结构 (知识库/{项目,领域,日记,收件箱}/ + 记忆/L0-L4/ + frontmatter 8 必填字段) 精调。

## 1. 项目仪表盘 — 按 score 排序

**用例**: `知识库/项目/_index.md` 或某领域聚合页, 一眼看高分项目。

````markdown
<!-- cortex-dataview v1 kind=table hash=auto -->
```dataview
TABLE WITHOUT ID
  file.link AS "项目",
  score AS "评分",
  maturity AS "成熟度",
  dateformat(file.mtime, "MM-dd") AS "更新"
FROM "知识库/项目"
WHERE type = "project" AND score
SORT score DESC, file.mtime DESC
LIMIT 20
```
````

## 2. 本月日记列表

````markdown
```dataview
LIST dateformat(file.day, "yyyy-MM-dd EEE")
FROM "知识库/日记/日"
WHERE file.day >= date(yyyy-MM-01) AND file.day < date(today) + dur(1 day)
SORT file.day DESC
```
````

## 3. 收件箱孤儿 — 无 outlinks 的待分发条目

**用例**: 找出"扔进收件箱后从没引用过外部"的条目, 优先消化。

````markdown
```dataview
TABLE WITHOUT ID
  file.link AS "孤儿条目",
  length(file.outlinks) AS "出链",
  dateformat(file.ctime, "yyyy-MM-dd") AS "落档"
FROM "知识库/收件箱"
WHERE length(file.outlinks) = 0
SORT file.ctime ASC
LIMIT 30
```
````

## 4. 领域关联反查 — 链入当前页的笔记

**用例**: 在某领域 hub 页, 列谁在引用我。

````markdown
```dataview
LIST
FROM [[]]
WHERE contains(file.outlinks, this.file.link)
SORT file.mtime DESC
LIMIT 15
```
````

## 5. 评分 review 队列 — score < 0.6 待重审

**用例**: 周末批量 review 低分笔记。

````markdown
```dataview
TABLE WITHOUT ID
  file.link AS "笔记",
  score, confidence, maturity,
  dateformat(file.mtime, "MM-dd") AS "上次改"
FROM "知识库"
WHERE score AND score < 0.6
SORT score ASC, file.mtime ASC
LIMIT 30
```
````

## 6. 记忆 L2 promote 候选 — L3 episodic 高频引用

**用例**: L3 笔记中 inlinks ≥ 3 且 score ≥ 0.7 → L2 promote 候选。

````markdown
```dataview
TABLE WITHOUT ID
  file.link AS "候选",
  length(file.inlinks) AS "被引",
  score, confidence
FROM "记忆/L3-episodic"
WHERE length(file.inlinks) >= 3 AND score >= 0.7
SORT length(file.inlinks) DESC, score DESC
LIMIT 10
```
````

## 7. 最近 7 天活跃 — file.mtime 滚动

**用例**: 仪表盘 "最近改动" 块。

````markdown
```dataview
TABLE WITHOUT ID
  file.link AS "笔记",
  type,
  dateformat(file.mtime, "MM-dd HH:mm") AS "时间"
FROM "知识库" OR "记忆"
WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
LIMIT 25
```
````

## 8. TASK 滚动 — 全 vault 未完成

**用例**: 跨笔记拉所有未完成 task。注意: TASK 查询会让 checkbox 可点击 (修改源文件)。

````markdown
```dataview
TASK
FROM "知识库"
WHERE !completed
GROUP BY file.link
SORT file.mtime DESC
LIMIT 50
```
````

## 通用 frontmatter 假设

上述 query 假设笔记符合 cortex frontmatter 契约:

```yaml
type: project | concept | source | inbox | ...   # 必填
title: ...
score: 0.0-1.0          # 必填浮点
confidence: 0.0-1.0     # 必填浮点
source_credibility: 0.0-1.0   # 必填
maturity: seed|draft|stable|frozen    # 必填 enum
created: YYYY-MM-DD
updated: YYYY-MM-DD
```

不符合的 query 会返回 null 列 (Dataview 默认行为)。

## 使用方式

- 选其一拷到目标笔记
- marker `hash=auto` 是占位 — cortex-dataview skill 写入时自动算 sha1 前 8 位 (见 modify-flow.md §3)
- 改 query 后 hash 变, 下次 skill 调用会重生成 marker

## 反模式 (本 cookbook 不写的)

- `FROM ""` 无 filter → 大 vault 性能死亡
- `dataviewjs` 任意 JS — 安全策略禁默认
- 嵌套 GROUP BY + lookup → 几秒查询
- 