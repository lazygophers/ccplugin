# skein-spec maintain — 手动全量体检

规则库积累后会漂移。prune 负责自动精简 (sediment 后顺跑), maintain 是**手动全量体检**, 供 user 在 sediment+prune 之外独立审查:

```
skein-spec maintain                 # 全量体检两层
skein-spec maintain --layer recall  # 仅指定层
```

**5 判据 + 2 补充发现** (同 prune 判定门, maintain 只报告不动手):

| 判据 | 触发 | 输出示例 |
| --- | --- | --- |
| 超预算 | core 全文 > 8000 字符 | `[超预算] core 8200 > 8000 字符 — 考虑降级: git/big-00(2100)` |
| stale | created 年龄 > 180 天 (~6 月) 且 updated 也老 | `[stale] recall/ops/old-00 (created 14月,420天前, updated 14月,420天前, status active)` |
| 断链 | body 的 `[[slug]]` 目标 stem 库内无匹配 | `[断链] recall/ops/old-00: [[nonexistent]] ✗ 目标缺失` |
| keywords 重复 | 同 keywords 组 ≥ 3 条 | `[重复 keywords] "merge,worktree" ×3: recall/arch/a, recall/ops/b, recall/ops/c` |
| 归档残留 | `.skein/spec/.archive/` 有未清理的旧归档 | `[归档残留] .archive/1784344973/ 已超 90 天 — 建议 purged` |

- prune 已 archive 的项 maintain 不会再报 stale/废弃/重复/断链 (已移出 active 规则集)。
- **stale 判据 (180 天) 主观可调** — 项目节奏快可收紧 (`STALE_DAYS` in `spec.py`); `created` 缺字段或非 epoch 容错跳过不报错。无任何 findings → 输出 `全清`。
