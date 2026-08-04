from __future__ import annotations

import re

from skeinlib.hooks import cmd_report

ISSUE_URL = "https://github.com/lazygophers/ccplugin/issues/new"
OURS = ("skein.py", "spec.py", "CLAUDE_PLUGIN_ROOT")
BIN_RE = re.compile(r"(?:^|[\s;&|(])(?:skein-spec|skein)(?:\s|$)")
TRACEBACK_MARK = "Traceback (most recent call last)"

_TRACEBACK_MARK = TRACEBACK_MARK
