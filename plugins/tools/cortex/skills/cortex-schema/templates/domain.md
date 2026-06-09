> 模板 — type=domain; 完整样例见 `../examples/domain.md`.

## 必备 / 推荐字段

- `type: domain` (必备)
- `area` (必备): domains 一级 area, 如 `tech` / `life` / `work`
- `tags` / `aliases` / `weight` 推荐
- 全字段表见 `_fields.md`

## frontmatter 块

领域笔记 (`领域/<area>/<sub>/[<sub2>/]<topic>.md`):

```yaml
---
type: domain
area: tech
created: 2026-06-09
updated: 2026-06-09
tags: [rust, async, tokio]
aliases: [tokio-runtime-notes]
weight: 0.6
---
```

## 备注

- `area` 决定物理目录第一段, 必须落在 vault 已声明的 area 集合.
- 完整样例: `../examples/domain.md`.
