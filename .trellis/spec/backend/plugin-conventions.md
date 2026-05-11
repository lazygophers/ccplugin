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
| `description` | string | one sentence; user-facing |

> Note: `version` 字段在 commit c9a7e615 移除 (single-source policy, 不再放入 plugin.json/marketplace.json); 仍可选填但非必需。

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

## Idempotent Install Pattern

Bash installers (`install.sh`) MUST be idempotent: running twice on a configured system produces no surprises and reuses prior choices.

### Detection-First Prompt Order

```bash
detect_local_state                       # set flags from filesystem
if [[ $CONFIG_EXISTS == 1 ]]; then
  if should_overwrite_config; then       # ask FIRST
    OVERWRITE_CONFIG=1
    collect_fields_from_prompt
  else
    OVERWRITE_CONFIG=0
    read_existing_config                 # reuse existing values
    log_info "复用现有 config: ..."
  fi
else
  OVERWRITE_CONFIG=1
  collect_fields_from_prompt
fi
```

**Anti-pattern**: prompting for values before asking "overwrite?" wastes user input when they answer "no".

### Reading Existing Config (path-injection-safe)

Pass the config path via env var; never interpolate into the python source.

```bash
out=$(CFG_PATH="$cfg" python3 -c '
import json, os, sys
try:
    d = json.load(open(os.environ["CFG_PATH"]))
    print(d.get("vault", ""))
    print(d.get("lang", "zh-CN"))
    print(d.get("settings", ""))
except Exception:
    sys.exit(1)
') || return 1
```

### Periodic-Task (cron/launchd) Idempotency

Three rules:

1. **Detect before install**: scan `crontab -l` and `launchctl list` for already-registered jobs; skip install if present.
2. **Prune stale**: crontab lines referencing `<plugin>/scripts/cron/*.sh` whose target file no longer exists MUST be removed.
3. **Anchored regex**: match the named wrapper allowlist (e.g., `cortex/scripts/cron/(lint|fold|dashboard)\.sh`) — never match the plugin name alone, to avoid pruning user-authored cron entries that happen to mention the plugin.

```bash
new=$(echo "$current" | awk -v home="$HOME" '
  /cortex\/scripts\/cron\/(lint|fold|dashboard)\.sh/ {
    match($0, /[^ ]*cortex\/scripts\/cron\/[a-z]+\.sh/)
    if (RSTART > 0) {
      path = substr($0, RSTART, RLENGTH)
      gsub("~", home, path)
      cmd = "test -f \"" path "\""    # QUOTED — injection-safe
      if (system(cmd) != 0) { next }
    }
  }
  { print }
')
```

`launchctl list` MUST swallow stderr (`2>/dev/null`) — macOS 14+ restricts non-root visibility into system domain. `crontab -l` reads from stdin without eval, so `printf '%s\n' "$new" | crontab -` is safe even with shell-meta chars in the content.

### Non-Interactive Flag-Override Semantics

When `--non-interactive` and config already exists:
- No `--vault` / `--lang` / `--settings` / `--reinstall` flags → **reuse** existing config
- Any one of those flags present → **overwrite** (user intent inferred from explicit flag)
- `--reinstall` always wins

Satisfies both `curl|bash` reuse semantics and explicit-flag override semantics from one code path.

### Acceptance test signals

- Scenario: config exists + answer "n" → no prompts for individual fields, `log_info "复用现有 config: ..."` printed
- Scenario: config exists + cron job already registered → no cron prompt, `log_info "已有 ... 周期任务, 跳过"` printed
- Scenario: `--reinstall` → forces both prompts/installs regardless of existing state
- Stale cron prune: introduce a crontab line pointing at a deleted wrapper; rerun installer; line MUST be gone

Reference impl: `plugins/tools/cortex/install.sh`.

---

## References

- `plugins/memory/.claude-plugin/plugin.json` — reference manifest with hooks
- `plugins/template/` — minimal scaffold
- `scripts/check.py:294-295` — required vs recommended fields
- `scripts/update_version.py` — version sync logic
- `docs/plugin-development.md` — narrative tutorial (complementary, less normative)
- See also: [marketplace](./marketplace.md), [hooks-contract](./hooks-contract.md)
