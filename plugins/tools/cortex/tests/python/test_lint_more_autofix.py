"""Tests for the 5 new lint autofixers added in 05-12 task.

- vault-structure-violation → mv to ~/.cache backup
- callout-unknown-type → unknown → info
- orphan-page → append wikilink to sibling _index.md
- path-naming-violation → slug-safe rename
- i18n-path-not-in-locale → same slug-safe rename
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import add_paths, make_vault

add_paths()

import run as lint_run  # noqa: E402


class CalloutUnknownAutofixTest(unittest.TestCase):
    def test_unknown_callout_replaced_with_info(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "page.md"
            p.write_text("> [!xxx] body\ntext\n> [!warning] keep\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)

            ok = lint_run._fix_callout_unknown_type(
                {"file": "page.md"}, vault, None, backup,
            )
            self.assertTrue(ok)
            txt = p.read_text(encoding="utf-8")
            self.assertIn("> [!info]", txt)
            self.assertIn("> [!warning]", txt)  # standard preserved

    def test_no_unknown_returns_false(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "page.md"
            p.write_text("> [!info] ok\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)
            self.assertFalse(lint_run._fix_callout_unknown_type(
                {"file": "page.md"}, vault, None, backup,
            ))


class OrphanPageAutofixTest(unittest.TestCase):
    def test_appends_wikilink_to_sibling_index(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            sub = vault / "concepts"
            sub.mkdir()
            (sub / "_index.md").write_text("# concepts\n", encoding="utf-8")
            orphan = sub / "lonely.md"
            orphan.write_text("body\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)

            ok = lint_run._fix_orphan_page(
                {"file": "concepts/lonely.md"}, vault, None, backup,
            )
            self.assertTrue(ok)
            idx_txt = (sub / "_index.md").read_text(encoding="utf-8")
            self.assertIn("[[lonely]]", idx_txt)

    def test_no_sibling_index_returns_false(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            sub = vault / "concepts"
            sub.mkdir()
            (sub / "lonely.md").write_text("body\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)
            self.assertFalse(lint_run._fix_orphan_page(
                {"file": "concepts/lonely.md"}, vault, None, backup,
            ))

    def test_already_linked_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            sub = vault / "concepts"
            sub.mkdir()
            (sub / "_index.md").write_text("# x\n\n- [[lonely]]\n", encoding="utf-8")
            (sub / "lonely.md").write_text("body\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)
            self.assertTrue(lint_run._fix_orphan_page(
                {"file": "concepts/lonely.md"}, vault, None, backup,
            ))


class PathViolationAutofixTest(unittest.TestCase):
    def test_rename_with_spaces_and_special(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            bad = vault / "test 文件 (1).md"
            bad.write_text("body\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)

            ok = lint_run._fix_path_violation(
                {"file": "test 文件 (1).md"}, vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertFalse(bad.exists())
            # Expect: 'test-文件-_1_' style slug
            survivors = [p.name for p in vault.iterdir() if p.is_file() and p.suffix == ".md"]
            renamed = [n for n in survivors if "文件" in n]
            self.assertEqual(len(renamed), 1)
            self.assertNotIn(" ", renamed[0])

    def test_top_level_dir_rename(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            bad_dir = vault / "weird dir"
            bad_dir.mkdir()
            (bad_dir / "x.md").write_text("a", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)

            ok = lint_run._fix_path_violation(
                {"file": "weird dir/"}, vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertFalse(bad_dir.exists())
            self.assertTrue((vault / "weird-dir").is_dir())


class VaultStructureViolationAutofixTest(unittest.TestCase):
    def test_mv_dir_to_backup_root(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            bad = vault / "记忆体系"
            bad.mkdir()
            (bad / "note.md").write_text("a", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "x"
            backup.mkdir(parents=True, exist_ok=True)

            finding = {
                "rule": "vault-structure-violation",
                "file": "记忆体系/", "path": "记忆体系/",
                "kind": "dir", "fixable": True,
            }
            ok = lint_run._fix_vault_structure_violation(
                finding, vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertFalse(bad.exists())


if __name__ == "__main__":
    unittest.main()
