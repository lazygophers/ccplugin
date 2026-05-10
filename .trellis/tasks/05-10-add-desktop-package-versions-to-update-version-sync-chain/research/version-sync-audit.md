# Version Sync Audit (extracted from deep-study session 2026-05-10)

## Golden source

`.version` file at repo root. Current content: `0.0.193.110` (4-part: M.m.p.b).

## Current sync chain (update_version.py)

| File | Sync? | Field | Format |
|------|-------|-------|--------|
| .version | source | full | M.m.p.b |
| pyproject.toml (root) | ✅ | version | M.m.p (build stripped) |
| lib/pyproject.toml | ✅ | version | M.m.p |
| plugins/*/pyproject.toml | ✅ | version | M.m.p |
| plugins/*/.claude-plugin/plugin.json | ✅ | version | M.m.p |
| .claude-plugin/marketplace.json | ✅ | metadata.version + plugins[].version | M.m.p |
| **desktop/package.json** | ❌ | version | (currently 0.1.0) |
| **desktop/src-tauri/Cargo.toml** | ❌ | [package].version | (currently 0.1.0) |
| **desktop/src-tauri/tauri.conf.json** | ❌ | version | (currently 0.1.0) |

## Key code refs

- `scripts/update_version.py:60` — `parse_version()` 3-4 part SemVer parser
- `scripts/update_version.py:82` — `format_version()`
- `scripts/update_version.py:156` — `update_plugin_versions()` concurrent
- `scripts/update_version.py:187` — `find_pyproject_paths()`
- `scripts/update_version.py:214` — `_update_single_pyproject()`
- `scripts/update_version.py:253` — `update_pyproject_versions()`
- `scripts/update_version.py:473` — `update_marketplace()`
- `scripts/update_version.py:493` — `update_version_file()`
- `scripts/update_version.py:537` — `load_version()`
- `scripts/update_version.py:553` — `main()` — sync order entry

## Sync order (lines 614-681)

1. `uv lock -U` (skippable via --skip-uv)
2. marketplace.json
3. plugin.json files
4. pyproject.toml files
5. .version (last — written only after all writes succeed)

Rationale: if 1-4 fail, .version still reflects pre-bump state, so re-run is idempotent.

## Insertion point for desktop sync

New `update_desktop_versions(target_version: str, dry_run: bool)` should run between step 2 (marketplace) and step 3 (plugin.json). Concurrent-safe with existing pyproject pool.

## File-format specifics

### desktop/package.json
- Standard JSON, top-level `"version": "0.1.0"`
- Use `safe_save_json` (lib.utils) or `json.dump` with `indent=2`
- npm convention: leading no-`v`, plain semver

### desktop/src-tauri/Cargo.toml
- TOML, `[package]` section, `version = "0.1.0"`
- Use `tomlkit` (already in root pyproject) to preserve formatting/comments
- Pattern matches `_update_single_pyproject` — same library

### desktop/src-tauri/tauri.conf.json
- JSON, top-level `"version": "0.1.0"`
- Tauri 2.x schema: version may also appear in `package.version` (older 1.x); confirm current schema before write

## Validation hook (check.py)

`scripts/check.py:574` — `check_plugin_config()` currently validates plugin.json schema only. Extend to:
- Read `.version` major.minor.patch
- Compare against desktop/package.json, Cargo.toml, tauri.conf.json
- Fail if any drift

## CLI flags (preserve existing)

- `--dry-run` — log writes, no actual file modification
- `--skip-uv` — skip uv lock step (also skip Cargo.lock regeneration if added)

## Risk: Cargo workspace inheritance

Confirm `desktop/src-tauri/Cargo.toml` is NOT a workspace member with `version.workspace = true`. If it is, must update workspace root instead. Current expectation: standalone crate.

## Risk: Tauri version metadata

App runtime reads version from tauri.conf.json typically. Verify after sync that compiled binary reports new version (`tauri info` or app About dialog).
