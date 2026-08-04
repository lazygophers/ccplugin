from __future__ import annotations

from skeinlib.hooks import (DBG, Debug, HookBlocked, _prefix_lines,
                            _run_hooks, budget_guard, debug_enabled, est_tokens)

CHARS_PER_TOKEN = 4
HOOK_TIMEOUT_DEFAULT = 60
