# Directory Structure

> How backend code is organized in the ccplugin monorepo.

---

## Scope

Where every kind of code lives, why, and what is published vs. internal.

---

## Repo Layout

```
ccplugin/
├── .claude-plugin/
│   └── marketplace.json         # marketplace registry (pluginRoot=./plugins)
├── .claude/
│   ├── hooks/                   # repo-level Claude Code hooks (Trellis, etc.)
│   ├── skills/                  # project skills
│   ├── memory/                  # long-term project memory (architecture notes)
│   └── rules/MEMORY.md          # memory index (auto-loaded)
├── .trellis/
│   ├── workflow.md              # Trellis development phases
│   ├── spec/                    # this directory (backend/, guides/, ...)
│   └── tasks/                   # active and archived tasks
├── plugins/                     # all Claude Code plugins
│   ├── tools/                   # tool plugins (git, deepresearch, ...)
│   ├── languages/               # language spec plugins (python, typescript, ...)
│   ├── themes/                  # theme/design plugins
│   ├── office/                  # office file plugins (docx/pptx/xlsx)
│   ├── memory/                  # memory plugin (most complex; reference example)
│   └── template/                # plugin scaffold template
├── lib/                         # shared Python library (own pyproject)
│   ├── db/                      # async ORM (core, models, schema, adapters/)
│   ├── logging/                 # Rich-based hourly-rotated logger
│   ├── hooks/                   # generic hook dispatch helpers
│   ├── utils/                   # env, gitignore, paths
│   └── tests/                   # pytest tests for lib
├── scripts/                     # root CLI (the ONLY thing root pyproject ships)
│   ├── clean.py / update.py / info.py / check.py / install.py
│   ├── update_version.py        # version sync across all manifests
│   └── statusline/              # statusline implementation
├── desktop/                     # Tauri desktop app
│   ├── src/                     # React frontend (TypeScript)
│   └── src-tauri/
│       ├── src/commands/        # #[tauri::command] entry points
│       └── src/services/        # Rust business logic + task queue
├── docs/                        # plugin development docs
├── pyproject.toml               # root package (publishes scripts only)
├── .python-version              # 3.11
└── .version                     # current version (with build segment)
```

---

## Rules

- **Root package boundary**: `pyproject.toml` `[tool.setuptools.packages.find]` declares `include = ["scripts*"]` and `exclude = ["plugins*", "lib*"]`. Never add modules outside `scripts/` to the root distribution. (`pyproject.toml:36-39`)
- **Each plugin is a package**: every directory under `plugins/<category>/<name>/` has its own `pyproject.toml` and `.claude-plugin/plugin.json`. Plugins do not import from each other.
- **Shared code goes to `lib/`**: if logic is reused in 2+ plugins or in `scripts/` + a plugin, it belongs in `lib/`. `lib/` is consumed via `[tool.uv.sources.lib]` (local path in workspace, git ref for downstream plugins).
- **`.claude/` vs `.claude-plugin/`**: `.claude/` (with hyphen) is repo-level Claude Code config (hooks, skills, agents). `.claude-plugin/` (inside a plugin) holds that plugin's manifest.
- **Marketplace registry only at root**: `.claude-plugin/marketplace.json` is the single source of truth for what is published. Plugin directories must not contain another `marketplace.json`.
- **Desktop is segregated**: `desktop/` is a self-contained Tauri app. Do not import desktop code from plugins or `lib/`.

---

## Code Excerpt — Root Package Boundary

From `pyproject.toml:33-42`:

```toml
[tool.setuptools.package-data]
"*" = ["*.json", "*.md"]

[tool.setuptools.packages.find]
where = ["."]
include = ["scripts*"]
exclude = ["plugins*", "lib*"]

[tool.uv.sources.lib]
path = "./lib"
```

Why: the root distribution is the user-facing CLI (`uvx --from git+... install ...`). Plugins live in their own `plugins/*` directories and are installed via Claude Code's plugin system, not via the root wheel.

---

## Where to Put New Code

| Kind of change | Location |
|----------------|----------|
| New CLI command shipped to all users | `scripts/<name>.py` + add `[project.scripts]` entry in root `pyproject.toml` |
| New plugin | `plugins/<category>/<name>/` (use `plugins/template/` as scaffold) |
| Reusable helper used by 2+ plugins | `lib/<module>/` |
| Plugin-private helper | `plugins/<category>/<name>/scripts/<module>.py` |
| Tauri command | `desktop/src-tauri/src/commands/<domain>.rs` |
| Tauri business logic / long-running task | `desktop/src-tauri/src/services/<service>.rs` |
| Repo-level Claude hook (e.g. Trellis injection) | `.claude/hooks/<name>.py` |
| Plugin-scoped Claude hook | `plugins/<category>/<name>/scripts/hooks.py` + manifest entry |

---

## Naming Conventions

- **Plugin directory & manifest `name`**: must match exactly. `plugins/tools/git/` ↔ `plugin.json:name = "git"`.
- **Marketplace entry `name`**: must match the plugin manifest `name` (NOT the directory path). See [marketplace](./marketplace.md) for the office-naming case study.
- **Python modules**: snake_case files; package directories lowercase.
- **Rust files**: snake_case (`task_queue.rs`, `python_bridge.rs`).
- **Event names** (Tauri): kebab-case `<domain>-<entity>-<action>` (see [tauri-patterns](./tauri-patterns.md)).

---

## Forbidden Patterns

```python
# ❌ Adding non-scripts modules to root pyproject.toml
include = ["scripts*", "common*"]   # do NOT extend; create lib/ module instead

# ❌ Cross-plugin imports
from plugins.memory.scripts.memory import create_memory   # never import another plugin

# ❌ Putting reusable helpers inside a plugin
plugins/tools/git/scripts/db_helper.py    # if used by 2+ plugins → move to lib/db/
```

Why bad: blurs publishing boundary; couples plugins; makes versioning ambiguous.

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Adding a new top-level Python package | Decide: CLI → `scripts/`; reusable → `lib/`; plugin-internal → `plugins/<x>/scripts/` |
| Creating two manifests with conflicting `name` | Manifest `name` must equal directory leaf name |
| Forgetting to register in `marketplace.json` | A plugin not in `.claude-plugin/marketplace.json` is invisible to users |
| Mixing desktop and plugin code | Keep `desktop/` self-contained; if shared logic is needed, expose via Tauri command, not Python import |
| Hardcoding paths inside plugins | Use `lib.utils.env` (`get_project_dir()`, `get_project_plugins_dir()`) |

---

## References

- `pyproject.toml:33-42` — root package boundary
- `lib/pyproject.toml:19-22` — lib package config
- `plugins/memory/pyproject.toml:23-30` — plugin pyproject template (uses `git+...` for `lib`)
- `AGENTS.md` §结构速览 — tabular layout summary
- `.claude-plugin/marketplace.json` — registry layout
