> 模板 — type=project, host=任意 website; 无独立 example, 参照 `../../examples/project.md` 形态.

## 必备 / 推荐字段

- `type: project` (必备)
- `source` (必备): 任意完整 URL (非 github/gitlab host)
- `summary` 推荐
- 全字段表见 `../_fields.md`

## frontmatter 块

入库非代码托管站点项目摘要 (`项目/<host>/<path>/README.md`):

```yaml
---
type: project
source: https://example.com/some/project
summary: 站点项目摘要 — 一行说明
mindmap: ./mindmap.canvas        # 可选
created: 2026-06-09
updated: 2026-06-09
tags: [website, reference]
aliases: []
---
```

## 备注

- 适用于无 owner/repo 概念的站点 (官网 / 文档站 / 博客 etc.).
- 物理路径段按 URL host + path 切分, 不强制 owner/repo 两段.
- 若 host 为 github.com / gitlab.com, 优先用对应变体模板.
- 同 type 其他变体: `github.md` / `gitlab.md`.
