# 关键性质

1. **新条目默认 L3**, 不直接进 L1 (即时 "记住" 也只走 L3, 由后续 promote 升)
2. **promote 由 lint/extract 离线触发**, 不由用户即时口令触发 — 即时 "记住" = L3 → L2 单跳, 不能跳级
3. **forget 永远只是标记**, 不自动删 — 由用户审批 (lint 输出候选清单, `--fix` 也不删 memory)
4. **L0 与 L4 不参与升降级流程** — L0 永久, L4 只能被 extract 消化
5. **路径名与 level 必须一致** — `memory/L1-long/foo.md` frontmatter 必须 `level: L1`, 否则 lint R6 报错
6. **降级是软警告** — demote 仅迁移到下级目录 + frontmatter level 改字段, 内容不变, 用户可手动 promote 回来

## 反直觉提醒

- L1 = 长期 (不是短期), 数字小 = 抗遗忘强 = 升级方向
- 默认入口是 L3 短期, 不是 L4 inbox — L4 仅供原始未分类堆叠
- forget 不会自动删文件, 仅 lint 标候选

## lint R6 护栏

R6 规则: 路径后缀 (`core` / `long` / `mid` / `short` / `inbox`) ↔ frontmatter `level` 必须严格匹配:

| 路径 | level |
| --- | --- |
| `memory/L0-core/` | L0 |
| `memory/L1-long/` | L1 |
| `memory/L2-mid/` | L2 |
| `memory/L3-short/` | L3 |
| `memory/L4-inbox/` | L4 |

任何错配组合直接报错, 不可 `--fix` 自动修正 (需人工判定语义后改 level 或挪路径)。
