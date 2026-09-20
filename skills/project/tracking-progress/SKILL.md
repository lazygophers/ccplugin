---
name: tracking-progress
description: 扫描当前项目 `.scratch` 目录下的 spec、票面和 checkpoint 清单，生成一张任务进度网页。用户想知道手上有哪些活、做到哪了、现在能开工的是哪张票，或说「进度」「看一下状态」「还剩什么」时使用。
---

Run the script. It does the whole job — scan, analyse, render.

```bash
python3 skills/project/tracking-progress/scripts/tracking_progress.py
```

It writes `.scratch/progress.html` and prints the path. Single self-contained file: no network, no dependencies, opens from `file://`. Pass a repo root as the first argument to scan a different project.

Then:

1. Open the HTML: `open .scratch/progress.html`.
2. Report the headline (the page leads with a one-sentence conclusion) and the 现在能开工的 table. Link the HTML as `[任务进度](.scratch/progress.html)`.
3. If stderr printed `UNPARSED=<n>`, read the 未能识别的文件 section. For each file, decide whether it actually holds tasks. If any does, the script is missing a convention — ask the user whether to file an issue at `.scratch/tracking-progress/issues/` describing the unrecognised format, then add the rule to the script.

## What it recognises

| Where tasks live | How status is read |
| --- | --- |
| `<spec>/issues/NN-slug.md`, `<spec>/impl/NN-slug.md`, `<spec>/NN-slug.md` | `Status:` / `状态：` line, bare or bold |
| `issues/open/` vs `issues/done/` | the directory name |
| ticket file with `Blocked by:` but no status | open (nobody marked it done) |
| `memory.md` checkpoint rows | `- [x]` done, `- [ ]` open, `- [~]` in progress |
| wayfinder `map.md` + its children | `Status: claimed` / `resolved`, `Blocked by: NN` |

`memory/` and `research/` are never scanned — they are history, not work in flight.

Status strings are matched loosely: `resolved` / `done` / `已完成` / `定稿` all count as done, `claimed` / `in-progress` / `进行中` as in progress, everything else as open.

## What the page says (and how to read odd bits)

- **Blocking only counts ids that exist.** A `Blocked by:` referencing a number no ticket owns (often a document reference like `ADR-0046` minted into an id) is shown as a dangling ref, not treated as a blocker.
- **互相阻塞的票** (A blocks B, B blocks A) are drawn with dashed amber edges in the wave diagram — someone has to break the loop by hand.
- **口径写在页面上**: progress = done ÷ total, blockers in the denominator; one ticket = one ticket file or one `memory.md` checklist row, so "done" can include process notes like 「写 spec.md」. The page states this instead of hiding it.
