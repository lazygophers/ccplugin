# Plugin Conventions

> How a Claude Code plugin under `plugins/<category>/<name>/` is structured in this repo.

---

## Scope

Manifest schema, directory layout, `pyproject.toml` template, and version-sync rules. Read before adding a new plugin or restructuring an existing one.

---

## Directory Layout

```
plugins/<category>/<name>/
├── .claude-plugin/
│   └── plugin.json              # required: manifest
├── commands/                    # optional: slash commands (markdown)
├── agents/                      # optional: subagents (markdown)
├── skills/                      # optional: skills (per-skill subdir with SKILL.md)
├── hooks/                       # optional: hook scripts referenced by plugin.json
├── scripts/                     # optional: Python entry points + helpers
│   ├── __init__.py
│   ├── main.py                  # convention: `uv run ... main.py <subcommand>`
│   └── hooks.py                 # if the plugin registers hooks
├── tests/                       # optional: pytest tests
├── pyproject.toml               # required: uv-managed Python project
├── README.md                    # required: user-facing docs
└── CHANGELOG.md                 # required when version changes
```

`commands/`, `agents/`, `skills/` MUST live at the plugin root — never inside `.claude-plugin/`. `SKILL.md` filenames are uppercase.

---

## `plugin.json` Schema

Required fields (`scripts/check.py:294`):

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | matches the plugin directory leaf and the `marketplace.json` entry name |
| `version` | string | semver; synced with root `pyproject.toml` and `marketplace.json` |
| `description` | string | one sentence; user-facing |

Recommended fields (`scripts/check.py:295`):

| Field | Type | Notes |
|-------|------|-------|
| `author` | object | `{ name, email, url }` |
| `license` | string | SPDX id (e.g. `MIT`) |
| `keywords` | string[] | for marketplace search |

Component fields (point to plugin root paths, never to `.claude-plugin/`):

| Field | Type | Example |
|-------|------|---------|
| `commands` | string or string[] | `"./commands/"` or `["./commands/foo.md"]` |
| `agents` | string or string[] | `"./agents/"` |
| `skills` | string or string[] | `"./skills/"` |
| `hooks` | object | see Hooks section below |

---

## Real Manifest

From `plugins/memory/.claude-plugin/plugin.json:1-34`:

```json
{
  "name": "memory",
  "version": "0.0.193",
  "description": "智能记忆插件 - ...",
  "author": {
    "name": "lazygophers",
    "email": "admin@lazygophers.dev",
    "url": "https://github.com/lazygophers"
  },
  "homepage": "https://github.com/lazygophers/ccplugin/tree/master/plugins/memory",
  "repository": "https://github.com/lazygophers/ccplugin/tree/master/plugins/memory",
  "license": "MIT",
  "keywords": ["memory", "persistence", "context", "uri", "sqlite", "hooks"],
  "skills": "./skills/",
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "PLUGIN_NAME=memory uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks",
            "async": true,
            "timeout": 1000
          }
        ]
      }
    ],
    "..."
  }
}
```

Key conventions visible above:

- `${CLAUDE_PLUGIN_ROOT}` is the plugin install directory at runtime.
- Plugin entry point is `uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py <subcommand>`.
- Hooks pass `PLUGIN_NAME=...` so the script knows which plugin's logging dir / config to use.
- `async: true` lets the hook return immediately while work continues; `timeout` is the budget in ms.

---

## `pyproject.toml` Template

Plugins are uv projects. Two valid `lib` source patterns:

1. **In-repo development** (workspace member): use `[tool.uv.sources.lib]` with `path = "../../lib"` (or appropriate relative path).
2. **Distribution** (installed by users): use git ref so the plugin works standalone.

From `plugins/memory/pyproject.toml:1-30`:

```toml
[project]
name = "code-memory"
version = "0.0.193"
requires-python = ">=3.11"
dependencies = ["click>=8.3.1", "lib", "aiosqlite>=0.19.0", ...]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "pytest-asyncio>=0.21.0", ...]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.setuptools.packages.find]
where = ["scripts"]
include = ["memory*", "web*"]

[tool.uv.sources.lib]
git = "https://github.com/lazygophers/ccplugin"
subdirectory = "lib"
rev = "master"
```

Notes:

- `project.name` may differ from manifest `name` (Python package name vs plugin name) but should be unambiguous.
- `requires-python = ">=3.11"` matches the repo.
- `where = ["scripts"]` so the plugin's Python package lives under `scripts/`.

---

## Version Sync

The single source of truth for the current version is `.version` at the repo root. After editing it, run:

```bash
uv run scripts/update_version.py
```

This propagates the version to:

- root `pyproject.toml`
- `lib/pyproject.toml`
- every `plugins/**/pyproject.toml`
- every `plugins/**/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` (per-plugin entries)

Never bump versions by hand in only one location.

---

## Forbidden Patterns

```jsonc
// ❌ Wrong: components inside .claude-plugin
{ "skills": "./.claude-plugin/skills/" }

// ❌ Wrong: hard-coded absolute paths
{ "command": "/Users/me/dev/ccplugin/plugins/memory/scripts/main.py hooks" }

// ❌ Wrong: missing required field
{ "name": "foo" }     // no version, no description → fails scripts/check.py
```

```toml
# ❌ Wrong: depending on another plugin
dependencies = ["lib", "code-memory"]   # plugins must not import each other

# ❌ Wrong: pinning lib to a different version than the repo
[tool.uv.sources.lib]
rev = "v0.0.100"      # diverges from repo version
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Plugin works locally but fails after install | You used `path = "..."` for `lib`; switch to `git = ...` for distributable plugins |
| Hook does nothing | Verify the manifest path is relative (`./scripts/main.py`), `${CLAUDE_PLUGIN_ROOT}` is set, and `async/timeout` are appropriate |
| Plugin rename leaves stale references | Update directory name, manifest `name`, and `marketplace.json` entry in one commit; run `scripts/check.py` |
| New version not picked up by users | Forgot to run `update_version.py` and/or commit `.claude-plugin/marketplace.json` |
| `SKILL.md` lowercase | Rename to `SKILL.md` (uppercase) — Claude Code skills loader is case-sensitive |

---

## References

- `plugins/memory/.claude-plugin/plugin.json` — reference manifest with hooks
- `plugins/template/` — minimal scaffold
- `scripts/check.py:294-295` — required vs recommended fields
- `scripts/update_version.py` — version sync logic
- `docs/plugin-development.md` — narrative tutorial (complementary, less normative)
- See also: [marketplace](./marketplace.md), [hooks-contract](./hooks-contract.md)
