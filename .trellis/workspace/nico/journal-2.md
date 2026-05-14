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
