---
description: 渐进披露召回 query 相关记忆 — 无入参时列 top 10 hot
---

# /cortex:recall

[AUTO_MODE strict: 禁询问, fail-fast]

渐进披露召回。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)**: 列 `hot.md` top 10 (按 recall_count + last_recalled 排序) + 各 level brief 计数
3. 若有显式 args (query): 按 cortex-recall SKILL 流程多级回退 (hot → uri-index → semantic → rg)
   - 默认: `top_k=5`, `levels=L0,L1,L2,L3` (排除 L4 raw ledger)

输出: brief + 子节点列表 (URI / weight / last_recalled)。
