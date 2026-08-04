from __future__ import annotations

import re

from skeinlib.hooks import cmd_fmt

PRD_RE = re.compile(r"(?:^|/)\.skein/task/([^/]+)/prd\.md$")
