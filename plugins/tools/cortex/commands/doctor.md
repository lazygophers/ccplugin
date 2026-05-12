---
description: 跑 cortex 健康检查 — vault/config/links/dead-links (无入参)
---

# /cortex:doctor

[AUTO_MODE strict: 禁询问, fail-fast, 仅读不写]

按 cortex-doctor SKILL 流程跑健康检查:

1. 从 `~/.cortex/config.json` 读 vault 与 install_path
2. 检查 vault 结构 (双 namespace / seed 文件 / _meta)
3. 扫死链 (\[\[wiki-link\]\]) 与孤儿文件
4. 校验 frontmatter (kind / locale / last_updated)
5. 报告 config / links / dead-links / 路径异常

输出: 可读分级报告 (✗ critical / ⚠ warning / ✓ healthy)。
