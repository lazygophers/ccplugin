# Marketplace

> Rules for `.claude-plugin/marketplace.json` — the registry that publishes plugins to users.

---

## Scope

What `marketplace.json` is, the invariants every entry must satisfy, and how to register / rename / retire a plugin.

---

## File

- Location: `.claude-plugin/marketplace.json` at the repo root.
- Owner: this repo. There is exactly one marketplace file; plugin directories MUST NOT contain another.
- Consumed by: Claude Code's plugin install command (`/plugin install ...@<marketplace>`), and the desktop app's marketplace UI.

---

## Schema (this repo)

```jsonc
{
  "name": "ccplugin-market",
  "owner": { "name": "...", "url": "..." },
  "metadata": { ... },
  "pluginRoot": "./plugins",        // base path; entries' source resolves relative to this
  "plugins": [
    {
      "name": "<plugin-name>",       // MUST equal plugins/.../<dir>/.claude-plugin/plugin.json:name
      "source": "./<category>/<dir>",// path under pluginRoot to the plugin directory
      "version": "<x.y.z>",          // MUST equal that plugin's plugin.json:version
      "description": "...",
      "author": { ... },
      "keywords": [ ... ],
      "category": "<category>"       // tools | languages | themes | office | ...
    }
  ]
}
```

`pluginRoot` MUST stay `./plugins`. New plugins live under one of the existing categories or a new sibling directory; do not introduce nested categories beyond depth one.

---

## Invariants

The following MUST all be true for every plugin entry:

1. **Name triple-equality**:
   `marketplace.json:plugins[i].name`
   == `plugins/<category>/<dir>/.claude-plugin/plugin.json:name`
   == directory leaf name `<dir>` (when reasonably possible — see "Office naming" below).
2. **Version triple-equality**: `marketplace.json[i].version` == that plugin's `plugin.json:version` == that plugin's `pyproject.toml:version`. Run `uv run scripts/update_version.py` after any version edit.
3. **Source path resolves**: `<repo>/plugins/<source>` MUST contain a `.claude-plugin/plugin.json`.
4. **Category matches placement**: `category` field matches the directory layer (`./tools/...` → `category: "tools"`).
5. **No duplicate names**: each `name` appears at most once across `plugins[]`.

`scripts/check.py` validates these; run it before opening a PR that touches the marketplace.

---

## Registration Procedure (new plugin)

1. Create `plugins/<category>/<name>/` (use `plugins/template/` as scaffold — see [plugin-conventions](./plugin-conventions.md)).
2. Edit `.claude-plugin/marketplace.json`: append an object to `plugins[]` matching the schema above.
3. Run `uv run scripts/check.py` — fails fast on missing fields or path mismatch.
4. Run `uv run scripts/update_version.py` to ensure version columns line up.
5. Commit all three changes (plugin dir + manifest + marketplace entry) in a single commit so reviewers see the full surface.

---

## Renaming Procedure

A plugin rename touches FOUR places. Doing one at a time leaves the marketplace in an invalid state — make all changes in one commit:

1. Move the directory: `git mv plugins/old plugins/new`
2. Edit `plugins/new/.claude-plugin/plugin.json:name`
3. Edit `plugins/new/pyproject.toml` `[project].name` (if it uses the same word)
4. Edit `.claude-plugin/marketplace.json`: update `plugins[i].name` AND `plugins[i].source`

Validate with `uv run scripts/check.py`.

---

## Retirement Procedure

To remove a plugin:

1. Delete the entry from `marketplace.json:plugins[]`.
2. Move the directory to an `archived/` location OR delete it; users with the plugin already installed continue to work, but new installs will fail.
3. Add a CHANGELOG note in the next release explaining the retirement and migration path.

Do not leave a tombstone entry in `plugins[]` — Claude Code will still try to install from a missing path.

---

## Code Excerpt — Required Fields Validation

`scripts/check.py:294-295`:

```python
REQUIRED_PLUGIN_FIELDS = ["name", "version", "description"]
RECOMMENDED_PLUGIN_FIELDS = ["author", "license", "keywords"]
```

The same constraint applies to the per-plugin `plugin.json`. Marketplace entries are checked against these fields plus `source` and `category`.

---

## Case Study: Office Plugin Naming

Historically the office plugins (`docx`, `pptx`, `xlsx`) had inconsistent `name` values between their directory leaf, `plugin.json`, and `marketplace.json` entry, which broke install commands. The convention now enforced:

- Directory: `plugins/office/<format>/` (e.g. `plugins/office/xlsx/`)
- `plugin.json:name`: `office-<format>` (e.g. `office-xlsx`) — disambiguates against any other `xlsx` package
- `marketplace.json[i].name`: same as `plugin.json:name`
- `marketplace.json[i].source`: `./office/<format>`

Triple-equality on `name` is preserved because both the manifest and the marketplace entry use the prefixed form. The directory leaf is the only odd one out, and that is acceptable as long as `source` resolves correctly.

If you create new office plugins, follow this exact pattern. Do not bare-name them as `xlsx`/`docx`/`pptx`.

---

## Forbidden Patterns

```jsonc
// ❌ Mismatched name triple
// marketplace.json
{ "name": "git-tool", "source": "./tools/git" }
// plugins/tools/git/.claude-plugin/plugin.json
{ "name": "git" }                 // → install command picks the wrong identifier

// ❌ Drifted version
// marketplace.json: "version": "0.0.190"
// plugin.json:      "version": "0.0.193"

// ❌ Tombstone after retirement
{ "name": "deprecated-thing", "source": "./tools/deprecated-thing" }   // dir already deleted

// ❌ Nested marketplace.json
plugins/tools/git/marketplace.json    // there can be only ONE
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Install fails with "plugin not found" | Check `source` resolves relative to `pluginRoot`; it's `./<category>/<dir>`, not `./plugins/<category>/<dir>` |
| User sees stale version after release | Run `uv run scripts/update_version.py`; commit the regenerated `marketplace.json` |
| Two plugins both named `cli` | `name` MUST be globally unique within `plugins[]` |
| Office plugin clashes with another `xlsx` | Use the `office-<format>` naming convention (see case study) |
| Forgot to register a new plugin | If it's not in `marketplace.json`, it's invisible — reviewers should reject the PR |

---

## References

- `.claude-plugin/marketplace.json` — the registry itself
- `scripts/check.py:294-295` — required field constants
- `scripts/update_version.py` — version sync across all manifests + marketplace
- See also: [plugin-conventions](./plugin-conventions.md)
