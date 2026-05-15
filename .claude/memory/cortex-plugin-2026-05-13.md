---
name: cortex-plugin
description: Cortex 插件当前真相 — vault 结构 / agent / skill / wrapper / 写契约 / 记忆层 / 默认行为
type: project
---

# Cortex 插件 — 单一真相清单

**Why**: 跨多轮重构后, cortex 的 vault 模型、agent 集合、preset、fold/historian 等已多次反转。本 memo 是当前真相基线, 历史变迁见 git log。

**How to apply**: 改 cortex 时以本清单为准, 旧 memory / docs 与此冲突时本清单优先。

## Vault 模型

- 单一 schema (无 preset 系统)。`_meta/version.json` 仅含 `lang` / `preserve_transcript` / `auto_commit` / `auto_push`
- 顶层: `_meta/ _templates/ _assets/ 知识库/ 记忆/ 仪表盘/ 归档/ locales/ .obsidian/ .trash/` (lint `vault-structure-violation` 强制)
- 知识库 4 子目录: `项目/<host>/<org>/<repo>/`, `领域/{创作,学习,工作,技术,生活,金融,未分类}/`, `日记/日/<YYYY-MM>/<YYYY-MM-DD>.md`, `收件箱/`
- 记忆 L0-L4: `L0-核心/ L1-长期/ L2-中期/ L3-短期/ L4-流水账/{ledger,sessions}/ working/ views/{consolidated,candidates.md}`
- 项目路径策略: github/gitlab 走 `host/org/repo` 三段; 本地仓库走相对 `$HOME` 路径, 不足 3 段补 `_local`
- AI 自决域: `--domain` 可选, 缺时 AI 读 body 自决 6 域, 不匹配默 `领域/未分类/`

## 资产计数

| 类型 | 计数 | 备注 |
|---|---|---|
| Agents | 7 | curator / researcher / archivist / cartographer / linker / summarizer / translator (historian 已删) |
| Skills | 21 | 自动触发 + 显式调 |
| Slash commands | 20 | `/cortex:<name>` 冒号 (dash 无法解析) |
| Wrappers | 24 | 10 slash + 3 shell + 11 CLI, 装在 `~/.cortex/scripts/*.sh` |
| Python CLI | 11 | save / search / deep_search / ingest_url / ingest_file / ingest_remote / refresh_projects / memory / ledger / session / html_render |
| Lint 规则 | 20 | run.py autofix 自循环至 clean; rule 18 = `path-lang-mismatch` (按 vault.lang 校验 path segment); rule 19 = `skill-references-exists` (SKILL/AGENT/agent 引用 `references/<x>.md` 必须存在); rule 20 = `base-format-yaml` (`.base` 顶层必须 YAML object, 禁 markdown header / 禁 Dataview DQL, warn 级, autofix=false) |
| Hooks | 5 | SessionStart / PostCompact / Stop / SubagentStop / UserPromptSubmit |
| Cron jobs | 9 | lint / dashboard / digest / memory-{promote,forget,compact,warden,archive} + refresh_projects (weekly Mon 03:00) |

## Vault 写硬契约 (session_start hook 注入)

1. **L1 强制 = `mcp__obsidian__*`** (save / ingest / patch / refactor / lint --fix 等所有 vault 写)
2. **L2 fallback = 官方 `obsidian` CLI** (MCP 工具失败本次回退)
3. **L3 兜底 = 直接文件 IO** (canvas / 非 md / L1+L2 失败时)
4. **MCP 未注册** → AI 必须先 `AskUserQuestion` 单次授权 (options: `安装 MCP` / `本次使用磁盘 IO (有风险)`), 授权仅本会话有效不写盘, 下次启动重新询问
5. **未授权前**: AI 硬拒绝所有 vault 写并提示用户先选择
6. **例外**: Stop hook / cron / python CLI (非 AI 上下文) 走文件 IO, 不受契约约束

## Hook 行为

- **session_start**: header 后立即注入 🔐 Vault 写契约 (探活 mcp-obsidian via `claude mcp list` → `~/.claude.json:.mcpServers`), 然后 stats + L0 core + hot.md + behavior contract + triggers + collab
- **user_prompt_submit**: 检 git remote → 推 project_hint (`host/org/repo`) + KB 相对路径 (`知识库/项目/<hint>/`). 触发词命中时强制 "禁止直接询问用户, 第一个工具调用必须先搜": 三步 a) `--scope domains` 限项目 + path grep repo 名 b) 跨项目 c) `--scope all` 泛搜。仅全无命中才允许向用户提问
- **stop / postcompact**: 纯 jsonl copy 到 `记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/<id>.jsonl`

## 搜索 / 召回优先级

- 知识库 `search.py`: hot.md grep → index.md grep → Smart Connections REST (1s 探活) → ripgrep (兜底)
- 深度 `deep_search.py`: `hybrid` (默认, SC+rg+BM25) / `iterative` (≤3 轮挖 gap token) / `subgraph` (≤3 hop, wikilink_index O(V) 一次构建)
- 记忆 `memory.py recall`: L0→L1→L2→L3→L4 加权, 策略走 `_meta/memory-policy.yaml`
- scope: `all=知识库/`, `concepts=知识库/领域/`, `domains=知识库/项目/`, `log=知识库/日记/`

## Ingest 项目级硬契约 (SKILL §1.1 / §7 / §8 / §9)

- **4 层目录** (`知识库/项目/<host>/<org>/<repo>/`): `主题/` (架构/决策/陷阱/依赖/配置/错误码/测试/功能 ≥4) + `模块/` (top-dir 拆) + `文件/` (源文件→.md) + `符号/api/` (函数/类级)
- **分级 .md 下限**: ≤50 文件 ≥15 .md / 50-500 ≥40 / >500 ≥100; 大 repo 用 `符号/api/<module>/<name>.md` 二级目录防爆炸
- **6 类抽取**: API surface + 配置 schema + 错误码 + 测试用例 + 功能模块 + 全局常量
- **强制排除**: build 产物 / lock / binary / 系统 IDE / 临时备份 / 压缩包
- **知识图谱 4 制品** (内联生): `_db.base` (Bases 3 视图 Obsidian 1.7+) + `_assets/canvases/<repo>.canvas` (≤20 节点) + Wikilink 网 (每 .md 出链 ≥5, 小 repo prorated ≥3) + websearch 扩展 (5 URL 容忍跳过)
- **拒交**: 4 层任一空 / 6 类任一缺 / ALL_MD < 下限 / M/R < 0.8 (R 应用排除清单) → AI 必须继续补

## Digest 路由识别 (SKILL §2-§3-§5)

- **6 信号识别** repo 归属: frontmatter `host/org/repo` (强) > `source_url` (强) > wikilink (中) > URL (中) > tag `host/org/repo/<v>` (中) > keyword ≥3 次 (弱)
- **路由表**: 反思/连接/矛盾/决策 4 类 — 命中 repo 落 `知识库/项目/<host>/<org>/<repo>/笔记/` 或 `主题/决策.md` append; 未命中 fallback `知识库/收件箱/`
- 多 repo: 强信号优先 + 其他 repo 加 backlink
- repo 目录缺: `mkdir -p` + minimal `_index.md` stub
- §5 清理: 收件箱 ≥30 天复扫识别, 命中迁项目/笔记/, 否则归档 `归档/收件箱-<YYYY-QN>.md`

## 关键约定

- AUTO_MODE persistent (禁询问 ≠ 中止, AI 自决循环修复至 clean)
- Frontmatter `tags` ≥10 强制, lint `fm-missing-tags` autofix 派生 (12 维度, 严禁占位符)
- Banned fm fields: `preset` (已废, lint autofix pop)
- 路径 lang 校验 (lint rule 18): vault.lang=zh-CN segment 全 ASCII 或 lang=en segment 含 CJK → warn; 豁免 host/org/repo + ASCII 专名 + frontmatter `path_lang_exempt: true`
- cortex-refactor 3 子操作: `rename` / `merge` / `split` (fold / restructure 已删)
- 插件路径硬编码 `$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex` (env var 解析 bug 规避)
- 自研 MCP 已移除, 走官方 `mcp-obsidian` (用户 `claude mcp add` 自行注册)
- Slash wrapper: `-h`/`--help` + `-i`/`--interactive` (无 -p 进 REPL, 注入 `/cortex:<name>` 首消息) + `--no-commit`; 调 claude 时 echo bash + `--dangerously-skip-permissions`
- 测试: `cd plugins/tools/cortex/tests/python && python3 -m pytest -q` (324 pass + 9 subtests)

## 关联 docs

- `plugins/tools/cortex/AGENT.md` §协作约定 — L1/L2/L3 写契约权威
- `plugins/tools/cortex/docs/{知识库结构,Agents,Commands,Skills 详解,Hooks 机制}.md`
- `plugins/tools/cortex/scripts/lint/schemas.py` — vault 单一 schema 定义

## P5 — 借鉴 agent-playbook 增强 (2026-05-14)

### 借鉴方法论

| 来源 | 应用 |
|---|---|
| context-layering 3 层 (L1 always-on / L2 routing / L3 on-demand) | cortex-ingest/digest SKILL.md 拆 references/ |
| self-improving multi-memory (episodic→semantic 抽取 + 反写) | cortex-digest 加 evolution 第 6 阶段 (semantic patterns 库 + proposal) |

### 资产变更

- cortex-ingest SKILL.md: 497 → ~200 行, 拆出 4 references/ (layout / extract / exclude / knowledge-graph)
- cortex-digest SKILL.md: 175 → ~140 行, 拆出 3 references/ (extraction / cleanup / evolution), 加第 6 阶段 evolution
- 新 CLI: `scripts/cli/digest.py` + `scripts/cli/lib/evolution.py` (evolution 子命令)
- 新 CLI: `scripts/refactor/evolution_apply.py` (list / check / delete 子命令)
- 新 wrapper 子命令: `digest.sh evolution`, `refactor.sh evolution-list/check/delete`
- 新 memory 层: `记忆/L0-核心/patterns.md` (semantic, 多 category section)
- 新 vault 路径: `_assets/evolution-proposals/<YYYY-MM-DD>-<slug>.md` (反写提议)
- 新 lint 规则: `skill-references-exists` (rule 18 → 19)
- 新测试: `test_digest_evolution.py` + `test_evolution_apply.py` + `test_skill_references_lint.py` (6)
- 测试基线: 324 → 360 (+36)

### 反写硬契约

- 阈值硬编码: `confidence ≥ 0.8 AND applications ≥ 3` (digest.py 内常量)
- 触发: 内联 cortex-digest 每次跑 (daily cron)
- 反写流程: AI 主线读 proposal → AskUserQuestion 一条一问接受 → safety gate (git clean + 白名单) → patch SKILL/AGENT 源文件
- Safety gate 白名单: `skills/*/SKILL.md`, `skills/*/references/*.md`, `agents/*.md`, `AGENT.md`
- Safety gate 黑名单: `commands/`, `scripts/`, `_meta/`, `_templates/`

### 关联文件

- `plugins/tools/cortex/skills/cortex-digest/references/evolution.md` — 抽取规范
- `plugins/tools/cortex/skills/cortex-refactor/SKILL.md §evolution-apply` — 反写流程
- `plugins/tools/cortex/scripts/lint/run.py` — `check_skill_references_exists()` (rule 19)

## P6 — 远程 ingest + 批量增量 (2026-05-14)

### 新入口

| Wrapper | python CLI | 用途 |
|---|---|---|
| ingest_remote.sh | scripts/cli/ingest_remote.py + lib/remote.py | github/gitlab clone + website sitemap crawl → 落 知识库/项目/<host>/<org>/<repo or _site/slug>/ |
| refresh_projects.sh | scripts/cli/refresh_projects.py | 扫 知识库/项目/ 全部, 增量更新 (git pull diff / website hash 对比), weekly cron Mon 03:00 |

### 路径策略

- github/gitlab repo: `知识库/项目/<host>/<org>/<repo>/`
- website 有 author: `知识库/项目/<host>/<author>/<slug>/`
- website 无 author: `知识库/项目/<host>/_site/<slug>/`

### 增量元数据

frontmatter 加 (在 `_index.md` 项目根 / 或每页 .md):
- `source_url` / `source_type` (github|gitlab|website) / `last_ingested_at` (UTC)
- git: `last_commit_sha`
- website: `content_hash` (每页 SHA256)

refresh 对比上述字段决定 skip / update。缺字段 → 视首次全量 (向后兼容)。

### 资产计数变更

- Wrappers 22 → 24 (10 slash + 3 shell + 11 CLI)
- Python CLI 9 → 11 (新 ingest_remote.py + refresh_projects.py)
- Cron jobs 8 → 9 (新 refresh_projects weekly Mon 03:00)
- 测试基线 360 → 389
- skills/cortex-ingest/references/layout.md 78 → 99 行 (加增量元数据 schema 节, PR2)

### 关联文件

- `plugins/tools/cortex/scripts/cli/ingest_remote.py` — 远程 ingest CLI
- `plugins/tools/cortex/scripts/cli/refresh_projects.py` — 批量增量 CLI
- `plugins/tools/cortex/scripts/cli/lib/remote.py` — git clone / website crawl 复用模块
- `plugins/tools/cortex/scripts/ingest_remote.sh` + `refresh_projects.sh` — wrapper
- `plugins/tools/cortex/scripts/install_wrappers.sh` — EXPECTED 24 项 + emit_cli 注册
- `plugins/tools/cortex/scripts/install_cron.sh` — 加 weekly cron line

## P7 — .base 格式硬契约 (2026-05-14)

cortex-ingest 生成 `.base` 文件时 AI 受 vault md-native 惯性把 `.base` 当 .md 写, 用户 Obsidian Bases 报"必须为 YAML 对象"。

### 资产变更

- `skills/cortex-ingest/references/knowledge-graph.md §9.1` 加禁忌小节 + 自检命令 (禁 markdown / 禁 Dataview DQL / 顶层 YAML object 强制)
- `scripts/lint/rules.json` 加 rule 20 `base-format-yaml` (warn, autofix=false)
- `scripts/lint/run.py` 加 `check_base_format_yaml()` + main() 加 `.base` 扫描 pass
- 新测试 `tests/python/test_base_format_lint.py` (13 case)
- `docs/Lint 规则.md` 同步表格 + rule 22 段 (含 rule 21 skill-references-exists 补录)
- Lint 规则计数 19 → 20
- 测试基线 389 → 402 (+13)

### 检查内容 (5 检)

1. 首行禁 markdown header (`#` / `##`)
2. 禁 Dataview DQL 行首关键字 (TABLE/LIST/TASK/FROM/WHERE/SORT/GROUP BY/FLATTEN)
3. `yaml.safe_load` 必须成功
4. 顶层必须是 dict
5. 顶层至少含 1 个 Bases schema 字段 (filters / views / formulas / properties)

跳过 `.obsidian/` / `归档/` / `.trash/`。

### 不 autofix

用户 vault 内现存错 `.base` 数据敏感, 不直接 patch。用户主动调 `bash ~/.cortex/scripts/ingest_remote.sh <项目 url>` 重 ingest 覆盖。

### 真 vault 验证

跑 `python3 scripts/lint/run.py --vault <user-vault>` 检出 14 个错 `.base` 文件 (markdown header / Dataview TABLE / YAML 解析失败 / 顶层 str), 符合预期。

## P8 — 评分字段强制 + digest 双路 + refresh maturity 重评 (2026-05-15)

### 字段 schema (0.0-10.0 浮点 + 1 enum)

知识库 .md 强制 4: `score` / `confidence` / `source_credibility` / `maturity` (enum: draft|review|stable|deprecated)
记忆 .md 强制 2: `importance` / `confidence`

### 评分初值 (AI 自评启发式)

- `score`: 6 类抽取覆盖率 × 10
- `confidence`: tag 完整性 (5) + when_to_read (3) + wikilink (2)
- `source_credibility`: host 白名单查表 (anthropic.com=10, react.dev=9.5, github.com=7.5, medium.com=5, 未知 4)
- `maturity`: score<5=draft, <8=review, ≥8=stable

权威: `skills/cortex-ingest/references/extract.md §3.1` + `scripts/cli/lib/remote.py:_HOST_CREDIBILITY`。

### digest 双路 (D4)

- 使用信号: sessions/jsonl 召回 + vault 反向 wikilink → `importance` ↑ (log10(N+M+1) - 0.1 自然衰减)
- 反馈信号: 用户 "不对/错了" → `confidence -= 1.0`, "对的/正确" → `confidence += 0.5`
- 实现: `scripts/cli/lib/evolution.py:update_doc_scores`, `digest evolution --update-scores` 默认开

### refresh maturity 重评 (D5)

- hash 变 ≥ 2 + < 30 天 → `draft`
- 变 1 次 + 旧 `stable` → `review`
- 不变 ≥ 180 天 → `deprecated`
- 不变 ≥ 90 天 → `stable`
- `score` / `confidence` / `source_credibility` 不动
- 实现: `scripts/cli/refresh_projects.py:revalue_maturity`

### 资产变更

- Lint 规则: 22 → 23 (新 `frontmatter-required-scores` warn + autofix)
- Python CLI: 11 → 12 (新 `scripts/migrate/migrate_scores_to_v2.py` 一次性, 不进 24 wrapper 集)
- Wrapper: 24 + 1 一次性 `migrate.sh` (≤ 60 行)
- 测试基线: 402 → 497 (+95 across PR1-PR6; PR6 +12)
- 新 `skills/cortex-memory/references/scoring.md`
- 评分字段: 旧 `score: 1-5 整数` → `0-10 浮点` (migration × 2.0)
- patterns confidence: `0-1` → `0-10` (migration × 10)

### Migration

一次性: `bash ~/.cortex/scripts/migrate.sh --to=v2`
自动 backup tar.gz 到 `/tmp/cortex-migration-backup-<YYYYMMDD-HHMMSS>.tar.gz` (用户手动 `tar xzf` 回滚)
script: `plugins/tools/cortex/scripts/migrate/migrate_scores_to_v2.py` (335 行, ≤ 350)
wrapper: `plugins/tools/cortex/scripts/migrate.sh` (58 行, ≤ 60)

## P9 — search MCP first + 召回率提升 (2026-05-15)

### 问题

用户报 4 个 cortex 搜索 bug:

- P1 AI 没先搜知识库 (hook 提示弱, 仅触发词命中时注入)
- P2 用 bash search.sh 不用 mcp__obsidian__* (设计冲突: hook 推 bash, SKILL 把 MCP 排 L4)
- P3 多 MCP 时用 qmd 而非 obsidian (AGENT 无 ranking, qmd description 更通用)
- P4 召回率低 (frontmatter 不含搜索词具体短语, hot.md 仅项目根 stub)

### 决策 (D1-D4)

- D1 (P2): MCP first 推翻五级回退 — search.sh 仅作 L3 fallback (Obsidian 不可达时)
- D2 (P3): 软提示 "优先 obsidian, 非 qmd", 不强制禁 (避免破坏其他 MCP 工作流)
- D3 (P1): hook 每个 user prompt 都注入硬契约 (移除触发词限定), 触发词命中时额外加项目 hint
- D4 (P4): ingest/save 自动抽 aliases (≥3) / keywords (≥5) frontmatter (启发式, 中英对 23 + 缩写 16)

### 实现

- hook `user_prompt_submit.sh` 每轮注入 MCP first + 禁忌段 (≤ 1200 字符 cap)
- AGENT.md §1 升级硬契约 (L1=mcp_simple_search / L2=complex / L3=search.sh / L4=rg)
- cortex-search SKILL 五级 → 四级 (砍 SC 独立, 保留在 search.sh CLI 内部)
- `lib/remote.py` 加 `extract_aliases` (中英对 23 + 缩写 16) + `extract_keywords` (path stem / repo meta / 代码标识符 / heading)
- ingest_git / website + save 落档自动写 aliases/keywords (空 list 不写, 保持 frontmatter 干净)
- save CLI 加 `--aliases` / `--keywords` override flags

### 资产变更

- hook 提示 1 处 (user_prompt_submit.sh) 重写
- AGENT.md §1 升级 + §P9 节
- cortex-search SKILL.md 五级 → 四级
- lib/remote.py 563 → 749 (+186, 加 aliases/keywords 启发式)
- save.py 569 → 617 (+48, 加 override flags)
- 测试基线 497 → 524 (+27)
- 不动 lint 规则 (aliases/keywords 不强制, 仅 hot.md 索引优先选含此字段的页)
- 不实现 hot.md 高分子页维护 (TODO 留下批)

### 文档同步 (PR4)

- docs/快速上手.md 加 §AI 搜索硬契约 + §召回率提升 (四级表 + aliases/keywords schema + CLI override)
- docs/故障排查.md 加 3 节: MCP 不可达 / 召回率低 / qmd MCP 误用
- AGENT.md 末尾加 §P9 简要
- 本 memory §P9 节

## P10 — hot.md 项目高分子页 + migration v3 (2026-05-15)

### hot.md 维护 (PR1)

save.py 落档时若 score ≥ 7.0 + maturity in (stable, review) + kind in (project, domain) → 入 hot.md `## 项目高分页面` 节:
- `### <host/org/repo>` 子段, ≤ 3 / 项目
- 行格式: `- [[wikilink]] (score: <N>, <maturity>)`
- 同 wikilink 重复 → 去重 + 按 score desc 保留 top 3
- 无 `## 项目高分页面` 节自动建

实现: `scripts/cli/save.py` 内 `_HOT_PROJECT_SECTION` / `_HOT_PROJECT_MAX` / `_derive_project_key` / `_extract_score_from_line` / `_patch_hot_project_subpages`, `_save_internal` 末尾按条件调用。

### Migration v3 (PR2)

老 .md 缺 aliases/keywords frontmatter, migrate v3 启发式批量补:
- 复用 `lib/remote.py` `extract_aliases` / `extract_keywords` (PR3 已落)
- 不调 AI (启发式: 中英对 / 缩写 / path / idents / headings)
- 目标: `知识库/项目/`, `知识库/领域/`, `知识库/日记/`, `记忆/L0-L3`
- 跳过: `知识库/收件箱/`, `归档/`, `_meta/`, `_templates/`, `_assets/`, `.obsidian/`, `.trash/`, `记忆/L4-`
- 命令: `bash ~/.cortex/scripts/migrate.sh --to=v3 [--dry-run]`
- backup tar.gz: `/tmp/cortex-migration-backup-v3-<TS>.tar.gz`

`migrate.sh` 现支持 `--to=v2` (scores 字段) + `--to=v3` (aliases/keywords)。

### 资产变更

- `scripts/cli/save.py` +127 行 (`_patch_hot_project_subpages` 等; PR1)
- `scripts/migrate/migrate_aliases_keywords_to_v3.py` 新建 247 行
- `scripts/migrate.sh` 58 → 70 行 (case 分发 v2/v3)
- 测试基线 524 → 548 (PR1 +13 + PR2 +11)
- 真 vault dry-run smoke: 685 scanned / 684 changed / 511 aliases / 684 keywords / 0 errors
- 不动 lint 规则 (aliases/keywords 不强制, 跟 P9 决策一致)
