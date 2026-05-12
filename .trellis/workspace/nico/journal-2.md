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
