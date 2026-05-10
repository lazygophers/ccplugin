# Statusline Architecture Audit (extracted from deep-study session 2026-05-10)

## Two tracks

### Monolithic
`scripts/statusline.py` — 1176 LOC, single file.

Components:
- Parsing: `ToolVersionParser` ABC + Go/Node/Python/Rust subclasses
- Git: `get_git_info(cwd, ttl)` + caching
- Tooling: `ToolDetector` class + `detect_project_tooling()`
- Formatting helpers: `progress_bar`, `compact_int`, `shorten_path`
- `render_statusline()` (200+ LOC) builds 3 output lines
- `main()` reads stdin, calls render, prints

### Modular
`scripts/statusline/` package. Tree:
```
scripts/statusline/
├── config/
│   └── manager.py:37 (Config dataclass), :97 (get_default_config)
├── core/
│   └── loop.py:21 (StatuslineLoop)
├── parser/
│   ├── incremental.py:51 (IncrementalParser)
│   └── events.py:12 (EventType), :27 (TranscriptEvent)
├── tracker/
│   ├── aggregator.py:15 (StateDimension), :27 (AggregatedState), :52 (StateAggregator)
│   └── cache.py:13 (StateCache)
├── layout/
│   ├── base.py:13 (Layout ABC)
│   ├── factory.py:13 (LayoutFactory)
│   ├── expanded.py:21 (ExpandedLayout)
│   └── compact.py:21 (CompactLayout)
├── renderer/
│   ├── incremental.py:54 (RenderCache), :105 (IncrementalRenderer)
│   └── theme.py:25 (ThemeColors), :73 (ThemeManager)
└── utils/
    ├── formatting.py
    └── validation.py
```

## Tests

`tests/statusline/` — 1666 LOC × 10 files. Targets modular pkg only.

| Test dir | Coverage |
|----------|----------|
| test_core/test_loop.py | workflow, caching, multi-event, expiry |
| test_config/test_manager.py | Config validation, to/from_dict |
| test_layout/ | render, width calc, components |
| test_parser/ | event parsing, state transitions |
| test_renderer/ | theme load, diff, ANSI strip |
| test_utils/ | format helpers |
| test_integration/test_e2e.py | end-to-end workflow |

Conftest fixtures: sample_config, sample_event, sample_state, temp_config_file.

## Examples

`examples/statusline/`:
- `basic_usage.py` — minimal Neovim setup, USES MONOLITH
- `custom_theme.py` — theme demo, USES MONOLITH

## Docs

`docs/statusline/`:
- README.md — intro
- getting-started.md — setup
- api-reference.md — API

## Functionality gap (monolith → modular)

What's in monolith but possibly missing from modular pkg:

| Feature | Monolith location | Modular equivalent |
|---------|-------------------|---------------------|
| Git info caching | get_git_info() | unclear; check tracker/ or services/ |
| Tool version detection | ToolDetector class + parsers | unclear; possibly missing |
| Subprocess timeout (0.35s) | inline | unclear |
| File-based cache | git_info cache | unclear |
| Compact int / progress bar | helpers | utils/formatting.py — present |
| Path shortening | shorten_path | utils/formatting.py — present |

To audit: read each modular file fully, list public API, diff against monolith function list.

## Refactor strategy

### Phase 1 (this task): shim

Replace monolith body with:

```python
# scripts/statusline.py (new, ~50 LOC)
import sys, json
from statusline.config.manager import get_default_config
from statusline.core.loop import StatuslineLoop

def main():
    payload = json.loads(sys.stdin.read())
    config = get_default_config()
    loop = StatuslineLoop(config)
    output = loop.process(json.dumps(payload))
    print(output)

if __name__ == "__main__":
    main()
```

Prerequisite: confirm modular `StatuslineLoop.process()` produces equivalent output to monolith's `render_statusline()`.

### Pre-shim audit

1. Snapshot test: capture monolith output for known input
2. Run modular `loop.process()` on same input
3. Diff outputs
4. Port any missing logic to modular pkg
5. Re-test; only commit shim when outputs match exactly (or differ acceptably with documented changes)

### Phase 2 (next task): delete shim

After shim stable for ≥1 release, delete `scripts/statusline.py` entirely; update any caller (Neovim integration, examples) to call modular pkg directly:

```python
python -m statusline
# or
python scripts/statusline/__main__.py
```

Add `__main__.py` to modular pkg for direct invocation.

## Risk: hidden behavior

Monolith may have side effects at import (env reads, cache warming) not replicated in modular. Audit by comparing import-time behavior.

## Risk: Neovim integration

If Neovim invokes monolith path directly (e.g., `:set statusline=...!cat | python scripts/statusline.py`), shim path must be preserved at exact location with identical entry semantics.

## Performance considerations

- Subprocess timeouts: monolith uses 0.35s for git/tool detection. Modular tracker/services should match or document.
- Cache hits: monolith file-based for git info; modular has L1 in-memory only — may regress if invocation creates fresh process each statusline tick.
- Stdin parsing: identical JSON payload format, no schema change.

## Acceptance for shim phase

- `scripts/statusline.py` ≤ 100 LOC
- All `tests/statusline/` pass
- Snapshot test (real Claude Code statusline payload → expected 3-line output) matches monolith output
- examples/statusline/ run unchanged
