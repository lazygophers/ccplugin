> 模板 — type=memory, level=L3; 完整样例见 `../../examples/memory-L3.md`.

## 必备 / 推荐字段

- `type: memory` (必备)
- `level: L3` (必备)
- `weight` 建议 0.2-0.5
- 全字段表见 `../_fields.md`

## frontmatter 块

L3 短期记忆 (extract 默认入口):

```yaml
---
type: memory
level: L3
created: 2026-06-09
weight: 0.4
tags: [observation]
---
```

## 备注

- L3 = extract 默认落点, 观察 / 短期上下文, 衰减快.
- 同 type 其他变体: `L1-long.md` / `L2-mid.md` / `L4-inbox.md`; rule 见 `L0-rule.md`.
