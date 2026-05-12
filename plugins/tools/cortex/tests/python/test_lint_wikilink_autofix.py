"""Tests for dead-wikilink + duplicate-alias autofix in lint/run.py."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import add_paths, make_vault, write_md

add_paths()

import run as lint_run  # noqa: E402


class DeadWikilinkAutofixTest(unittest.TestCase):
    def test_freq2_creates_stub(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            (vault / "a.md").write_text("see [[X]]", encoding="utf-8")
            (vault / "b.md").write_text("also [[X]]", encoding="utf-8")

            backup_dir = vault / "_meta" / ".cortex-backup" / "lint" / "test"
            backup_dir.mkdir(parents=True, exist_ok=True)

            freq = lint_run._wikilink_freq(vault)
            self.assertGreaterEqual(freq.get("x", 0), 2)

            stub_counter = {"n": 0}
            finding = {
                "rule": "dead-wikilink", "severity": "error",
                "file": "a.md", "line": 1,
                "msg": "dead link: [[X]]", "fixable": True,
            }
            ok = lint_run._fix_dead_wikilink(
                finding, vault, None, backup_dir,
                freq_cache=freq, stub_counter=stub_counter,
            )
            self.assertTrue(ok)
            stub = vault / "知识库" / "收件箱" / "X.md"
            self.assertTrue(stub.exists())
            content = stub.read_text(encoding="utf-8")
            self.assertIn("type: stub", content)
            self.assertIn("auto_created_by: lint-autofix", content)
            self.assertEqual(stub_counter["n"], 1)
            # source file unchanged
            self.assertEqual((vault / "a.md").read_text(encoding="utf-8"), "see [[X]]")

    def test_freq1_strips_wikilink(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            (vault / "a.md").write_text("see [[Y]] tail", encoding="utf-8")

            backup_dir = vault / "_meta" / ".cortex-backup" / "lint" / "test"
            backup_dir.mkdir(parents=True, exist_ok=True)

            freq = lint_run._wikilink_freq(vault)
            self.assertEqual(freq.get("y", 0), 1)

            finding = {
                "rule": "dead-wikilink", "severity": "error",
                "file": "a.md", "line": 1,
                "msg": "dead link: [[Y]]", "fixable": True,
            }
            ok = lint_run._fix_dead_wikilink(
                finding, vault, None, backup_dir,
                freq_cache=freq, stub_counter={"n": 0},
            )
            self.assertTrue(ok)
            self.assertEqual((vault / "a.md").read_text(encoding="utf-8"), "see Y tail")
            # backup exists
            self.assertTrue((backup_dir / "a.md").exists())

    def test_freq1_strips_with_label(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            (vault / "a.md").write_text("see [[Y|alias]]", encoding="utf-8")

            backup_dir = vault / "_meta" / ".cortex-backup" / "lint" / "test"
            backup_dir.mkdir(parents=True, exist_ok=True)

            freq = lint_run._wikilink_freq(vault)
            finding = {
                "rule": "dead-wikilink", "severity": "error",
                "file": "a.md", "line": 1,
                "msg": "dead link: [[Y]]", "fixable": True,
            }
            ok = lint_run._fix_dead_wikilink(
                finding, vault, None, backup_dir,
                freq_cache=freq, stub_counter={"n": 0},
            )
            self.assertTrue(ok)
            self.assertEqual((vault / "a.md").read_text(encoding="utf-8"), "see alias")

    def test_stub_cap(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            backup_dir = vault / "_meta" / ".cortex-backup" / "lint" / "test"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Force freq≥2 via cache; counter starts at cap
            stub_counter = {"n": lint_run._STUB_CAP}
            finding = {
                "rule": "dead-wikilink", "severity": "error",
                "file": "a.md", "line": 1,
                "msg": "dead link: [[Z]]", "fixable": True,
            }
            (vault / "a.md").write_text("[[Z]]", encoding="utf-8")
            ok = lint_run._fix_dead_wikilink(
                finding, vault, None, backup_dir,
                freq_cache={"z": 5}, stub_counter=stub_counter,
            )
            self.assertFalse(ok)
            self.assertFalse((vault / "知识库" / "收件箱" / "Z.md").exists())


class DuplicateAliasAutofixTest(unittest.TestCase):
    def test_keeps_earliest_by_created(self):
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("yaml not available")
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "first.md",
                {"type": "concept", "title": "first",
                 "created": "2026-01-01", "aliases": ["shared"]},
                "# first\n",
            )
            write_md(
                vault / "sub" / "second.md",
                {"type": "concept", "title": "second",
                 "created": "2026-02-01", "aliases": ["shared"]},
                "# second\n",
            )
            backup_dir = vault / "_meta" / ".cortex-backup" / "lint" / "test"
            backup_dir.mkdir(parents=True, exist_ok=True)

            n = lint_run._fix_duplicate_alias_group(
                "shared", ["first.md", "sub/second.md"], vault, backup_dir,
            )
            self.assertEqual(n, 1)

            import yaml
            first_text = (vault / "first.md").read_text(encoding="utf-8")
            second_text = (vault / "sub" / "second.md").read_text(encoding="utf-8")
            # First (earliest) unchanged
            self.assertIn("shared", first_text)
            # Second renamed with parent suffix
            second_fm = yaml.safe_load(second_text.split("---")[1])
            self.assertIn("shared (sub)", second_fm["aliases"])
            self.assertNotIn("shared", [a for a in second_fm["aliases"] if a == "shared"])
            # Backup created
            self.assertTrue((backup_dir / "sub" / "second.md").exists())

    def test_mtime_fallback_when_no_created(self):
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("yaml not available")
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "a.md",
                {"type": "concept", "title": "a", "aliases": ["x"]},
                "# a\n",
            )
            write_md(
                vault / "b.md",
                {"type": "concept", "title": "b", "aliases": ["x"]},
                "# b\n",
            )
            # Force a.md older
            import os
            os.utime(vault / "a.md", (1000, 1000))
            os.utime(vault / "b.md", (2000, 2000))
            backup_dir = vault / "_meta" / ".cortex-backup" / "lint" / "test"
            backup_dir.mkdir(parents=True, exist_ok=True)

            n = lint_run._fix_duplicate_alias_group(
                "x", ["a.md", "b.md"], vault, backup_dir,
            )
            self.assertEqual(n, 1)
            import yaml
            b_text = (vault / "b.md").read_text(encoding="utf-8")
            b_fm = yaml.safe_load(b_text.split("---")[1])
            # b is the newer one — should be renamed
            self.assertTrue(any("(root)" in a or "(" in a for a in b_fm["aliases"]))


if __name__ == "__main__":
    unittest.main()
