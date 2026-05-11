"""Tests for new refactor scripts: restructure / dedupe / extract_inline /
graph_rebalance.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _helpers import PLUGIN_ROOT, add_paths, make_vault, write_md

add_paths()

REFACTOR = PLUGIN_ROOT / "refactor"


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REFACTOR / name), *args],
        capture_output=True, text=True, timeout=60,
    )


class RestructureTest(unittest.TestCase):
    def test_flat_to_lyt_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "foo.md", {"title": "foo"},
                     "# foo\nsee [[bar]]\n")
            write_md(vault / "domains" / "biz.md", {"title": "biz"}, "# biz\n")
            r = run_script("restructure.py", "--vault", str(vault),
                           "--from", "flat", "--to", "LYT")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["op"], "restructure")
            self.assertFalse(data["applied"])
            froms = {mv["from"] for mv in data["mv_plan"]}
            self.assertIn("concepts/foo.md", froms)
            self.assertIn("domains/biz.md", froms)
            tos = {mv["to"] for mv in data["mv_plan"]}
            self.assertTrue(any(t.startswith("10_concepts/") for t in tos))

    def test_lyt_to_para_apply_rewires(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "10_concepts" / "foo.md", {"title": "foo"},
                     "# foo\n")
            write_md(vault / "10_concepts" / "ref.md", {"title": "ref"},
                     "see [[foo]]\n")
            r = run_script("restructure.py", "--vault", str(vault),
                           "--from", "LYT", "--to", "PARA", "--apply")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(data["applied"])
            # foo moved
            self.assertFalse((vault / "10_concepts" / "foo.md").exists())
            self.assertTrue((vault / "1_projects" / "foo.md").exists())
            # ref's wikilink rewritten
            ref_text = (vault / "1_projects" / "ref.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("[[1_projects/foo]]", ref_text)

    def test_collision_renamed_and_warned(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "concepts" / "x.md", {}, "src\n")
            write_md(vault / "10_concepts" / "x.md", {}, "dst\n")
            r = run_script("restructure.py", "--vault", str(vault),
                           "--from", "flat", "--to", "LYT")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(any(
                "collision" in w for w in data["warnings"]
            ))
            tos = [mv["to"] for mv in data["mv_plan"]]
            self.assertTrue(any(".restructure-" in t for t in tos))


class DedupeTest(unittest.TestCase):
    def test_dry_run_finds_near_duplicates(self):
        if shutil.which("rg") is None:
            self.skipTest("ripgrep not installed")
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            # two near-identical bodies
            body = "alpha beta gamma delta epsilon zeta eta theta " * 5
            write_md(vault / "10_concepts" / "a.md", {"title": "alpha"},
                     "# alpha\n" + body)
            write_md(vault / "10_concepts" / "b.md", {"title": "alpha"},
                     "# alpha-dup\n" + body)
            r = run_script("dedupe.py", "--vault", str(vault),
                           "--scope", "concepts", "--threshold", "0.5",
                           "--top-k", "5")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["op"], "dedupe")
            self.assertFalse(data["applied"])
            self.assertGreaterEqual(len(data["candidates"]), 1)

    def test_no_candidates_below_threshold(self):
        if shutil.which("rg") is None:
            self.skipTest("ripgrep not installed")
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "10_concepts" / "a.md", {"title": "a"},
                     "# a\nyellow green blue cyan\n")
            write_md(vault / "10_concepts" / "b.md", {"title": "b"},
                     "# b\nred orange purple magenta\n")
            r = run_script("dedupe.py", "--vault", str(vault),
                           "--scope", "concepts", "--threshold", "0.99")
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["candidates"], [])


class ExtractInlineTest(unittest.TestCase):
    def test_extract_section_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "10_concepts" / "parent.md",
                {"title": "parent", "tags": ["topic"]},
                "# Parent\n\n"
                "intro\n\n"
                "## Detail\n\nbody of detail section\n\n"
                "## Other\n\nelse\n",
            )
            r = run_script(
                "extract_inline.py",
                "--vault", str(vault),
                "--page", "10_concepts/parent.md",
                "--section", "Detail",
                "--direction", "extract",
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["op"], "extract")
            self.assertFalse(data["applied"])
            self.assertIn("detail", data["child_path"].lower())

    def test_extract_apply_writes_child_and_transclusion(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "10_concepts" / "parent.md",
                {"title": "parent"},
                "# Parent\n\n## Sec\n\nbody of sec\n",
            )
            r = run_script(
                "extract_inline.py",
                "--vault", str(vault),
                "--page", "10_concepts/parent.md",
                "--section", "Sec",
                "--direction", "extract",
                "--apply",
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(data["applied"])
            child_path = vault / data["child_path"]
            self.assertTrue(child_path.is_file())
            ctext = child_path.read_text(encoding="utf-8")
            self.assertIn("type: concept", ctext)
            self.assertIn("source: [[parent]]", ctext)
            parent_text = (
                vault / "10_concepts" / "parent.md"
            ).read_text(encoding="utf-8")
            self.assertIn("![[", parent_text)
            self.assertIn(child_path.stem, parent_text)

    def test_inline_apply_merges_child_back(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "10_concepts" / "parent.md",
                {"title": "parent"},
                "# Parent\n\nintro\n\n![[child]]\n",
            )
            write_md(
                vault / "10_concepts" / "child.md",
                {"type": "concept"},
                "# Child\nchild body\n",
            )
            r = run_script(
                "extract_inline.py",
                "--vault", str(vault),
                "--page", "10_concepts/parent.md",
                "--child", "10_concepts/child.md",
                "--direction", "inline",
                "--apply",
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(data["applied"])
            parent_text = (
                vault / "10_concepts" / "parent.md"
            ).read_text(encoding="utf-8")
            self.assertIn("child body", parent_text)
            self.assertFalse((vault / "10_concepts" / "child.md").exists())

    def test_inline_warns_on_nested_transclusion(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "10_concepts" / "parent.md",
                {}, "# Parent\n![[child]]\n",
            )
            write_md(
                vault / "10_concepts" / "child.md",
                {}, "body with ![[nested]] inside\n",
            )
            r = run_script(
                "extract_inline.py",
                "--vault", str(vault),
                "--page", "10_concepts/parent.md",
                "--child", "10_concepts/child.md",
                "--direction", "inline",
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertIn("nested_transclusion", data.get("warnings", []))

    def test_extract_out_path_exists_errors(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "10_concepts" / "parent.md", {},
                "# parent\n\n## sec\nbody\n",
            )
            write_md(vault / "10_concepts" / "sec.md", {}, "existing\n")
            r = run_script(
                "extract_inline.py",
                "--vault", str(vault),
                "--page", "10_concepts/parent.md",
                "--section", "sec",
                "--direction", "extract",
            )
            self.assertEqual(r.returncode, 2)


class GraphRebalanceTest(unittest.TestCase):
    def test_detects_orphan_hub_and_link_gaps(self):
        if shutil.which("rg") is None:
            self.skipTest("ripgrep not installed")
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            # hub: referenced by many
            write_md(vault / "10_concepts" / "hub.md", {}, "# Hub\nhub\n")
            for nm in ("a", "b", "c"):
                write_md(
                    vault / "10_concepts" / f"{nm}.md", {},
                    f"# {nm}\nsee [[hub]]\n",
                )
            # orphan with title that another page mentions in text
            write_md(
                vault / "10_concepts" / "orphan.md", {},
                "# orphan-topic\norphan body\n",
            )
            write_md(
                vault / "10_concepts" / "mention.md", {},
                "# mention\nthis discusses orphan-topic without linking\n",
            )
            r = run_script(
                "graph_rebalance.py",
                "--vault", str(vault),
                "--scope", "concepts",
                "--hub-threshold", "2",
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertEqual(data["op"], "graph_rebalance")
            orphan_paths = {o["path"] for o in data["orphans"]}
            self.assertIn("10_concepts/orphan.md", orphan_paths)
            hub_paths = {h["path"] for h in data["hubs"]}
            self.assertIn("10_concepts/hub.md", hub_paths)

    def test_apply_appends_link_to_candidate(self):
        if shutil.which("rg") is None:
            self.skipTest("ripgrep not installed")
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "10_concepts" / "orphan.md", {},
                "# unique-orphan-key\nbody\n",
            )
            write_md(
                vault / "10_concepts" / "mention.md", {},
                "# mention\nrefers to unique-orphan-key in prose\n",
            )
            r = run_script(
                "graph_rebalance.py",
                "--vault", str(vault),
                "--scope", "concepts",
                "--apply",
            )
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            data = json.loads(r.stdout)
            self.assertTrue(data["applied"])
            mention_text = (
                vault / "10_concepts" / "mention.md"
            ).read_text(encoding="utf-8")
            # at least one orphan link appended somewhere in vault
            appended = mention_text.count("相关: [[orphan]]")
            # Either mention.md or orphan.md got the link — assert at least
            # one file in the vault now contains the linker line.
            any_appended = appended > 0 or any(
                "相关:" in (p.read_text(encoding="utf-8"))
                for p in vault.rglob("*.md")
            )
            self.assertTrue(any_appended)


if __name__ == "__main__":
    unittest.main()
