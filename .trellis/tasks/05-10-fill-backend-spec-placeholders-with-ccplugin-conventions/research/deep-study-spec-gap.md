# Spec Gap Audit (extracted from deep-study session 2026-05-10)

## Current state

`.trellis/spec/backend/` files: all placeholder. Word counts ~20-80 per file. No project-specific content.

| File | Status | Words | Content |
|------|--------|-------|---------|
| backend/index.md | Placeholder | ~80 | Header + "to fill" checklist |
| backend/directory-structure.md | Empty | ~20 | Template only |
| backend/database-guidelines.md | Empty | ~20 | Template only |
| backend/error-handling.md | Empty | ~20 | Template only |
| backend/quality-guidelines.md | Empty | ~20 | Template only |
| backend/logging-guidelines.md | Empty | ~20 | Template only |
| guides/index.md | Partial | ~180 | 2 guide headers + triggers |
| guides/code-reuse-thinking-guide.md | Partial | ~250+ | 6/8 sections; ends mid-checklist |
| guides/cross-layer-thinking-guide.md | Filled | ~200 | Generic; lacks Desktop Rust↔TS, Plugin lib boundaries |

## Gap matrix vs ccplugin reality

| Topic | Needed | Spec has | Severity |
|-------|--------|----------|----------|
| plugin.json schema | Yes | None | Critical |
| plugins/<cat>/<name>/ layout | Yes | None | Critical |
| Tauri command patterns | Yes | None | Critical |
| Python uv workspace conventions | Yes | None | Critical |
| lib/ exportable surface | Yes | None | High |
| marketplace.json registration rules | Yes | None | High |
| Hooks contract (lifecycle, return shape) | Yes | None | High |
| Desktop layer boundaries (Rust↔TS) | Yes | None | High |
| MCP server structure | Yes | None | Medium |
| Scripts CLI anatomy | Yes | None | Medium |
| Plugin testing (pytest fixtures) | Yes | None | Medium |
| Forbidden Python patterns | Yes | None | Medium |
| Logging guidance (PII, levels) | Yes | None | Low |

## Convention sources (where to extract from)

For each spec file, read these to learn actual conventions:

### directory-structure.md
- `pyproject.toml` (root workspace)
- `lib/pyproject.toml`
- `plugins/memory/pyproject.toml` (most complex plugin)
- `AGENTS.md` §structure
- `.claude-plugin/marketplace.json` (registry layout)

### database-guidelines.md
- `lib/db/core.py` (DatabaseConfig, DatabaseConnection)
- `lib/db/models.py` (Model + 13 Field types)
- `lib/db/adapters/{sqlite,mysql,postgresql}.py`
- `plugins/memory/scripts/memory/models.py` (real Model usage)

### error-handling.md
- Plugins: `plugins/memory/scripts/main.py`, `plugins/tools/git/scripts/main.py`
- Desktop Rust: `desktop/src-tauri/src/commands/python.rs` (Result wrapping)
- Tauri command error envelope pattern

### quality-guidelines.md
- `pyproject.toml` ruff config
- Existing tests `lib/tests/`, `plugins/memory/tests/`
- Forbidden: top-level side effects, blocking I/O in async hooks, sync subprocess in Tauri commands

### logging-guidelines.md
- `lib/logging/` API (info/debug/warn/error)
- Plugin logging usage (45+ scripts use `from lib.logging import info`)
- File rotation (hourly, 3h auto-cleanup)

### plugin-conventions.md (NEW)
- `plugins/template/.claude-plugin/plugin.json` reference template
- `plugins/memory/.claude-plugin/plugin.json` complex example with hooks
- `docs/plugin-development.md`

### tauri-patterns.md (NEW)
- `.claude/memory/desktop-event-driven-architecture.md` (cite directly)
- `desktop/src-tauri/src/commands/python.rs:5-65` (compliant pattern)
- `desktop/src-tauri/src/services/task_queue.rs` (background spawn)
- Event naming `<domain>-<entity>-<action>` rule

### marketplace.md (NEW)
- `.claude-plugin/marketplace.json`
- `scripts/check.py` validation rules
- Office naming inconsistency case study

### hooks-contract.md (NEW)
- `.claude/hooks/{session-start,inject-workflow-state,inject-subagent-context}.py`
- `plugins/memory/scripts/hooks.py` (12 hook handlers)
- Input schema: stdin JSON; output: stdout JSON
- Exit codes: 0 success, non-zero halts

## Recommended file template (for each spec)

```markdown
# <Topic> Conventions

## Scope
What this covers, who reads.

## Rules
- Rule 1 (concrete)
- Rule 2 ...

## Code Example
\`\`\`<lang>
// from <file>:<line>
\`\`\`

## Forbidden Patterns
\`\`\`<lang>
// don't do this
\`\`\`

Why bad: ...

## Common Mistakes
- Mistake -> Fix

## References
- file:line
- file:line
```

## Cross-reference: existing project memory

`.claude/memory/desktop-event-driven-architecture.md` already documents Desktop Tauri rules — should be CITED in `tauri-patterns.md`, not duplicated. Spec layer = canonical; memory = session learnings that may be promoted.

`.claude/memory/desktop-code-quality-2026-04-05.md` documents reuse audit findings — relevant to `quality-guidelines.md` (extract reusable principles).
