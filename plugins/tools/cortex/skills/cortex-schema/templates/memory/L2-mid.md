> 模板 — type=memory, level=L2; 完整样例见 `../../examples/memory-L2.md`.

## 必备 / 推荐字段

- `type: memory` (必备)
- `level: L2` (必备)
- `weight` 建议 0.4-0.7
- 全字段表见 `../_fields.md`

## frontmatter 块

L2 中期记忆:

```yaml
---
type: memory
level: L2
created: 2026-06-09
updated: 2026-06-09
weight: 0.6
tags: [decision]
---
```

## 备注

- L2 = 中期记忆, 决策类 / 阶段性结论, 衰减中等.
- 同 type 其他变体: `L1-long.md` / `L3-short.md` / `L4-inbox.md`; rule 见 `L0-rule.md`.
