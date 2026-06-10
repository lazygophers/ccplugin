# signals — 三轴评分

evolve 升降级判定基于 3 个独立信号轴, 加权合成 `promote_score` / `demote_score`. 复用 `cortex-extract` 的三轴模式 (抗遗忘度 / 强度 / 复用面), 但语义聚焦于"再平衡"而非"入门级路由".

## 1. 频率 (recency-frequency)

最近窗口内的提及/访问次数. 高频 → 升; 低频 → 降.

- **窗口**: 默认 N = 14d (≥ 7d 最小, 防短时噪声)
- **计算**:
  - `freq_recent` = 最近 N 天内该条目被提及/被 wikilink 引用/被读取的次数
  - `freq_history` = 历史总提及次数 (建库以来)
  - `freq_score` = min(1.0, `freq_recent` / max(3, `freq_history` / age_days * N))
- **升级阈**: 近 14d ≥ 3 次提及 → 强升级信号 (freq_score ≥ 0.7)
- **降级阈**: 近 30d 0 次提及 + 历史曾提 ≥ 1 → 弱降级信号 (freq_score ≤ 0.2)
- **数据源**: git log (file path 出现) / wikilink 反链扫描 / mtime

最小提及计数 = 3 (低于不触发, 防误判).

## 2. 时间 (event-recency)

事件距今的"新鲜度". 越近 → 升; 越远 → 降.

- **计算**:
  - 优先取 frontmatter `event_date` (事件实际发生时间)
  - 缺则取 frontmatter `updated` 或文件 mtime
  - `age_days` = today - event_date
  - `recency_score` = exp(-age_days / 30) (30d 半衰期)
- **升级阈**: `age_days` ≤ 7 → recency_score ≥ 0.8 (+1 升级权重)
- **降级阈**: `age_days` ≥ 90 → recency_score ≤ 0.05 (+1 降级权重)

注意: 仅时间老 ≠ 必须降. 频率仍高的"经典条目"由频率轴拉回.

## 3. 重要度 (importance)

用户主观赋权 + 关键词信号. 不主动降.

- **计算**:
  - 基础 = frontmatter `weight` 字段 (0.0 ~ 1.0, 默认 0.5)
  - 关键词加分: 正文含 `永远/硬性/never/严禁/绝不` → weight = max(weight, 1.0)
  - 关键词减分: 正文含 `暂时/临时/这次` → weight = min(weight, 0.3)
  - `importance_score` = weight
- **升级阈**: weight ≥ 0.8 → 强升级信号
- **降级阈**: weight ≤ 0.3 + freq_score ≤ 0.2 → 弱降级 (仅 L4-L3, 不触发 L2 以上主动降)

重要度只能**强化升级 / 抑制降级**, 不主动触发降.

## 综合得分

```
promote_score = 0.4 * freq_score + 0.3 * recency_score + 0.3 * importance_score
demote_score  = 0.4 * (1 - freq_score) + 0.3 * (1 - recency_score) + 0.3 * (1 - importance_score)
```

权重 0.4 / 0.3 / 0.3: 频率是最强信号 (实际使用), 时间与重要度次之.

### 触发阈

| 动作 | 阈 |
| --- | --- |
| 候选升级 | promote_score ≥ 0.7 |
| 候选降级 | demote_score ≥ 0.7 |
| 跳级升级 (L3→L1) | promote_score ≥ 0.9 + 用户反复强调 ≥ 3 |
| 跳级降级 | **禁止**, 每次只降 1 级 |

### 用户强调计数

`user_emphasis_count` = 正文 + frontmatter `notes` 中"永远/硬性/never/严禁/绝不"关键词出现次数 (+ 用户对话中显式 "记住这条" 等指令, 由 main 维护).

≥ 3 → 跳级允许 (L3→L1 / L2→L0 单步).

## 示例

条目 A: 近 14d 提及 5 次, 7d 前更新, weight=0.9 →
- freq_score = 1.0, recency_score = 0.79, importance_score = 0.9
- promote_score = 0.4*1.0 + 0.3*0.79 + 0.3*0.9 = 0.91 → **强升级**

条目 B: 近 30d 0 提及, 100d 前更新, weight=0.3 →
- freq_score = 0.0, recency_score = 0.04, importance_score = 0.3
- demote_score = 0.4 + 0.29 + 0.21 = 0.90 → **强降级候选** (若在 L2-L3 主动降; 若在 L1/L0 仅标 audit-candidate)
