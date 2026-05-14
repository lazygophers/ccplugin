---
description: log/session 数据日处理 — 调度 cortex-digest skill 跑五阶段 pipeline (无入参, 每日 cron)
---

# /cortex:digest

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

调度 `cortex-digest` skill 执行完整 log/session 数据生命周期 (读+析+处+更新+清理+归档)。

## 执行步骤

1. 调 `Skill cortex-digest` 加载五阶段规范 (SKILL.md 单一真相源)
2. 按 skill 描述顺序执行五阶段, 无跳跃, 无询问
3. 输出 compact JSON (字段见 skill `## 输出`)

## 关键约束 (skill 已规定, 此处提醒)

- L4-流水账: 单向漏斗, 每次跑必清 0 残留 (promote/archive/delete 三选一)
- L0/L1: 永不删条目, 仅 weight bump
- 既有 L0-L3 + 知识库: 全量交叉参照, 命中即学习更新 (append 例证 / wikilink / 反思矛盾页)
- 收件箱: ≥30 天强清 (classify/archive/delete)

## 调度

每日 **03:00** cron 自动跑 `~/.cortex/scripts/digest.sh`。
用户手动: `bash ~/.cortex/scripts/digest.sh` 或会话内 `/cortex:digest`。

## 路由 (阶段 3)

反思/连接/矛盾/决策 4 类候选在落档前跑 repo 归属识别 (6 信号: frontmatter host/org/repo · source_url · wikilink · git URL · tag · keyword ≥3), 命中即落 `知识库/项目/<host>/<org>/<repo>/笔记/`, 否则 fallback `知识库/收件箱/` (反思 fallback 日记)。详见 skill §2 / §3。

## Sanity Check

跑完 digest 后 `知识库/收件箱/` ≥30 天文件数应递减 (阶段 5 强制重扫):

```bash
find "$VAULT/知识库/收件箱" -type f -name "*.md" -mtime +30 | wc -l
# 期望: 较上次 digest 前递减; 长期稳态应趋近 0
```
