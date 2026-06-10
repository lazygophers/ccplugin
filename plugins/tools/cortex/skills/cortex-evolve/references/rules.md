# rules — 升降级规则 + 金字塔约束

## 金字塔模型

```
        L0  ← 稠密、稀少 (尽可能少, 默认 ≤ 20 条)
       L1
      L2     ← 主要工作区 (双向自动)
     L3
    L4       ← 庞大, 收件箱 + 短期
```

L0 信息**稠密**: 每条都是核心硬规, 越少越好.
L4 容量**庞大**: 收件箱 + 短期, 信息密集容忍.
**主要工作区 = L4-L2** (自动双向); L1/L0 受限 (仅自动升, 禁自动降).

## 升级规则

| 来源 → 目标 | 阈值 |
| --- | --- |
| L4 → L3 | **不在 evolve 范围**, 走 `cortex-extract` (inbox 入门级路由) |
| L3 → L2 | promote_score ≥ 0.6 |
| L2 → L1 | promote_score ≥ 0.7 + 复用 ≥ 5 + weight ≥ 0.8 |
| L1 → L0 | promote_score ≥ 0.9 + 用户多次强调 (≥ 3 次 "永远/硬性") + 复用 ≥ 10 |

跳级 (L3 → L1 直跳) 仅当 promote_score ≥ 0.9 + user_emphasis_count ≥ 3.

## 降级规则

| 来源 → 目标 | 阈值 | 例外 |
| --- | --- | --- |
| L2 → L3 | demote_score ≥ 0.7 + 30d 未访问 | — |
| L3 → L4 | **不直接**, 标 forget candidate, 走 `cortex-lint --check` forget audit | — |
| L1 → L2 | **L1 不主动降级** (硬规) | 仅标 audit-candidate, 用户显式 forget 才执行 |
| L0 → L1 | **L0 不主动降级** (硬规) | 同上 |

## 5 修饰规则

1. **用户反复强调 (≥ 3 次)** → 强升级, **跳级允许** (L3→L1, L2→L0 单步). 计数由 signals.md `user_emphasis_count` 维护.
2. **L1/L0 自动升允许** (从下级 promote): L2→L1, L1→L0 满足阈值时自动执行, **无需 ask**, 但 lint 标 `audit-candidate` 让用户事后审.
3. **L1/L0 新写入 ask** (非 promote 路径): 用户直接落 L0/L1 新条目 (不经 L2 升上来), **必须 ask 确认**. 与 `cortex-save` / `cortex-extract` 的 L0/L1 ask 行为一致.
4. **L1/L0 不主动降 (硬规)**: 即使 demote_score ≥ 0.9, L1/L0 条目仅写入 lint audit 报告, 不移动文件. 用户显式 `forget` 才动.
5. **L0 audit warn**: vault 中 `memory/L0-core/` 条目数 > 20 → `cortex-lint` warn "金字塔顶部膨胀, 建议审查". 默认阈 20, 可配置.

## 适用范围速查

| 级别 | 自动升 | 自动降 | 直接写入新条目 |
| --- | --- | --- | --- |
| L4 → L3 | 走 `cortex-extract` | — | — |
| L3 ↔ L2 | ✓ | ✓ | 否 (走 extract/save) |
| L2 → L1 | ✓ (无 ask, 标 audit) | ✗ | 否 |
| L1 → L0 | ✓ (无 ask, 标 audit) | ✗ | 否 |
| 直接写 L1 | — | — | **必须 ask** |
| 直接写 L0 | — | — | **必须 ask** |

## 边界 vs cortex-extract

`cortex-extract` 处理 **L4-inbox 入门级路由** (新条目从 inbox → L3/L2/L1/L0 或项目/领域). 它的"三轴" (抗遗忘度/强度/复用面) 用于**初次分类**.

`cortex-evolve` 处理 **已入 vault 后的跨级再平衡**, 不碰 inbox. 它的"三轴" (频率/时间/重要度) 关注**使用模式**而非内容特征.

两者可共享评分函数实现, 但触发场景不同:
- extract 触发: "整理 inbox" / 新条目落地
- evolve 触发: "记忆 audit" / 定期再平衡 / 跨级 promote/demote

## 边界 vs cortex-save

`cortex-save` = **一次性写入新条目** (用户主动添加).
`cortex-evolve` = **移动既有条目** (跨级再平衡, 不新建内容).

apply 阶段 evolve 调用 cortex-save 仅复用其"frontmatter 校正 + 文件移动"机制, 不重写正文.
