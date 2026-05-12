---
description: cortex-refactor 子命令 (dry-run 默认) — 无入参时列建议
---

# /cortex:refactor

[AUTO_MODE strict: 禁询问, fail-fast]

cortex-refactor 操作。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)**: 扫 vault 列重构建议 (top 20):
   - rename 候选 (typo / locale 不一致)
   - merge 候选 (相似 title / overlap > 70%)
   - split 候选 (单文件 > 5KB)
   - dedupe 候选 (相同内容)
   - 输出 plan JSON, **dry-run 不落盘**
3. 若有显式 args: 执行子命令 `rename / merge / split / fold / migrate-locale / restructure / dedupe / extract / inline / graph-rebalance`
   - 默认 dry-run, 仅当 `--apply` 时落盘

输出: plan JSON (候选列表 + 影响范围 + 风险等级)。
