# PRD: Fill backend spec placeholders with ccplugin conventions

## Problem

`.trellis/spec/backend/` contains 5 files (index, directory-structure, database-guidelines, error-handling, quality-guidelines, logging-guidelines) that are 100% placeholder scaffolds. New tasks and AI sub-agents have no concrete project rules to follow. Specs were never tailored to ccplugin (Python plugins + lib + Tauri desktop + scripts).

## Goal

Replace all placeholder content with ccplugin-specific conventions extracted from actual code. Add new spec files for plugin/Tauri/marketplace/Hooks domains absent from current scaffold.

## Scope

### In-scope

Update existing placeholders:
- `backend/index.md` — accurate Pre-Development Checklist pointing to filled guides
- `backend/directory-structure.md` — actual repo tree (plugins/, lib/, scripts/, desktop/, .claude-plugin/)
- `backend/database-guidelines.md` — `lib.db` ORM usage (Model, Field, async adapters); SQLite default for plugins
- `backend/error-handling.md` — Python exception patterns from plugins; Rust Result wrapping; Tauri command error envelopes
- `backend/quality-guidelines.md` — ruff config, pytest standards, forbidden patterns (top-level side effects, sync I/O in hooks)
- `backend/logging-guidelines.md` — `lib.logging` API (info/debug/warn/error), structured fields, no PII

Create new spec files:
- `backend/plugin-conventions.md` — `plugin.json` schema, directory layout (`.claude-plugin/`, `scripts/`, `tests/`), `pyproject.toml` template, manifest version sync
- `backend/tauri-patterns.md` — `#[tauri::command]` signature, return-immediate + emit pattern (cite `desktop-event-driven-architecture.md` memory), event naming `<domain>-<entity>-<action>`
- `backend/marketplace.md` — `marketplace.json` registration rules, dir-name vs manifest.name alignment, version field sync
- `backend/hooks-contract.md` — Hook event list (SessionStart/PreToolUse/etc), input/output JSON schema, exit codes, timeout budget

### Out-of-scope

- Frontend spec layer (no `.trellis/spec/frontend/` exists yet)
- Modifying any code; this task only writes spec docs
- Adding `guides/` files (separate concern)

## Approach

1. Extract conventions by reading real code: `plugins/memory/`, `plugins/tools/git/`, `lib/`, `desktop/src-tauri/src/commands/`, `scripts/update_version.py`
2. Write each spec with: signature/contract + ≥1 code example from repo + forbidden patterns + common mistakes
3. Cross-link: `backend/index.md` table updated to `Status: filled` and link new files
4. Verify AI comprehension via project quality-check command (CLAUDE.md §代码质量检查规范):
   ```bash
   claude --settings ~/.claude/settings.glm-4.5-flash.json -p "<spec content>" --output-format stream-json | jq -r '...'
   ```

## Acceptance Criteria

- All 6 existing `backend/*.md` files have `Status: filled` (no "To fill" markers, no template-only headers)
- 4 new spec files created and linked from `index.md`
- Each spec contains ≥1 code excerpt from actual ccplugin repo
- Pre-Development Checklist in `index.md` reflects all 10 spec files
- AI quality-check returns non-empty meaningful response for each spec
- No code changes outside `.trellis/spec/`

## Risk / Dependencies

- Depends on accurate read of existing code; if convention drift exists, document actual not aspirational
- Conflicts with: parallel work on plugin restructure (Task 3: marketplace office naming) — coordinate spec for office plugin naming after Task 3 lands

## References

- Deep-study report: `research/deep-study-spec-gap.md` (this task)
- `CLAUDE.md` — project conventions snapshot
- `AGENTS.md` — Agent Teams + structure
- `docs/plugin-development.md` — existing plugin guide
- `.claude/memory/desktop-event-driven-architecture.md` — Tauri rules
