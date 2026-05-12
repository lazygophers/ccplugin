---
description: 跑腐化检测 — 扫记忆/知识库一致性 (无入参)
---

# /cortex:warden

[AUTO_MODE strict: 禁询问, fail-fast, 仅读不写]

跑 cortex vault 腐化检测:

1. 从 `~/.cortex/config.json` 读 vault
2. 扫双 namespace 一致性: 记忆 ↔ 知识库交叉引用
3. 检测 frontmatter 字段缺失 / 类型错误
4. 检测 wiki-link 死链
5. 检测重复 title (同 namespace 内冲突)
6. 检测 weight / freq 异常 (突增/突降)

输出: 腐化等级报告 (✗ corrupted / ⚠ suspect / ✓ healthy) + 修复建议。
