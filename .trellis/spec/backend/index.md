# Backend Development Guidelines

> Project-specific conventions for the **ccplugin** backend (Python plugins, `lib/` shared library, Tauri desktop, root `scripts/`).

---

## Overview

ccplugin is a monorepo Claude Code plugin marketplace:

- `plugins/<category>/<name>/` — plugins (Python + manifests)
- `lib/` — shared Python library (`lib.db`, `lib.logging`, `lib.hooks`, `lib.utils`)
- `scripts/` — root CLI commands (the only thing the root package publishes)
- `desktop/` — Tauri desktop app (Rust backend + React frontend)
- `.claude-plugin/marketplace.json` — marketplace registry
- `.claude/hooks/` — repo-level Claude Code hooks (Trellis injection, etc.)

These specs encode the **actual** conventions in this repo. Document reality, not aspiration.

---

## Pre-Development Checklist

Before writing any backend code, confirm you have read the relevant guides:

| When you are about to...                       | Read                                                                            |
| ---------------------------------------------- | ------------------------------------------------------------------------------- |
| Create or modify a plugin                      | [plugin-conventions](./plugin-conventions.md) + [marketplace](./marketplace.md) |
| Add a `#[tauri::command]` or emit/listen event | [tauri-patterns](./tauri-patterns.md)                                           |
| Persist data in a plugin                       | [database-guidelines](./database-guidelines.md)                                 |
| Raise/catch/return errors (Python or Rust)     | [error-handling](./error-handling.md)                                           |
| Add log lines                                  | [logging-guidelines](./logging-guidelines.md)                                   |
| Implement a Claude Code hook handler           | [hooks-contract](./hooks-contract.md)                                           |
| Place new files                                | [directory-structure](./directory-structure.md)                                 |
| Submit code for review                         | [quality-guidelines](./quality-guidelines.md)                                   |

---

## Guidelines Index

| Guide                                           | Description                                          | Status |
| ----------------------------------------------- | ---------------------------------------------------- | ------ |
| [Directory Structure](./directory-structure.md) | Repo tree, where each kind of code lives             | Filled |
| [Plugin Conventions](./plugin-conventions.md)   | `plugin.json` schema, plugin layout, version sync    | Filled |
| [Marketplace](./marketplace.md)                 | `marketplace.json` registration rules and invariants | Filled |
| [Tauri Patterns](./tauri-patterns.md)           | `#[tauri::command]` + event-driven architecture      | Filled |
| [Hooks Contract](./hooks-contract.md)           | Claude Code hook events, I/O JSON schema, exit codes | Filled |
| [Database Guidelines](./database-guidelines.md) | `lib.db` ORM (Model / Field / async adapters)        | Filled |
| [Error Handling](./error-handling.md)           | Python exceptions + Rust `Result` + Tauri envelopes  | Filled |
| [Quality Guidelines](./quality-guidelines.md)   | ruff, pytest, forbidden patterns, review checklist   | Filled |
| [Logging Guidelines](./logging-guidelines.md)   | `lib.logging` API, levels, structured fields, no PII | Filled |

> See also: `.trellis/spec/guides/` for thinking guides (cross-layer, code reuse).

---

## Conventions Summary

- **Python**: 3.11+, managed by `uv`. Root package only publishes `scripts/`; `lib/` and `plugins/*` are excluded from the wheel.
- **Plugins**: each plugin is a self-contained directory with its own `pyproject.toml`, `.claude-plugin/plugin.json`, and optional `scripts/` + `tests/`.
- **Shared library**: `lib` is consumed via `[tool.uv.sources.lib]` (path locally, git rev for plugins).
- **Desktop**: Rust owns business logic; TypeScript renders UI; communication is event-driven (`<domain>-<entity>-<action>`).
- **Versioning**: root `pyproject.toml`, every `plugin.json`, `lib/pyproject.toml`, and `marketplace.json` MUST share the same version. Run `uv run scripts/update_version.py` to sync.
- **Logging**: use `from lib import logging; logging.info(...)`. Never `print` in long-running code.
- **Documentation language**: spec files are written in English; in-repo guides may be bilingual (zh/en).

---

## How to Update These Guidelines

1. Find the actual convention in code (cite `file:line`).
2. Edit the relevant spec file; keep it ≥ 80 lines and ≤ 400 lines.
3. Each spec must contain: scope, rules, ≥ 1 real code excerpt, forbidden patterns, common mistakes.
4. Run the project quality-check (CLAUDE.md §代码质量检查规范) on the new content:
   ```bash
   claude --settings ~/.claude/settings.glm-4.7-flash.json -p "<spec content>" \
     --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'
   ```
5. Cross-link from `index.md` if you add a new file.

---

**Language**: All spec documentation is written in **English**.
