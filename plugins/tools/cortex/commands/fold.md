---
description: 跑 cortex 周巩固 — ledger → views 周报 + 反思 (无入参)
---

# /cortex:fold

[AUTO_MODE strict: 禁询问, fail-fast]

按 cortex-consolidate SKILL 流程跑周报巩固 (默认上周):

1. 从 `~/.cortex/config.json` 读 vault, cd 进入
2. 扫 `L4/ledger/<week>/*.md` 抽取事件
3. 模式聚合: 同事件类型 ≥ 5 → 抽象为 L2 候选
4. 生成 `views/consolidated/<week>.md` 周报 (主题分布 / 高频实体 / 反思洞察)
5. 触发 cortex-promote 子流程: 写晋级候选到 `views/candidates.md`

输出: 生成的 views 文件路径 + 主题统计 + 候选数。
