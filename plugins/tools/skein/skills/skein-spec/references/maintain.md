# skein-spec maintain — 手动全量体检

规则库积累后会漂移。prune 负责自动精简 (sediment 后顺跑), maintain 是**手动全量体检**, 供 user 在 sediment+prune 之外独立审查:

```
skein-spec maintain                    # 全量体检 (全 namespace)
skein-spec maintain --namespace rules  # 仅指定 namespace
```

## 判据与输出

判据定义、按 namespace 的分表、判定顺序全部以 [prune-workflow.md](prune-workflow.md) 为准 —— maintain 跑的是**同一套判据**, 区别只在 maintain 只报告不动手 (加 `--apply` 才修)。各判据的输出长这样:

```
[超预算]   rules/git/big-00 超 spec.always_budget — 考虑降级: git/big-00
[断链]     rules/ops/old-00: [[nonexistent]] ✗ 目标缺失
[stale]    rules/ops/old-00 (created 14月,420天前, updated 14月,420天前, status active)
[废弃]     external/xxx status=deprecated
[anchors失效] product/login/state.md: anchors 指向的 file:line 已不存在 — 需人判断需求是否真过时
```

- prune 已 archive 的项 maintain 不会再报 (已移出 active 规则集)。
- **stale 判据 (180 天) 主观可调** — 项目节奏快可收紧 (`STALE_DAYS` 常量); `created` 缺字段或非 epoch 容错跳过不报错。无任何 findings → 输出 `全清`。

## 补充发现 (非规则内容判据, 库整体卫生)

| 项 | 触发 | 输出示例 |
|---|---|---|
| 归档残留 | `.skein/spec/.archive/` 有未清理的旧归档 | `[归档残留] .archive/1784344973/ 已超 90 天 — 建议 purged` |
| keywords 重复 | 同 keywords 组 ≥ 3 条 (rules namespace) | `[重复 keywords] "merge,worktree" ×3: rules/arch/a, rules/ops/b, rules/ops/c` |

## `--apply` 自动修复

`skein-spec maintain --apply` 同一次扫描自动修复可修项 (逻辑与 prune 完全共享, 见 [prune-workflow.md](prune-workflow.md)):

| 判据 | 处置 |
|---|---|
| 超预算 | 循环降级 top-1 最大 always 页 → auto, 直到不超 `spec.always_budget` |
| stale (rules) | archive (可逆) |
| keywords 重复 (rules) | 保留最新, 余 archive (可逆) |
| deprecated·superseded (rules/external) | archive (可逆) |
| orphan (rules) | archive (可逆) |
| anchors 失效 (map) | archive (可逆, 骨架现算, 语义页失效无损) |
| 断链 | **只报告, 不修** — 需人判断改链还是建目标 |
| anchors 失效 (product) | **只报告, 不修** — 需求真值只有人知道该不该删 |

每步写 `.audit-log` (7 天轮转)。`protected: true` 的规则跳过不精简 (命中判据也不动)。
