"""Tests for scripts/cortex_config.py CLI."""
from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _helpers import add_paths

add_paths()

# The CLI module shares its name with the loader (`cortex_config`). Load it
# from an explicit path via importlib so test order can't shadow it.
import importlib.util as _ilu  # noqa: E402

_PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_CLI_PATH = _PLUGIN_ROOT / "scripts" / "cortex_config.py"
_spec = _ilu.spec_from_file_location("_cortex_config_cli_under_test", _CLI_PATH)
cli = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(cli)


class _FakeHomeMixin:
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.cfg_dir = self.home / ".cortex"
        self.cfg_path = self.cfg_dir / "config.json"
        self._env_patch = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        self._env_patch.start()
        # Real existing path used as valid vault/settings/install_path value.
        self.real_dir = self.home / "real"
        self.real_dir.mkdir()

    def tearDown(self):
        self._env_patch.stop()
        self._tmp.cleanup()

    def write_cfg(self, data):
        self.cfg_dir.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            self.cfg_path.write_text(data, encoding="utf-8")
        else:
            self.cfg_path.write_text(json.dumps(data), encoding="utf-8")

    def run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv)
            except SystemExit as e:
                rc = int(e.code) if e.code is not None else 0
        return rc, out.getvalue(), err.getvalue()


class GetCmdTest(_FakeHomeMixin, unittest.TestCase):
    def test_get_existing(self):
        self.write_cfg({"vault": "/v"})
        rc, out, _ = self.run_cli(["get", "vault"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "/v")

    def test_get_missing_field_empty(self):
        self.write_cfg({"vault": "/v"})
        rc, out, _ = self.run_cli(["get", "lang"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_get_no_config(self):
        rc, out, _ = self.run_cli(["get", "vault"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

    def test_get_unknown_key(self):
        rc, _, err = self.run_cli(["get", "bogus"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown key", err)


class SetCmdTest(_FakeHomeMixin, unittest.TestCase):
    def test_set_valid_path(self):
        rc, _, _ = self.run_cli(["set", "vault", str(self.real_dir)])
        self.assertEqual(rc, 0)
        data = json.loads(self.cfg_path.read_text())
        self.assertEqual(data["vault"], str(self.real_dir))

    def test_set_invalid_path(self):
        rc, _, err = self.run_cli(["set", "vault", "/nonexistent/abs/path/xyz"])
        self.assertEqual(rc, 1)
        self.assertIn("does not exist", err)

    def test_set_invalid_lang(self):
        rc, _, err = self.run_cli(["set", "lang", "not-a-locale-string"])
        self.assertEqual(rc, 1)
        self.assertIn("invalid lang code", err)

    def test_set_valid_lang(self):
        rc, _, _ = self.run_cli(["set", "lang", "zh-CN"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(self.cfg_path.read_text())["lang"], "zh-CN")

    def test_set_unknown_key(self):
        rc, _, err = self.run_cli(["set", "bogus", "x"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown key", err)

    def test_set_merges_with_existing(self):
        self.write_cfg({"lang": "zh-CN"})
        rc, _, _ = self.run_cli(["set", "vault", str(self.real_dir)])
        self.assertEqual(rc, 0)
        data = json.loads(self.cfg_path.read_text())
        self.assertEqual(data["lang"], "zh-CN")
        self.assertEqual(data["vault"], str(self.real_dir))

    def test_set_does_not_corrupt_on_invalid(self):
        self.write_cfg({"lang": "zh-CN"})
        rc, _, _ = self.run_cli(["set", "vault", "/no/such/path"])
        self.assertEqual(rc, 1)
        # Original file untouched.
        self.assertEqual(json.loads(self.cfg_path.read_text()), {"lang": "zh-CN"})


class InitCmdTest(_FakeHomeMixin, unittest.TestCase):
    def test_non_interactive_all_flags(self):
        rc, _, _ = self.run_cli([
            "init", "--non-interactive",
            "--vault", str(self.real_dir),
            "--lang", "en",
            "--settings", str(self.real_dir),
            "--install-path", str(self.real_dir),
        ])
        self.assertEqual(rc, 0)
        data = json.loads(self.cfg_path.read_text())
        self.assertEqual(data["vault"], str(self.real_dir))
        self.assertEqual(data["lang"], "en")
        self.assertEqual(data["settings"], str(self.real_dir))
        self.assertEqual(data["install_path"], str(self.real_dir))

    def test_non_interactive_partial(self):
        rc, _, _ = self.run_cli([
            "init", "--non-interactive",
            "--lang", "zh-CN",
        ])
        self.assertEqual(rc, 0)
        data = json.loads(self.cfg_path.read_text())
        self.assertEqual(data, {"lang": "zh-CN"})

    def test_non_interactive_invalid_lang(self):
        rc, _, err = self.run_cli([
            "init", "--non-interactive", "--lang", "?bad?",
        ])
        self.assertEqual(rc, 1)
        self.assertIn("invalid lang code", err)

    def test_non_interactive_preserves_existing(self):
        self.write_cfg({"vault": str(self.real_dir), "lang": "en"})
        rc, _, _ = self.run_cli([
            "init", "--non-interactive", "--lang", "ja",
        ])
        self.assertEqual(rc, 0)
        data = json.loads(self.cfg_path.read_text())
        self.assertEqual(data["vault"], str(self.real_dir))
        self.assertEqual(data["lang"], "ja")


class ValidateCmdTest(_FakeHomeMixin, unittest.TestCase):
    def test_validate_absent(self):
        rc, out, _ = self.run_cli(["validate"])
        self.assertEqual(rc, 0)
        self.assertIn("config absent", out)

    def test_validate_ok(self):
        self.write_cfg({"vault": str(self.real_dir), "lang": "zh-CN"})
        rc, out, _ = self.run_cli(["validate"])
        self.assertEqual(rc, 0)
        self.assertIn("config ok", out)

    def test_validate_bad_json(self):
        self.write_cfg("{not json")
        rc, _, err = self.run_cli(["validate"])
        self.assertEqual(rc, 1)
        self.assertIn("config syntax error", err)

    def test_validate_bad_field(self):
        self.write_cfg({"vault": "/no/such/path", "lang": "??"})
        rc, out, _ = self.run_cli(["validate"])
        self.assertEqual(rc, 1)
        self.assertIn("config invalid", out)
        self.assertIn("vault:", out)
        self.assertIn("lang:", out)

    def test_validate_unknown_key(self):
        self.write_cfg({"bogus": "x"})
        rc, out, _ = self.run_cli(["validate"])
        self.assertEqual(rc, 1)
        self.assertIn("bogus:", out)
        self.assertIn("unknown key", out)


if __name__ == "__main__":
    unittest.main()
