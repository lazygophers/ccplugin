# PRD: Unify office plugin naming across dirs and manifests

## Problem

`marketplace.json` registers office plugins by source path (`./plugins/office/docx`, etc) but each `plugin.json` declares `name: "office-docx"`. Scanner that compares directory name vs manifest.name flags 4 office plugins as ghosts/orphans. Same root-cause for `llms` (manifest=`plugin-llms`), `template` (manifest=`plugin-template`).

## Goal

Eliminate name mismatch so directory name ≡ manifest.name. Pick one canonical convention and apply repo-wide.

## Scope

### Decision Required (resolved during brainstorm)

**Option A**: Rename directories to match manifest
- `plugins/office/docx` → `plugins/office/office-docx`
- `plugins/office/pdf` → `plugins/office/office-pdf`
- etc.
- `plugins/llms` → `plugins/plugin-llms`
- `plugins/template` → `plugins/plugin-template`

**Option B**: Strip prefix from manifest.name
- All `office-*` manifests → bare names (`docx`, `pdf`, etc.)
- `plugin-llms` → `llms`
- `plugin-template` → `template`

**Recommendation**: Option B. Less file movement. Marketplace.json paths unchanged. CLI commands (e.g., `claude plugin install xlsx`) match user intuition.

### In-scope

Apply chosen option to:
- `plugins/office/{docx,pdf,pptx,xlsx}/.claude-plugin/plugin.json` — name field
- `plugins/llms/.claude-plugin/plugin.json` — name field
- `plugins/template/.claude-plugin/plugin.json` — name field
- `.claude-plugin/marketplace.json` — name field per entry (must match)
- `scripts/check.py` — add invariant: dir name == manifest.name == marketplace entry name

### Out-of-scope

- Renaming pyproject.toml package names (pyproject is independent of plugin manifest name)
- Updating documentation references (separate doc task)
- Renaming actual plugin functionality

## Approach

1. Pick option (default B unless user override)
2. Edit all affected JSON files via `Edit` tool (preserve formatting)
3. Run `scripts/check.py` to confirm 0 ghosts / 0 orphans
4. Test install flow: `claude plugin install xlsx` end-to-end
5. Add invariant check in `check.py` to prevent regression

## Acceptance Criteria

- `scripts/check.py` reports 0 ghosts, 0 orphans, 0 name drift
- Every `plugins/<cat>/<dir>/` has `plugin.json` with `name == basename(dir)`
- Every `marketplace.json` entry: `name == basename(source path) == manifest.name`
- `claude plugin install <name>` works for all 35 plugins
- New invariant in `check.py` fails on intentional drift (test by mutating one file)

## Risk

- Public-facing plugin name change breaks user installs; document migration in CHANGELOG
- Hidden references in docs/skills mentioning old names

## References

- Deep-study report: `research/marketplace-naming-audit.md` (this task)
- `.claude-plugin/marketplace.json`
- `scripts/check.py:574` — current `check_plugin_config`
