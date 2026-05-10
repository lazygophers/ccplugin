# PRD: Add desktop package versions to update_version sync chain

## Problem

`scripts/update_version.py` syncs `.version` (golden source `0.0.193.110`) to: root `pyproject.toml`, `lib/pyproject.toml`, all `plugins/*/pyproject.toml`, all `plugins/*/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`. **Desktop is excluded.** `desktop/package.json` (0.1.0), `desktop/src-tauri/Cargo.toml` (0.1.0), `desktop/src-tauri/tauri.conf.json` (0.1.0) drift permanently. Manual `npm version` or `cargo set-version` orphans desktop versions vs marketplace + plugins.

## Goal

Extend `update_version.py` to write the same canonical version into the 3 desktop files, on the same sync run, with the same dry-run/skip-uv flag semantics as existing targets.

## Scope

### In-scope

- Add `update_desktop_versions()` function in `scripts/update_version.py`
  - Updates `desktop/package.json` `version` field
  - Updates `desktop/src-tauri/Cargo.toml` `[package].version`
  - Updates `desktop/src-tauri/tauri.conf.json` `version`
- Wire into `main()` sync order between marketplace.json and plugin.json (concurrent-safe)
- Honor `--dry-run` flag (log writes, don't touch files)
- 3-part version (M.m.p), strip build segment (matches pyproject convention)
- Update `scripts/check.py` validation to flag desktop version drift

### Out-of-scope

- `package-lock.json` regeneration (separate concern; npm install handles it)
- `Cargo.lock` regeneration (cargo build handles it)
- Desktop-only release flow (no separate desktop versioning policy)
- Modifying `.version` format

## Approach

1. Read current versions from 3 files (parse JSON, parse TOML)
2. Write target version using same idempotent pattern as `_update_single_pyproject`
3. For Cargo.toml use `tomlkit` (already a root dep) to preserve formatting/comments
4. For tauri.conf.json use stdlib `json` with 2-space indent (match Tauri convention)
5. Add to concurrent task pool in `main()`
6. Add cross-check in `check.py`: assert all 3 desktop files match `.version` major.minor.patch

## Acceptance Criteria

- `python3 scripts/update_version.py` updates desktop/package.json + Cargo.toml + tauri.conf.json to 0.0.193 (or next bump)
- `--dry-run` shows planned writes, no file modification
- `scripts/check.py` exits non-zero if any desktop file drifts from .version
- Desktop builds succeed after sync (no Cargo.lock/package-lock conflicts)
- Tauri app version metadata reflects new value at runtime

## Risk

- Tauri.conf.json schema may have nested version paths in some setups; current is top-level — verify before bump
- Cargo workspace inheritance: confirm src-tauri is standalone Cargo crate (not workspace member with `version.workspace = true`)

## References

- Deep-study report: `research/version-sync-audit.md` (this task)
- `scripts/update_version.py:473` — existing `update_marketplace`
- `scripts/update_version.py:553` — `main()` sync order
- `.version` golden source format: M.m.p.b
