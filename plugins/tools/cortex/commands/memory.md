---
description: cortex 记忆 CRUD (URI 寻址) — 无入参时全扫 verify
---

# /cortex:memory

[AUTO_MODE strict: 禁询问, fail-fast]

cortex 记忆 CRUD 操作 (URI: `L<N>://<path>`)。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)**: 全扫记忆 verify 模式:
   - 遍历 `记忆/L0..L4` 所有文件
   - 校验 frontmatter (level / uri / weight / last_recalled)
   - 校验 URI 唯一性 (无重复)
   - 报告 invalid / orphan / duplicate URI 数
3. 若有显式 args: `<verb> <uri> [args...]`:
   - read: 渐进披露 (brief → full on demand)
   - write: 按 L<N> 边界/审判规则
   - update: 修订并写 ledger 留痕
   - forget: 移到 `归档/forgotten/` 留 tombstone

输出: JSON `{ok, code, data?, error?}` 或 verify 报告。
