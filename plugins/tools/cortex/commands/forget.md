---
description: 跑遗忘扫描 — 低权重/过期记忆移到归档 tombstone (无入参)
---

# /cortex:forget

[AUTO_MODE strict: 禁询问, fail-fast]

按 cortex-forget SKILL 流程跑遗忘扫描:

1. 从 `~/.cortex/config.json` 读 vault
2. 扫 L3/L2 记忆: weight < 阈值 (见 `_meta/memory-policy.yaml`) 且 last_recalled 超期
3. 候选 → 移到 `归档/forgotten/<date>/` 留 tombstone (保留 URI + 简要)
4. 写 ledger 留痕 (forget 事件)
5. L0/L1 受保护永不遗忘

输出: 遗忘候选列表 + 移除文件数 + tombstone 路径。
