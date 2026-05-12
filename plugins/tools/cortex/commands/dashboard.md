---
description: 刷新 cortex 仪表盘 (无入参, 严约束防漫游)
---

# /cortex:dashboard

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

按 cortex-dashboard SKILL AUTO_MODE 严约束执行刷新:

1. Bash 调 `cd $(jq -r .vault ~/.cortex/config.json)` 进入 vault
2. Glob `仪表盘/*.md` (cap 20 个)
3. 每页**仅读 frontmatter** 前 30 行 (禁读全文)
4. ledger 仅 `wc -l` 不读全文
5. 注入 `<!-- DASH:BEGIN -->...<!-- DASH:END -->` callout 区
6. 不破坏正文 / frontmatter 其余字段
7. 输出单行 JSON: `{ refreshed: [...paths], skipped: N, errors: [...] }`

仅 stale > 1d 才渲染。禁 AskUserQuestion, 默认决策跳过任何询问。
