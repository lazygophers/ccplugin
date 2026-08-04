from __future__ import annotations

from skeinlib.hooks import git_root, load_stdin

BLOCKED = {"task.json", "task.md", "prd.md"}
ENGINE = ("skein.py", "spec.py", "skein ", "skein-spec ")
