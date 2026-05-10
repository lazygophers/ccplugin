"""Tests for lint/run.py."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _helpers import PLUGIN_ROOT, add_paths, make_vault, write_md

add_paths()

SCRIPT = PLUGIN_ROOT / "lint" / "run.py"


def run_lint(vault: Path, *args: str) -> tuple[int, dict]:
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--vault", str(vault), *args],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0 and not r.stdout.strip():
        return r.returncode, {}
    try:
        return r.returncode, json.loads(r.stdout)
    except Exception:
        return r.returncode, {"_raw_stdout": r.stdout, "_stderr": r.stderr}


def rules_hit(report: dict) -> set[str]:
    return set(report.get("summary", {}).get("rules_hit", []))


class LintRulesTest(unittest.TestCase):
    def test_clean_vault_lint_runs(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            # add one well-formed concept page
            write_md(
                vault / "概念" / "demo.md",
                {"type": "concept", "title": "demo", "created": "2026-05-11",
                 "tags": ["x"]},
                "# demo\n\nbody\n",
            )
            rc, rep = run_lint(vault)
            self.assertEqual(rc, 0)
            # demo.md itself should not have a fm-missing-type / dead-wikilink finding
            for f in rep["errors"]:
                self.assertNotEqual(f["file"], "概念/demo.md", msg=str(f))

    def test_rule1_fm_missing_type(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "概念" / "x.md",
                     {"title": "x", "created": "2026-05-11"}, "# x\n")
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-type", rules_hit(rep))

    def test_rule2_fm_missing_created(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "概念" / "x.md", {"type": "concept", "title": "x"},
                     "# x\n")
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-created", rules_hit(rep))

    def test_rule3_dead_wikilink(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "概念" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11"},
                "[[Nonexistent]]\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("dead-wikilink", rules_hit(rep))

    def test_rule4_orphan_page(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "概念" / "lonely.md",
                {"type": "concept", "title": "lonely", "created": "2026-05-11"},
                "# lonely\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("orphan-page", rules_hit(rep))

    def test_rule5_duplicate_alias(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "概念" / "a.md",
                     {"type": "concept", "title": "Same", "created": "2026-05-11",
                      "tags": ["t"]}, "# Same\n")
            write_md(vault / "概念" / "b.md",
                     {"type": "concept", "title": "Same", "created": "2026-05-11",
                      "tags": ["t"]}, "# Same\n")
            rc, rep = run_lint(vault)
            self.assertIn("duplicate-alias", rules_hit(rep))

    def test_rule6_hot_too_long(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            (vault / "hot.md").write_text("\n".join(["x"] * 250), encoding="utf-8")
            rc, rep = run_lint(vault)
            self.assertIn("hot-too-long", rules_hit(rep))

    def test_rule8_index_missing_section(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            (vault / "概念").mkdir()
            write_md(vault / "概念" / "x.md",
                     {"type": "concept", "title": "x",
                      "created": "2026-05-11", "tags": ["t"]}, "x")
            (vault / "index.md").write_text("# index\n", encoding="utf-8")
            rc, rep = run_lint(vault)
            self.assertIn("index-missing-section", rules_hit(rep))

    def test_rule9_title_h1_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "概念" / "x.md",
                     {"type": "concept", "title": "Real Title",
                      "created": "2026-05-11", "tags": ["t"]},
                     "# Wrong H1\n")
            rc, rep = run_lint(vault)
            self.assertIn("title-h1-mismatch", rules_hit(rep))

    def test_rule10_filename_illegal(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            bad = vault / "概念" / "bad?name.md"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_text("---\ntype: concept\ntitle: x\ncreated: 2026-05-11\ntags: [t]\n---\n# x\n", encoding="utf-8")
            rc, rep = run_lint(vault)
            self.assertIn("filename-illegal", rules_hit(rep))

    def test_rule11_block_id_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            for n in ("a", "b"):
                write_md(
                    vault / "概念" / f"{n}.md",
                    {"type": "concept", "title": n, "created": "2026-05-11",
                     "tags": ["t"]},
                    f"# {n}\n\ntext ^cortex-12345678\n",
                )
            rc, rep = run_lint(vault)
            self.assertIn("block-id-duplicate", rules_hit(rep))

    def test_rule12_callout_unknown_type(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "概念" / "x.md",
                {"type": "concept", "title": "x",
                 "created": "2026-05-11", "tags": ["t"]},
                "# x\n\n> [!unknownweird] something\n> body\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("callout-unknown-type", rules_hit(rep))

    def test_rule13_path_naming_violation_log(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            bad = vault / "log" / "2026-05" / "BADNAME.md"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_text("---\ntype: log\ntitle: x\ncreated: 2026-05-11\n---\n# x\n", encoding="utf-8")
            rc, rep = run_lint(vault)
            self.assertIn("path-naming-violation", rules_hit(rep))

    def test_rule14_i18n_lang_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            write_md(
                vault / "概念" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["t"], "lang": "ja"},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("i18n-frontmatter-lang-mismatch", rules_hit(rep))

    def test_rule15_i18n_path_not_in_locale(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            # "concepts" is the en name; in zh-CN dirs map it should be 概念
            write_md(
                vault / "concepts" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["t"]},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("i18n-path-not-in-locale", rules_hit(rep))


class AutofixTest(unittest.TestCase):
    def test_fix_missing_type(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            f = vault / "概念" / "x.md"
            write_md(f, {"title": "x", "created": "2026-05-11", "tags": ["t"]},
                     "# x\n")
            rc, rep = run_lint(vault, "--fix")
            self.assertEqual(rc, 0)
            self.assertGreater(rep["summary"]["fixed"], 0)
            text = f.read_text(encoding="utf-8")
            self.assertIn("type:", text)
            # backup dir was created
            backup = vault / "_meta" / ".cortex-backup" / "lint"
            self.assertTrue(backup.is_dir())

    def test_fix_h1_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            f = vault / "概念" / "x.md"
            write_md(f, {"type": "concept", "title": "Right",
                         "created": "2026-05-11", "tags": ["t"]},
                     "# Wrong H1\n\nbody\n")
            rc, rep = run_lint(vault, "--fix")
            self.assertEqual(rc, 0)
            text = f.read_text(encoding="utf-8")
            self.assertIn("# Right", text)
            self.assertNotIn("# Wrong H1", text)


class ErrorPathTest(unittest.TestCase):
    def test_missing_vault_exits_2(self):
        rc, _ = run_lint(Path("/tmp/no-such-cortex-vault"))
        self.assertEqual(rc, 2)

    def test_lang_override(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            # `concepts` matches en map
            write_md(
                vault / "concepts" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["t"]},
                "# x\n",
            )
            # with --lang en, concepts is fine
            rc, rep = run_lint(vault, "--lang", "en")
            self.assertNotIn("i18n-path-not-in-locale", rules_hit(rep))


if __name__ == "__main__":
    unittest.main()
