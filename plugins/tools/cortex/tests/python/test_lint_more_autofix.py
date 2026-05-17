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


class RepoPathDeprecatedAutofixTest(unittest.TestCase):
    def test_rule_repo_path_deprecated_autofix_moves_to_项目(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            old_dir = vault / "知识库" / "来源" / "代码仓库" / "x" / "y" / "z"
            old_dir.mkdir(parents=True)
            old_file = old_dir / "foo.md"
            old_file.write_text(
                "---\ntype: domain\ntitle: foo\n---\n\nbody\n",
                encoding="utf-8",
            )
            backup = vault / "_meta" / ".cortex-backup" / "r"
            backup.mkdir(parents=True, exist_ok=True)

            finding = {
                "rule": "repo-path-deprecated",
                "file": "知识库/来源/代码仓库/x/y/z/foo.md",
                "fixable": True,
                "line": 1,
            }
            ok = lint_run._fix_repo_path_deprecated(
                finding, vault, None, backup,
            )
            self.assertTrue(ok)
            new_file = vault / "知识库" / "项目" / "x" / "y" / "z" / "foo.md"
            self.assertTrue(new_file.exists())
            self.assertFalse(old_file.exists())
            text = new_file.read_text(encoding="utf-8")
            self.assertIn("type: project", text)
            self.assertIn("host: x", text)
            self.assertIn("org: y", text)
            self.assertIn("repo: z", text)

    def test_finding_emitted_for_deprecated_path(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            old_dir = vault / "知识库" / "来源" / "代码仓库" / "github.com" / "foo" / "bar"
            old_dir.mkdir(parents=True)
            (old_dir / "_index.md").write_text(
                "---\ntype: project\ntitle: bar\n---\n\nbody\n",
                encoding="utf-8",
            )
            files = list(vault.rglob("*.md"))
            findings = lint_run.check_global(vault, files, {}, locale_dirs=None)
            rules = [f["rule"] for f in findings]
            self.assertIn("repo-path-deprecated", rules)


class KbDeprecatedPathRulesTest(unittest.TestCase):
    """5 new vault-structure deprecation rules (knowledge/反思 ... → 收件箱/归档)."""

    def _make_finding(self, rule: str, rel: str) -> dict:
        return {"rule": rule, "file": rel, "path": rel, "fixable": True, "line": 1}

    def test_rule_kb_reflection_path_deprecated_autofix_moves_to_收件箱(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            src = vault / "知识库" / "反思" / "洞察" / "x.md"
            src.parent.mkdir(parents=True)
            src.write_text("---\ntype: reflection\ntitle: x\n---\nbody\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "r"
            backup.mkdir(parents=True, exist_ok=True)
            ok = lint_run._fix_mv_to_inbox(
                self._make_finding("kb-reflection-path-deprecated", "知识库/反思/洞察/x.md"),
                vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertFalse(src.exists())
            dst = vault / "知识库" / "收件箱" / "x.md"
            self.assertTrue(dst.exists())
            text = dst.read_text(encoding="utf-8")
            self.assertIn("was_path: 知识库/反思/洞察/x.md", text)

    def test_rule_kb_question_fleeting_path_deprecated_autofix_moves_to_收件箱(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            src = vault / "知识库" / "问题" / "q.md"
            src.parent.mkdir(parents=True)
            src.write_text("---\ntype: question\ntitle: q\n---\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "r"
            backup.mkdir(parents=True, exist_ok=True)
            ok = lint_run._fix_mv_to_inbox(
                self._make_finding("kb-question-fleeting-path-deprecated", "知识库/问题/q.md"),
                vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertTrue((vault / "知识库" / "收件箱" / "q.md").exists())

    def test_rule_kb_entity_concept_path_deprecated_autofix_moves_to_未分类(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            f = vault / "知识库" / "实体" / "p.md"
            f.parent.mkdir(parents=True)
            f.write_text("---\ntype: entity\ntitle: p\n---\n", encoding="utf-8")
            files = list(vault.rglob("*.md"))
            findings = lint_run.check_global(vault, files, {}, locale_dirs=None)
            rules = [x["rule"] for x in findings]
            self.assertIn("kb-entity-concept-path-deprecated", rules)
            ec_finding = next(x for x in findings if x["rule"] == "kb-entity-concept-path-deprecated")
            self.assertTrue(ec_finding.get("fixable", False))
            backup = vault / "_meta" / ".cortex-backup" / "r"
            backup.mkdir(parents=True, exist_ok=True)
            ok = lint_run._fix_kb_entity_concept_to_domain(
                ec_finding, vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertFalse(f.exists())
            self.assertTrue((vault / "知识库" / "领域" / "未分类" / "p.md").exists())

    def test_rule_kb_journal_multi_freq_deprecated_autofix_archives(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            src = vault / "知识库" / "日记" / "月" / "2026-05.md"
            src.parent.mkdir(parents=True)
            src.write_text("---\ntype: journal\ndate: '2026-05-15'\n---\nmonth content\n", encoding="utf-8")
            backup = vault / "_meta" / ".cortex-backup" / "r"
            backup.mkdir(parents=True, exist_ok=True)
            ok = lint_run._fix_journal_multi_freq_to_archive(
                self._make_finding("kb-journal-multi-freq-deprecated", "知识库/日记/月/2026-05.md"),
                vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertFalse(src.exists())
            # 2026-05 → Q2 (May)
            self.assertTrue((vault / "归档" / "日记" / "2026-Q2.md").exists())

    def test_rule_kb_source_non_repo_path_deprecated_autofix_moves_to_收件箱(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            src = vault / "知识库" / "来源" / "网页" / "example.com" / "foo.md"
            src.parent.mkdir(parents=True)
            src.write_text(
                "---\ntype: source\ntitle: foo\nurl: https://example.com/x\n---\nbody\n",
                encoding="utf-8",
            )
            backup = vault / "_meta" / ".cortex-backup" / "r"
            backup.mkdir(parents=True, exist_ok=True)
            ok = lint_run._fix_mv_source_non_repo_to_inbox(
                self._make_finding("kb-source-non-repo-path-deprecated", "知识库/来源/网页/example.com/foo.md"),
                vault, None, backup,
            )
            self.assertTrue(ok)
            self.assertFalse(src.exists())
            # host extracted from url frontmatter → example.com
            self.assertTrue((vault / "知识库" / "收件箱" / "example.com-foo.md").exists())

    def test_findings_emitted_for_new_deprecation_rules(self):
        """check_global emits findings for all 5 new deprecation rules."""
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            for rel, body in [
                ("知识库/反思/洞察/a.md", "---\ntype: reflection\ntitle: a\n---\n"),
                ("知识库/问题/b.md", "---\ntype: question\ntitle: b\n---\n"),
                ("知识库/临时/c.md", "---\ntype: fleeting\ntitle: c\n---\n"),
                ("知识库/实体/d.md", "---\ntype: entity\ntitle: d\n---\n"),
                ("知识库/概念/e.md", "---\ntype: concept\ntitle: e\n---\n"),
                ("知识库/日记/周/2026-W19.md", "---\ntype: journal\ndate: '2026-05-13'\n---\n"),
                ("知识库/来源/网页/example.com/f.md",
                 "---\ntype: source\ntitle: f\nurl: https://example.com/f\n---\n"),
            ]:
                p = vault / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(body, encoding="utf-8")
            files = list(vault.rglob("*.md"))
            findings = lint_run.check_global(vault, files, {}, locale_dirs=None)
            rules = {f["rule"] for f in findings}
            self.assertIn("kb-reflection-path-deprecated", rules)
            self.assertIn("kb-question-fleeting-path-deprecated", rules)
            self.assertIn("kb-entity-concept-path-deprecated", rules)
            self.assertIn("kb-journal-multi-freq-deprecated", rules)
            self.assertIn("kb-source-non-repo-path-deprecated", rules)


if __name__ == "__main__":
    unittest.main()
