# 关键性质

1. **新条目默认 L3**, 不直接进 L1 (即时 "记住" 也只走 L3, 由后续 promote 升)
2. **promote 由 lint/extract 离线触发**, 不由用户即时口令触发 — 即时 "记住" = L3 → L2 单跳, 不能跳级
3. **forget 永远只是标记**, 不自动删 — 由用户审批 (lint 输出候选清单, `--fix` 也不删 memory)
4. **L0 与 L4 不参与升降级流程** — L0 永久, L4 只能被 extract 消化
5. **路径名与 level 必须一致** — `memory/L1-long/foo.md` frontmatter 必须 `level: L1`, 否则 lint R6 报错. 完整 level↔dir 映射见 `references/levels.md`.
6. **降级是软警告** — demote 仅迁移到下级目录 + frontmatter level 改字段, 内容不变, 用户可手动 promote 回来

## 遗忘曲线说明 (Ebbinghaus)

- L1 = 长期 (不是短期), 数字小 = 抗遗忘强 = 升级方向
- 升级阈值: L3 → L2 (访问 ≥ 3 次), L2 → L1 (访问 ≥ 5 次 + weight ≥ 0.8), L1 → L0 (仅手动)
- 降级阈值: L1 (≥ 365d 未访问) → L2; L2 (≥ 90d) → L3; L3 (≥ 7d) → forget 候选
- 默认入口是 L3 短期, 不是 L4 inbox — L4 仅供原始未分类堆叠
- forget 不会自动删文件, 仅 lint 标候选

## 反直觉提醒

- L1 = 长期, L3 = 短期, 数字与时长**反向**
- 路径后缀 (`core/long/mid/short/inbox`) 强制内嵌语义, 防止反写; 完整映射 + 反例见 `references/levels.md`

## lint R6 引用

lint R6 (路径段后缀 ↔ frontmatter `level` 严格匹配, error 级) 的**权威映射表**已迁入本 skill: 见 `references/levels.md` "level ↔ dir 映射表" 与 "反写防呆" 段. lint 仅保留算法 (正则抓段 + 读 frontmatter + 三方对照), 路径 / 后缀 / 反例清单不再硬列.
