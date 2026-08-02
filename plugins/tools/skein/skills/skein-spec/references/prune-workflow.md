# prune 精简流程 (sediment 后自动跑, skein-specer) — 判定门 + 自主归档

sediment 写盘后, skein-specer 顺带跑一轮精简: 扫全 namespace 规则, 按下文判据检出 candidate, 对命中项**自动 archive** (可逆) 而非只报告。**异步 fire-and-forget**: main 派即放手, 不等回传 (同 sediment)。

## 1. 全局判据 (与 namespace 无关, 恒跑)

| 判据 | 触发 | 处置 |
|---|---|---|
| always 超预算 | `inclusion: always` 全文超 `spec.always_budget` (config.yaml) | 降级最少复用的 always 规则到 auto (`sediment` 调 inclusion) |
| 断链 | `[[slug]]` 目标 stem 库内无匹配 | 只报告, 需人判断改链还是建目标 (不自动) |

## 2. 按 namespace 分表 (自动 archive 或只报告, 判据集合按 namespace 不同)

| namespace | 生效判据 | 处置 |
|---|---|---|
| **rules** (含未归类的历史目录, 默认判据集) | stale (超 180 天无更新) / keywords 重复 (同组 ≥3 条, 保留最新) / deprecated·superseded / orphan (无入度 + active + 超 180 天) | 命中任一即 `skein-spec archive <path>` (可逆) |
| **external** | deprecated·superseded | `skein-spec archive <path>`; 无 stale / keywords 重复 / orphan 判据 |
| **product** | anchors 失效 | **只报告, 禁自动 archive** (需求真值只有人知道该不该删); 无 stale / keywords 重复 / deprecated / orphan 判据 (需求真值无时效性、无入度要求) |
| **map** | anchors 失效 | `skein-spec archive <path>` (骨架现算, 语义页失效无损) |

**为什么 product 特殊**: rules/external/map 的判据 (stale、重复、废弃) 衡量的是「这条内容还值不值得留在记忆里」, 时效性与入度都是合理信号; product 是需求现状 wiki, 只有人才知道某个功能域是否真的下线, 时效久不代表过时 (可能就是稳定不变), 所以 product 只留 anchors 失效一项做**提示**, 处置权留给人。

## 3. 判定顺序

1. 扫全 namespace (`skein-spec list` 或直接遍历 `.skein/spec/<namespace>/`)。
2. 每条规则先过「全局判据」(超预算/断链), 命中即处置 (降级 / 只报告)。
3. 再按规则所在 namespace 查「按 namespace 分表」, 命中任一即按该行处置。
4. 无命中 → 跳过, 不输出该条。

## 4. 保护标记

规则头 `protected: true` 的**跳过不精简** — 手工核验后标记, 禁自动 archive (即便命中判据也不动)。用于人工确认「明知过期但要保留」的条目 (如历史决策存档)。

## 5. 无命中处理

未检出任何 candidate 则如实报「无精简项」, **不空跑 archive**。

## 6. archive 语义

- **可逆, 不删文件** — 全走 `skein-spec archive <path>` 归档到 `.skein/spec/.archive/<ts>/`, 如需恢复 `skein-spec restore <ts>`。
- 归档后 index 自动重建 (被归档条目从 active 规则集移出)。
- 已归档的项后续 maintain/prune 不会重复检出 (已移出扫描范围)。

## 7. 与 maintain 的关系

prune 是**自动**执行 (sediment 后顺跑, 命中即 archive); maintain 是**手动**体检 (只报告不动手, 供 user 独立审查)。两者判据集合共享同一张「按 namespace 分表」, 详见 [maintain.md](maintain.md)。`maintain --apply` 走的是与 prune 相同的自动修复逻辑 (product namespace 同样只报告不修)。

## 8. 反例

| 禁 | 改为 |
|---|---|
| product namespace anchors 失效直接 archive | 只报告, 交人判断 |
| `protected: true` 规则命中判据仍 archive | 跳过, 尊重保护标记 |
| 无命中还是跑一次 archive 空操作 | 检出 0 条则报「无精简项」, 不调用 archive |
| 断链判据自动改链或建目标 | 只报告, 改链/建目标需人判断该动哪头 |
