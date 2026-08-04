from __future__ import annotations

import re

from skeinlib.hooks import cmd_spec_meta, parse_spec_frontmatter

SPEC_RE = re.compile(r"(?:^|/)\.skein/spec/[^/]+/[^/]+/.+\.md$")
SPEC_REQUIRED = ("title", "namespace", "inclusion", "keywords")
SPEC_INCLUSIONS = ("always", "auto", "fileMatch", "manual")
_parse_fm = parse_spec_frontmatter

__all__ = ["SPEC_RE", "SPEC_REQUIRED", "SPEC_INCLUSIONS", "cmd_spec_meta", "_parse_fm"]
