---
name: cortex-digest
description: log/session 数据日处理 — 读 (含既有 L0-L3 + 知识库) → 析 → 处 (含学习更新) → 更新 → 清理 + 归档。L4 全清单向漏斗, L0/L1 永不删条目。触发: daily cron 03:00 / 用户显式 "digest" / "巩固记忆"。
disable-model-invocation: false
allowed-tools: Bash Read Write Edit Glob Grep Skill
---

# cortex-digest

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

每日运行一次完整的 log/session 数据生命周期 (六阶段), 包含 L4 全清 + 既有知识层交叉学习更新 + evolution 经验抽取 (semantic 模式库 + 反写提议)。

## 触发场景

- daily cron 03:00 自动 (`~/.cortex/scripts/digest.sh` → `/cortex:digest auto`)
- 用户显式 "digest" / "巩固记忆" / "整合 ledger" / "consolidate"
- 会话内 `/cortex:digest` 走交互模式

## 六阶段决策树 (顺序严格, 一次跑完)

```
1. 读 (Read)         — L4-流水账 + 日记/收件箱 (待清) + L0-L3 + 知识库 (索引)
   ↓
2. 析 (Analyze)      — 4 类候选 (反思/连接/矛盾/决策) + 6 信号 repo 归属
   ↓
3. 处 (Process)      — 路由命中 repo → 项目/<host>/<org>/<repo>/, 否则 fallback 收件箱/
   ↓
4. 更新 (Update)     — uri-index 重建 + L4→L3 自动晋 + L3↑/L2↑ 晋级候选扫 (写 candidates.md) + L2/L3 过期标 archive_pending + index/hot 引用
   ↓
5. 清理 (Cleanup)    — L4 全清 + L3 90d weight<0.3 删 + 收件箱 ≥30d 复扫
   ↓
6. Evolution         — sessions pattern 抽取 → patterns.md + proposal 列表 (不自动 patch)
```

**L0/L1 永不删条目** (硬约束)。L4 单向漏斗 (promote/archive/delete)。

## AUTO_MODE 分支 (D10)

`/cortex:digest auto` (wrapper / cron 触发):
- 跳所有 `AskUserQuestion` (allowed-tools 已禁)
- 6 阶段顺序 + 默认参数 (lookback=7, update-scores=on, dry-run=off)
- 任一阶段失败 → 重试一次, 仍失败 → stderr 报错继续下一阶段, 不中止 pipeline

`/cortex:digest` (会话内交互): 同 auto 行为 (digest 整流程无需用户决策)。

## 输入 (wrapper 注入, skill 不接位置参数)

- `--vault <path>` (必须, 由 wrapper 传入)
- `--lang <code>` (可选, 默认 vault `_meta/version.json:lang` 或 zh-CN)
- `--dry-run` (可选, 仅分析不写盘)

## evolution 子命令 (PR3, 单独跑)

`bash ~/.cortex/scripts/digest.sh evolution --lookback-days 7 --json` — 直 exec python CLI, 不走 slash, 输出 JSON (sessions_scanned / patterns_added / proposals_generated 列表)。proposal 反写 SKILL/AGENT 由用户调 cortex-refactor `evolution-apply` 单独消化。

## References 指针

| 文件 | 内容 |
|---|---|
| [pipeline-stages.md](references/pipeline-stages.md) | 六阶段详细规范 + 输出 JSON schema + 错误处理 |
| [extraction.md](references/extraction.md) | 阶段 2-3 抽取 + 路由细节 |
| [cleanup.md](references/cleanup.md) | 阶段 5 清理 + 归档规则 |
| [evolution.md](references/evolution.md) | 阶段 6 pattern 抽取 + proposal 落盘 |
| [level-routing.md](references/level-routing.md) | L0-L4 级别边界 + AUTO_MODE 严禁清单 + 调度 + 评分双路调 |
