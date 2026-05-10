# PRD: Consolidate statusline monolithic and modular dual track

## Problem

`scripts/statusline.py` (1176 LOC, monolithic) and `scripts/statusline/` (modular pkg: config, core, parser, tracker, layout, renderer, utils) coexist. Logic partially duplicated. Examples + main entry use monolith; tests cover modular pkg. Maintenance cost doubles; drift risk high.

## Goal

Pick one track (modular pkg) as source of truth. Either delete monolith entirely, or reduce it to thin compatibility shim that delegates to modular pkg.

## Scope

### Decision required

**Option A**: Replace monolith with thin shim
- `scripts/statusline.py` becomes ≤50 LOC: read stdin → call `StatuslineLoop.process()` → stdout
- Existing entry point (Neovim invocation) unchanged
- Backward compat preserved for any external caller

**Option B**: Delete monolith, use modular pkg directly
- Update Neovim integration / examples to invoke modular pkg
- Move shared utilities (git info cache, tool version detection) into modular pkg if missing

**Recommendation**: Option A first (low-risk shim), then iterate to Option B once parity confirmed.

### In-scope

Phase 1 (this task):
- Audit feature parity: list every helper/parser/cache in monolith → confirm equivalent in modular pkg
- Port missing functionality to modular pkg (git info, tool detection, formatting helpers)
- Replace `scripts/statusline.py` body with shim
- Run all `tests/statusline/` against shim entry to verify behavior unchanged

Phase 2 (follow-up task, out of scope here):
- Delete shim entirely

### Out-of-scope

- Wiring Neovim event loop (`StatuslineLoop.start()` remains stub)
- Adding new features
- Theme expansion

## Approach

1. Diff monolith vs modular: list functions present only in monolith
2. Move git info caching (`get_git_info`) to `statusline/utils/git.py` or `services/git.py`
3. Move tool detection (`ToolDetector`, `ToolVersionParser` subclasses) to `statusline/services/tools.py`
4. Move formatting helpers (`progress_bar`, `compact_int`, `shorten_path`) — verify already in `utils/formatting.py`
5. Rewrite `scripts/statusline.py` as thin entry: parse stdin → instantiate `StatuslineLoop` → process → print
6. Run `tests/statusline/` + `examples/statusline/*` to verify identical output
7. Add test fixture: feed real Claude Code statusline payload, assert output matches snapshot

## Acceptance Criteria

- `scripts/statusline.py` ≤ 100 LOC (thin shim)
- All existing tests pass on shim
- Snapshot test: known input → known output (3-line render)
- No functional regression: git info, tool versions, theme rendering identical
- Modular pkg has all helpers previously only in monolith

## Risk

- Hidden Neovim integration depending on monolith side effects (e.g., env var reads at import time)
- Performance regression if modular pkg adds overhead (subprocess timeouts, cache misses)
- Tests covering monolith may not exist; need parity snapshot first

## References

- Deep-study report: `research/statusline-architecture.md` (this task)
- `scripts/statusline.py` (monolith, 1176 LOC)
- `scripts/statusline/` (modular pkg)
- `tests/statusline/` (1666 LOC across 10 files, modular-focused)
- `examples/statusline/{basic_usage,custom_theme}.py`
