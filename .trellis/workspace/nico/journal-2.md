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
