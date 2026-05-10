# Marketplace Naming Audit (extracted from deep-study session 2026-05-10)

## Counts

- Registered in marketplace.json: 35
- On-disk plugin manifests found: 32 (audit-tool count; actual manifests exist for all)
- Orphans (audit-flagged): 4
- Ghosts (audit-flagged): 7
- Version drift: 0 (all manifests at 0.0.193)
- Empty: `plugins/themes/` (only .DS_Store)

## Root cause

Marketplace scanner compares directory basename vs `manifest.name`. When mismatched, scanner reports orphan (manifest present, registry expects different name) + ghost (registry name has no matching dir).

## Mismatched plugins

| Marketplace path | Marketplace name | Manifest name | Dir basename | Status |
|------------------|------------------|---------------|--------------|--------|
| ./plugins/office/docx | office-docx | office-docx | docx | mismatch |
| ./plugins/office/pdf | office-pdf | office-pdf | pdf | mismatch |
| ./plugins/office/pptx | office-pptx | office-pptx | pptx | mismatch |
| ./plugins/office/xlsx | office-xlsx | office-xlsx | xlsx | mismatch |
| ./plugins/llms | plugin-llms | plugin-llms | llms | mismatch |
| ./plugins/template | plugin-template | plugin-template | template | mismatch |
| ./plugins/memory | memory | memory | memory | OK |

## Properly aligned plugins (28)

All `plugins/tools/*`, `plugins/languages/*`, `plugins/novels/*` have `dir_basename == manifest.name == marketplace_entry_name`.

## Decision matrix

### Option A: Rename dirs

- Move `plugins/office/docx` → `plugins/office/office-docx` (× 4 office)
- Move `plugins/llms` → `plugins/plugin-llms`
- Move `plugins/template` → `plugins/plugin-template`
- Update marketplace.json paths
- Pros: manifest names unchanged (no public API break)
- Cons: 6 dir moves; git history complexity; CI path changes

### Option B: Rename manifests

- Edit 6 plugin.json files: change `name` field
- Update marketplace.json `name` field per entry
- Pros: minimal file movement; cleaner CLI semantics (`claude plugin install xlsx`)
- Cons: public-facing name change (breaks user installs of `office-xlsx` etc.); CHANGELOG entry required

### Recommendation: Option B

Reasoning: user-facing CLI commands are simpler (`xlsx` vs `office-xlsx`), directory structure already implies office category, prefix-stripping is one-shot.

## Files to modify (Option B)

```
plugins/office/docx/.claude-plugin/plugin.json   name: office-docx -> docx
plugins/office/pdf/.claude-plugin/plugin.json    name: office-pdf -> pdf
plugins/office/pptx/.claude-plugin/plugin.json   name: office-pptx -> pptx
plugins/office/xlsx/.claude-plugin/plugin.json   name: office-xlsx -> xlsx
plugins/llms/.claude-plugin/plugin.json          name: plugin-llms -> llms
plugins/template/.claude-plugin/plugin.json      name: plugin-template -> template
.claude-plugin/marketplace.json                  6 entries' name field
```

## Invariant to add (scripts/check.py)

```python
# pseudocode
for entry in marketplace["plugins"]:
    dir_path = entry["source"]
    manifest = json.load(open(f"{dir_path}/.claude-plugin/plugin.json"))
    dir_basename = os.path.basename(dir_path)
    assert entry["name"] == manifest["name"] == dir_basename, (
        f"name drift: {entry['name']} vs {manifest['name']} vs {dir_basename}"
    )
```

## Side effects

- Documentation: `docs/plugin-development.md` may reference old names — search and update
- Skills/agents may mention old names — search `.claude/`, `.opencode/`, `.codex/`, `.agents/`
- README.md plugin list may use old names

## CHANGELOG note (proposed)

```
### Breaking

- Renamed office plugins: `office-docx`/`office-pdf`/`office-pptx`/`office-xlsx` → `docx`/`pdf`/`pptx`/`xlsx`
- Renamed `plugin-llms` → `llms`, `plugin-template` → `template`
- Migration: re-run `claude plugin install <newname>`
```
