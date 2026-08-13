> 样例 — type=memory level=L3, 完整可直接落盘到 memory/L3-short/today-tmp-fix.md

---
type: memory
level: L3
created: 2026-06-09
weight: 0.4
tags: [tmp, fix, today, ccplugin]
aliases: [today-tmp-fix]
---

# 今天临时 Fix

短期记忆: 1-2 周内可能遗忘, 留作 trace.

## 问题

`plugin.json` 的 `skills` 数组在 schema 合并后从 4 项缩成 3 项, 旧 sub-agent 缓存的引用名 (knowledge / memory 两个旧 schema skill) 报 "skill not found".

## 临时方案

S4 子任务批量 sed 旧名为 [[cortex-schema]], 跑 grep 验证 0 命中旧前缀.

## 后续

如果 sprint 结束验证稳定, 这条可降级 / 删除. 上下文见 [[current-sprint-context]] 与 [[shell-quoting-rules]] (改 plugin.json 时注意 JSON 转义).
