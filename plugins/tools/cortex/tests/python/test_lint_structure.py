"""Tests for lint rule #16: vault-structure-violation (lint/run.py + schemas.py)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _helpers import add_paths

add_paths()

import run as lint_run  # noqa: E402
import schemas as lint_schemas  # noqa: E402


def _bare_vault(root: Path, preset: str = "LYT",
                whitelist: list[str] | None = None) -> Path:
    """Build a minimal vault with explicit preset (no localized dirs)."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "_meta").mkdir(exist_ok=True)
    meta: dict = {"preset": preset, "lang": "zh-CN"}
    if whitelist is not None:
        meta["lint_whitelist"] = whitelist
    (root / "_meta" / "version.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    return root


def _structure_violations(vault: Path) -> list[dict]:
    """Run check_vault_structure directly (no subprocess)."""
    preset = lint_run._load_vault_preset(vault)
    whitelist = lint_run._load_lint_whitelist(vault)
    return lint_run.check_vault_structure(vault, preset, whitelist, None)


class SchemasTest(unittest.TestCase):
    def test_schema_has_required_shape(self):
        schema = lint_schemas.SCHEMA
        self.assertIsInstance(schema["root_dirs"], set)
        self.assertIsInstance(schema["root_files"], set)
        self.assertGreater(len(schema["root_dirs"]), 0)

    def test_get_schema_ignores_preset_arg(self):
        self.assertIs(lint_schemas.get_schema("LYT"), lint_schemas.SCHEMA)
        self.assertIs(lint_schemas.get_schema(None), lint_schemas.SCHEMA)
        self.assertIs(lint_schemas.get_schema(), lint_schemas.SCHEMA)

    def test_hidden_obsidian_dirs_allowed(self):
        self.assertIn(".obsidian", lint_schemas.SCHEMA["root_dirs"])
        self.assertIn(".trash", lint_schemas.SCHEMA["root_dirs"])


class VaultStructureRuleTest(unittest.TestCase):
    def test_lyt_illegal_dir_and_file_both_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            vault = _bare_vault(Path(d), preset="LYT")
            (vault / "foobar").mkdir()
            (vault / "random.txt").write_text("x", encoding="utf-8")

            violations = _structure_violations(vault)
            rules = {v["rule"] for v in violations}
            self.assertEqual(rules, {"vault-structure-violation"})

            paths = {v["path"] for v in violations}
            self.assertEqual(paths, {"foobar/", "random.txt"})

            kinds = {v["path"]: v["kind"] for v in violations}
            self.assertEqual(kinds["foobar/"], "dir")
            self.assertEqual(kinds["random.txt"], "file")

            # standard finding shape preserved
            for v in violations:
                self.assertEqual(v["severity"], "error")
                self.assertTrue(v["fixable"])
                self.assertIn("msg", v)

    def test_whitelist_skips_violation(self):
        with tempfile.TemporaryDirectory() as d:
            vault = _bare_vault(Path(d), preset="LYT",
                                whitelist=["foobar/", "random.txt"])
            (vault / "foobar").mkdir()
            (vault / "random.txt").write_text("x", encoding="utf-8")

            violations = _structure_violations(vault)
            self.assertEqual(violations, [])

    def test_hidden_obsidian_dirs_not_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            vault = _bare_vault(Path(d), preset="LYT")
            (vault / ".obsidian").mkdir()
            (vault / ".trash").mkdir()

            violations = _structure_violations(vault)
            self.assertEqual(violations, [])

    def test_extra_allowed_dirs_locale_passthrough(self):
        """Locale-derived dir names (e.g. 概念) bypass schema strictness."""
        with tempfile.TemporaryDirectory() as d:
            vault = _bare_vault(Path(d), preset="LYT")
            (vault / "概念").mkdir()
            (vault / "foobar").mkdir()

            violations = lint_run.check_vault_structure(
                vault, "LYT", set(), extra_allowed_dirs={"概念"}
            )
            paths = {v["path"] for v in violations}
            self.assertEqual(paths, {"foobar/"})

    def test_whitelist_loads_when_no_preset(self):
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            (vault / "_meta").mkdir()
            (vault / "_meta" / "version.json").write_text(
                json.dumps({"lang": "zh-CN"}), encoding="utf-8"
            )
            self.assertEqual(lint_run._load_lint_whitelist(vault), set())


class StructurePurgeMvPlanTest(unittest.TestCase):
    """run.py main() emits structure_purge.mv_plan for vault-structure violations."""

    RUN_PY = (
        Path(__file__).resolve().parent.parent.parent / "scripts" / "lint" / "run.py"
    )

    def _run_lint(self, vault: Path) -> dict:
        proc = subprocess.run(
            [sys.executable, str(self.RUN_PY), "--vault", str(vault)],
            capture_output=True, text=True, check=False,
        )
        # run.py exits 0 even with findings; stderr only on hard errors
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        return json.loads(proc.stdout)

    def test_mv_plan_emitted_with_iso_backup_root(self):
        with tempfile.TemporaryDirectory() as d:
            vault = _bare_vault(Path(d), preset="LYT")
            (vault / "foobar").mkdir()
            (vault / "random.txt").write_text("x", encoding="utf-8")

            report = self._run_lint(vault)
            self.assertIn("structure_purge", report)
            sp = report["structure_purge"]
            self.assertEqual(sp["violation_count"], 2)

            # backup_root lives OUTSIDE the vault:
            # <home>/.cache/cortex/lint-backup/<vault-hash>/structure-<ts>
            self.assertRegex(
                sp["backup_root"],
                r"/\.cache/cortex/lint-backup/[0-9a-f]{8}/structure-\d{8}T\d{6}Z$",
            )
            self.assertNotIn(str(vault), sp["backup_root"])

            mv_plan = sp["mv_plan"]
            self.assertEqual(len(mv_plan), 2)
            froms = {item["from"] for item in mv_plan}
            self.assertEqual(froms, {"foobar/", "random.txt"})
            for item in mv_plan:
                self.assertTrue(
                    item["to"].startswith(sp["backup_root"] + "/"),
                    msg=f"unexpected to: {item['to']}",
                )
                # to == backup_root + "/" + from
                self.assertEqual(item["to"], f"{sp['backup_root']}/{item['from']}")

            # individual violations also carry backup_target
            sp_errors = [e for e in report["errors"]
                         if e.get("rule") == "vault-structure-violation"]
            self.assertEqual(len(sp_errors), 2)
            for v in sp_errors:
                self.assertIn("backup_target", v)
                self.assertTrue(
                    v["backup_target"].startswith(sp["backup_root"] + "/"),
                    msg=f"unexpected backup_target: {v['backup_target']}",
                )

    def test_no_structure_purge_when_clean(self):
        with tempfile.TemporaryDirectory() as d:
            vault = _bare_vault(Path(d), preset="LYT")
            # clean vault: only _meta/, no violations
            report = self._run_lint(vault)
            # Either absent or violation_count == 0; PRD allows either.
            sp = report.get("structure_purge")
            if sp is not None:
                self.assertEqual(sp["violation_count"], 0)
                self.assertEqual(sp.get("mv_plan", []), [])


if __name__ == "__main__":
    unittest.main()
