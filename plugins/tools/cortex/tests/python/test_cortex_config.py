"""Tests for hooks/_lib/cortex_config.py."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import add_paths

add_paths()

from cortex_config import (  # noqa: E402
    ConfigSyntaxError,
    load_config,
    resolve,
)


class _FakeHomeMixin:
    """Provide a tmp $HOME so tests never touch real ~/.cortex/."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        self.cfg_dir = self.home / ".cortex"
        self._env_patch = mock.patch.dict(os.environ, {"HOME": str(self.home)})
        self._env_patch.start()

    def tearDown(self):
        self._env_patch.stop()
        self._tmp.cleanup()

    def write_cfg(self, data):
        self.cfg_dir.mkdir(parents=True, exist_ok=True)
        path = self.cfg_dir / "config.json"
        if isinstance(data, str):
            path.write_text(data, encoding="utf-8")
        else:
            path.write_text(json.dumps(data), encoding="utf-8")
        return path


class LoadConfigTest(_FakeHomeMixin, unittest.TestCase):
    def test_missing_returns_empty(self):
        self.assertEqual(load_config(), {})

    def test_valid_returns_dict(self):
        self.write_cfg({"vault": "/v", "lang": "zh-CN"})
        self.assertEqual(load_config(), {"vault": "/v", "lang": "zh-CN"})

    def test_invalid_json_raises(self):
        self.write_cfg("{not json")
        with self.assertRaises(ConfigSyntaxError) as ctx:
            load_config()
        self.assertIn("config syntax error at", str(ctx.exception))

    def test_non_object_root_raises(self):
        self.write_cfg("[1, 2, 3]")
        with self.assertRaises(ConfigSyntaxError):
            load_config()


class ResolveTest(_FakeHomeMixin, unittest.TestCase):
    def test_env_overrides_config(self):
        self.write_cfg({"vault": "/from-config"})
        with mock.patch.dict(os.environ, {"CORTEX_VAULT": "/from-env"}):
            self.assertEqual(
                resolve("vault", "CORTEX_VAULT", "/fallback"),
                "/from-env",
            )

    def test_config_overrides_fallback(self):
        self.write_cfg({"vault": "/from-config"})
        env = {k: v for k, v in os.environ.items() if k != "CORTEX_VAULT"}
        with mock.patch.dict(os.environ, env, clear=True):
            os.environ["HOME"] = str(self.home)
            self.assertEqual(
                resolve("vault", "CORTEX_VAULT", "/fallback"),
                "/from-config",
            )

    def test_fallback_when_env_and_config_missing(self):
        env = {k: v for k, v in os.environ.items() if k != "CORTEX_VAULT"}
        with mock.patch.dict(os.environ, env, clear=True):
            os.environ["HOME"] = str(self.home)
            self.assertEqual(
                resolve("vault", "CORTEX_VAULT", "/fallback"),
                "/fallback",
            )

    def test_empty_config_value_falls_through(self):
        self.write_cfg({"vault": ""})
        env = {k: v for k, v in os.environ.items() if k != "CORTEX_VAULT"}
        with mock.patch.dict(os.environ, env, clear=True):
            os.environ["HOME"] = str(self.home)
            self.assertEqual(
                resolve("vault", "CORTEX_VAULT", "/fallback"),
                "/fallback",
            )

    def test_no_env_var_argument(self):
        self.write_cfg({"lang": "en"})
        self.assertEqual(resolve("lang", None, "zh-CN"), "en")


if __name__ == "__main__":
    unittest.main()
