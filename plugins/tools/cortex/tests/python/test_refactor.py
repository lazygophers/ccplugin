"""Tests for refactor/*.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _helpers import PLUGIN_ROOT, add_paths, make_vault, write_md

add_paths()

import _common  # noqa: E402

REFACTOR = PLUGIN_ROOT / "refactor"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REFACTOR / name), *args],
        capture_output=True, text=True, timeout=60,
    )


class CommonTest(unittest.TestCase):
    def test_rewrite_basename(self):
        text = "see [[old]] and [[old|alias]]"
        new, n = _common.rewrite_wikilinks(text, {"old": "new"})
        self.assertEqual(n, 2)
        self.assertIn("[[new]]", new)
        self.assertIn("[[new|alias]]", new)

    def test_rewrite_anchor_preserved(self):
        text = "[[old#section]]"
        new, n = _common.rewrite_wikilinks(text, {"old": "new"})
        self.assertEqual(n, 1)
        self.assertIn("[[new#section]]", new)

    def test_rewrite_transclusion(self):
        text = "![[old]]"
        new, n = _common.rewrite_wikilinks(text, {"old": "new"})
        self.assertEqual(n, 1)
        self.assertIn("![[new]]", new)

    def test_no_match_zero(self):
        text = "[[other]]"
        new, n = _common.rewrite_wikilinks(text, {"old": "new"})
        self.assertEqual(n, 0)
        self.assertEqual(new, text)


class RenameTest(unittest.TestCase):
    def test_dry_run_lists_plan(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "old.md",
                     {"title": "old"}, "# old\n")
            write_md(vault / "concepts" / "ref.md",
                     {"title": "ref"}, "see [[old]]\n")
            r = run_script("rename.py", "--vault", str(vault),
                           "--from", "concepts/old.md",
                           "--to", "concepts/new.md")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertFalse(data["applied"])
            self.assertEqual(len(data["files_to_update"]), 1)
            # files unchanged
            self.assertTrue((vault / "concepts" / "old.md").exists())

    def test_apply_renames_and_rewrites(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "old.md", {"title": "old"}, "body\n")
            write_md(vault / "concepts" / "ref.md", {"title": "ref"},
                     "see [[old]]\n")
            r = run_script("rename.py", "--vault", str(vault),
                           "--from", "concepts/old.md",
                           "--to", "concepts/new.md", "--apply")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertTrue((vault / "concepts" / "new.md").exists())
            self.assertFalse((vault / "concepts" / "old.md").exists())
            ref = (vault / "concepts" / "ref.md").read_text(encoding="utf-8")
            self.assertIn("[[new]]", ref)

    def test_missing_source_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            r = run_script("rename.py", "--vault", str(vault),
                           "--from", "nope.md", "--to", "x.md")
            self.assertEqual(r.returncode, 2)

    def test_target_exists_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "a.md", {}, "x")
            write_md(vault / "b.md", {}, "y")
            r = run_script("rename.py", "--vault", str(vault),
                           "--from", "a.md", "--to", "b.md")
            self.assertEqual(r.returncode, 2)


class MergeTest(unittest.TestCase):
    def test_merge_apply(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "src.md", {"title": "src"},
                     "# src\n\nsource body\n")
            write_md(vault / "concepts" / "dst.md", {"title": "dst"},
                     "# dst\n\ndest body\n")
            write_md(vault / "concepts" / "ref.md", {"title": "ref"},
                     "[[src]]\n")
            r = run_script("merge.py", "--vault", str(vault),
                           "--from", "concepts/src.md",
                           "--into", "concepts/dst.md", "--apply")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            dst_text = (vault / "concepts" / "dst.md").read_text(encoding="utf-8")
            self.assertIn("source body", dst_text)
            self.assertIn("(merged) src", dst_text)
            # ref should redirect
            ref_text = (vault / "concepts" / "ref.md").read_text(encoding="utf-8")
            self.assertIn("[[dst]]", ref_text)
            # src archived
            self.assertFalse((vault / "concepts" / "src.md").exists())

    def test_missing_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "dst.md", {"title": "dst"}, "body\n")
            r = run_script("merge.py", "--vault", str(vault),
                           "--from", "concepts/missing.md",
                           "--into", "concepts/dst.md")
            self.assertEqual(r.returncode, 2)


class SplitTest(unittest.TestCase):
    def test_split_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "big.md", {"title": "big"},
                     "# big\n\n## A\n\nfirst\n\n## B\n\nsecond\n")
            r = run_script("split.py", "--vault", str(vault),
                           "--from", "concepts/big.md")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(len(data["sections"]), 2)
            self.assertFalse(data["applied"])

    def test_split_apply(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "big.md", {"title": "big"},
                     "## A\n\nfirst\n\n## B\n\nsecond\n")
            r = run_script("split.py", "--vault", str(vault),
                           "--from", "concepts/big.md", "--apply")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            files = list((vault / "concepts").glob("big--*.md"))
            self.assertEqual(len(files), 2)

    def test_no_h2_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "x.md", {"title": "x"},
                     "# x\n\njust text\n")
            r = run_script("split.py", "--vault", str(vault),
                           "--from", "concepts/x.md")
            self.assertEqual(r.returncode, 2)


class FoldTest(unittest.TestCase):
    def test_fold_old_files(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            old_dir = vault / "log" / "2024-01"
            old_dir.mkdir(parents=True)
            (old_dir / "01-1200-foo.md").write_text(
                "---\ntype: log\ntitle: foo\n---\n# foo\nbody\n",
                encoding="utf-8",
            )
            (old_dir / "02-1300-bar.md").write_text(
                "---\ntype: log\ntitle: bar\n---\n# bar\nbody\n",
                encoding="utf-8",
            )
            r = run_script("fold.py", "--vault", str(vault),
                           "--days", "7", "--apply")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(data["applied"])
            # produced fold file
            folds = list((vault / "folds").glob("2024-01-fold-*.md"))
            self.assertEqual(len(folds), 1)
            # NNN format
            self.assertRegex(folds[0].name, r"^2024-01-fold-001\.md$")

    def test_dry_run_no_writes(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            old_dir = vault / "log" / "2024-01"
            old_dir.mkdir(parents=True)
            (old_dir / "01-1200-foo.md").write_text("body", encoding="utf-8")
            r = run_script("fold.py", "--vault", str(vault), "--days", "7")
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertFalse(data["applied"])

    def test_no_log_dir_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            (vault / "_meta").mkdir()
            (vault / "_meta" / "version.json").write_text("{}", encoding="utf-8")
            r = run_script("fold.py", "--vault", str(vault))
            self.assertEqual(r.returncode, 2)


class MigrateLocaleTest(unittest.TestCase):
    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            (vault / "概念").mkdir()
            (vault / "概念" / "x.md").write_text("# x\n", encoding="utf-8")
            r = run_script("migrate_locale.py", "--vault", str(vault),
                           "--from", "zh-CN", "--to", "en")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(data["dry_run"])
            self.assertEqual(data["vault_lang_after"], "en")

    def test_apply_renames(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            (vault / "概念").mkdir()
            (vault / "概念" / "x.md").write_text("# x\n", encoding="utf-8")
            r = run_script("migrate_locale.py", "--vault", str(vault),
                           "--from", "zh-CN", "--to", "en", "--apply")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertTrue((vault / "concepts").is_dir())
            self.assertFalse((vault / "概念").exists())
            # version.json updated
            meta = json.loads((vault / "_meta" / "version.json").read_text())
            self.assertEqual(meta["lang"], "en")
            # migration log written
            mig = list((vault / "_meta" / "migrations").glob("*-migrate-locale.json"))
            self.assertEqual(len(mig), 1)

    def test_apply_rewrites_path_prefixed_wikilinks(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            (vault / "概念").mkdir()
            (vault / "概念" / "x.md").write_text("# x\n", encoding="utf-8")
            (vault / "ref.md").write_text(
                "see [[概念/x]]\n", encoding="utf-8",
            )
            r = run_script("migrate_locale.py", "--vault", str(vault),
                           "--from", "zh-CN", "--to", "en", "--apply")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            ref = (vault / "ref.md").read_text(encoding="utf-8")
            self.assertIn("[[concepts/x]]", ref)

    def test_missing_vault(self):
        r = run_script("migrate_locale.py", "--vault", "/tmp/nope-cortex-xxx",
                       "--from", "zh-CN", "--to", "en")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
