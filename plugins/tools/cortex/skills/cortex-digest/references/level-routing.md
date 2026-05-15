# cortex-digest — L0-L4 级别边界 + AUTO_MODE 契约

## 级别边界速查

| level | 边界 | digest 行为 |
|-------|------|------------|
| L0 | 性格/价值观/硬约束, ≤1500c | 仅交叉参照, 永不改 |
| L1 | 技能/稳定语义, ≤5000c | 仅 weight bump + append 新例证 |
| L2 | 语义, ≤3000c, 365 天时效 | weight bump + append; 365 天衰减由 cortex-memory forget 子流程 |
| L3 | 情节, ≤2000c, 90 天时效 | append; 90d weight<0.3 删 |
| L4 | ledger/sessions, single-pass | 全清 (promote/archive/delete) |

## AUTO_MODE 契约

**核心原则**: "禁问" ≠ "中止". AI 必须**自决并执行直至任务完成**。遇歧义按推荐默认值; 工具不熟悉则尝试其他工具组合 (Bash/Edit/Write/MCP/Read 既有样本); 禁报"需人工"/"AI 不会"/"建议后续处理"。

### 严禁

| # | 禁止 |
|---|------|
| 1 | "修复建议"/"建议"/"推荐操作" 章节/表格/列表 |
| 2 | 用户确认问句 (`需确认?`, `是否执行?`, `要继续吗?`, `ok?`, 末尾问号) |
| 3 | AskUserQuestion 调用 (allowed-tools 已禁) |
| 4 | "下一步"/"后续"/"如需"/"可选" 导引 |
| 5 | "需人工"/"待人工"/"建议人工" 推卸辞令 |
| 6 | "AI 能力不足"/"无法自动" 类借口 |
| 7 | 报状态后停 (除非客观失败: 磁盘只读/权限拒绝/git lock) |

## 调度

每日 03:00 cron 自动跑 `~/.cortex/scripts/digest.sh` (wrapper) → `/cortex:digest auto` (slash) → 本 skill (会在阶段 6 内联调 `digest.sh evolution` 抽 pattern)。
用户手动: `bash ~/.cortex/scripts/digest.sh` 或会话内 `/cortex:digest`。
evolution 单独跑: `bash ~/.cortex/scripts/digest.sh evolution --lookback-days 7 --json` (直调 python CLI, 不走 claude session)。

## 评分双路调 (digest 内联)

- **使用信号**: `log10(召回次数 + wikilink 反向引用 + 1) - 0.1 自然衰减` → importance ↑
- **反馈信号**: 用户 "不对/错了" → confidence -= 1.0, "对的/正确" → confidence += 0.5
- 实现: `scripts/cli/lib/evolution.py:update_doc_scores` + digest evolution `--update-scores` 默认开
