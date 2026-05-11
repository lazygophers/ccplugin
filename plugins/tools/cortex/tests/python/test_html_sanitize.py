"""Tests for hooks/_lib/html_sanitize.py."""
from __future__ import annotations

import subprocess
import sys
import unittest

from _helpers import PLUGIN_ROOT, add_paths

add_paths()

from html_sanitize import sanitize  # noqa: E402

MODULE = PLUGIN_ROOT / "hooks" / "_lib" / "html_sanitize.py"


class SanitizeBlockTest(unittest.TestCase):
    """拦截向量。"""

    def test_script_tag_removed(self) -> None:
        out = sanitize("before <script>alert(1)</script> after")
        self.assertNotIn("<script", out.lower())
        self.assertNotIn("alert(1)", out)
        self.assertIn("before", out)
        self.assertIn("after", out)

    def test_iframe_tag_removed(self) -> None:
        out = sanitize("x <iframe src='evil'></iframe> y")
        self.assertNotIn("<iframe", out.lower())
        self.assertIn("x", out)
        self.assertIn("y", out)

    def test_onerror_attr_stripped(self) -> None:
        out = sanitize('<img src="a.png" onerror="alert(1)" alt="x">')
        self.assertNotIn("onerror", out.lower())
        self.assertNotIn("alert(1)", out)
        self.assertIn("src=", out)

    def test_javascript_protocol_neutralized(self) -> None:
        out = sanitize('<a href="javascript:alert(1)">click</a>')
        self.assertNotIn("javascript:", out.lower())
        self.assertTrue('href="#' in out or "href='#" in out, out)

    def test_data_text_html_protocol_neutralized(self) -> None:
        out = sanitize('<a href="data:text/html,<script>alert(1)</script>">x</a>')
        self.assertNotIn("data:text/html", out.lower())

    def test_object_embed_removed(self) -> None:
        out = sanitize("<object data='evil.swf'></object><embed src='x.swf'>")
        self.assertNotIn("<object", out.lower())
        self.assertNotIn("<embed", out.lower())


class SanitizePreserveTest(unittest.TestCase):
    """合法 markdown 保留。"""

    def test_table_preserved(self) -> None:
        md = "| a | b |\n|---|---|\n| 1 | 2 |"
        self.assertEqual(sanitize(md), md)

    def test_wikilink_preserved(self) -> None:
        md = "see [[some/page]] and [[other|alias]] for refs"
        self.assertEqual(sanitize(md), md)

    def test_fenced_code_block_preserved(self) -> None:
        md = (
            "intro\n\n"
            "```html\n"
            "<script>alert(1)</script>\n"
            "<iframe src='x'></iframe>\n"
            "```\n\n"
            "outro <script>bad()</script> end"
        )
        out = sanitize(md)
        # fence 内字面量保留
        self.assertIn("<script>alert(1)</script>", out)
        self.assertIn("<iframe src='x'></iframe>", out)
        # fence 外被剥
        self.assertNotIn("bad()", out)
        self.assertIn("outro", out)
        self.assertIn("end", out)

    def test_callout_preserved(self) -> None:
        md = "> [!info]\n> hello world"
        self.assertEqual(sanitize(md), md)

    def test_empty_input(self) -> None:
        self.assertEqual(sanitize(""), "")

    def test_idempotent(self) -> None:
        md = '<script>x</script><a href="javascript:y">z</a>'
        once = sanitize(md)
        twice = sanitize(once)
        self.assertEqual(once, twice)


class CLITest(unittest.TestCase):
    def test_cli_stdin_stdout(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(MODULE)],
            input="hi <script>x</script> bye",
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertNotIn("<script", proc.stdout.lower())
        self.assertIn("hi", proc.stdout)
        self.assertIn("bye", proc.stdout)


if __name__ == "__main__":
    unittest.main()
