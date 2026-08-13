> 模板 — type=memory, level=L4; 无独立 example, 参照 `../../examples/memory-L3.md` 形态.

## 必备 / 推荐字段

- `type: memory` (必备)
- `level: L4` (必备)
- `weight` 不建议 (原始未分类, 尚未评估强度)
- 全字段表见 `../_fields.md`

## frontmatter 块

L4 收件箱 (原始未分类):

```yaml
---
type: memory
level: L4
created: 2026-06-09
tags: [inbox]
---
```

## 备注

- L4 = 未分类原始收件箱, 等待人工 / 自动分捡到 L3 及以上.
- 不带 `weight` (尚未评估).
- 同 type 其他变体: `L1-long.md` / `L2-mid.md` / `L3-short.md`; rule 见 `L0-rule.md`.
