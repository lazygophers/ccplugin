---
title: cortex digest 识别项目/仓库 — 条目按 host/org/repo 路由到合适位置
status: planning
priority: P2
owner: nico
created: 2026-05-14
---

# 背景

`/cortex:digest` 阶段 3 处理候选条目时, **统一**落 `知识库/收件箱/` (反思候选 / 连接候选 / 矛盾页), 不识别条目是否属某 repo。

用户诉求: digest 时**识别**条目归属 host/org/repo → 落到对应 `知识库/项目/<host>/<org>/<repo>/` (笔记 / 决策 / 陷阱 子目录), 而非通通进收件箱。

# 设计

## 1. SKILL.md §2 析阶段加 repo 识别

每个候选条目 (反思 / 连接 / 矛盾 / 概念) 跑识别:

**识别信号 (并集, 任一命中即归属)**:
- frontmatter `host` / `org` / `repo` 字段
- frontmatter `source_url` 含 `github.com/<org>/<repo>` 或 `gitlab.*/<org>/<repo>` 或 `<host>:<port>/<org>/<repo>`
- 正文 wikilink `[[知识库/项目/<host>/<org>/<repo>/...]]` 或 `[[<repo-name>]]` 命中已知 repo
- 正文含 `git@<host>:<org>/<repo>` / `https://<host>/<org>/<repo>` URL
- tag `repo/<name>` / `host/<host>` / `org/<org>`
- 关键词匹配 (`<repo-name>` 出现 ≥ 3 次, repo 名单从 `知识库/项目/` 现有目录拉)

识别结果: `route_target = 知识库/项目/<host>/<org>/<repo>/` 或 `route_target = inbox` (无信号 fallback)。

## 2. SKILL.md §3 处阶段加路由表

| 候选类型 | 命中 repo (route_target ≠ inbox) | 未命中 (fallback inbox) |
|---|---|---|
| 反思 | `知识库/项目/<repo>/笔记/<YYYY-MM-DD>-反思-<topic>.md` | `知识库/收件箱/<date>-反思-<topic>.md` |
| 连接 | `知识库/项目/<repo>/笔记/<YYYY-MM-DD>-连接-<a-b>.md` (若 a/b 同 repo) 或 `知识库/项目/<a-repo>/笔记/...` (跨 repo 落 a 端 + b 端反链) | `知识库/收件箱/<date>-连接-<a-b>.md` |
| 矛盾 | `知识库/项目/<repo>/笔记/<YYYY-MM-DD>-矛盾-<topic>.md` (frontmatter 列既有条目 path) | `知识库/收件箱/<date>-矛盾-<topic>.md` |
| 概念 (升 L2/L3) | 不路由到 项目/ (记忆层独立) | 不变 |
| 决策提炼 | `知识库/项目/<repo>/主题/决策.md` append 新段 (若已存在主题/决策.md) | `知识库/收件箱/<date>-决策-<topic>.md` |

`<repo>` 占位 = `<host>/<org>/<repo>` 三段。

## 3. SKILL.md §3 加路由 fallback 规则

- 多 repo 候选 (一个条目识别到 ≥ 2 repos): 路由到**首要 repo** (信号强度: frontmatter > wikilink > URL > keyword), 其他 repo 各加 backlink 兜底
- repo 不存在 (`知识库/项目/<host>/<org>/<repo>/` dir 缺): 自动 `mkdir -p` 创建, 同时 `_index.md` 不存在则触发 minimal stub (`type: project`, frontmatter 5 字段, body 1 行说明)
- 笔记目录 (`知识库/项目/<repo>/笔记/`) 不存在: 自动创建

## 4. SKILL.md §5 清理阶段同步

`知识库/收件箱/` 老条目 (≥ 30 天) 强制处理: 重跑识别, 命中即迁移到对应 项目/笔记/; 仍无命中则归档 `归档/收件箱-<YYYY-QN>.md` 季度桶。

## 5. commands/digest.md 同步

末段加路由说明 + bash sanity check (跑完 `find 知识库/收件箱/ -type f -newer <30d-ago>` 应递减)。

## 6. agents/cortex-archivist.md 同步

description 加 "digest 阶段路由识别失败的条目, archivist 再扫做二次归属"。

# 验收

1. SKILL.md §2 含 repo 识别 6 信号 (frontmatter / source_url / wikilink / URL / tag / keyword)
2. SKILL.md §3 含路由表 (反思/连接/矛盾/决策 4 类 × 命中/未命中)
3. SKILL.md §3 含跨 repo / repo 不存在 / fallback 规则
4. SKILL.md §5 收件箱 30 天复扫规则
5. commands/digest.md 同步 sanity check
6. agents/cortex-archivist.md 同步
7. GLM 自检识别 "host/org/repo 识别 6 信号" + "路由表 4 类"
8. pytest 314 pass

# 不做

- 不改 python `memory.py consolidate` (路由是 AI 行为, 在 SKILL 层)
- 不改 ledger 落档 (它仍按时间走, digest 阶段才路由)
- 不强制 repo 自动创建 _index.md 完整内容 (minimal stub 即可, 详细由后续 ingest 补)

# 风险

- 识别误判 (wikilink 命中 `[[react]]` 但用户文是讲 react 概念非 react repo) → 用强信号优先 (frontmatter > wikilink), 弱信号 (keyword) 阈值 ≥ 3 次防误识
- 跨 repo 连接条目落到 a 端易丢 b 端可见性 → b 端必加 backlink (`## 相关` 列 `[[a-side-path]]`)
- 大量收件箱老条目复扫慢 → 仅扫 ≥ 30 天 (用户场景小, 加缓存可后续)
