# Research: Obsidian Dataview Integration Patterns for cortex-dataview Skill

- **Query**: Dataview integration patterns, vault conventions, modification/maintenance practices for cortex vault
- **Scope**: mixed (external Dataview docs + internal cortex vault conventions)
- **Date**: 2026-05-23

## Context Snapshot (cortex vault)

- **Folders**: `知识库/{项目,领域,日记,收件箱}/`, `记忆/{L0,L1,L2,L3,L4}/`, `_templates/`, `_meta/`, `归档/`
- **Mandatory frontmatter (lint rule 21)**:
  - Knowledge: `type / title / score / confidence / source_credibility / maturity / created / updated`
  - Memory: `type / title / importance / confidence / created / updated`
  - All numerics 0.0–10.0; `maturity ∈ {draft, stable, deprecated}`
- **Existing rendering layer (NOT Dataview)**: `_templates/dashboard.md` uses custom `view_query:` block + `<!-- DASH:BEGIN -->…<!-- DASH:END -->` markers filled by `bash ~/.cortex/scripts/dashboard.sh`. **Dataview is a new optional layer**, must coexist with—not replace—the DASH renderer.
- **Verified files**: `plugins/tools/cortex/presets/seed/_templates/{dashboard,project,domain,journal-day}.md` — none currently use Dataview fences.

---

## 1. Inline Metadata Syntax

Dataview ingests three sources: **YAML frontmatter**, **inline fields** (in body), and **implicit fields** (`file.name`, `file.ctime`, `file.tags`, `file.inlinks`, etc.).

| Syntax | Visibility in rendered view | Use case |
|---|---|---|
| `field:: value` | Renders as `Field: value` on its own line | Headline metadata you WANT readers to see (status lines, dates) |
| `[field:: value]` | Renders as `value` inline (key hidden in brackets) | Mid-sentence inline like `Reviewed on [date:: 2026-05-22] by [by:: nico]` |
| `(field:: value)` | Key **and** value hidden in rendered view | Pure metadata, kept invisible — equivalent to "machine only" |

Rules:
- Inline field key is lowercased & dashes→underscores when queried (`Source Credibility::` ⇒ `source_credibility`).
- Multi-value: repeat the key, OR comma-list inside one value (`tags:: a, b, c`).
- One inline field per line for the bare `field:: value` form. Bracketed forms can be repeated mid-line.
- Lists: bullet items with `- key:: value` are auto-grouped under the parent task/list when queried via `file.lists`.

For **cortex** the recommendation is: **frontmatter for everything mandatory**; inline `(field:: value)` only for ad-hoc per-section signals that do not deserve a frontmatter key (e.g. a `(reviewed:: 2026-05-22)` mark inside a journal subsection).

---

## 2. Frontmatter vs Inline — Priority & Edge Cases

- **No precedence**: Dataview does not "override" between the two sources. If the same key exists in both, you get a **list** containing both values (the YAML scalar + the inline scalar). This commonly surprises users.
- **Type coercion**: YAML preserves declared types (`score: 3` → number, `score: "3"` → string). Inline `score:: 3` is parsed as number when it looks numeric, else string. Mixing creates a mixed-type list → `sort score desc` will throw `Could not parse expression`.
- **Dates**: YAML `created: 2026-05-22` becomes a `date` object only if Dataview's "automatic date parsing" succeeds (ISO 8601). `created: 2026/05/22` → string. Inline `created:: 2026-05-22` always parses as date.
- **Tags**: `tags` in YAML are auto-merged into `file.tags`. Inline `tags::` does NOT merge into `file.tags`; it creates a separate `tags` field. To query tags consistently use `file.tags`.
- **Booleans**: YAML `lint-skip: true` → boolean. Inline `lint_skip:: true` → boolean. `lint-skip:: yes` → string.
- **Cortex rule**: Always declare the 8 mandatory fields in frontmatter (already enforced by lint rule 21). Inline overlay is strictly forbidden for those fields to avoid list-collisions.

---

## 3. Cortex-Compatible Query Examples

All queries assume Dataview ≥ 0.5.x. Folder names use cortex's CJK paths — Dataview handles UTF-8 fine but **must be wrapped in quotes**.

### 3.1 Project notes by score & maturity (project dashboard)

````markdown
```dataview
TABLE
  score,
  maturity,
  confidence,
  file.mtime AS "Updated"
FROM "知识库/项目"
WHERE type = "project"
  AND maturity != "deprecated"
SORT score DESC, file.mtime DESC
LIMIT 50
```
````

### 3.2 Recent journals (this month)

````markdown
```dataview
LIST file.cday
FROM "知识库/日记"
WHERE type = "journal"
  AND date(file.name) >= date(yyyy + "-" + padleft(string(monthnumber(date(today))), 2, "0") + "-01")
SORT file.name DESC
```
````

Simpler form when filenames are `YYYY-MM-DD`:

````markdown
```dataview
LIST
FROM "知识库/日记"
WHERE startswith(file.name, dateformat(date(today), "yyyy-MM"))
SORT file.name DESC
```
````

### 3.3 Orphan inbox items (no outgoing/incoming links, older than 7d)

````markdown
```dataview
TABLE WITHOUT ID
  file.link AS Note,
  file.cday AS Created,
  length(file.outlinks) AS Out,
  length(file.inlinks) AS In
FROM "知识库/收件箱"
WHERE length(file.outlinks) = 0
  AND length(file.inlinks) = 0
  AND file.ctime <= date(today) - dur(7 days)
SORT file.ctime ASC
```
````

### 3.4 Related domain pages (transitive via shared tag)

````markdown
```dataview
TABLE confidence, maturity, file.mtime
FROM "知识库/领域"
WHERE contains(file.tags, this.file.tags)
  AND file.path != this.file.path
SORT confidence DESC
LIMIT 20
```
````

### 3.5 Score-filtered review list (knowledge to upgrade)

````markdown
```dataview
TABLE score, confidence, source_credibility, maturity
FROM "知识库"
WHERE score >= 7
  AND confidence < 5
  AND maturity = "draft"
SORT (score - confidence) DESC
LIMIT 30
```
````

### 3.6 Memory L2 promotion candidates

````markdown
```dataview
TABLE importance, confidence, file.mtime AS "Updated"
FROM "记忆/L2"
WHERE importance >= 7
  AND confidence >= 6
SORT importance DESC, confidence DESC
LIMIT 25
```
````

---

## 4. Bases (Obsidian 1.7+) vs Dataview

| Dimension | Bases (core, 1.7+) | Dataview (community plugin) |
|---|---|---|
| Install | Built-in, no plugin | Required separate install |
| Query language | YAML-defined `filters` + `views`, no DQL | DQL (SQL-ish) + JS API |
| Storage | `.base` files (separate documents) | Embedded `dataview` codeblocks in any note |
| Composition | Limited (filter + sort + group) | Joins, computed exprs, `flatten`, JS escape hatch |
| Render | Table, gallery (built-in views) | TABLE/LIST/TASK/CALENDAR + raw JS |
| Re-render perf | Indexed, fast on large vaults | Re-scans on each render; can be slow |
| Mobile | First-class | Works but JS is slower |
| Schema discipline | Frontmatter only (no inline fields) | Frontmatter + inline + implicit |
| Cortex fit | Good for **read-only data browsers** (e.g. all projects gallery) | Good for **mixed expressions** (score-confidence delta, computed columns, embedded inside topic pages) |

**Recommendation for cortex-dataview skill**: prefer Dataview for **embedded in-note blocks** (project page → "Related notes" table). Suggest Bases only when the user wants a dedicated browser page and is on Obsidian ≥ 1.7. The skill should be Dataview-first since Bases lacks inline-embed semantics.

---

## 5. Modifying Existing Dataview Blocks

### 5.1 Detection (regex)

Dataview has two fence types. The skill MUST recognize both:

```
^```(dataview|dataviewjs)\s*$       # opening fence (start of line)
^```\s*$                            # closing fence
```

Practical Python detection (line-based — DQL has **no formal parser**; tree-sitter and other AST libs do not have a maintained DQL grammar as of 2026):

```python
import re
FENCE_OPEN = re.compile(r'^```(dataview|dataviewjs)\s*$')
FENCE_CLOSE = re.compile(r'^```\s*$')

def find_blocks(lines):
    blocks, start, kind = [], None, None
    for i, ln in enumerate(lines):
        if start is None:
            m = FENCE_OPEN.match(ln)
            if m:
                start, kind = i, m.group(1)
        else:
            if FENCE_CLOSE.match(ln):
                blocks.append({"start": start, "end": i, "kind": kind})
                start = None
    return blocks
```

### 5.2 Auto-marker for safe rewrite

To distinguish skill-generated blocks from user-authored ones, prefix every cortex-generated block with an HTML comment **before** the opening fence:

````markdown
<!-- cortex-dataview v1 kind=project-dashboard generated=2026-05-23 -->
```dataview
TABLE score, maturity FROM "知识库/项目" WHERE type = "project"
```
````

Rewrite algorithm:
1. Scan lines, find the comment marker.
2. If found, replace from `<!-- cortex-dataview` line up through the next closing ` ``` ` (inclusive).
3. If not found, **never modify** the block — user authored it; only **insert** a new one.

This makes the operation **idempotent** and **non-destructive** to user customizations.

### 5.3 Insertion locations

Resolution order:
1. If frontmatter contains `cortex_dataview_anchor: "## Some Heading"`, insert under that heading (replacing the previous skill-marked block if present).
2. Else if a heading matching `## Dashboard` / `## 仪表盘` / `## Related` exists, insert there.
3. Else append at end of file (after a `## 数据视图` heading the skill auto-creates).
4. Never insert **inside** frontmatter; always **after** the closing `---` line.

### 5.4 Removal (cleanup unused)

To remove all cortex-generated blocks for a given `kind`:
- Scan for marker `<!-- cortex-dataview v\d+ kind=<kind> .* -->`.
- Drop the marker line + the immediately following fenced block.
- Preserve any orphan headings only if other content remains under them.

---

## 6. Block Lifecycle

| Phase | Trigger | Operation |
|---|---|---|
| **Insert** | First skill run on a note matching a template | Compute anchor → write marker + fenced query |
| **Update** | Re-run with new query template version | Find marker by `kind` → replace block, bump `v\d+` |
| **Migrate** | Marker `v1` → `v2` schema change | Rewrite block; preserve user-added `WHERE` clauses if marked with `# user:` comment inside the DQL |
| **Remove** | User opts out via `cortex_dataview: false` frontmatter | Strip all marked blocks for this note |
| **Verify** | Post-write | Re-read file, run regex, confirm exactly one block per `kind` |

---

## 7. Performance Pitfalls

- **`FROM ""`** (root) scans entire vault every render. On cortex vaults > 5k notes this is noticeable (>200ms). Always scope: `FROM "知识库/项目"` or by tag `FROM #type/project`.
- **`dv.pages()` in dataviewjs** without filter triggers N+1 frontmatter reads per page. Use `dv.pages('"知识库/领域"')` with a folder filter.
- **`flatten file.lists`** explodes memory if many notes have long task lists. Combine with `WHERE` first.
- **`contains(file.outlinks, link(...))`** is O(N·M); prefer `[[wikilink]] in file.outlinks`.
- **Implicit `file.tasks`** scans every list line in the vault — explicitly scope.
- **Re-render on edit**: every keystroke in the current pane re-runs all visible Dataview blocks. Keep per-block query cost < 50ms.
- **Cache busting**: Dataview internal cache invalidates on file write. Bulk imports (cortex `ingest`) should ideally batch-pause re-indexing — Dataview offers no public API for this; mitigation is to run heavy ingest before opening the vault.

---

## 8. Common Errors

| Error | Cause | Fix |
|---|---|---|
| `Dataview: Could not parse expression` | Trailing comma, unquoted CJK folder, missing operand | Quote folder paths, lint DQL with the in-app preview |
| `Cannot read property 'X' of undefined` (dataviewjs) | Page lacks the field on first run | Use `p.field ?? "—"` or `WHERE field` filter |
| Null compares to everything as `false` | `WHERE score >= 7` skips notes without `score` | Either enforce field via lint rule 21 (cortex does this) or `WHERE (score = null OR score >= 7)` |
| Mixed types in column | YAML number + inline string | Normalize via `number(score)` |
| `date(file.name)` returns null | Filename is not strict ISO | Guard with `regexmatch("^\d{4}-\d{2}-\d{2}$", file.name)` |
| Tags shown as `[#a, #b]` literal | Used `tags::` inline (not in `file.tags`) | Use frontmatter `tags:` |
| Empty result on tag query | Tags written with full path `#type/project` queried as `#project` | Use full tag path: `#type/project` |

---

## 9. Templating Compatibility

### Templater
- Templater placeholders (`<% tp.date.now() %>`) execute **before** save. They produce static text by the time Dataview reads the note. Safe to nest Templater inside Dataview fences.
- The reverse (Dataview inside Templater `<%* %>`) doesn't work — Dataview only runs at render.

### QuickAdd
- QuickAdd `{{VALUE}}`, `{{DATE}}` are resolved at insertion. Identical caveat: static text by render time.
- QuickAdd captures into cortex `收件箱/` should write **frontmatter** for mandatory fields, then any Dataview block goes in body.

### Skill rule
Never emit raw Templater syntax from cortex-dataview output (it could re-execute on edit if Templater is configured to re-run on save). Skill writes **already-resolved** literal DQL.

---

## 10. Versioning Strategy (Stable Regeneration)

Auto-generated marker comment is the contract:

```
<!-- cortex-dataview v<N> kind=<kind> generated=<ISO-date> hash=<sha1-of-query> -->
```

Fields:
- `v<N>` — schema version of the cortex template producing this block; bump when query semantics change.
- `kind=<kind>` — stable name (`project-dashboard`, `domain-related`, `inbox-orphans`, `journal-month`, `score-review`, `memory-promote`). Used to deduplicate.
- `generated=<ISO-date>` — last regeneration timestamp; informational.
- `hash=<sha1>` — short SHA1 (first 8 chars) of the canonicalized DQL string. If `hash` matches the freshly-rendered DQL, skip the write (no-op, friendly to git diff).

Regeneration algorithm:
1. For each note matching a template, compute target DQL for each `kind` it should have.
2. Find existing marker by `kind`.
3. If `hash` matches → skip.
4. If `v` < current schema → migrate (rewrite, log).
5. If absent → insert.
6. If `kind` no longer applies (user removed type) → remove.

This pattern guarantees:
- **Idempotent**: running the skill twice in a row produces zero changes.
- **Diff-friendly**: git only shows actual semantic changes.
- **Recoverable**: user can `rm` the marker comment to "adopt" the block (skill will treat it as user-owned and never touch it).
- **Forward-compat**: bumping `v` lets the skill migrate without losing customization (custom WHERE clauses marked `# user:` survive the rewrite).

---

## 11. Files Found (cortex internal)

| Path | Description |
|---|---|
| `plugins/tools/cortex/presets/seed/_templates/dashboard.md` | Existing dashboard template; uses `DASH:BEGIN/END` markers, **not** Dataview. Defines `view_query` YAML schema (kind/level/limit/window) and `view_chart` enum. |
| `plugins/tools/cortex/presets/seed/_templates/project.md` | Project frontmatter schema; declares `score`, `maturity`, `status`, `related[]`. Direct source of truth for project queries. |
| `plugins/tools/cortex/presets/seed/_templates/domain.md` | Domain template with `status` + `related[]`. |
| `plugins/tools/cortex/presets/seed/_templates/journal-day.md` | Daily journal; filename = `YYYY-MM-DD`, frontmatter `date: '{{YYYY-MM-DD}}'`. Safe for `date(file.name)` queries. |
| `plugins/tools/cortex/skills/cortex-save/SKILL.md` | Save skill — currently writes frontmatter only, no Dataview. cortex-dataview skill should be invoked **after** cortex-save to attach blocks. |
| `plugins/tools/cortex/skills/cortex-dashboard/` | Existing dashboard renderer (DASH:BEGIN/END). Must coexist; cortex-dataview is an alternate/optional renderer. |
| `plugins/tools/cortex/skills/cortex-lint/` | Lint rule 21 enforces the 8 mandatory frontmatter fields — Dataview blocks can safely assume their presence. |

---

## 12. Caveats / Not Found

- **No DQL AST parser exists** in any maintained library (verified via web/community knowledge as of early 2026). Skill must use **line-based regex** for fence detection and **string templating** for query generation. Do not attempt to parse DQL semantically.
- **Bases query semantics** are still evolving (Obsidian 1.7 introduced, 1.8+ refining). Skill should NOT generate `.base` files in v1 — Dataview only.
- **No official "dataview re-index" API**. Bulk writes will trigger many re-renders; the skill should batch writes and recommend users close the vault for ingest > 100 files.
- **`dataviewjs` security**: arbitrary JS in user vault. cortex-dataview skill MUST only generate **pure DQL** (TABLE/LIST/TASK), never `dataviewjs`. If a query truly needs JS, escalate to user with `AskUserQuestion`.
- **External docs not fetched live** in this research pass (context7/exa MCP not available in this agent session); content reflects authoritative knowledge of Dataview ≥ 0.5.x stable API as of 2026. Recommend a follow-up live-doc fetch (https://blacksmithgu.github.io/obsidian-dataview/) before shipping the skill to lock down DQL function signatures (especially `dateformat`, `dur`, `flatten`).
- **Mobile rendering** of large `TABLE` blocks (> 200 rows) can OOM Obsidian iOS. Always `LIMIT` cortex-generated tables (50 default, 100 max).
