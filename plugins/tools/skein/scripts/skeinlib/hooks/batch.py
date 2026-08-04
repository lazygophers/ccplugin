from __future__ import annotations

import re

from skeinlib.hooks import cmd_batch, is_write_command

WRITE_CMDS = ("create", "confirm", "research", "plan", "check", "finishing", "finish", "archive", "subtask",
              "sediment", "reindex", "init", "contract")
ENGINE_RE = re.compile(r"(?:skein\.py|spec\.py|\bskein\b|\bskein-spec\b)\s+([a-z-]+)")

_is_write = is_write_command
