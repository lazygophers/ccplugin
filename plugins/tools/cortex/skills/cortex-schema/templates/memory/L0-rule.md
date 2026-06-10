> 模板 — type=rule, level=L0; 完整样例见 `../../examples/rule.md`.

## 必备 / 推荐字段

- `type: rule` (必备, 注意是 `rule` 不是 `memory`)
- `level: L0` (必备)
- `weight: 1.0` (建议固定, L0 永久最高权重)
- 全字段表见 `../_fields.md`

## frontmatter 块

核心规则, 永久, 不进入遗忘曲线:

```yaml
---
type: rule
level: L0
weight: 1.0
created: 2026-06-09
tags: [safety, hardrule]
aliases: []
---
```

## 备注

- L0 是 memory 五级中最顶层, 但 `type` 用 `rule` 而非 `memory` (语义区分: 强制规则 vs 普通记忆).
- 不参与遗忘曲线衰减.
- 同 type 其他变体: 无 (rule 仅 L0).
- 同 level 其他变体: 见 `L1-long.md` / `L2-mid.md` / `L3-short.md` / `L4-inbox.md`.
