"""Tests for hooks/_lib/save_session.py."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import PLUGIN_ROOT, add_paths, make_vault

add_paths()

import save_session as ss  # noqa: E402

SCRIPT = PLUGIN_ROOT / "hooks" / "_lib" / "save_session.py"


def _make_transcript(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")


def _user(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def _assistant(text: str) -> dict:
    return {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
    }


class HeuristicTest(unittest.TestCase):
    def test_trivial_no_kw_returns_false(self):
        s = ss.heuristic_score("hello world")
        self.assertFalse(ss.is_nontrivial(s))

    def test_two_keywords_triggers(self):
        s = ss.heuristic_score("debug fix 修复")
        self.assertTrue(ss.is_nontrivial(s))

    def test_three_file_lines_triggers(self):
        s = ss.heuristic_score("src/a.py:10 and lib/b.rs:42 plus mod/c.go:1-3")
        self.assertTrue(ss.is_nontrivial(s))

    def test_diff_triggers(self):
        s = ss.heuristic_score("diff --git a/foo b/foo\n@@ -1,2 +1,2 @@")
        self.assertTrue(ss.is_nontrivial(s))


class SlugifyTest(unittest.TestCase):
    def test_chinese_kept(self):
        s = ss.slugify("修复 auth 中间件")
        self.assertTrue(s)
        self.assertNotIn("/", s)

    def test_long_truncated(self):
        s = ss.slugify("a" * 200, max_len=40)
        self.assertLessEqual(len(s), 40)

    def test_empty(self):
        self.assertEqual(ss.slugify(""), "session")

    def test_illegal_chars_stripped(self):
        s = ss.slugify("hello: world?*<>")
        for c in ":?*<>":
            self.assertNotIn(c, s)


class ExtractTextTest(unittest.TestCase):
    def test_string_content(self):
        e = {"role": "user", "content": "hi"}
        self.assertEqual(ss.extract_text_from_entry(e), "hi")

    def test_list_content(self):
        e = {"message": {"content": [{"type": "text", "text": "abc"}]}}
        self.assertEqual(ss.extract_text_from_entry(e), "abc")

    def test_tool_use_redacted(self):
        e = {"message": {"content": [{"type": "tool_use", "name": "Bash"}]}}
        self.assertIn("Bash", ss.extract_text_from_entry(e))


class CollectFilesTest(unittest.TestCase):
    def test_dedupe_and_limit(self):
        text = "src/a.py:1 src/a.py:2 lib/b.rs:10"
        files = ss.collect_modified_files(text)
        self.assertEqual(files, ["src/a.py", "lib/b.rs"])


class InjectBlockIdsTest(unittest.TestCase):
    def test_h2_injected(self):
        body = "## A\n\ntext\n\n## B\n\nmore\n"
        used: set[str] = set()
        out = ss.inject_block_ids(body, "seed", used)
        self.assertIn("^cortex-", out)
        self.assertEqual(len(used), 2)

    def test_no_headings_unchanged(self):
        body = "just text\n"
        out = ss.inject_block_ids(body, "seed", set())
        self.assertEqual(out, body)

    def test_collision_rehash(self):
        used: set[str] = set()
        # pre-fill with the natural sha8 to force collision
        body = "## A\n\ntext\n"
        first = ss.inject_block_ids(body, "seed", used)
        self.assertEqual(len(used), 1)
        # second call with same seed → must rehash
        used2 = set(used)
        ss.inject_block_ids(body, "seed", used2)
        self.assertEqual(len(used2), 2)
        self.assertNotEqual(first, "")


class ReadVaultMetaTest(unittest.TestCase):
    def test_missing_returns_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(ss.read_vault_meta(Path(d)), {})

    def test_reads_meta(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            self.assertEqual(ss.read_vault_meta(vault).get("lang"), "zh-CN")


class ReadVaultLangFallbackChainTest(unittest.TestCase):
    """env > _meta > config.lang > zh-CN."""

    def setUp(self):
        self._tmp_home = tempfile.TemporaryDirectory()
        self._tmp_vault = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp_home.name)
        self.vault = Path(self._tmp_vault.name)
        self._env = mock.patch.dict(os.environ, {"HOME": str(self.home)}, clear=False)
        self._env.start()
        os.environ.pop("CORTEX_LANG", None)

    def tearDown(self):
        self._env.stop()
        self._tmp_home.cleanup()
        self._tmp_vault.cleanup()

    def _write_meta(self, lang):
        (self.vault / "_meta").mkdir(exist_ok=True)
        (self.vault / "_meta" / "version.json").write_text(
            json.dumps({"lang": lang}), encoding="utf-8"
        )

    def _write_cfg(self, lang):
        (self.home / ".cortex").mkdir(exist_ok=True)
        (self.home / ".cortex" / "config.json").write_text(
            json.dumps({"lang": lang}), encoding="utf-8"
        )

    def test_env_wins(self):
        self._write_meta("ja")
        self._write_cfg("fr")
        os.environ["CORTEX_LANG"] = "en-US"
        self.assertEqual(ss.read_vault_lang(self.vault), "en-US")

    def test_meta_wins_over_config(self):
        self._write_meta("ja")
        self._write_cfg("fr")
        self.assertEqual(ss.read_vault_lang(self.vault), "ja")

    def test_config_used_when_meta_missing(self):
        self._write_cfg("fr")
        self.assertEqual(ss.read_vault_lang(self.vault), "fr")

    def test_default_when_all_missing(self):
        self.assertEqual(ss.read_vault_lang(self.vault), "zh-CN")


class HasObsidianGitTest(unittest.TestCase):
    def test_false_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            self.assertFalse(ss.has_obsidian_git(vault))

    def test_true_when_present(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / ".obsidian" / "plugins" / "obsidian-git"
            p.mkdir(parents=True)
            (p / "data.json").write_text("{}", encoding="utf-8")
            self.assertTrue(ss.has_obsidian_git(vault))


class IntegrationCLITest(unittest.TestCase):
    def _run(self, args: list[str], cwd: Path | None = None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(cwd) if cwd else None,
        )

    def test_missing_vault_exits_1(self):
        r = self._run(["--vault", "/tmp/nonexistent-cortex-vault-xxx"])
        self.assertEqual(r.returncode, 1)

    def test_trivial_stop_returns_2(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            tp = vault / "transcript.jsonl"
            _make_transcript(tp, [_user("hello"), _assistant("hi there")])
            r = self._run([
                "--vault", str(vault),
                "--transcript", str(tp),
                "--reason", "stop",
            ])
            self.assertEqual(r.returncode, 2, msg=r.stderr)

    def test_nontrivial_stop_writes_log(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            tp = vault / "transcript.jsonl"
            payload = (
                "决策 修复 src/a.py:10 lib/b.rs:42 mod/c.go:5\n"
                "diff --git a/foo b/foo\n@@ -1,1 +1,1 @@\n"
            )
            _make_transcript(tp, [_user("帮我决策"), _assistant(payload)])
            r = self._run([
                "--vault", str(vault),
                "--transcript", str(tp),
                "--reason", "stop",
            ])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            out_path = Path(r.stdout.strip())
            self.assertTrue(out_path.is_file())
            text = out_path.read_text(encoding="utf-8")
            self.assertIn("lang: zh-CN", text)
            self.assertIn("cli: claude-code", text)
            # block-id present
            self.assertIn("^cortex-", text)

    def test_manual_force_writes(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            r = self._run([
                "--vault", str(vault),
                "--reason", "manual",
                "--title", "manual test entry",
                "--cli", "manual",
                "--cli-session", "abc-123",
            ])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            text = Path(r.stdout.strip()).read_text(encoding="utf-8")
            self.assertIn("cli: manual", text)
            self.assertIn("cli_session: abc-123", text)

    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            r = self._run([
                "--vault", str(vault),
                "--reason", "manual",
                "--title", "dry test",
                "--dry-run",
            ])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            self.assertFalse(Path(r.stdout.strip()).exists())

    def test_preserve_transcript_backs_up(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), preserve_transcript=True)
            tp = vault / "transcript.jsonl"
            _make_transcript(tp, [_user("决策 配置 修复")])
            r = self._run([
                "--vault", str(vault),
                "--transcript", str(tp),
                "--reason", "manual",
                "--title", "preserve-test",
            ])
            self.assertEqual(r.returncode, 0, msg=r.stderr)
            sess = vault / "sessions" / "claude-code"
            jsonls = list(sess.rglob("*.jsonl"))
            self.assertEqual(len(jsonls), 1)


if __name__ == "__main__":
    unittest.main()
