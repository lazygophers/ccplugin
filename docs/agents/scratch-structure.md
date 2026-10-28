# .scratch directory structure

The canonical layout of `.scratch/`, as fixed by the user's working spec. The tracking-progress scanner (`skills/project/tracking-progress/`) and the matt-family skills (`to-spec` / `to-tickets` / `wayfinder` / `ask-matt`) both key off these names, so treat them as frozen.

## Per-feature layout

`.scratch/<feature>/` is partitioned by concern. Directories are created on demand, never pre-created empty; files whose classification is unclear sit at the feature root until wrap-up.

Root-level fixed files (four):

- `memory.md` — task status file (checkpoints)
- `spec.md` — requirements
- `decisions.md` — decision ledger; at wrap-up its content merges into the day's `.scratch/memory/YYYY-MM-DD.md`, then the file is deleted
- `map.md` — wayfinder map; created only when wayfinder is used

Subdirectories (four):

- `issues/` — tickets laid flat as `NN-slug.md`, numbered from `01`. State lives only in each file's `Status:` line — no `open/` or `done/` subdirectories
- `research/` — comparisons, explorations, explanatory docs
- `design-demos/` — design demos only (html / png). Anything that is not a design artifact does not belong in the feature dir
- `reports/` — one-off reports

## Compatibility constraints

The following are hard-coded or special-cased in to-spec / to-tickets / wayfinder / ask-matt / tracking-progress and must not be renamed: root-level `spec.md` / `map.md` / `memory.md`, `issues/NN-slug.md`, `research/`, `design-demos/`. New subdirectories must avoid the reserved names `issues`, `impl`, `research`, `memory`, `design-demos`, `.ask-me`.

`readme.md` is tolerated for legacy reasons (existing projects use it); it stays in tracking-progress's known-files set but is not part of the canonical four.

## Wrap-up cleanup

When a feature finishes, `.scratch/` keeps only: `memory/`, `research/`, `report/<feature>/`, `progress.html` (read-only — never edited or deleted), any `<feature>/` with unresolved tickets, and in-progress task status files. Everything else is deleted without asking (conclusions merged into the day's decision file first), and the deleted paths are listed.

Two migration rules apply before deleting:

- research-type docs — comparisons, explorations, explanatory write-ups — move to `.scratch/research/` from wherever they sat (new files get Chinese names, words joined by `-`) and are kept
- one-off reports from `<feature>/reports/` move to `.scratch/report/<feature>/` (singular `report/`) and are kept

The task status file (`memory.md`) is deleted once the task ends.

## How tracking-progress renders this

- `decisions.md` is in the known-files set: previewed via the in-page modal channel, never reported as unrecognised, no dedicated section
- `<feature>/reports/` gets its own `reports` block in the feature view (file list + links + modal preview), like the `research` block
- top-level `.scratch/report/` (singular) is never scanned as a feature; its files render as a 公共报告 section in the 调研 archive view
- `design-demos/` renders gallery cards only for html + images (png/jpg/webp/svg/gif); other extensions do not get cards — the section ends with a folded 「N 个非设计文件未展示」 count
