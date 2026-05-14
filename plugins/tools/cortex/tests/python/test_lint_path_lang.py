"""Tests for lint rule 20: path-lang-mismatch.

Vault path segment must align with vault.lang.
Exemptions: 项目/<host>/<org>/<repo>/ prefix, ASCII proper-name stems,
frontmatter path_lang_exempt: true, infra dirs.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _helpers import add_paths, make_vault, write_md

add_paths()

import run as lint_run  # noqa: E402


def _run_check_file(vault: Path, rel: str, lang: str) -> list[dict]:
    p = vault / rel
    text = p.read_text(encoding="utf-8")
    return lint_run.check_file(
        p, rel, text, by_name={}, by_alias={}, referrers={},
        vault_lang=lang, fm_schema=None,
    )


def _rules(findings: list[dict]) -> list[str]:
    return [f["rule"] for f in findings]


class PathLangMismatchTest(unittest.TestCase):
    def test_zh_path_with_chinese_stem_passes(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            rel = "知识库/领域/技术/笔记/架构.md"
            write_md(
                vault / rel,
                {"type": "concept", "title": "架构", "created": "2026-05-14"},
                "body\n",
            )
            findings = _run_check_file(vault, rel, "zh-CN")
            self.assertNotIn("path-lang-mismatch", _rules(findings))

    def test_zh_path_with_ascii_stem_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            rel = "知识库/领域/技术/笔记/architecture.md"
            write_md(
                vault / rel,
                {"type": "concept", "title": "architecture", "created": "2026-05-14"},
                "body\n",
            )
            findings = _run_check_file(vault, rel, "zh-CN")
            rules = _rules(findings)
            self.assertIn("path-lang-mismatch", rules)
            # Verify enriched fields
            hit = [f for f in findings if f["rule"] == "path-lang-mismatch"][0]
            self.assertEqual(hit["segment"], "architecture.md")
            self.assertEqual(hit["vault_lang"], "zh-CN")
            self.assertEqual(hit["severity"], "warn")
            self.assertFalse(hit["fixable"])

    def test_zh_project_host_org_repo_exempted(self):
        """`知识库/项目/<host>/<org>/<repo>/` 前 5 段豁免."""
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            rel = "知识库/项目/github.com/lazygophers/ccplugin/笔记/架构.md"
            write_md(
                vault / rel,
                {"type": "project", "title": "架构", "created": "2026-05-14"},
                "body\n",
            )
            findings = _run_check_file(vault, rel, "zh-CN")
            self.assertNotIn("path-lang-mismatch", _rules(findings))

    def test_zh_project_ascii_subpath_after_repo_still_flagged(self):
        """前 5 段豁免, 但项目内的 segment 仍受检 (除 README 等专名)."""
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            rel = "知识库/项目/github.com/lazygophers/ccplugin/notes/algorithm.md"
            write_md(
                vault / rel,
                {"type": "project", "title": "algo", "created": "2026-05-14"},
                "body\n",
            )
            findings = _run_check_file(vault, rel, "zh-CN")
            self.assertIn("path-lang-mismatch", _rules(findings))

    def test_zh_readme_ascii_exempt(self):
        """README.md / LICENSE 等 ASCII 专名 stem 豁免."""
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            rel = "知识库/项目/github.com/foo/bar/README.md"
            write_md(
                vault / rel,
                {"type": "project", "title": "readme", "created": "2026-05-14"},
                "body\n",
            )
            findings = _run_check_file(vault, rel, "zh-CN")
            self.assertNotIn("path-lang-mismatch", _rules(findings))

    def test_en_vault_ascii_path_passes(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="en")
            rel = "kb/projects/github.com/foo/bar/notes/architecture.md"
            write_md(
                vault / rel,
                {"type": "project", "title": "arch", "created": "2026-05-14"},
                "body\n",
            )
            findings = _run_check_file(vault, rel, "en")
            self.assertNotIn("path-lang-mismatch", _rules(findings))

    def test_en_vault_cjk_segment_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="en")
            rel = "kb/projects/github.com/foo/bar/notes/架构.md"
            write_md(
                vault / rel,
                {"type": "project", "title": "arch", "created": "2026-05-14"},
                "body\n",
            )
            findings = _run_check_file(vault, rel, "en")
            self.assertIn("path-lang-mismatch", _rules(findings))

    def test_frontmatter_path_lang_exempt_passes(self):
        """frontmatter path_lang_exempt: true 兜底豁免."""
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            rel = "知识库/领域/技术/笔记/OAuth2.md"
            write_md(
                vault / rel,
                {
                    "type": "concept",
                    "title": "OAuth2",
                    "created": "2026-05-14",
                    "path_lang_exempt": "true",
                },
                "body\n",
            )
            findings = _run_check_file(vault, rel, "zh-CN")
            self.assertNotIn("path-lang-mismatch", _rules(findings))

    def test_infra_dirs_exempt(self):
        """_meta / _templates / 记忆 / 仪表盘 等顶层不受检."""
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            for rel in [
                "_templates/concept.md",
                "_assets/foo/bar.md",
            ]:
                write_md(
                    vault / rel,
                    {"type": "concept", "title": "t", "created": "2026-05-14"},
                    "body\n",
                )
                findings = _run_check_file(vault, rel, "zh-CN")
                self.assertNotIn(
                    "path-lang-mismatch", _rules(findings),
                    f"infra dir {rel} should be exempt",
                )

    def test_lint_skip_short_circuits(self):
        """lint-skip: true 跳过全部 check_file 规则 (含 path-lang-mismatch)."""
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            rel = "知识库/领域/技术/笔记/architecture.md"
            write_md(
                vault / rel,
                {
                    "type": "concept",
                    "title": "x",
                    "created": "2026-05-14",
                    "lint-skip": "true",
                },
                "body\n",
            )
            findings = _run_check_file(vault, rel, "zh-CN")
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
