---
name: cortex-consolidate
description: 记忆固化 — ledger/sessions → views, L4→L3 episodic / L3→L2 semantic 巩固提炼。触发: "consolidate" / "巩固记忆" / weekly cron 自动触发。
disable-model-invocation: true
allowed-tools: Bash Read Write Glob
---

# cortex-consolidate

读 L4 流水账 + L3 短期记忆, 提炼高频模式 → views/consolidated/, 推升候选到 views/candidates.md (待 cortex-promote 处理)。

## 触发场景
- weekly cron `memory-consolidate.sh` (Sun 04:30)
- 用户显式 "consolidate memory" / "巩固记忆" / "周报"
- cortex-reflect 内部调用做预处理

## 输入
- --since: 默认 `7d` (最近 7 天 ledger + sessions); 可 `30d` / `90d`
- --target: 默认 `weekly` (写 `views/consolidated/<YYYY-Wnn>.md`); 可 `monthly`
- --dry-run: 仅打印分析, 不写盘

## 流程

1. **扫源**:
   - Glob `记忆/L4-流水账/ledger/<since>.jsonl` 全部行
   - Glob `记忆/L4-流水账/sessions/<cli>/<recent-month>/*.md`
   - Glob `记忆/L3-短期/episodic/<since>/` 已有情节
2. **频次分析**:
   - 提取实体 (tags/wikilinks/标题关键词)
   - 计 entity_freq, topic_freq
   - 识别重复模式 (≥3 次出现, 跨 ≥2 天)
3. **L4→L3 提炼** (daily 部分, 不在此 skill 做; 仅汇报):
   - 引用 cortex-memory write L3://episodic/<date>/<slot>
   - 高频但仍单日 → 写 L3, ref 回 ledger 行号
4. **L3→L2 候选** (本 skill 主战场):
   - 跨周重复模式 → 写 `记忆/views/candidates.md` 一行:
     ```
     - [ ] L3://episodic/<date>/<slot> → L2://semantic/<topic>  (recurrence: 5x in 7d, weight 0.6)
     ```
   - 不直接 promote, 交 cortex-promote 处理
5. **跨域 connections** → 写 `知识库/反思/连接/<YYYY-Wnn>.md`:
   - 不同 domain 实体在同一 episode 共现 → 连接候选
6. **周报落盘** `记忆/views/consolidated/<YYYY-Wnn>.md`:
   - frontmatter: window, since, until, generated_at
   - 正文: top entities / top topics / candidates count / connections count
7. **更新 candidates.md**: append 新候选, 去重 (按目标 URI)

## 输出
```
[consolidate] window=2026-W19  since=2026-05-05  until=2026-05-12
  scanned: 7 ledger files (412 events), 3 session files, 18 episodic notes
  top entities: goroutine(8), channel(5), select(4)
  L3→L2 candidates: 3 (written to views/candidates.md)
  cross-domain connections: 2 (written to 知识库/反思/连接/2026-W19.md)
  weekly report: 记忆/views/consolidated/2026-W19.md
```

## 错误处理
- ledger 行 JSON 解析失败 → 跳过该行, 末尾汇总 invalid_lines count
- session md frontmatter 缺失 → 视为纯文本, 仅参与 entity 提取
- views/candidates.md 不存在 → 自动创建空骨架
- 写盘并发冲突 → 配合 file_lock (cron run.sh 提供 flock)

## 重复检测 → 晋级

扫 L4 ledger 上 7 天, 统计 (entity, topic, context) 三元组:
- freq ≥ 3 → 抽象为 L3 episodic 候选 (auto)
- 跨域出现 ≥3 次 → 写 `知识库/反思/连接/<week>.md`

触发 memory-promote 跑下一阶段晋级 (L3→L2, L2→L1 候选; L1→L0 永不自动)。

## 级别边界速查 (详见 `_meta/memory-policy.yaml`)

| level | 边界 | review |
|-------|------|--------|
| L0 | 性格/价值观/硬约束, ≤1500c | monthly hash 检测 |
| L1 | 技能/稳定语义, ≤5000c | monthly 矛盾告警 |
| L2 | 语义, ≤3000c, 365 天时效 | monthly 365 天衰减 |
| L3 | 情节, ≤2000c, 90 天时效 | weekly 同事件 ≥5 抽象 L2 |
| L4 | ledger/sessions, append-only | weekly 30 天 gzip 60 天归档 |

## AUTO_MODE 兼容
[AUTO_MODE: ...] (cron 默认场景) 全自动执行写盘; 仅在 --dry-run 时不写。candidate 永不直接 promote (这是 cortex-promote 职责)。

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/consolidate.sh`, cron 默认场景):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁此工具, 强行调用必失败)
2. 任何需用户决策处 → 走默认值跳过
3. persistent: 任何 error 自决降级 / 重试 / 换工具, 禁询问, 禁中止
4. 写盘前不需二次确认 (AUTO_MODE 隐含已授权); 仅在显式 `--dry-run` 时不写
5. candidate 永不直接 promote (那是 cortex-promote 职责)
