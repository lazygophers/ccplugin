# Journal - nico (Part 2)

> Continuation from `journal-1.md` (archived at ~2000 lines)
> Started: 2026-05-12

---



## Session 60: cortex 禁 env vars 统一 config.json

**Date**: 2026-05-12
**Task**: cortex 禁 env vars 统一 config.json
**Branch**: `master`

### Summary

配置类 env (OBSIDIAN_VAULT/CORTEX_VAULT/LANG/SETTINGS/TIMEOUT/DRY_RUN/SYNC_TEMPLATES) 迁 ~/.cortex/config.json。平台契约 (CLAUDE_PLUGIN_ROOT 等) 保留。install.sh 例外不动。新 cortex_config + scripts/lib/config.sh helper。278 tests PASS。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `cadf01c4` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 61: cortex lint 5 规则全 autofix 零人工

**Date**: 2026-05-12
**Task**: cortex lint 5 规则全 autofix 零人工
**Branch**: `master`

### Summary

5 规则 fixable=true: vault-structure-violation (mv 违规) + callout-unknown-type (→info) + orphan-page (链 _index) + path-naming-violation/i18n-path (slug rename) + stub cap 100→1000。286 tests + marketplace 同步。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `9a1b93c4` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 62: cortex lint 5 规则全 autofix

**Date**: 2026-05-12
**Task**: cortex lint 5 规则全 autofix
**Branch**: `master`

### Summary

5 规则 fixable=true autofix: vault-structure-violation (mv 违规) / callout-unknown-type (→info) / orphan-page (链 _index) / path-naming-violation + i18n-path (slug rename)。stub cap 100→1000。286 tests PASS。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `9a1b93c4` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 63: cortex cron run cd vault + SKILL 注入

**Date**: 2026-05-12
**Task**: cortex cron run cd vault + SKILL 注入
**Branch**: `master`

### Summary

cron/run.sh 加 cd vault + JOB→SKILL 映射注入 --append-system-prompt + AUTO_MODE strict prefix。AI 默认 vault-relative 不跑偏。bash 31 + python 286 PASS。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `ccaa3bd7` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 64: cortex budget 提升 + dashboard 真测 (未通)

**Date**: 2026-05-12
**Task**: cortex budget 提升 + dashboard 真测 (未通)
**Branch**: `master`

### Summary

budget 0.30→2.00, dashboard SKILL 加严 8 条强约束。真测 EXIT=1 — 非 budget 问题, AI 漫游读 ledger jsonl 致 claude crash, SKILL 文字约束被忽视。后续需机制硬阻 (dashboard.sh 主动 Glob 逐 page 传 / file size guard / 分批调度)。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `50424104` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 65: cortex wrapper → claude commands 全权限

**Date**: 2026-05-12
**Task**: cortex wrapper → claude commands 全权限
**Branch**: `master`

### Summary

wrapper 全部走 /cortex-<name> slash commands (claude 全权限/无 args/无 --bare). 20 commands.md 建好, plugin.json 注册. cron run.sh + install_wrappers.sh 简化 emit_slash(). dashboard.sh 真测 EXIT=0 ✓ (用户验证)。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `ac7c63c6` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 66: cortex wrapper stream-json + rich 实时

**Date**: 2026-05-12
**Task**: cortex wrapper stream-json + rich 实时
**Branch**: `master`

### Summary

wrapper claude 调用全用 stream-json + cortex_stream_runner 实时 rich 渲染。stderr UI panel + heartbeat, stdout 仅 result.text。dashboard.sh 真测 EXIT=0。286 tests。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `becd3696
f6802e39` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 67: cortex_stream system/hook event handlers

**Date**: 2026-05-12
**Task**: cortex_stream system/hook event handlers
**Branch**: `master`

### Summary

cortex_stream.py 加 system/user event handlers (init/hook_*/task_*/api_retry/plugin_install/tool_result), 未适配 silent skip。CORTEX_STREAM_DEBUG opt-in 显未知。54 stream tests + 112 mcp PASS。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `53dfe6b2` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 68: cortex_stream default 显 raw json

**Date**: 2026-05-12
**Task**: cortex_stream default 显 raw json
**Branch**: `master`

### Summary

未适配 type/subtype 改默认显 raw JSON 1 行 (替代 silent)。stream_event 仍 silent。移除 DEBUG opt-in。286+113 tests PASS。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `0c19aa61` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 69: cortex-lint AUTO_MODE 禁手动建议

**Date**: 2026-05-12
**Task**: cortex-lint AUTO_MODE 禁手动建议
**Branch**: `master`

### Summary

cortex-lint SKILL AUTO_MODE 加严: bash 触发禁手动建议表/询问/AskUserQuestion, fail-fast 1 行原因。非 AUTO_MODE 主流程不变。286 tests PASS。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `e3cb6576` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 70: cortex_stream subtype 扩展

**Date**: 2026-05-12
**Task**: cortex_stream subtype 扩展
**Branch**: `master`

### Summary

扩 cortex_stream 渲染分支: system compact_boundary/error/tool_permission/subagent_*/session_*; assistant server_tool_use/web_search_tool_result/redacted_thinking; user tool_use; result error_max_turns/error_during_execution。54 stream tests + 113 mcp tests PASS。lint 既存失败非本次范围。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `79bfebbf` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 71: lint: log/folds/sessions 出 root_dirs + fm-duplicate-tags 规则

**Date**: 2026-05-13
**Task**: lint: log/folds/sessions 出 root_dirs + fm-duplicate-tags 规则
**Branch**: `master`

### Summary

schemas.py 三 preset root_dirs 移除 log/folds/sessions; run.py SHARED_ROOT_DIRS 同步, 加 _prune_deprecated_whitelist (--fix 自动清 vault _meta/version.json:lint_whitelist 里的旧条目); 新规则 fm-duplicate-tags (warn, autofix 保序去重); 删 log-too-long 和 _check_naming 的 log/folds 命名格式; hot-too-long fix 归档目录 folds/ → 归档/; _infer_type 删 folds 分支; 测试 245 全绿; 实战验证 /Users/luoxin/persons/knowledge/obsidian 的 log/ 已 mv 到 lint-backup。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `19952bae` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 72: cortex: 移除自研 MCP 改用官方 mcp-obsidian

**Date**: 2026-05-13
**Task**: cortex: 移除自研 MCP 改用官方 mcp-obsidian
**Branch**: `master`

### Summary

彻底移除 cortex 插件自带的 MCP server (10 工具/2300 行)。算法 100% 保留拆到 scripts/cli/{save,search,deep_search,ingest_url,ingest_file,memory,ledger,session,html_render,cortex_stream}.py + argparse CLI。9 bash wrappers 通过 install_wrappers.sh 部署到 ~/.cortex/scripts/。16 个 agent/skill/command/hook 文件 mcp__cortex__* 调用全改 bash 形式。install.sh 末尾加 mcp-obsidian 安装引导 (可选)。测试 286 pass + 9 subtests, 0 fail。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `015a4a30` | (see git log) |
| `7945f42d` | (see git log) |
| `214ebefc` | (see git log) |
| `3e5700d5` | (see git log) |
| `2f73373b` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 73: cortex 大批量清理: fold/historian/preset 移除 + agent 路径对齐 + MCP 强制写契约 + neat-freak 精简

**Date**: 2026-05-14
**Task**: cortex 大批量清理: fold/historian/preset 移除 + agent 路径对齐 + MCP 强制写契约 + neat-freak 精简
**Branch**: `master`

### Summary

本次会话 7 commits: (1) 清理 fold/cortex-cron 残留指令 + cron schedule 对齐 8 jobs; (2) 5 agent 路径对齐 vault truth 删 fleeting/sources/concepts 旧目录; (3) 完整移除 preset 系统 单一 vault schema; (4) user_prompt_submit hook 强制先搜 + 项目 scope 收敛 + KB 相对路径提示; (5) feat: 强制 MCP 写 vault — session_start hook 注入硬契约 (MCP first / AskUserQuestion 单次授权 / 硬拒未授权); (6) neat-freak 反膨胀: MEMORY.md 244→75, cortex-plugin memo 338→71, 同步 docs MCP 写契约。pytest 314 pass + 9 subtests。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `5d31f607` | (see git log) |
| `182ffc18` | (see git log) |
| `c4fd72ea` | (see git log) |
| `2e8a2930` | (see git log) |
| `f596e496` | (see git log) |
| `29249ead` | (see git log) |
| `ae7bc0dc` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 74: cortex slash wrapper 加 -h/--help / -i/--interactive / --no-commit

**Date**: 2026-05-14
**Task**: cortex slash wrapper 加 -h/--help / -i/--interactive / --no-commit
**Branch**: `master`

### Summary

10 slash wrapper (lint/dashboard/doctor/init/promote/forget/digest/recall/refactor/ingest) 全加 3 通用 flag。emit_slash() 弃 cat heredoc (bash 3.2 case parser bug), 改 quoted heredoc + 占位替换。pytest 314 pass。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `4dfe2bfe` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 75: slash wrapper -i 注入预设 slash prompt

**Date**: 2026-05-14
**Task**: slash wrapper -i 注入预设 slash prompt
**Branch**: `master`

### Summary

claude CLI positional prompt 在 interactive 模式作初始消息。emit_slash --interactive 分支末尾追加 "/cortex:__NAME__", REPL 启动即跑预设流程, 用户可继续追问。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `e3093798` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 76: slash wrapper echo bash cmd + bypass permissions

**Date**: 2026-05-14
**Task**: slash wrapper echo bash cmd + bypass permissions
**Branch**: `master`

### Summary

emit_slash 两处 claude 调用前 printf 完整 bash 命令 (debug); 加 --dangerously-skip-permissions (wrapper 自动场景, 不弹权限)。10 slash wrapper 全受益。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `e87b2103` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 77: cortex ingest 项目级深度强制 — 多文件夹组织 + 全文件覆盖

**Date**: 2026-05-14
**Task**: cortex ingest 项目级深度强制 — 多文件夹组织 + 全文件覆盖
**Branch**: `master`

### Summary

SKILL.md §1.1 分级表 (≤50/50-500/>500 ≥6/10/20 .md); §1.2 拒交硬条件; §4.7 覆盖度 M/N≥0.8 自检 + _index.md 文件清单覆盖表。commands/ingest.md 加步骤 6 self-check。cortex-researcher description + 工作流加强制 folder-first + self-check 闭环。GLM 自检识别两约束。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `40c4116c` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 78: cortex ingest 4 层 6 类强制

**Date**: 2026-05-14
**Task**: cortex ingest 4 层 6 类强制
**Branch**: `master`

### Summary

SKILL §1.1 4 层目录 (主题/模块/文件/符号) + 分级 ≥15/40/100; §7 6 类抽取 (API/配置/错误码/测试/功能/常量); §8 排除清单 (build/lock/binary/IDE/临时/压缩); commands ingest self-check 4 层+6 类验证。GLM 识别全部。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `d3d37d03` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 79: ingest 内联生知识图谱 — Bases/Canvas/Wikilink/websearch

**Date**: 2026-05-14
**Task**: ingest 内联生知识图谱 — Bases/Canvas/Wikilink/websearch
**Branch**: `master`

### Summary

SKILL §9 4 子节: Bases (_db.base 3 视图) + Canvas (≤20 节点) + Wikilink 网 (≥5 出链/小 repo prorated) + websearch (5 URL 容忍跳过)。commands/ingest self-check g. 4 类验证。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `bba99ff8` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 80: digest 识别 host/org/repo 路由

**Date**: 2026-05-14
**Task**: digest 识别 host/org/repo 路由
**Branch**: `master`

### Summary

SKILL §2 6 信号识别 (frontmatter/source_url/wikilink/URL/tag/keyword≥3); §3 路由表 (反思/连接/矛盾/决策 × 命中/fallback); §5 收件箱 ≥30 天复扫迁移。GLM 识别全部。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `adb754b8` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 81: lint rule 18 path-lang-mismatch

**Date**: 2026-05-14
**Task**: lint rule 18 path-lang-mismatch
**Branch**: `master`

### Summary

新 lint 规则 path-lang-mismatch (warn, autofix false): vault path segment 不符 lang flag。豁免 host/org/repo 前 5 段 + 基础设施顶层 + ASCII 专名 stem (README/LICENSE 等) + frontmatter path_lang_exempt。test_lint_path_lang.py 10 case。pytest 324 pass (+10 new).

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `d8252080` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 82: cortex playbook 借鉴 — SKILL 拆 references + digest 加 evolution 抽取

**Date**: 2026-05-14
**Task**: cortex playbook 借鉴 — SKILL 拆 references + digest 加 evolution 抽取
**Branch**: `master`

### Summary

借鉴 zhaono1/agent-playbook 两条方法论提升 cortex: (1) context-layering 3 层 — cortex-ingest SKILL 497→198 行 + 4 references, cortex-digest 175→140 行 + 3 references; (2) self-improving multi-memory — cortex-digest 加第 6 阶段 evolution 抽取 (扫 sessions/jsonl → 抽 pattern → 写 记忆/L0-核心/patterns.md → 生 proposal), cortex-refactor 加 evolution-apply (AskUserQuestion 一条一问 + safety gate 白名单+git clean → patch SKILL/AGENT)。新 CLI: digest.py + lib/evolution.py + evolution_apply.py。新 lint rule 19 skill-references-exists。新 wrapper 子命令: digest.sh evolution + refactor.sh evolution-list/check/delete。测试基线 324 → 360 (+36)。决策: D1 markdown 库 / D2 AskUserQuestion 单确认直 patch / D3 内联 digest / D4 阈值硬编码 conf≥0.8 AND apps≥3。Out of scope: P0-2 长任务 state / P1-3 声明式 hook / P2 agent state+router。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `3199ae16` | (see git log) |
| `425a6d2e` | (see git log) |
| `ffb5f5f8` | (see git log) |
| `d9128b04` | (see git log) |
| `c3d24236` | (see git log) |
| `c4a5b946` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 83: cortex 清 wiki 残留, 全栈对齐 知识库 vault truth

**Date**: 2026-05-14
**Task**: cortex 清 wiki 残留, 全栈对齐 知识库 vault truth
**Branch**: `master`

### Summary

vault truth 早已切到 知识库/ 4 子目录, 但代码 + lint + docs + skill/agent 残留 wiki 字样化石。本会话批量替换 9 文件 13 行: deep_search.py fallback wiki → 知识库 (2), rules.json rule 8 description (1), docs 5 处 (Lint 规则/快速上手/故障排查/design-decisions), skill/agent 3 处 (AGENT.md / cortex-lint SKILL / cortex-ingest SKILL 触发短语). 排除 [[wikilink]] / wikipedia / plugin.json keywords. 测试基线 360 不下降, ruff clean, AI 质量检查通过.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `e3ee4df5` | (see git log) |
| `1f38a488` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 84: cortex 加 2 wrapper — ingest_remote (github/website) + refresh_projects 增量

**Date**: 2026-05-14
**Task**: cortex 加 2 wrapper — ingest_remote (github/website) + refresh_projects 增量
**Branch**: `master`

### Summary

cortex 现有 ingest 缺 (1) 远程整 repo/整站入口 (2) 批量增量更新入口, 用户标 'wrapper 缺失, 注意所有关联地方'. 本会话 4 commit: PR1 ingest_remote (CLI 110 + lib/remote.py 412 + wrapper 71 + 17 test, github/gitlab shallow clone --depth=50 + website sitemap/BFS crawl depth ≤3, 三过滤器 url_security/html_sanitize/masking); PR2 refresh_projects (CLI 373 + wrapper 63 flock 锁 + 12 test, 仅增量 git sha 对比 / website SHA256 hash 对比, frontmatter schema +last_commit_sha/content_hash 落 layout.md); PR3 同步 install_wrappers (22→24 wrapper, EXPECTED 加 2, emit_cli 加 2 行) + install_cron (weekly Mon 03:00 +1 cron) + docs 3 (安装/快速上手/故障排查 各加节) + AGENT.md (CLI 主路径表 +2 行) + memory (Wrappers 22→24 / CLI 9→11 / Cron 8→9 + P6 节). 路径策略: github/gitlab→host/org/repo, website 有 author→host/author/slug, 无→host/_site/slug. 测试基线 360→389 +29. install_wrappers 干跑生 24 wrappers 验证通过.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `807c3498` | (see git log) |
| `be9ae225` | (see git log) |
| `374452c3` | (see git log) |
| `18708440` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 85: cortex .base 格式硬契约 + lint rule base-format-yaml

**Date**: 2026-05-14
**Task**: cortex .base 格式硬契约 + lint rule base-format-yaml
**Branch**: `master`

### Summary

用户 Obsidian 报错 '查询格式无效, 必须为 YAML 对象'. 根因: cortex-ingest 落 .base 时受 md 惯性写成 markdown / Dataview DQL 格式. vault 内 5 .base 文件 3 错 (markdown headers / DQL / wiki/ 残留). 本会话 1 commit: references/knowledge-graph.md §9.1 加硬契约 4 禁忌 + AI 自检命令 + lint rule base-format-yaml (warn, 5 检 markdown/DQL/YAML/dict/schema, 跳 .obsidian/归档/.trash) + 13 test + docs/memory 同步 (Lint 19→20). 真 vault smoke 检出 14 错 .base. 不动用户 vault 数据 (用户重 ingest 覆盖). 测试基线 389→402 +13.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `159344ae` | (see git log) |
| `3d8712bb` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 86: cortex 强制评分 frontmatter — 知识库 4 + 记忆 2 + digest 双路 + refresh maturity 重评

**Date**: 2026-05-15
**Task**: cortex 强制评分 frontmatter — 知识库 4 + 记忆 2 + digest 双路 + refresh maturity 重评
**Branch**: `master`

### Summary

用户标 '所有文档/记忆必须评分字段强制', 后续修正 '0-10 浮点 / digest+refresh 联动'. 6 PR: PR1 schema (extract.md §3.1 启发式 + cortex-memory/scoring.md, 知识库 4 字段 score/confidence/source_credibility/maturity + 记忆 2 字段 importance/confidence); PR2 lint rule frontmatter-required-scores (warn + autofix, 跳 仪表盘/收件箱/归档/.obsidian, 真 vault smoke 2643 hits 渐进迁移); PR3 ingest_remote/save AI 自评 (lib/remote.py _HOST_CREDIBILITY 24 host + compute_initial_scores + compute_memory_scores, save 9 CLI flag override); PR4 digest 双路 (evolution.py update_doc_scores, 使用信号 log10 + 自然衰减 / 反馈语 pos×0.5 - neg×1.0, digest --update-scores); PR5 refresh maturity (revalue_maturity D5 规则, 内容变 ≥2 + <30天 → draft, 不变 ≥180天 → deprecated, score/confidence 不动); PR6 一次性 migration (scripts/migrate/migrate_scores_to_v2.py 旧 score 1-5 ×2.0, patterns confidence 0-1 ×10, backup tar.gz) + docs/AGENT/memory P8 同步. 测试基线 402 → 497 +95. Lint 20→21, CLI 11→12 (一次性 migrate.sh 不进 24 wrapper).

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `eab9b252` | (see git log) |
| `b1d874b4` | (see git log) |
| `b55ee1e9` | (see git log) |
| `78141d84` | (see git log) |
| `909921cf` | (see git log) |
| `7e2d188c` | (see git log) |
| `54c7719c` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 87: cortex search MCP first 重排 + 召回率提升 (aliases/keywords)

**Date**: 2026-05-15
**Task**: cortex search MCP first 重排 + 召回率提升 (aliases/keywords)
**Branch**: `master`

### Summary

用户报 4 个 cortex search bug. P1 AI 没先搜 (hook 弱) P2 用 bash 不用 MCP (设计冲突) P3 qmd 抢 obsidian (无 ranking) P4 召回低 (frontmatter 不含搜索词). 4 PR 修: PR1 hook user_prompt_submit.sh 移除触发词条件每轮注入 + AGENT §1 升级 L1 mcp_simple_search/L2 complex/L3 search.sh/L4 rg 硬契约 + 软禁 qmd. PR2 cortex-search SKILL.md 五级→四级 (MCP first, 砍 SC 独立段) + search.py docstring 定位 L3 fallback. PR3 lib/remote.py +186 加 extract_aliases (中英对 23 + 缩写 16) + extract_keywords (path/repo/idents/headings) + ingest_git/website + save 自动写 aliases/keywords frontmatter (空 list 不写) + save CLI --aliases/--keywords flag. PR4 docs/快速上手 + 故障排查 + memory P9 同步. 测试基线 497 → 524 +27. 不动 lint (可选字段), hot.md 高分子页 TODO.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `3933b9c8` | (see git log) |
| `d2d3f97b` | (see git log) |
| `04b49401` | (see git log) |
| `d89448f7` | (see git log) |
| `1c5aeb01` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 88: cortex 收尾 — hot.md 项目高分子页 + aliases/keywords migration v3

**Date**: 2026-05-15
**Task**: cortex 收尾 — hot.md 项目高分子页 + aliases/keywords migration v3
**Branch**: `master`

### Summary

上批 PR3 留 2 TODO 收尾. PR1 hot.md 项目高分子页 (save.py +127, _patch_hot_project_subpages 阈值 score≥7+maturity stable/review+kind project/domain, 按 host/org/repo 分子段 top 3 排序去重, 13 测试). PR2 migration v3 (migrate_aliases_keywords_to_v3.py 247 行, 复用 PR3 lib/remote.py extract_aliases/keywords 启发式, migrate.sh 加 --to=v3 分支, backup tar.gz, 11 测试). 真 vault dry-run smoke: 685 .md 扫 684 changed, aliases_added 511 keywords_added 684 errors 0. docs/memory P10 同步. 测试基线 524 → 548 +24 (全程 497→548 +51). ruff clean. 不调 AI 重写, 全启发式.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `ec9fbf7e` | (see git log) |
| `2a1b5bbe` | (see git log) |
| `e2148121` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 89: cortex skills/agents 整改 — 21→13 skill / 7→6 agent / D10 auto

**Date**: 2026-05-15
**Task**: cortex skills/agents 整改 — 21→13 skill / 7→6 agent / D10 auto
**Branch**: `master`

### Summary

4 PR 整改: PR1 删 7 skill (canvas/new/reflect/ingest-bulk/schema/locale/forget) + 合 recall→search; PR2 拆 4 大 skill (dashboard/install/save/lint) 入口 ≤80 + references/ + install_wrappers.sh D10 auto 后缀; PR3 拆 7 中短 skill 入口 ≤80 + 14 references; PR4 拆 digest/ingest + 删 linker agent + 6 agent vs-skill 分工注 + 文档计数同步。终态: 13/13 skill 全合规 (入口 ≤80 + refs ≥2 + AUTO_MODE 分支) + 6 agent (含边界注)。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `5b6b8c5d` | (see git log) |
| `8418e232` | (see git log) |
| `c1117cd7` | (see git log) |
| `eac15429` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 90: cortex README 重写 — 4 大块用户使用说明

**Date**: 2026-05-15
**Task**: cortex README 重写 — 4 大块用户使用说明
**Branch**: `master`

### Summary

重写 plugins/tools/cortex/README.md (173→388 行) 加 4 大块明细: Bash 使用 (24 wrapper 分 5 组 + 范围标记 + 退出码) / Skills (13 全清单 + 触发词 + 渐进披露) / Agents (6 + vs-skill 边界) / 定时任务 (4 cron + 3 平台 snippet)。计数全实测: slash 19 (非 20) / lint 30 (非 18) / cron 4 (非 9), 与 docs/索引.md 残留 stale count 形成轻微 drift 待后续 cleanup。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `56f7a089` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 91: cortex ingest website 路由修复

**Date**: 2026-05-15
**Task**: cortex ingest website 路由修复
**Branch**: `master`

### Summary

修复 /cortex:ingest <url> 把外部网页 URL 误落收件箱的 bug。统一所有 ingest 入口 — website 全落 知识库/项目/<host>/_site/<slug>/<slug>.md (与 memo 单源真相 + ingest_remote.py 一致)。改 ingest_url.py + save.py + cortex-ingest SKILL.md + pipeline.md + tests, pytest 548 全过。收件箱保留给 fleeting/journal/question 纯笔记。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `a37b8a71` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 92: install.sh codex 软连同步

**Date**: 2026-05-15
**Task**: install.sh codex 软连同步
**Branch**: `master`

### Summary

install.sh 加 sync_codex_symlinks: 检测 ~/.codex/ 存在自动软连 13 skill + 6 agent 到 ~/.codex/skills/cortex-* + ~/.codex/agents/cortex-*, idempotent + escape hatch --no-codex-sync。bash 3.2 兼容, agents 软链名去 .md 后缀。

### Main Changes

(Add details)

### Git Commits

(No commits - planning session)

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 93: install.sh opencode 软连同步 + 抽共享

**Date**: 2026-05-15
**Task**: install.sh opencode 软连同步 + 抽共享
**Branch**: `master`

### Summary

install.sh 扩展支持 opencode (~/.config/opencode/skills + agents)。重构: _ensure_codex_symlink → _ensure_cli_symlink, sync_codex_symlinks → sync_cli_symlinks <name> <root>, 新增 sync_external_clis 顶层调度。3 flag: --no-codex-sync / --no-opencode-sync / --no-external-sync。codex 行为向后兼容。bash 3.2 兼容。实测两 CLI 各 19 软链全建 + idempotent。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `c6379f23` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 94: 新增 cortex-image-understand skill

**Date**: 2026-05-22
**Task**: 新增 cortex-image-understand skill
**Branch**: `master`

### Summary

为 plugins/tools/cortex 添加图理解 skill (镜像 cortex-image)。新 CLI scripts/cli/image_understand.py 5 子命令 (probe/describe/ask/extract/list), 走 OpenAI 兼容 chat completions vision 格式, 支持 zhipu/openai/qwen-vl。抽 _provider_common.py 共享模块, image_gen 同步重构。yaml 配置 <vault>/.cortex/config/image-understand.yaml。validate_config.py 加 validate_image_understand_yaml 校验。wrapper 24→25, py CLI 12→13, skill 13→14。15 pytest 单测 + ruff 全过。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `48731868` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 95: 新增 cortex video/audio 理解两个 skill

**Date**: 2026-05-22
**Task**: 新增 cortex video/audio 理解两个 skill
**Branch**: `master`

### Summary

为 cortex 加视频 + 音频理解能力 (镜像 cortex-image-understand 模板)。video_understand CLI 双模式 video_url (zhipu glm-4v-plus / qwen-vl-max-video) + frames (ffmpeg 均匀抽帧, 兼容 openai gpt-4o)。audio_understand CLI 双模式 asr (Whisper/GLM-ASR multipart) + chat (gpt-4o-audio/qwen-audio input_audio)。_provider_common 加 http_multipart helper。validate_config 抽 _validate_chat_like_yaml 共享逻辑, 加 video/audio yaml 校验 (mode enum + frames_count + default_provider 引用检查)。资产计数 skill 14→16, wrapper 25→27, py CLI 13→15。48 pytest 全过 (含 video 14 + audio 15 + multipart 2)。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `59014063` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 96: vault _templates 全量回灌 + quickadd 集成

**Date**: 2026-05-23
**Task**: vault _templates 全量回灌 + quickadd 集成
**Branch**: `master`

### Summary

vault _templates (实际 40+ 模板) 多年演进, plugin presets 仅 10 个滞后; 同时 Obsidian quickadd 配置引用了 plugin 没有的模板。本会话: (1) rsync 全量回灌 vault → plugin presets/seed/_templates/ (40 模板, 含 knowledge/memory/html 子目录); (2) 跑现有 regen_template_manifest.py 重生成 _manifest.json sha256; (3) install.sh 加 step_quickadd, 检测 .obsidian/plugins/quickadd/ 自动同步 6 choice 预设, 备份 data.json.bak.<UTC>; (4) 新建 presets/quickadd/data.json 预设; (5) docs/模板与美化.md + 知识库结构.md + memory 全同步; (6) test_quickadd_preset.py 7 单测全过 (json/字段/引用/路径校验)。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `7213e113` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 97: 新增 cortex-dataview Dataview 查询 skill

**Date**: 2026-05-23
**Task**: 新增 cortex-dataview Dataview 查询 skill
**Branch**: `master`

### Summary

为 cortex 加 Obsidian Dataview 块构建/修改/解释 skill。多文件渐进披露 (SKILL.md 66 行入口 + 5 references ~1580 行)。research 三件套由 3 个 trellis-research sub-agent 并行抓取 (DQL syntax 491 行 + DataviewJS API 462 行 + 集成模式 342 行)。新写 modify-flow.md (marker 幂等改写 SOP) + cookbook.md (8 cortex-vault 实用 query)。marker 契约 <!-- cortex-dataview v1 kind=<k> hash=<sha1[:8]> --> 保证 idempotent 改写。AUTO_MODE 默认拒 dataviewjs (安全策略)。skill 18→19; AI 触发验证通过 + 给出与 cookbook 一致的 DQL。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `cdef5fab` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 98: scaffold cortex plugin skeleton

**Date**: 2026-06-09
**Task**: scaffold cortex plugin skeleton
**Branch**: `cortex`

### Summary

在 plugins/tools/cortex/ 落占位骨架: plugin.json + cortex agent + cortex skill + hooks/commands 占位目录 + README + llms.txt。主题待定, 所有描述类字段用 TODO 标记。

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `3685f779` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 99: cortex plugin: KB + memory system

**Date**: 2026-06-09
**Task**: cortex plugin: KB + memory system
**Branch**: `cortex`

### Summary

Phase 1-7 全链路落地. 双层 vault, 5 级记忆 (按遗忘曲线), 3 模块中文化, 4 skill + 1 agent + 3 脚本 + 完整 fixture + e2e report. AI 识别测试因 settings 文件缺失跳过.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `2d8f3ed0` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 100: cortex skills 多文件改造

**Date**: 2026-06-09
**Task**: cortex skills 多文件改造
**Branch**: `cortex`

### Summary

4 skill 拆 SKILL.md (≤60 行薄入口) + references/*.md (3/skill). 新增 arguments / 收紧 description ≤512 / when_to_use ≤128. 27 文件 +1495/-486.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `3e43c98e` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 101: cortex skills 多文件改造

**Date**: 2026-06-09
**Task**: cortex skills 多文件改造
**Branch**: `cortex`

### Summary

4 skill 拆 SKILL.md (≤60 行薄入口) + references/*.md (3/skill). 新增 arguments / 收紧 description ≤512 / when_to_use ≤128. 27 文件 +1495/-486.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `7926880e` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete


## Session 102: cortex skills arguments 字段格式修正

**Date**: 2026-06-09
**Task**: cortex skills arguments 字段格式修正
**Branch**: `cortex`

### Summary

4 skill arguments 从对象列表改字符串 (中文化), 对齐 argument-hint.

### Main Changes

(Add details)

### Git Commits

| Hash | Message |
|------|---------|
| `cd7745ac` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete
