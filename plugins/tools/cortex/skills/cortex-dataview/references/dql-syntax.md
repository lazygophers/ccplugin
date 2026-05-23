# Research: Obsidian Dataview DQL Syntax Reference

- **Query**: Full DQL reference for `cortex-dataview` skill
- **Scope**: external (official docs)
- **Date**: 2026-05-23
- **Primary sources**:
  - https://github.com/blacksmithgu/obsidian-dataview/tree/master/docs/docs
  - Specifically: `queries/structure.md`, `queries/query-types.md`, `queries/data-commands.md`, `queries/differences-to-sql.md`, `reference/sources.md`, `reference/expressions.md`, `reference/functions.md`, `reference/literals.md`, `annotation/metadata-pages.md`, `annotation/metadata-tasks.md`, `resources/faq.md`

This file is the canonical DQL reference. Future agents read it and write DQL queries from here.

---

## 1. General Query Structure

Every DQL query lives inside a fenced ` ```dataview ` codeblock. Pattern:

```
<QUERY-TYPE> <fields>
FROM <source>
<DATA-COMMAND> <expression>
<DATA-COMMAND> <expression>
...
```

**Rules**

- Query Type (`LIST` | `TABLE` | `TASK` | `CALENDAR`) is the ONLY mandatory line.
- `FROM` is optional, at most ONE, must come right after Query Type.
- All other data commands (`WHERE`, `SORT`, `GROUP BY`, `FLATTEN`, `LIMIT`) are optional, can repeat, and execute **top-to-bottom**, line by line — DQL is procedural, NOT declarative SQL. Each line takes the previous result set and reshapes it.
- Inline DQL: `` `= this.field + 1` `` and `` `$= dv.current().field` `` (JS).

**Procedural consequence**: Order matters. Putting `SORT` after `LIMIT` sorts the already-limited rows. Putting `WHERE` after `GROUP BY` filters groups, not rows.

---

## 2. Query Types

### 2.1 LIST

Outputs a bullet list of file links (or group keys when grouped). At most **one** additional expression as the bullet's tail value.

```dataview
LIST                                 # all files as bullets
LIST file.folder                     # link: folder
LIST "Path: " + file.folder + " (" + file.cday + ")"   # computed string
LIST FROM #games/mobas OR #games/crpg
```

**LIST WITHOUT ID** — drops the leading file link / group key:

```dataview
LIST WITHOUT ID length(rows) + " pages of type " + key
GROUP BY type
```

With `GROUP BY`, default output shows only the group key. Pass `rows.file.link` to expand:

```dataview
LIST rows.file.link
GROUP BY type
```

### 2.2 TABLE

Tabular view, accepts a **comma-separated** list of column expressions. Use `AS "Header"` for column aliases.

```dataview
TABLE started, file.folder AS Path, file.etags AS "File Tags"
FROM #games

TABLE
  default(finished, date(today)) - started AS "Played for",
  file.folder AS Path
FROM #games
```

First column is always `File` (or `Group` when grouped) and shows the result count, e.g. `File (7)`. Hide via Dataview settings → Display result count. To rename or drop it use **TABLE WITHOUT ID**:

```dataview
TABLE WITHOUT ID file.link AS "Game", file.etags AS "Tags" FROM #games
```

Custom headers with spaces require double quotes: `AS "File Tags"`.

### 2.3 TASK

Operates at **task level**, NOT page level — i.e. every `WHERE`/`SORT` evaluates against each task. Renders interactive checkboxes; **clicking writes back to the original file** (the only DQL query type that mutates).

```dataview
TASK
WHERE !completed AND contains(tags, "#shopping")

TASK
WHERE !completed
GROUP BY file.link
```

Child tasks (indented one tab beneath an unindented task) are returned **with their parent** as long as the parent matches. A child only appears standalone when it itself matches but parent doesn't.

Implicit task fields directly accessible (no `file.tasks.` prefix needed inside `TASK` queries): `status`, `checked`, `completed`, `fullyCompleted`, `text`, `line`, `path`, `section`, `tags`, `outlinks`, `link`, `children`, `parent`, `task`, `annotated`, `blockId`, plus shorthands (`due`, `completion`, `created`, `start`, `scheduled`).

### 2.4 CALENDAR

Renders a monthly calendar dot per result. **Requires exactly one date expression**.

```dataview
CALENDAR file.ctime
CALENDAR due
WHERE typeof(due) = "date"
```

`SORT` / `GROUP BY` are accepted syntactically but **have no effect** on a calendar render. If the date field is missing or wrong type the calendar may not render — filter with `typeof(x) = "date"`.

---

## 3. Data Commands (Clauses)

### 3.1 FROM

Selects the initial page set. ZERO or ONE FROM per query, immediately after Query Type. Combine sources with `and`, `or`, `-` (negation), and `(...)`.

| Source kind | Syntax | Example |
|---|---|---|
| Tag (and subtags) | `#tag` | `FROM #status/open` |
| Folder (recursive) | `"folder/path"` | `FROM "10 Projects"` (no trailing slash) |
| Single file | `"folder/file"` or `"folder/file.md"` | `FROM "Daily/2025-01-01"` |
| Incoming links to file | `[[note]]` | `FROM [[Project A]]` → pages linking TO Project A |
| Outgoing links from file | `outgoing([[note]])` | `FROM outgoing([[Dashboard]])` → links FROM Dashboard |
| Current file (incoming) | `[[]]` or `[[#]]` | `FROM [[]]` |

Combinations:

```
FROM #tag AND "folder"
FROM #food AND -#fastfood
FROM [[Food]] OR [[Exercise]]
FROM (#assignment AND "30 School") OR ("30 School/32 Homeworks" AND outgoing([[Dashboard]]))
```

**Gotcha**: If a folder path collides with a file path, Dataview prefers the folder. Force a file by appending `.md`.

### 3.2 WHERE

Boolean filter; only rows where the expression is truthy survive. Multiple `WHERE` allowed.

```
WHERE due AND due < date(today)
WHERE typeof(due) = "date" AND due <= date(today)
WHERE !completed AND file.ctime <= date(today) - dur(1 month)
```

### 3.3 SORT

```
SORT field [ASC|ASCENDING|DESC|DESCENDING]
SORT field1 ASC, field2 DESC, ...
```

Default direction is ASC. Multi-field sort breaks ties left-to-right.

### 3.4 GROUP BY

```
GROUP BY field
GROUP BY (computed_expr) AS aliasName
```

Output rows shrink to one per unique key. The result row exposes:

- The group-key field (named after the field, or `key` when computed/aliased)
- `rows` — array of all the originally matching rows

**Field swizzling**: `rows.file.link` auto-maps to an array of links. Then aggregate with `sum()`, `length()`, `flat()`, etc.

**Critical gotcha**: After `GROUP BY` you LOSE direct access to per-row fields. The aliases/columns you defined earlier are gone — you must reach them via `rows.<field>`. Example:

```dataview
TABLE length(rows) AS Count, rows.file.link AS Files
FROM #project
GROUP BY status
```

`rows` is the only window into the underlying pages from this point on.

### 3.5 FLATTEN

Inverse of `GROUP BY`: explodes an array field into one result row per element.

```
FLATTEN field
FLATTEN (computed_expr) AS alias
```

```dataview
TABLE authors FROM #LiteratureNote
FLATTEN authors

TABLE T.text AS "Task"
FROM "Scratchpad"
FLATTEN file.tasks AS T
WHERE T.text
```

Use `FLATTEN` to turn nested data (file.tasks, multi-value fields) into simple per-row predicates rather than wrestling with `map`/`filter`.

### 3.6 LIMIT

```
LIMIT 5
```

Cuts result count. Because commands execute in order, `LIMIT 5` **before** `SORT` sorts only the first 5 received — almost always wrong. Put `SORT` first.

---

## 4. Expressions

Everything that yields a value is an expression: fields, literals, arithmetic, comparisons, function calls, lambdas.

### 4.1 Field references

- `fieldname` — direct access
- `simple-field` — fields with spaces/punctuation normalize to lowercase + dashes. `Field With Space` → `field-with-space`. `Hello!` → `hello`.
- `row["Field With Space"]` — index-style, robust to special chars / keyword collisions (`row.from`, `row.where`).
- `a.b` — object/page property access
- `a[expr]` — computed index, lists are 0-based
- `[[Page]].field` — index through a link to fetch a field on that page

Inside fields whose VALUE is a link (e.g. `Class:: [[Math]]`), `Class.timetable` follows the link. `[[Class]].timetable` does NOT — it tries to load a page literally named "Class".

### 4.2 Operators

| Category | Operators |
|---|---|
| Arithmetic | `+ - * / %` |
| Comparison | `< > <= >= = !=` |
| Boolean | `AND OR NOT` / `&& || !` |
| String | `+` concat, `"a" * 3` repeat |
| Negation in FROM | `-#tag`, `-"folder"` |

`=` is equality (NOT assignment).

### 4.3 Comparison gotchas

Comparing different types yields surprises. `null <= date(today)` is true → pages without `due` would pass `WHERE due <= date(today)`. Guards:

```
WHERE due AND due <= date(today)            # truthy check first
WHERE typeof(due) = "date" AND due <= date(today)   # safest
```

---

## 5. Literals

| Literal | Type |
|---|---|
| `0`, `1337`, `-200` | number |
| `"text"` | string |
| `true` / `false` | boolean |
| `[[Page]]`, `[[]]` (current file) | link |
| `[1, 2, 3]`, `[[1,2],[3,4]]` | list |
| `{ a: 1, b: 2 }` | object |
| `date(2021-11-11)` | date |
| `date(2021-09-20T20:17)` | datetime |
| `dur(2 days 4 hours)` | duration |

### Date shortcuts

`date(today)`, `date(now)`, `date(yesterday)`, `date(tomorrow)`, `date(sow)` start-of-week, `date(eow)`, `date(som)`, `date(eom)`, `date(soy)`, `date(eoy)`.

### Duration units (singular/plural/abbreviation all accepted)

`s|sec|second`, `m|min|minute`, `h|hr|hour`, `d|day`, `w|wk|week`, `mo|month`, `yr|year`. Combine: `dur(1 s 2 m 3 h)`, `dur(3 days 7 hours 43 seconds)`.

---

## 6. Implicit `file.*` Fields (Pages)

| Field | Type | Notes |
|---|---|---|
| `file.name` | text | basename (no extension) |
| `file.folder` | text | parent folder path |
| `file.path` | text | full path incl. name |
| `file.ext` | text | usually `md` |
| `file.link` | link | link to self |
| `file.size` | number | bytes |
| `file.ctime` | datetime | created |
| `file.cday` | date | created (no time) |
| `file.mtime` | datetime | modified |
| `file.mday` | date | modified (no time) |
| `file.tags` | list | EXPANDED — `#a/b/c` → `[#a, #a/b, #a/b/c]` |
| `file.etags` | list | EXACT tags — `[#a/b/c]` |
| `file.inlinks` | list | pages linking TO this |
| `file.outlinks` | list | links FROM this |
| `file.aliases` | list | YAML aliases |
| `file.tasks` | list | every `- [ ]` task |
| `file.lists` | list | every bullet (tasks ⊂ lists) |
| `file.frontmatter` | list | raw `key | value` pairs (debug/dynamic key listing) |
| `file.day` | date | extracted from filename `yyyy-mm-dd` / `yyyymmdd` or `Date` field |
| `file.starred` | boolean | bookmarked |

### Frontmatter access patterns

Direct: `myKey` works for most YAML keys (lowercased + dashes for special chars). `file.frontmatter.myKey` gives you the **raw** value — useful when Dataview's coercion mangles a value (e.g. you want the literal string `"2021-01-01"` instead of an auto-parsed date). For dynamic key enumeration, iterate `file.frontmatter`.

### Implicit task fields

(See section 2.3 for the full list.) Inside a `TASK` query they are top-level. Elsewhere reach them via `file.tasks` / `file.lists`:

```dataview
LIST
WHERE any(file.tasks, (t) => !t.fullyCompleted)
```

Task emoji shorthands map to fields automatically: 🗓️→due, ✅→completion, ➕→created, 🛫→start, ⏳→scheduled.

---

## 7. Functions (most useful subset)

Most functions **auto-vectorize** over lists: `lower(["YES","NO"])` → `["yes","no"]`.

### Constructors

- `object("k1", v1, ...)`, `list(v1, ...)` / `array(...)`
- `date(any)` parse string/link → date; `date(text, "yyyy-MM-dd")` Luxon-token parse
- `dur(any)`, `number(string)`, `string(any)`
- `link(path, [display])`, `embed(link)`, `elink(url, [display])`
- `typeof(any)` → `"number" | "string" | "array" | "object" | "date" | "duration" | "link" | "boolean" | "null"`

### Numeric

`round(n, [d])`, `trunc(n)`, `floor(n)`, `ceil(n)`, `min(...)`, `max(...)`, `sum(arr)`, `product(arr)`, `average(arr)`, `minby(arr, fn)`, `maxby(arr, fn)`, `reduce(arr, "+|-|*|/|&|\|")`.

### List / object / string `contains` family

| Function | Case | Behavior |
|---|---|---|
| `contains(c, v)` | sensitive | substring/element/key |
| `icontains(c, v)` | insensitive | same as contains, case-blind |
| `econtains(c, v)` | sensitive | EXACT element/key match (no substring on lists/objects) |
| `containsword(s\|list, w)` | insensitive | whole-word match |

```
contains("Hello", "lo") = true
econtains(["this","is","example"], "ex") = false
econtains(["this","is","example"], "is") = true
```

### List ops

`length(c)`, `sort(l)`, `reverse(l)`, `unique(l)`, `nonnull(l)`, `firstvalue(l)`, `all(l[, pred])`, `any(l[, pred])`, `none(l[, pred])`, `join(l, [sep])`, `filter(l, pred)`, `map(l, fn)`, `flat(l, [depth])` (often `flat(rows.file.outlinks)` after GROUP BY), `slice(l, [start[, end]])`, `extract(obj, "k1", "k2", ...)`.

### String ops

`lower`, `upper`, `replace(s, pat, repl)` (literal), `regexreplace(s, pattern, replacement)` (JS regex, supports `$1`), `regextest(pat, s)` (anywhere), `regexmatch(pat, s)` (full string), `split(s, delim, [limit])` (delim is regex), `startswith(s, pre)`, `endswith(s, suf)`, `padleft(s, n, [pad])`, `padright(...)`, `substring(s, start, [end])`, `truncate(s, n, [suffix="..."])`.

### Date / duration

- `striptime(date)` — drop time portion, equivalent to `file.cday`/`file.mday`
- `dateformat(date, "yyyy-MM-dd")` — Luxon tokens, returns **string** (cannot then be compared with `date(...)` directly — format both sides)
- `durationformat(dur, "ddd'd' hh'h' ss's'")` — tokens `S s m h d w M y`, quote literals
- `localtime(date)` — convert fixed-tz → local
- `currencyformat(n, "EUR")` — locale-aware

### Utility

- `default(field, fallback)` — vectorized; `ldefault(...)` non-vectorized version for lists
- `choice(cond, ifTrue, ifFalse)` — inline ternary
- `display(any)` — render-friendly string (preserves link display text)
- `hash(seed, [text], [variant])` — deterministic pseudo-random sort key
- `meta(link)` — exposes `.display`, `.embed`, `.path`, `.subpath`, `.type` (`"file"|"header"|"block"`)

### Lambdas

`(x) => x.field`, `(x, y) => x + y`. Used by `map`, `filter`, `all`, `any`, `none`, `minby`, `maxby`, `reduce`.

---

## 8. Aliases & Implicit Column Names

- `TABLE expr AS "Header"` — explicit alias
- Without alias, Dataview derives the column name from the expression text — fragile, prefer explicit `AS`
- `GROUP BY (expr) AS name` aliases the group key, otherwise key is named after the field or simply `key`
- `FLATTEN expr AS name` introduces `name` for subsequent commands
- **After `GROUP BY`, prior aliases vanish** — only `key` (or your `GROUP BY ... AS name`) and `rows` survive. Re-derive via `rows.<field>` or aggregate functions.

---

## 9. Sorting Direction

- `ASC` / `ASCENDING` (default)
- `DESC` / `DESCENDING`
- Multi-key: `SORT priority DESC, file.ctime ASC`
- Random/stable shuffle: `SORT hash("seed", file.name)` (use `position.start.line` extra arg for tasks where filename collides)
- Nulls sort as smaller-than-everything in ASC (so DESC pushes them to the end)

---

## 10. Common Gotchas (cheatsheet)

1. **Procedural execution**: lines run top-to-bottom. `LIMIT` before `SORT` is a bug. Multiple `WHERE` clauses are legal and stack.
2. **GROUP BY destroys per-row context**. Use `rows.<field>` afterward; aliases set before `GROUP BY` do not survive.
3. **Null comparisons are truthy with `<= / >=`** against dates/numbers. Guard with `WHERE field AND ...` or `typeof(field) = "date"`.
4. **`file.tags` vs `file.etags`**: `tags` is exploded across hierarchy (good for `contains(file.tags, "#a")` matching `#a/b`); `etags` is exact tags only.
5. **Folder paths**: no trailing slash; quotes required; case-sensitive on most platforms; folder wins over same-named file (append `.md` to force file).
6. **Link traversal**: `[[Class]].field` looks up the literal page "Class". A field that already holds a link uses `Class.field` (no brackets) to follow it.
7. **Inline DQL stored in metadata**: the stored value is the source string (`= this.x + 1`), NOT the computed result. Cannot filter against it as if it were the computed type.
8. **`dateformat` returns string**: never compare its output directly with `date(...)` — format both, or compare raw dates.
9. **Reserved-word fields** (`from`, `where`, `sort`, `group`, etc.) require `row["from"]` syntax.
10. **Fields with spaces/punctuation**: either normalize (`my field` → `my-field`) or use `row["My Field!"]`.
11. **`file.frontmatter.x` vs `x`**: direct `x` is coerced (auto-parses dates, lists, etc.); `file.frontmatter.x` is the raw YAML value, handy when coercion misbehaves.
12. **CALENDAR ignores SORT / GROUP BY** and silently breaks on non-date fields — filter with `typeof(...) = "date"`.
13. **`TASK` writes back**: clicking a checkbox in a `TASK` view edits the source file. Inform users.
14. **Subtags in FROM**: `FROM #games` matches `#games/moba` etc.; use `-` to exclude (`#games AND -#games/finished`).
15. **`regexreplace` is regex; `replace` is literal**. Don't mix.
16. **`split` delimiter is a regex** — escape special chars, or use a literal-safe alternative.
17. **`flat(rows.file.outlinks)`** is the canonical idiom for de-nesting after GROUP BY.

---

## 11. End-to-end examples

**All open shopping tasks, oldest first, capped at 20**

```dataview
TASK
WHERE !completed AND contains(tags, "#shopping")
SORT file.ctime ASC
LIMIT 20
```

**Per-project rollup with counts**

```dataview
TABLE length(rows) AS Tasks, length(filter(rows, (r) => r.completed)) AS Done
FROM #project
FLATTEN file.tasks AS t
GROUP BY file.link AS Project
SORT Tasks DESC
```

**Files due this week, grouped by status, with null-safe filter**

```dataview
TABLE due, status FROM "Work"
WHERE typeof(due) = "date" AND due >= date(sow) AND due <= date(eow)
SORT due ASC
```

**All authors across literature notes**

```dataview
TABLE authors FROM #LiteratureNote
FLATTEN authors
```

**Recent files, last 7 days**

```dataview
LIST WHERE file.mtime >= date(today) - dur(7 days)
SORT file.mtime DESC
```

**Calendar of due dates, valid only**

```dataview
CALENDAR due
WHERE typeof(due) = "date"
```

**Random daily-stable order**

```dataview
LIST FROM #inbox
SORT hash(dateformat(date(today), "yyyy-MM-dd"), file.name)
LIMIT 5
```

---

## 12. Not Covered Here (out of scope but exists)

- DataviewJS (`dataviewjs` block, full JS API: `dv.pages()`, `dv.table()`, `dv.view()`)
- Inline JS queries `` `$= ...` ``
- Settings (table primary column rename, result-count toggle, completion-date auto-write for tasks)
- CSS styling of query output

For any of these, fetch from the same docs repo under `api/` and `queries/dql-js-inline.md`.
