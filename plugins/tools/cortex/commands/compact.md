---
description: 压缩 L4 raw ledger — 老 ledger 压缩归档释放空间 (无入参)
---

# /cortex:compact

[AUTO_MODE strict: 禁询问, fail-fast]

跑 L4 ledger 压缩:

1. 从 `~/.cortex/config.json` 读 vault
2. 扫 `记忆/L4-原始/ledger/` 老于 30 天的 `<week>/*.md`
3. 按周聚合为单 `<week>-compact.md` (保留时间戳 + 事件类型 + 简要)
4. 原始 raw 文件移到 `归档/ledger-raw/<year>/<week>/`
5. 更新 ledger 索引

输出: 压缩前 / 后 文件数 + 释放字节数。
