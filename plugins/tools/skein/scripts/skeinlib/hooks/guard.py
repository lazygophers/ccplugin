from __future__ import annotations

from skeinlib.hooks import cmd_guard, file_matches_globs, filematch_context, find_filematch_specs, parse_frontmatter, strip_frontmatter

GATED = {"Read", "Edit", "Write", "MultiEdit"}

_parse_frontmatter = parse_frontmatter
_strip_frontmatter = strip_frontmatter
_find_filematch_specs = find_filematch_specs
_match_file_with_globs = file_matches_globs
_inject_filematch_context = filematch_context

__all__ = ["GATED", "cmd_guard", "_parse_frontmatter", "_strip_frontmatter", "_find_filematch_specs",
           "_match_file_with_globs", "_inject_filematch_context"]
