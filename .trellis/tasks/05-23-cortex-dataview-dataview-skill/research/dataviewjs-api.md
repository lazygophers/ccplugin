# Research: Obsidian DataviewJS API — Reference + Cookbook

- **Query**: DataviewJS API reference for AI agents constructing scripts (cortex-dataview skill)
- **Scope**: external (Obsidian Dataview plugin official docs + community patterns)
- **Date**: 2026-05-23
- **Primary sources**:
  - https://blacksmithgu.github.io/obsidian-dataview/api/intro/
  - https://blacksmithgu.github.io/obsidian-dataview/api/code-reference/
  - https://blacksmithgu.github.io/obsidian-dataview/api/data-array/
  - https://blacksmithgu.github.io/obsidian-dataview/api/code-examples/
  - https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-pages/

> Asynchronous API calls are marked with ⌛ — they MUST be `await`-ed.

---

## 0. Codeblock Modes (very important — pick the right fence)

| Fence | Engine | Use for |
|---|---|---|
| ```` ```dataview ```` | DQL (Dataview Query Language) | Pure declarative TABLE / LIST / TASK / CALENDAR queries. No JS. |
| ```` ```dataviewjs ```` | DataviewJS (this doc) | Anything involving loops, conditionals, async, custom rendering, file I/O. `dv` is implicit. |
| `` `= expr` `` | Inline DQL | Single-value inline expression rendered in flowing text. |
| `` `$= jsExpr` `` | Inline DataviewJS | Single JS expression rendered inline. `dv` is available. Example: `` `$= dv.current().file.mtime` ``. |
| ```` ```js ```` | Plain markdown JS | NOT executed by Dataview. Will just be highlighted as JS source. |

Rule of thumb: prefer DQL when the query is fully declarative. Drop to DataviewJS the moment you need:
- nested loops over groups,
- conditional rendering,
- calling `await dv.io.*` / `await dv.query()`,
- merging data from multiple sources,
- custom row HTML.

---

## 1. Entry Points — the `dv` object

`dv` (alias `dataview`) is auto-injected into every `dataviewjs` block.

| Call | Returns | Notes |
|---|---|---|
| `dv.current()` | page object | Shortcut for `dv.page(currentPath)`. The page the script is rendering inside. |
| `dv.pages(source)` | `DataArray<Page>` | `source` is a DQL source string. See source syntax below. |
| `dv.pagePaths(source)` | `DataArray<string>` | Just paths, no metadata load. |
| `dv.page(path)` | `Page \| undefined` | Resolves a link/path to a single page. Extension optional. |
| `dv.query(src, [file, settings])` ⌛ | `Result<QueryResult>` | Run a DQL query; returns `{successful, value}` or `{successful:false, error}`. |
| `dv.tryQuery(src, [file, settings])` ⌛ | `QueryResult` | Throws on error. Convenient for short scripts. |
| `dv.queryMarkdown(src, ...)` ⌛ | `Result<{value: string}>` | Same as `dv.query` but the value is rendered Markdown. |
| `dv.tryQueryMarkdown(...)` ⌛ | string | Throws version. |
| `dv.evaluate(expr, [ctx])` | `Result<value>` | Run a DQL expression like `2+2`, `length(this.file.tasks)`. |
| `dv.tryEvaluate(expr, [ctx])` | value | Throws version. |
| `dv.execute(dqlSrc)` | void | Render an embedded DQL query inline. |
| `dv.executeJs(jsSrc)` | void | Render an embedded DataviewJS block inline. |

**No public `dv.index` API** — there is no documented `dv.index` property in the codeblock reference. To access the raw index from a plugin (not a codeblock), use `app.plugins.plugins.dataview.api` or `app.plugins.plugins.dataview.index`. Inside dataviewjs blocks, stay with `dv.pages()` etc.

### Source string syntax (passed to `dv.pages()`, `dv.pagePaths()`, DQL `FROM`)

```
dv.pages()                       // all pages in vault
dv.pages("#books")               // tag
dv.pages("#books and #fiction")  // boolean AND
dv.pages("#yes or -#no")         // OR, with negation via leading -
dv.pages('"folder"')             // FOLDER — must be inside double quotes
dv.pages('"folder" or #tag')     // mixed
dv.pages('[[Some Page]]')        // pages that link TO Some Page
dv.pages('outgoing([[Some Page]])') // pages linked FROM Some Page
dv.pages("")                     // same as dv.pages() — all pages
```

Gotcha: folder names need the literal `'"folder"'` (single-quoted JS string containing double-quoted folder path).

---

## 2. Page Object Shape

Every page object exposes:
- All user fields (frontmatter + `key:: inline` syntax) directly at top level: `p.rating`, `p.genre`, `p["time-read"]` (use bracket notation for keys with spaces, dashes, etc.).
- `p.file` — implicit fields:

| Field | Type | Description |
|---|---|---|
| `file.name` | string | filename (no extension) |
| `file.folder` | string | containing folder path |
| `file.path` | string | full vault path including extension |
| `file.ext` | string | usually `md` |
| `file.link` | Link | renderable link object |
| `file.size` | number | bytes |
| `file.ctime` | DateTime | created (Luxon) |
| `file.cday` | Date | created (date only) |
| `file.mtime` | DateTime | last modified |
| `file.mday` | Date | last modified (date only) |
| `file.tags` | List<string> | EXPLODED tags: `#a/b/c` → `[#a, #a/b, #a/b/c]` |
| `file.etags` | List<string> | exact tags: `[#a/b/c]` |
| `file.inlinks` | List<Link> | backlinks |
| `file.outlinks` | List<Link> | links this file makes |
| `file.aliases` | List<string> | frontmatter aliases |
| `file.tasks` | List<Task> | every `- [ ]` / `- [x]` |
| `file.lists` | List<ListItem> | all list items (includes tasks) |
| `file.frontmatter` | object | raw frontmatter map |
| `file.day` | Date | parsed from filename (`yyyy-mm-dd`) or `Date` field |
| `file.starred` | boolean | bookmarked via core Bookmarks plugin |

Task object fields (commonly used): `text`, `completed`, `fullyCompleted`, `status`, `checked`, `line`, `path`, `section`, `link`, `tags`, `subtasks`, `due`, `completion`, `scheduled`, `start`, `created`.

---

## 3. Render API

All render calls append to the rendered output of the codeblock.

| Call | Effect |
|---|---|
| `dv.header(level, text)` | h1–h6 header |
| `dv.paragraph(text)` | `<p>` block |
| `dv.span(text)` | inline `<span>` (no vertical padding) |
| `dv.el(tag, text, {cls, attr})` | arbitrary element with classes & attrs |
| `dv.list(items)` | bullet list; items can be strings, links, or Markdown |
| `dv.taskList(tasks, groupByFile=true)` | interactive task list (checkable). Pass `false` to flatten across files. |
| `dv.table(headers, rows)` | Markdown table. `headers` = `string[]`. `rows` = `any[][]`. A cell that is itself an array is rendered as a bullet list inside the cell. |
| `dv.execute(dql)` | embed DQL result |
| `dv.executeJs(js)` | embed JS result |
| `dv.view(path, input)` ⌛ | load `path.js` (or `path/view.js` + optional `view.css`) and run with `{dv, input}`. **Must `await`.** Path is from vault root. Cannot live in dot-folders like `.views`. |

### Markdown-as-string variants (for composing larger documents)

| Call | Returns |
|---|---|
| `dv.markdownTable(headers, rows)` | string |
| `dv.markdownList(items)` | string |
| `dv.markdownTaskList(tasks)` | string |

Then pass through `dv.paragraph(md)` or concatenate before rendering.

---

## 4. DataArray — chainable query operators

`dv.pages()` returns a **DataArray**, NOT a vanilla `Array`. It is immutable — every transformation returns a new array. It supports normal indexing (`arr[0]`), `for..of`, AND **swizzling**.

### Swizzling
Indexing a DataArray with a field name maps that field over every element and flattens one level:
```js
dv.pages("#book").file.name        // DataArray<string>
dv.pages("#book").file.tasks       // flattened DataArray<Task>
dv.pages("#book").genres           // flattened DataArray<string>
```

### Full operator list

| Method | Purpose |
|---|---|
| `.where(fn)` / `.filter(fn)` | predicate filter |
| `.map(fn)` | transform |
| `.flatMap(fn)` | map + flatten |
| `.mutate(fn)` | in-place mutate (rare; prefer map) |
| `.sort(keyFn, "asc"\|"desc", comparator?)` | stable sort by key |
| `.groupBy(keyFn, comparator?)` | returns `DataArray<{key, rows: DataArray}>` |
| `.distinct(keyFn?, comparator?)` | dedupe |
| `.limit(n)` | first n |
| `.slice(start?, end?)` | slice |
| `.concat(iter)` | concat |
| `.find(fn)` / `.findIndex(fn)` | scan |
| `.indexOf(el, from?)` / `.includes(el)` | lookup |
| `.first()` / `.last()` | endpoints (undefined if empty) |
| `.every(fn)` / `.some(fn)` / `.none(fn)` | quantifiers |
| `.forEach(fn)` | iterate |
| `.join(sep=", ")` | stringify |
| `.to(key)` | swizzle method form |
| `.expand(key)` | recursive flatten (e.g. tasks → subtasks tree) |
| `.sum()` / `.avg()` / `.min()` / `.max()` | numeric reductions |
| `.array()` | back to plain `T[]` |
| `.length` | size |

Comparator note: pass `dv.compare` as fallback when writing custom comparators.

---

## 5. File I/O — `dv.io.*` (all ⌛)

| Call | Returns |
|---|---|
| `await dv.io.load(path, [origin])` | string contents or `undefined` if missing |
| `await dv.io.csv(path, [origin])` | `DataArray<object>` — one object per CSV row, keyed by column header |
| `dv.io.normalize(path, [origin])` | absolute vault path; sync |

Relative paths resolve from `origin` (defaulting to the current file). Always `await` the first two.

---

## 6. Date / Duration / Link helpers

```js
dv.date("2026-05-22")              // Luxon DateTime
dv.date(dv.fileLink("2026-05-22")) // also works on links
dv.duration("8 minutes")           // Luxon Duration
dv.duration("9 hours, 2 minutes, 3 seconds")

dv.fileLink("Index")                          // [[Index]]
dv.fileLink("book/X", true)                   // ![[book/X]] (embed)
dv.fileLink("Test", false, "Display")         // [[Test|Display]]
dv.sectionLink("Index", "Books")              // [[Index#Books]]
dv.sectionLink("Index", "Books", false, "My") // [[Index#Books|My]]
dv.blockLink("Notes", "12gdhjg3")             // [[Notes#^12gdhjg3]]

dv.parse("[[A]]")        // Link
dv.parse("2026-05-22")   // DateTime
dv.parse("9 seconds")    // Duration

dv.compare(a, b)         // -1/0/1 per DV rules
dv.equal(a, b)           // boolean
dv.clone(v)              // deep clone (handles links/dates)
dv.isArray(v)            // true for arrays & DataArrays
dv.array(v)              // wrap into DataArray
```

Luxon DateTime formatting (common idioms):
```js
const d = dv.current().file.mtime;
d.toFormat("yyyy-MM-dd HH:mm");   // "2026-05-23 14:05"
d.toISODate();                    // "2026-05-23"
d.diff(dv.date("2026-01-01"), "days").days;  // numeric day delta
```

---

## 7. DQL vs DataviewJS — when to use which

| Need | Pick |
|---|---|
| Simple TABLE/LIST with WHERE/SORT/GROUP BY | DQL — shorter, declarative |
| One-liner inline value | `` `= ...` `` inline DQL |
| Aggregation across grouped data with per-group rendering | DataviewJS (`for (const g of …groupBy(…)) { dv.header(…); dv.table(…); }`) |
| Reading external file (.md/.csv) | DataviewJS (`dv.io.load` / `dv.io.csv`) |
| Conditional UI (hide section if empty, show counter banner) | DataviewJS |
| Reusable view across many notes | DataviewJS + `dv.view("scripts/foo", input)` |
| Calling another DQL programmatically | DataviewJS + `await dv.query(...)` |
| Single inline JS value | `` `$= expression` `` |

A pragmatic recipe: PROTOTYPE in DQL → if you hit a wall, port to DataviewJS by wrapping in `dv.executeJs` body.

---

## 8. Gotchas

1. **Async loops**: `for (const p of pages) await dv.io.load(p.file.path)` works fine. But `pages.map(async p => await dv.io.load(...))` returns a DataArray of Promises — you must `await Promise.all(...)`. Easier: stick to `for..of` with sequential `await`.
2. **Folder source quoting**: `dv.pages("myFolder")` is interpreted as a TAG/keyword (and returns nothing). Use `dv.pages('"myFolder"')`.
3. **Tag matching**: `file.tags` includes parent prefixes (`#a/b` → `[#a, #a/b]`). Match exact with `file.etags`.
4. **`dv.current()` in templates**: when DataviewJS is invoked from a templating engine (Templater) BEFORE the file is committed, `dv.current()` can be `undefined`. Resolve via `dv.page(tp.file.path)` instead.
5. **`dv.view()` path rules**: vault-root relative, no leading dot-folder. `.views/foo` throws "custom view not found".
6. **`js` codeblock ≠ `dataviewjs`**: a `js` fence is rendered as a code listing, NOT executed. Only `dataviewjs` runs.
7. **DataArray ≠ Array**: methods like `.reduce` / `.includes` exist but `.reduceRight` / spread quirks differ. Convert via `.array()` if you need full ECMAScript Array semantics.
8. **Mutation**: `where`, `map`, `sort` all return new arrays. `.mutate` is the only in-place op.
9. **Lookup performance**: calling `dv.page(path)` thousands of times in a tight loop is O(N). Prefer building a Map once: `const byPath = new Map(dv.pages().map(p => [p.file.path, p]));`.
10. **`dv.pages()` is index-time, not live**: results reflect the index when the script runs. After heavy bulk edits, allow re-index (or call `app.plugins.plugins.dataview.api.index.touch()` from a plugin context).
11. **Inline `$=` is sync only**: cannot `await` inside inline DataviewJS expressions. Use a fenced block for async.
12. **Render order**: every `dv.header/list/table/...` call appends in source order. Build up structure top-down; no virtual-DOM diffing.
13. **Result wrapping**: `dv.query` returns `{successful, value}` — accessing `.value` when `successful===false` is `undefined`. Use `dv.tryQuery` for short scripts.
14. **Empty source**: `dv.pages("")` is equivalent to "all pages" — useful when source is a dynamic variable; guard against accidentally scanning the entire vault.

---

## 9. Cookbook Recipes (full working blocks)

Each block below is a complete, paste-into-Obsidian DataviewJS recipe.

### Recipe 1 — Project dashboard grouped by status

```dataviewjs
const projects = dv.pages('"projects"').where(p => p.type === "project");

for (const group of projects.groupBy(p => p.status ?? "no-status")
                            .sort(g => g.key, "asc")) {
  dv.header(3, `${group.key}  (${group.rows.length})`);
  dv.table(
    ["Project", "Owner", "Due", "Progress"],
    group.rows
      .sort(p => p.due, "asc")
      .map(p => [
        p.file.link,
        p.owner ?? "—",
        p.due ? dv.date(p.due).toFormat("yyyy-MM-dd") : "—",
        p.progress != null ? `${Math.round(p.progress * 100)}%` : "—",
      ])
  );
}
```

### Recipe 2 — Journal aggregation (last 7 daily notes)

```dataviewjs
const today = dv.date("today");
const days = dv.pages('"journal"')
  .where(p => p.file.day && today.diff(p.file.day, "days").days <= 7)
  .sort(p => p.file.day, "desc");

dv.header(2, "This week");
for (const d of days) {
  dv.header(4, d.file.day.toFormat("EEEE, yyyy-MM-dd"));
  const open = d.file.tasks.where(t => !t.completed);
  if (open.length) dv.taskList(open, false);
  else dv.paragraph("_No open tasks._");
}
```

### Recipe 3 — Kanban from frontmatter status

```dataviewjs
const cols = ["todo", "doing", "done"];
const cards = dv.pages("#card");

const grid = cols.map(col => [
  `**${col.toUpperCase()}**`,
  cards.where(c => (c.status ?? "todo") === col)
       .sort(c => c.priority ?? 99)
       .map(c => c.file.link),
]);

// Render as 3-column table; array cells become bullet lists.
dv.table(cols.map(c => c.toUpperCase()),
         [cols.map(col =>
            cards.where(c => (c.status ?? "todo") === col)
                 .sort(c => c.priority ?? 99)
                 .map(c => c.file.link).array())]);
```

### Recipe 4 — Tag heatmap (count per tag, sorted)

```dataviewjs
const counts = new Map();
for (const p of dv.pages()) {
  for (const t of p.file.etags) {
    counts.set(t, (counts.get(t) ?? 0) + 1);
  }
}
const rows = dv.array(Array.from(counts.entries()))
  .sort(r => r[1], "desc")
  .limit(30)
  .map(([tag, n]) => [tag, n, "▇".repeat(Math.min(n, 40))]);

dv.table(["Tag", "Count", "Heat"], rows);
```

### Recipe 5 — Task rollup across a folder, grouped by due-week

```dataviewjs
const tasks = dv.pages('"areas"').file.tasks
  .where(t => !t.completed && t.due);

const byWeek = tasks.groupBy(t => dv.date(t.due).toFormat("kkkk-'W'WW"))
                    .sort(g => g.key, "asc");

for (const w of byWeek) {
  dv.header(4, `Week ${w.key}  (${w.rows.length})`);
  dv.taskList(w.rows, false);
}
```

### Recipe 6 — Backlink graph BFS (all directly or indirectly linked notes)

```dataviewjs
const start = dv.current().file.path;
const seen  = new Set();
const stack = [start];

while (stack.length) {
  const path = stack.pop();
  const meta = dv.page(path);
  if (!meta) continue;
  for (const lnk of meta.file.inlinks.concat(meta.file.outlinks).array()) {
    if (seen.has(lnk.path)) continue;
    seen.add(lnk.path);
    stack.push(lnk.path);
  }
}

const linked = dv.array(Array.from(seen)).map(p => dv.page(p)).where(p => p);
dv.header(3, `Network of ${linked.length} notes`);
dv.list(linked.sort(p => p.file.mtime, "desc").map(p => p.file.link));
```

### Recipe 7 — Read a CSV and render as table

```dataviewjs
const rows = await dv.io.csv("data/expenses.csv");
if (!rows) { dv.paragraph("⚠ expenses.csv not found"); return; }

const headers = Object.keys(rows[0]);
const total = rows.map(r => Number(r.amount) || 0).sum();

dv.header(3, `Expenses — total ${total.toFixed(2)}`);
dv.table(headers,
  rows.sort(r => r.date, "desc")
      .map(r => headers.map(h => r[h])));
```

### Recipe 8 — Programmatic DQL with `dv.tryQuery`

```dataviewjs
const result = await dv.tryQuery(`
  TABLE WITHOUT ID file.link AS "Note", rating
  FROM #book
  WHERE rating >= 8
  SORT rating DESC
  LIMIT 10
`);
// result.type === "table", result.headers, result.values (2D array)
dv.table(result.headers, result.values);
```

### Recipe 9 — Reusable view (`views/recent/view.js`)

```js
// views/recent/view.js — invoked via: await dv.view("views/recent", { tag: "#blog", n: 5 })
const { tag, n = 10 } = input;
const pages = dv.pages(tag).sort(p => p.file.mtime, "desc").limit(n);
dv.header(4, `Latest ${n} ${tag}`);
dv.list(pages.map(p => `${p.file.link}  _(${p.file.mtime.toFormat("yyyy-MM-dd")})_`));
```

Calling page:
```dataviewjs
await dv.view("views/recent", { tag: "#blog", n: 5 });
```

---

## 10. Inline DataviewJS examples

```
Last modified: `$= dv.current().file.mtime.toFormat("yyyy-MM-dd HH:mm")`
Open tasks: `$= dv.current().file.tasks.where(t => !t.completed).length`
Linked notes: `$= dv.current().file.outlinks.length`
```

Inline DQL counterparts (often shorter):
```
Last modified: `= this.file.mtime`
Open tasks: `= length(filter(this.file.tasks, (t) => !t.completed))`
```

---

## 11. Quick mental model for an AI writing DataviewJS

1. **Pick fence**: `dataviewjs` (multi-line, async) vs `$=` (single inline expr) vs `dataview` (pure DQL).
2. **Get the source set**: `dv.pages(<source>)` — remember folder quoting.
3. **Shape it**: chain `.where → .sort → .groupBy → .limit → .map`. Stay in DataArray; only `.array()` at boundaries.
4. **Render**: pick ONE of `dv.list / dv.table / dv.taskList / dv.paragraph / dv.header`. For tables, build `rows` as `array.map(p => [col1, col2, ...])`.
5. **Async-aware**: `await` every call marked ⌛ (`io.load`, `io.csv`, `query`, `tryQuery`, `view`).
6. **Empty-safe**: guard `dv.io.load` / `dv.page` returning `undefined`, guard `.first()` / `.last()` returning `undefined`.
7. **Field access**: prefer dot for clean keys (`p.rating`), bracket for dashes/spaces (`p["time-read"]`). Implicit fields live under `p.file.*`.

---

## Caveats / Not Found

- `dv.index` is NOT a documented codeblock API surface. Only the plugin-facing `app.plugins.plugins.dataview.index` exists. The task prompt mentioned `dv.index` — flag this if surfaced in skill docs; recommend `dv.pages()` / `dv.page()` instead.
- The `queries/expressions/` page on the docs site returned 404 at scrape time (2026-05-23). DQL expression syntax was inferred from `dv.evaluate` examples in the API reference rather than a dedicated page.
- The data-array TypeScript interface uses generics; the scraped HTML lost the `<T>` brackets in places. Treat the interface in §4 as semantically correct but consult the source `data-array.ts` in the dataview repo for exact type params.
- "Inline JS expressions" (`$=`) and "inline DQL" (`=`) are documented but spread across multiple pages; behavior described here was cross-checked against the inline-queries page (not scraped here — flag if precise syntax matters).
- Performance notes (lookup, async loops) are best-practice guidance from the data-array doc + community wisdom, not a formal "performance" doc page.
