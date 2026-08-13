> 模板 — type=vault-script; 完整样例见 `../examples/vault-script.md`.

## 必备 / 推荐字段

- `type: vault-script` (必备)
- `name` 推荐: 脚本短名
- `created` 必备
- 全字段表见 `_fields.md`

## frontmatter 块

vault 内部脚本 (写为脚本顶部注释块, 推荐不强制):

bash:

```bash
# ---
# type: vault-script
# name: canvas-from-mindmap
# created: 2026-06-09
# ---
```

python:

```python
"""
---
type: vault-script
name: canvas-from-mindmap
created: 2026-06-09
---
"""
```

## 备注

- frontmatter 嵌入脚本头部注释块, 语言决定注释语法 (`#` / `"""`).
- 完整样例 (.md 描述形式): `../examples/vault-script.md`.
