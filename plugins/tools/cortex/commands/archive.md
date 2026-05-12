---
description: 归档执行 — 老旧/已遗忘记忆移到归档目录 (无入参)
---

# /cortex:archive

[AUTO_MODE strict: 禁询问, fail-fast]

按 cortex 归档策略执行:

1. 从 `~/.cortex/config.json` 读 vault
2. 扫 `归档/staging/` 待归档候选 (forget / promote 产物)
3. 按时间分桶: `归档/<year>/<month>/<kind>/`
4. 保留 tombstone 索引 (URI / 原路径 / 归档时间 / 原因)
5. 写 ledger 留痕

输出: 归档文件数 + 各分桶统计。
