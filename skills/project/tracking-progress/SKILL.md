---
name: tracking-progress
description: 扫描当前项目 `.scratch` 目录下的 spec、票面和 checkpoint 清单，生成一张任务进度网页。用户想知道手上有哪些活、做到哪了、现在能开工的是哪张票，或说「进度」「看一下状态」「还剩什么」时使用。
---

Run the script. It does the whole job — scan, analyse, render.

```bash
python3 skills/project/tracking-progress/scripts/tracking_progress.py
```

It writes `.scratch/progress.html` and prints the path. Single self-contained file: no network, no dependencies, opens from `file://` (a flowchart-only mermaid build, `scripts/mermaid.flow.min.js`, is inlined — the page weighs about 1 MB). The page is the entry directory to `.scratch/`: hash-routed views (`#/overview`, `#/now`, `#/specs`, `#/spec-<名>`, `#/memory`, `#/research`, `#/unknown`) driven by a sidebar (工作台 / 功能台 per spec / 档案库) plus top tabs — each tab/menu item is its own page, browser back/forward works. Renders light (晨雾) by default; the 深色 button (top-right) switches to dark and the choice is remembered via localStorage. Pass a repo root as the first argument to scan a different project.

The page includes per-spec dependency diagrams (mermaid, colours follow the theme), and every spec name / ticket id has a copy-icon button next to it — ticket ids copy as `spec#id`. There is no 未能识别 bucket: a top-level `.scratch/<name>.md` that parses to no tasks becomes a **single-file feature** (own view, `单文件` badge); non-task files inside a feature dir (`design.md`, `brief.md`, …) become its 附件 chips, `design-demos/` (or `demos/`, `设计样例/`) is semantically recognised as a **设计样例** section: every file in it gets a gallery card in the feature view (same-stem `.png` screenshots become card thumbnails), not a generic asset chip. Every html file in a 设计样例 dir renders a **live iframe preview** as its card face (lazy-loaded, scaled to the card). Other common asset dirs (non-issues/impl/research) are listed as **expandable** entries (`<details>` open by default; subdirectories nest recursively, one `<details>` per level showing its recursive file count, files as leaves), and every remaining non-md file in the feature dir (html/png/csv screenshots etc., system junk like `.DS_Store` excluded) shows as a chip in the bottom 附件 filebox — nothing invisible. Files already listed inside an asset-dir tree are **not repeated** as filebox chips (dedup by path; only top-level loose files stay outside). In the 可开工/停滞/最近 tables the first column is the **feature** (`.scratch/<feature>/` unit — spec.md and wayfinder map are both kinds of content inside it), and the feature name links to its detail view `#/spec-<名>`. The `wayfinder 地图` / `spec` / `单文件` badges next to it are **plain labels, not clickable**; the docs live in a docbar row right under the spec head, labelled with the md's extracted h1 title (`标题（文件名）`). Clicking a docbar / filebox / ticket-title link opens a **centered in-page modal** (`#pvWrap`): md renders as formatted markdown, csv/tsv as a table, json pretty-printed with basic highlighting, yaml with basic highlighting — parse failures fall back to raw text; html design docs render in a sandboxed `iframe` (`srcdoc`); images of any known extension (png/jpg/gif/svg/webp/bmp/ico/avif) inline as base64 data URIs; any other text file (utf-8 decodable, no NUL byte in the first 8 KB) shows its raw text in a monospace pre with horizontal scroll; undecodable binary files are not in the modal channel. The 2 MB inline budget covers md/text; html docs and images carry their own separate budgets (0.6 MB / 1.4 MB of file bytes, filled smallest-file-first so one big file cannot starve the rest). Files over any budget are not in the modal channel: they open in a real new tab, marked with `↗`. The top search box filters table rows as you type (⌘K focuses it).

Then:

1. Open the HTML: `open .scratch/progress.html`.
2. Report the headline (the page leads with a one-sentence conclusion) and the 现在能开工的 table. Link the HTML as `[任务进度](.scratch/progress.html)`.
3. Open the page's 未能识别的文件 section if it is non-empty. For each file, decide whether it actually holds tasks. If any does, the script is missing a convention — ask the user whether to file an issue at `.scratch/tracking-progress/issues/` describing the unrecognised format, then add the rule to the script. (The script prints only the output path; the count, if any, lives on the page.)

## What it recognises

| Where tasks live | How status is read |
| --- | --- |
| `<feature>/issues/NN-slug.md`, `<feature>/impl/NN-slug.md`, `<feature>/NN-slug.md` | `Status:` / `状态：` line, bare or bold |
| `issues/open/` vs `issues/done/` | the directory name |
| ticket file with `Blocked by:` / `Type:` but no status | open (nobody marked it done) |
| `memory.md` checkpoint rows | `- [x]` done, `- [ ]` open, `- [~]` / `- [-]` in progress |
| wayfinder `map.md` + its children | `Status: claimed` / `resolved`, `Blocked by: NN` |

`memory/` and the top-level `research/` are never scanned for tasks — they are history, not work in flight. The 决策档案 (`#/memory`) view renders the ledger as 变更审计流: day stubs with counts only; clicking a day parses that day's text on demand from the inlined `tp-files` JSON (canonical `- 改成: … | 原本 | 我说 | 为什么 | 否掉了` lines become diff cards, everything else stays as verbatim 原文 blocks — nothing hidden, nothing dropped). Decision content is never written into the HTML at generation time, so page size and DOM stay bounded. A feature-level `<feature>/research/*.md` is listed under its feature with links (in-page modal, same `#pvWrap` channel), status-free.

Status strings are matched loosely: `resolved` / `done` / `已完成` / `定稿` all count as done, `claimed` / `in-progress` / `进行中` as in progress, everything else as open. A negated status (`未完成`, `无法完成`, `not done`, `unresolved`) counts as open, not done — the negation prefix cancels the keyword hit.

## What the page says (and how to read odd bits)

- **Blocking only counts ids that exist.** A `Blocked by:` referencing a number no ticket owns (often a document reference like `ADR-0046` minted into an id) is shown as a dangling ref, not treated as a blocker.
- **互相阻塞的票** (A blocks B, B blocks A) are drawn with dashed amber edges in the wave diagram — someone has to break the loop by hand.
- **未建票 vs 票已建齐**: a map/checklist row with no ticket file behind it is marked 未建 (badge on the spec head, mark on the row, dashed node in the graph, count in the per-spec table). A spec where every row has a ticket file gets the 票已建齐 badge.
- **口径写在页面上**: progress = done ÷ total, blockers in the denominator; one ticket = one ticket file or one `memory.md` checklist row, so "done" can include process notes like 「写 spec.md」. The page states this instead of hiding it.
