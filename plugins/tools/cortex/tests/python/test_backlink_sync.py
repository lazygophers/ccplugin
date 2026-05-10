"""Tests for hooks/_lib/backlink_sync.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _helpers import PLUGIN_ROOT, add_paths, make_vault, write_md

add_paths()

import backlink_sync as bs  # noqa: E402

SCRIPT = PLUGIN_ROOT / "hooks" / "_lib" / "backlink_sync.py"


class StripCodeBlocksTest(unittest.TestCase):
    def test_fenced_removed(self):
        text = "before\n```py\n[[Inside]]\n```\nafter\n"
        cleaned = bs.strip_code_blocks(text)
        self.assertNotIn("Inside", cleaned)
        self.assertIn("before", cleaned)
        self.assertIn("after", cleaned)

    def test_no_fences_unchanged(self):
        text = "abc\n[[X]]\n"
        self.assertIn("[[X]]", bs.strip_code_blocks(text))


class ExtractWikilinksTest(unittest.TestCase):
    def test_simple(self):
        ts = bs.extract_wikilinks("see [[Foo]] and [[Bar|alias]]")
        self.assertEqual(ts, ["Foo", "Bar"])

    def test_with_anchor(self):
        ts = bs.extract_wikilinks("ref [[Page#section]] and [[X^bid]]")
        self.assertEqual(ts, ["Page", "X"])

    def test_transclusion_skipped(self):
        ts = bs.extract_wikilinks("![[Embed]] and [[Real]]")
        self.assertEqual(ts, ["Real"])

    def test_dot_md_stripped(self):
        ts = bs.extract_wikilinks("[[Foo.md]]")
        self.assertEqual(ts, ["Foo"])

    def test_dedup(self):
        ts = bs.extract_wikilinks("[[A]] [[A]] [[B]]")
        self.assertEqual(ts, ["A", "B"])


class ParseFrontmatterTest(unittest.TestCase):
    def test_title_aliases(self):
        text = "---\ntitle: Hello\naliases: [a, b]\n---\nbody\n"
        title, aliases = bs.parse_frontmatter_titles(text)
        self.assertEqual(title, "Hello")
        self.assertEqual(aliases, ["a", "b"])

    def test_no_frontmatter(self):
        title, aliases = bs.parse_frontmatter_titles("# H1\nbody")
        self.assertIsNone(title)
        self.assertEqual(aliases, [])


class IntegrationTest(unittest.TestCase):
    def _run(self, vault: Path, source: str, dry_run: bool = False, quiet: bool = False):
        args = [sys.executable, str(SCRIPT), "--vault", str(vault), "--source", source]
        if dry_run:
            args.append("--dry-run")
        if quiet:
            args.append("--quiet")
        return subprocess.run(args, capture_output=True, text=True, timeout=30)

    def test_happy_path_appends_backlink(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "target.md",
                     {"title": "Target"}, "# Target\n\nBody\n")
            write_md(vault / "log" / "2026-05" / "11-1430-source.md",
                     {"title": "Source"}, "# Source\n\nlinks to [[Target]]\n")
            r = self._run(vault, "log/2026-05/11-1430-source.md")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            payload = json.loads(r.stdout)
            self.assertEqual(len(payload["updated"]), 1)
            self.assertEqual(payload["missing"], [])
            target = (vault / "concepts" / "target.md").read_text(encoding="utf-8")
            self.assertIn("## Backlinks", target)
            self.assertIn("log/2026-05/11-1430-source.md", target)

    def test_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "t.md", {"title": "T"}, "body\n")
            write_md(vault / "log" / "2026-05" / "11-1430-s.md",
                     {"title": "S"}, "[[T]]\n")
            r1 = self._run(vault, "log/2026-05/11-1430-s.md")
            self.assertEqual(json.loads(r1.stdout)["updated"], ["concepts/t.md"])
            r2 = self._run(vault, "log/2026-05/11-1430-s.md")
            payload = json.loads(r2.stdout)
            self.assertEqual(payload["updated"], [])
            self.assertEqual(payload["skipped"], ["concepts/t.md"])

    def test_missing_targets_listed(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "log" / "2026-05" / "11-x.md",
                     {"title": "X"}, "links to [[Nope]] and [[Also Nope]]\n")
            r = self._run(vault, "log/2026-05/11-x.md")
            payload = json.loads(r.stdout)
            self.assertIn("Nope", payload["missing"])

    def test_alias_match(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "real.md",
                     {"title": "Real Title", "aliases": ["Alias One"]},
                     "body\n")
            write_md(vault / "log" / "2026-05" / "11-x.md",
                     {"title": "X"}, "[[Alias One]]\n")
            r = self._run(vault, "log/2026-05/11-x.md")
            payload = json.loads(r.stdout)
            self.assertEqual(payload["updated"], ["concepts/real.md"])

    def test_self_reference_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "log" / "2026-05" / "11-self.md",
                     {"title": "Self"}, "[[11-self]]\n")
            r = self._run(vault, "log/2026-05/11-self.md")
            payload = json.loads(r.stdout)
            # self-reference must not be a backlink to self
            self.assertEqual(payload["updated"], [])

    def test_codeblock_links_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "t.md", {"title": "T"}, "body\n")
            write_md(
                vault / "log" / "2026-05" / "11-x.md", {"title": "X"},
                "in code:\n```\n[[T]]\n```\nnot a real link\n",
            )
            r = self._run(vault, "log/2026-05/11-x.md")
            payload = json.loads(r.stdout)
            self.assertEqual(payload["updated"], [])

    def test_quiet_no_stdout(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "t.md", {"title": "T"}, "body\n")
            write_md(vault / "log" / "2026-05" / "11-x.md", {"title": "X"}, "[[T]]\n")
            r = self._run(vault, "log/2026-05/11-x.md", quiet=True)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout.strip(), "")

    def test_missing_vault_returns_0(self):
        r = subprocess.run(
            [sys.executable, str(SCRIPT), "--vault", "/tmp/no-such-vault-xxx",
             "--source", "x.md"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(r.returncode, 0)

    def test_missing_source_returns_0(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            r = self._run(vault, "log/missing.md")
            self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
