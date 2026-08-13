> 模板 — type=memory, level=L1; 完整样例见 `../../examples/memory-L1.md`.

## 必备 / 推荐字段

- `type: memory` (必备)
- `level: L1` (必备)
- `weight` 建议 0.7-1.0 (已稳固的长期记忆)
- 全字段表见 `../_fields.md`

## frontmatter 块

L1 长期记忆 (已稳固):

```yaml
---
type: memory
level: L1
created: 2026-06-09
updated: 2026-06-09
weight: 0.85
tags: [process, project-x]
---
```

## 备注

- L1 = 已被多次复现 / 强化的长期记忆, 衰减极慢.
- 同 type 其他变体: `L2-mid.md` / `L3-short.md` / `L4-inbox.md`; rule 见 `L0-rule.md`.
