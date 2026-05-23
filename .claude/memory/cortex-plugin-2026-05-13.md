---
name: cortex-plugin
description: Cortex 插件当前真相 — vault 结构 / agent / skill / wrapper / 写契约 / 搜索契约 / 评分字段 / 记忆层
type: project
---

# Cortex 插件 — 单一真相清单

**Why**: 跨多轮重构后, cortex 的 vault 模型 / agent 集合 / 路径布局 / 评分体系已多次反转。本 memo 是当前真相基线; 历史变迁见 git log。

**How to apply**: 改 cortex 时以本清单为准, 旧 memory / docs 与此冲突时本清单优先。

## Vault 模型

- 单一 schema (无 preset 系统)。`_meta/version.json` 仅含 `lang` / `preserve_transcript` / `auto_commit` / `auto_push`
- 顶层: `_meta/ _templates/ _assets/ 知识库/ 记忆/ 仪表盘/ 归档/ locales/ .obsidian/ .trash/` (lint `vault-structure-violation` 强制)
- 知识库 4 子目录: `项目/<host>/<org>/<repo>/` (站点无 author 补 `_site`), `领域/{创作,学习,工作,技术,生活,金融,未分类}/`, `日记/日/<YYYY-MM>/<YYYY-MM-DD>.md`, `收件箱/`
- 记忆 L0-L4: `L0-核心/ L1-长期/ L2-中期/ L3-短期/ L4-流水账/{ledger,sessions}/ working/ views/{consolidated,candidates.md}`
- 项目路径: github/gitlab 走 `host/org/repo` 三段; 本地走相对 `$HOME`, 不足 3 段补 `_local`; website 无 author 补 `_site`
- AI 自决域: `--domain` 可选, 缺时 AI 读 body 自决 6 域, 不匹配默 `领域/未分类/`

## 资产计数 (实测真值)

| 类型 | 计数 | 备注 |
|---|---|---|
| Agents | 6 | curator / researcher / archivist / cartographer / summarizer / translator (PR4 删 linker, 6 含 vs-skill 分工注) |
| Skills | 19 | 多模态理解三件套 cortex-image/video/audio-understand (2026-05-22) + cortex-dataview (Dataview 查询 skill, 2026-05-23); 全部多文件渐进披露, SKILL.md 入口 ≤80 行 |
| Templates | 40 | presets/seed/_templates/ (顶层 6 + html 7 + knowledge 13 + memory 6 + 共有结构 8); _manifest.json sha256, 改后 regen_template_manifest.py 重生成。2026-05-23 全量回灌 vault 落后版本 |
| Quickadd preset | 6 choice | presets/quickadd/data.json (闪念/网页剪藏/写日记/概念/项目/问题); install.sh step_quickadd 自动同步, 备份 data.json.bak.<UTC> |
| Slash commands | 19 | `/cortex:<name>` 冒号 |
| Wrappers | 27 | +image/video/audio_understand.sh (2026-05-22); slash 走 stream-json + rich UI, CLI 直 exec python3, `~/.cortex/scripts/*.sh` |
| Python CLI | 15 | save/search/deep_search/digest/ingest_{url,file,remote}/refresh_projects/memory/ledger/session/html_render/image_gen/image_understand/video_understand/audio_understand; 共享 `cli/_provider_common.py` (多 provider OpenAI 兼容 + multipart helper) |
| Migration scripts | 2 | `migrate_scores_to_v2.py` + `migrate_aliases_keywords_to_v3.py` → `migrate.sh --to=v2\|v3` |
| Lint 规则 | 30 | frontmatter / wikilink / orphan / 命名 / i18n / 评分字段 / .base YAML / path-deprecated 等 |
| Hooks | 5 | SessionStart / PostCompact / Stop / SubagentStop / UserPromptSubmit |
| Cron jobs | 4 | 3 daily (lint 01:00 / dashboard 02:30 / digest 03:00) + 1 weekly (refresh_projects Mon 03:00) |

## Skill/Agent 整改契约 (PR1-4)

- **D9 无参数**: 所有 skill 入口不接受位置参数; 多分支用 `AskUserQuestion`, 不在调用面暴露
- **D10 AUTO_MODE**: wrapper / cron / CI 调 slash 必传 `auto` 后缀 (`/cortex:<name> auto`) → skill 跳 AskUserQuestion 走默认值; 交互会话省略 `auto`
- **D2/D3 渐进披露**: SKILL.md 入口 ≤80 行 (frontmatter + 触发 + 决策树 + AUTO_MODE 分支 + references 指针), 细节迁 `references/<topic>.md` 2-4 子文件按需加载
- **agent 边界**: 6 agent 头部含 "vs <skill>" 分工注释 (archivist vs refactor / cartographer vs dashboard / curator vs lint+doctor / researcher vs ingest / summarizer vs digest / translator 无对应)

## Vault 写硬契约 (session_start hook 注入)

1. **L1 强制 = `mcp__obsidian__*`** (所有 vault 写)
2. **L2 fallback = 官方 `obsidian` CLI**
3. **L3 兜底 = 直接文件 IO** (canvas / 非 md / L1+L2 失败)
4. **MCP 未注册** → AI 先 `AskUserQuestion` 单次授权 (本会话有效, 不写盘)
5. **未授权前**: 硬拒所有 vault 写
6. **例外**: Stop hook / cron / python CLI (非 AI 上下文) 走文件 IO

## 搜索硬契约 (user_prompt_submit hook 每轮注入)

非通用问答前, **第一个工具调用必须是搜索**:

1. **L1** `mcp__obsidian__obsidian_simple_search` (强制 first, **非 qmd**)
2. **L2** `mcp__obsidian__obsidian_complex_search` (JsonLogic tag/path 过滤)
3. **L3 fallback** `bash ~/.cortex/scripts/search.sh --query <q>` (MCP 不可达时)
4. **L4 兜底** ripgrep (search.sh 也失败时)

禁忌: 跳搜直问用户 / qmd 替代 obsidian / Bash rg 替代 MCP search。

## Hook 行为

- **session_start**: header + stats + L0 core + hot.md + behavior contract + triggers + collab + 🔐 Vault 写契约
- **user_prompt_submit**: 每轮注入 🔍 搜索硬契约 (≤1200 字符), 触发词命中加项目 hint
- **stop / postcompact**: jsonl 落 `记忆/L4-流水账/sessions/<cli>/<YYYY>/<MM>/<DD>/<id>.jsonl`

## 评分字段强制 (lint rule 30 `frontmatter-required-scores`)

知识库 .md 强制 4 字段 (全 0.0-10.0 浮点 + maturity enum):
- `score` (质量) / `confidence` (AI 自信度) / `source_credibility` (源可信度, host 白名单) / `maturity` (draft|review|stable|deprecated)

记忆 .md 强制 2 字段: `importance` / `confidence` (0.0-10.0)。

可选 (推荐, 召回率): `aliases` (≥3, 中英对+缩写) / `keywords` (≥5, path/repo/idents/headings)。

启发式 + host 白名单 (24 host): `scripts/cli/lib/remote.py` (`compute_initial_scores` / `compute_memory_scores` / `host_credibility` / `extract_aliases` / `extract_keywords`)。

**digest 双路调** (`evolution.py:update_doc_scores`): 使用信号 → importance↑; 反馈 "不对/错了" → confidence-=1.0, "对的" → confidence+=0.5。

**refresh maturity 重评** (`refresh_projects.py:revalue_maturity`): hash 变 ≥2 且 <30 天 → draft; 变 1 + 旧 stable → review; 不变 ≥180 天 → deprecated 候选; 不变 ≥90 天 → stable。

详见 `skills/cortex-ingest/references/extract.md §3.1` + `skills/cortex-memory/references/scoring.md`。

## hot.md 项目高分子页

`score ≥7.0 + maturity ∈ (stable, review) + kind ∈ (project, domain)` → 入 `hot.md ## 项目高分页面 ### <host/org/repo>` 子段, ≤3/项目, score desc。实现: `save.py:_patch_hot_project_subpages`。

## Ingest 项目级硬契约

详见 `skills/cortex-ingest/SKILL.md` + `references/{layout,extract,safety-filters,global-rules,knowledge-graph,exclude,pipeline}.md`。要点: 4 层目录 (主题/模块/文件/符号-api) + 分级 .md 下限 (15/40/100) + 6 类抽取 + 强制排除 + 知识图谱 4 制品 (`_db.base` Bases YAML, lint rule 30 `base-format-yaml` 强制, **非 markdown/DQL**)。

## 远程 ingest + 批量增量 refresh

- `ingest_remote.sh <url>` — github/gitlab clone 或 website crawl (sitemap → BFS, depth ≤3)
- `refresh_projects.sh [--scope=...]` — 全扫 `知识库/项目/`, 增量 (git diff sha / website hash)
- frontmatter 增量元: `source_url` / `source_type` / `last_ingested_at` / `last_commit_sha` / `content_hash`
- weekly cron Mon 03:00 自动 refresh

## Digest 路由识别

详见 `skills/cortex-digest/SKILL.md` (单文件渐进式披露 815 行, 不再用 references/)。要点: 6 信号 repo 归属 (frontmatter > source_url > wikilink > URL > tag > keyword), 反思/连接/矛盾/决策 4 类命中 repo 落 `项目/<...>/笔记/` 否则 `收件箱/`; **stage 5 双向桥** (5a 项目→领域 / 5b 记忆→KB 晋升 weight≥0.7+recall≥5 / 5c KB→记忆 具化 score≥7+backref≥3 / 5d 双向 backlink + `_meta/bridge.jsonl` 审计); 第 8 阶段 evolution 抽 patterns → proposal → `cortex-refactor evolution-apply` 用户确认 patch。

## 关键约定

- AUTO_MODE persistent (禁询问 ≠ 中止, AI 自决循环修复至 clean)
- Frontmatter `tags` 仅校验字段存在 + 类型 list (无数量下限); `fm-banned-tags` 禁裸结构 (`index/meta/template/_index/stub`) + 裸时间 (`YYYY[-MM[-DD]]/YYYY-Q[1-4]/YYYY-W##`), hierarchical `xxx/yyy` 允许; autofix 派生语义 tag 严禁占位符
- Banned fm fields: `preset` (已废)
- 路径 lang 校验 (rule `path-lang-mismatch`): vault.lang=zh-CN segment 全 ASCII 或 lang=en segment 含 CJK → warn; 豁免 host/org/repo + ASCII 专名 + frontmatter `path_lang_exempt: true`
- cortex-refactor 子操作: `rename` / `merge` / `split` / `evolution-apply` (proposal → AskUserQuestion → patch SKILL/AGENT, safety gate: 白名单 skills/agents/AGENT.md, 黑名单 commands/scripts/_meta/_templates)
- 插件路径硬编码 `$HOME/.claude/plugins/marketplaces/ccplugin-market/plugins/tools/cortex`
- 自研 MCP 已移除, 走官方 `mcp-obsidian`
- Slash wrapper: `-h/--help` + `-i/--interactive` + `--no-commit`; 调 claude 时 echo bash + `--dangerously-skip-permissions`

## 关联 docs

- `plugins/tools/cortex/AGENT.md` §1 搜索硬契约 / §3 vault 写契约权威
- `plugins/tools/cortex/docs/{知识库结构,Agents,Commands,Skills 详解,Bash 脚本,Lint 规则,安装与配置,快速上手,故障排查,周期任务}.md`
- `plugins/tools/cortex/scripts/lint/{rules.json,schemas.py}` — 30 规则定义 + vault 单一 schema
- 历史变迁 (P5-P10 / PR1-4 详细叙事): git log + `.trellis/tasks/archive/2026-05/`
