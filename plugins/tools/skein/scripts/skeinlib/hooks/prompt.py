from __future__ import annotations

from skeinlib.hooks import cmd_user_prompt, run_config

_EXPLICIT = ("go", "exec", "do", "plan", "继续", "continue")
_EXPLICIT_PREFIX = ("/skein-", "/skein:skein-", "skein-")
_run_config = run_config
