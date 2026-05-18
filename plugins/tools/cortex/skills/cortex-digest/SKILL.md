---
name: cortex-digest
description: 全量深度 digest — log/session 数据 + 全 vault 深读 (8 阶段, 默认 deep, 无 depth 参数), 增量游标 (vault/.cortex/state/*.json) 自动跳已处理。L4 全清单向漏斗, L0/L1 永不删条目。触发: daily cron 03:00 / 用户显式 "digest" / "巩固记忆" / "consolidate"。
disable-model-invocation: false
allowed-tools: Bash Read Write Edit Glob Grep Skill
---

# cortex-digest

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

**全量深度模式 — 默认 deep, 无 depth 参数**。每日跑一次完整 8 阶段, 增量游标 (`vault/.cortex/state/*.json`) 驱动避免重复处理。全量跑可能数小时, 不中止 / 不分批。

## 触发场景

- daily cron 03:00 自动 (`~/.cortex/scripts/digest.sh` → `/cortex:digest auto`)
- 用户显式 "digest" / "巩固记忆" / "整合 ledger" / "consolidate"
- 会话内 `/cortex:digest` 走交互模式 (行为同 auto)

## 8 阶段决策树 (顺序严格, 一次跑完)

| # | 阶段 | 行为 | 状态文件 |
|---|---|---|---|
| 1 | 读 (Read) 增量扫 | 读 `.cortex/state/digest.json` 拿 cursor; 扫 inbox + log + sessions + L4 中 mtime > cursor 的; 文件 hash 命中 processed_files 则跳 | 读 state/digest.json |
| 2 | 析 (Analyze) 深度 | LLM 深读全文 (非启发式), 抽 4 类候选 (反思/连接/矛盾/决策) + 实体 + 概念 + repo 6 信号归属 | — |
| 3 | 处 (Process) 路由 | 路由 4 类 → 项目/<host>/<org>/<repo>/ 或 收件箱/; 概念/实体 → 领域/<域>/; episodic → L3 | 写新文件 |
| 4 | 维护 | 委派 `Skill(cortex-memory)` 跑维护扫 (整理 / 升级候选 / 补充 / forget / 评分双路调) | cortex-memory 内部 |
| 5 | 整合 (Consolidate) 项目→领域 (new) | LLM 深读 `知识库/项目/<repo>/` 通用概念 → 抽到 `知识库/领域/<域>/`; 与既有合并/比对 | 写 state/consolidate.json |
| 6 | 优化 (Enrich) 图表+tags (new) | LLM 判每个 md 适合图表 (flow/timeline/mindmap/table), 注 mermaid 块 (frontmatter 后, 不动正文); 重抽 tags/aliases (≥3 alias, ≥5 keyword, 中英对) | 写 state/enrich.json |
| 7 | 验证 (Verify) search 多次 (new) | 对高 weight 记忆 / 重要知识库条目 search 多次 (不同关键词组合); 无反向引用 / 无相似 → frontmatter 标 `verify_issue: <reason>` | 写 state/verify.json |
| 8 | Evolution + 清理 | sessions pattern 抽取 → patterns.md + proposals; L4 全清 (promote/archive/delete); L3 90d w<0.3 删; 收件箱 ≥30d 复扫 | 写 patterns.md, 清 L4 |

**L0/L1 永不删条目** (硬约束)。L4 单向漏斗。各阶段独立 cursor, 单阶段失败不影响其他。

## 增量游标 (核心机制)

每个阶段独立 state 文件 (`vault/.cortex/state/{digest,consolidate,enrich,verify}.json`):

- 文件 hash 比对: `state/<stage>.json:processed_files[<rel_path>].hash == sha256(file)` → 跳过该文件该阶段
- mtime > cursor 才进 phase
- 阶段结束写回累计统计 + 更新 cursor (`cursors.inbox_last_mtime` / `log_last_date` / `session_last_id`)
- 失效阈值: `state.last_run` 距今 > 30 天 (config 可调 `incremental_max_age_days`) → 视为首次跑, 全量重处理

state JSON schema 详见 [references/state-store.md](references/state-store.md)。

## 配置 (vault/.cortex/config/)

- `digest.yaml` — 各阶段开关 (consolidate/enrich/verify) + 增量失效阈值 + 域名强映射
- `enrich.yaml` — mermaid 类型白名单 + 跳过路径
- `tags.yaml` — tag 命名约定 + alias 同义词表

缺省 (文件不存在 / 字段缺) 按 skill 默认值跑。

## AUTO_MODE 分支 (D10)

`/cortex:digest auto` (wrapper / cron) 与 `/cortex:digest` (会话) 行为一致:
- 跳所有 `AskUserQuestion` (allowed-tools 已禁)
- 8 阶段顺序 + 默认参数 (lookback=7, update-scores=on, dry-run=off)
- 任一阶段失败 → 重试一次, 仍失败 → stderr 报错继续下一阶段, 不中止 pipeline
- 全量跑数小时是预期, **不分批 / 不报 "建议人工"**

## 输入 (wrapper 注入, skill 不接位置参数)

- `--vault <path>` (必须, 由 wrapper 传入)
- `--lang <code>` (可选, 默认 vault `_meta/version.json:lang` 或 zh-CN)
- `--dry-run` (可选, 仅分析不写盘 + state)

**不接受 `--depth` 参数** (硬约束: 默认 deep, 增量游标处理性能, 不降级深度)。

## evolution 子命令 (独立, 阶段 8 内联同 CLI)

`bash ~/.cortex/scripts/digest.sh evolution --lookback-days 7 --json` — 直 exec python CLI, 不走 slash, 输出 JSON。proposal 反写 SKILL/AGENT 由用户调 cortex-refactor `evolution-apply` 单独消化。

## References 指针

| 文件 | 内容 |
|---|---|
| [pipeline-stages.md](references/pipeline-stages.md) | 8 阶段详细规范 + 输出 JSON schema + 错误处理 |
| [state-store.md](references/state-store.md) | `.cortex/state/*.json` 完整 schema + 读写规约 + 失效策略 + migration |
| [extraction.md](references/extraction.md) | 阶段 2-3 抽取 + 路由细节 |
| [consolidate.md](references/consolidate.md) | 阶段 5 项目→领域 提炼算法 + LLM prompt + 合并冲突 |
| [enrich.md](references/enrich.md) | 阶段 6 图表注入规则 + tags/aliases 抽取 + 跳过路径 |
| [verify.md](references/verify.md) | 阶段 7 多次 search 交叉验证 + 问题分级 |
| [cleanup.md](references/cleanup.md) | 阶段 8 清理 + 归档规则 |
| [evolution.md](references/evolution.md) | 阶段 8 pattern 抽取 + proposal 落盘 |
| [level-routing.md](references/level-routing.md) | L0-L4 级别边界 + AUTO_MODE 严禁清单 + 调度 + 评分双路调 |
