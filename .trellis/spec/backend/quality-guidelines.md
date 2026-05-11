# Quality Guidelines

> Code quality standards for ccplugin backend (Python plugins, `lib/`, `scripts/`, Rust desktop).

---

## Scope

What every PR must satisfy before review: tooling, testing, banned patterns, and the reviewer checklist.

---

## Tooling

- **Python toolchain**: `uv` only. Do not run `pip`, `pip-tools`, or `poetry` directly. Common commands:
  ```bash
  uv sync                                  # install per uv.lock
  uv run ruff check .                      # lint
  uv run ruff format .                     # format
  uv run pytest lib/tests                  # lib tests
  uv run --directory plugins/<name> pytest # per-plugin tests
  ```
- **Linter / formatter**: `ruff`. The repo has no project-level `[tool.ruff]` block as of this writing — defaults apply. If a future config is added, it lives in the root `pyproject.toml` (single source of truth; do not duplicate in plugins).
- **Python version**: `requires-python = ">=3.11"` (`pyproject.toml:6`); `.python-version` pins `3.11` for `uv`.
- **Rust**: `cargo fmt` + `cargo clippy --all-targets -- -D warnings` for `desktop/src-tauri`.
- **Frontend** (`desktop/src/`): see frontend specs (out of scope for backend).

---

## Testing Standards

- **Async tests**: use `pytest-asyncio` with `asyncio_mode = "auto"` (set in plugin pyproject, e.g. `plugins/memory/pyproject.toml:16-18`). Mark async tests by writing `async def test_...`.
- **Test placement**:
  - `lib/tests/` for shared library tests
  - `plugins/<x>/tests/` for plugin-specific tests
- **No network in tests** unless explicitly marked and skippable in CI.
- **Use SQLite in-memory** (`DatabaseConfig.sqlite(path=":memory:")`) for DB tests; avoid touching real files.
- **Coverage**: pragmatic, not enforced. Critical paths (DB, hooks, command parsing) MUST have tests.

---

## Required Patterns

- **Imports from `lib`**: use the public surface (`from lib.db import Model, Field`), never reach into `lib.db.adapters.*`.
- **Logging**: `from lib import logging; logging.info(...)`. Never use `print` in long-running code.
- **Async DB lifecycle**: pair `init_db()` with `close_db()` on every code path (try/finally) — see [database-guidelines](./database-guidelines.md).
- **Tauri command shape**: `Result<T, String>`, immediate return, background work via `tokio::spawn` + events — see [tauri-patterns](./tauri-patterns.md).
- **Version bumps**: run `uv run scripts/update_version.py` to sync every `plugin.json`, `pyproject.toml`, and `marketplace.json`.

---

## Forbidden Patterns

```python
# ❌ Top-level side effects in plugin modules (slows hook startup, breaks import order)
import requests
SESSION = requests.Session()              # at import time
init_db_sync()                             # blocking I/O at import

# Why: hooks import the module on every Claude Code event; module-level work runs each time.

# ❌ Synchronous I/O inside async hooks
async def handle_pre_tool_use(data):
    with open("/etc/passwd") as f:        # blocks the event loop
        ...

# ❌ Catching everything and continuing
try:
    risky()
except Exception:
    pass

# ❌ String-formatting SQL
await DatabaseConnection.execute(f"SELECT * FROM t WHERE id = '{x}'")

# ❌ Cross-plugin imports
from plugins.memory.scripts.memory import create_memory

# ❌ print() in library code or hooks (use lib.logging)
print("debug:", something)
```

```rust
// ❌ Synchronous std::process::Command inside a Tauri command
#[tauri::command]
fn slow() -> Result<(), String> {
    std::process::Command::new("claude").output().unwrap();   // blocks Tauri's runtime
    Ok(())
}

// ❌ unwrap()/expect() in non-test code
let q = task_queue().unwrap();

// ❌ Long-running work in a #[tauri::command]
#[tauri::command]
async fn do_everything() -> Result<(), String> {
    install_plugin_blocking().await?;        // UI freezes; use task queue + events
    Ok(())
}
```

---

## Manifest & Version Hygiene

- Plugin `version`, root `pyproject.toml.version`, `lib/pyproject.toml.version`, and `marketplace.json` plugin entries MUST all match.
- After editing any version, re-run `uv run scripts/update_version.py` and commit the resulting changes together.
- `scripts/check.py:294-295` defines the manifest contract:
  ```python
  REQUIRED_PLUGIN_FIELDS = ["name", "version", "description"]
  RECOMMENDED_PLUGIN_FIELDS = ["author", "license", "keywords"]
  ```
  Missing required fields fails `uv run scripts/check.py`.

---

## Spec & Skill Quality Check

For changes to `commands/`, `skills/`, `agents/`, or any `agent.md` (and equally for these `.trellis/spec/*` files), run the AI comprehension check from `CLAUDE.md` §代码质量检查规范:

```bash
claude --settings ~/.claude/settings.glm-4.7-flash.json -p "<content under test>" \
  --output-format stream-json | jq -r 'select(.type == "result" and .subtype == "success") | .result'
```

The result MUST be non-empty and meaningfully describe the content. Empty/garbled output means the spec is too ambiguous for downstream agents.

---

## Code Review Checklist

Before approving a backend PR:

- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] Relevant `pytest` suites pass (`lib/tests`, plugin tests)
- [ ] `cargo fmt --check` + `cargo clippy` clean for desktop changes
- [ ] No top-level side effects in plugin modules
- [ ] No synchronous I/O inside async functions
- [ ] All `try` blocks either recover or re-raise (no silent swallow)
- [ ] Tauri commands return `Result<T, String>` and don't block
- [ ] DB lifecycle has matched `init_db` / `close_db` on every path
- [ ] Versions are synced (`scripts/update_version.py` was run if any `version` was touched)
- [ ] `marketplace.json` updated when adding/renaming a plugin
- [ ] No PII or secrets in log lines (see [logging-guidelines](./logging-guidelines.md))
- [ ] New spec/skill content passes the AI comprehension check above

---

## Common Mistakes

| Mistake                                   | Fix                                                                            |
| ----------------------------------------- | ------------------------------------------------------------------------------ |
| Forgot to bump `marketplace.json` version | Re-run `uv run scripts/update_version.py`                                      |
| `unwrap()` slipped into Rust release code | Replace with `?` or `ok_or`                                                    |
| Plugin tests reach the network            | Mock or mark with `pytest.mark.network` and skip in CI default                 |
| `print` debug left in                     | Replace with `lib.logging.debug` (only emits to console with `enable_debug()`) |
| Ruff rule disabled inline                 | Don't disable; fix the underlying issue or raise it in review                  |

---

## References

- `pyproject.toml:6, 22-39` — Python version, scripts, package boundary
- `lib/pyproject.toml:8-13` — optional extras (mysql/sqlite/postgresql)
- `plugins/memory/pyproject.toml:16-18` — pytest-asyncio config
- `scripts/check.py:294-295` — required plugin fields
- `CLAUDE.md` §代码质量检查规范 — AI quality-check command
- `.claude/memory/desktop-code-quality-2026-04-05.md` — historical audit findings
