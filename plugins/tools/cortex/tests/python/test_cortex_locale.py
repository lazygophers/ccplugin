"""Tests for hooks/_lib/cortex_locale.py."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import PLUGIN_ROOT, add_paths

add_paths()

from cortex_locale import (  # noqa: E402
    Locale,
    _deep_merge,
    _fallback_chain,
    detect_vault_lang,
    load_locale,
    parse_yaml,
)


class ParseYamlTest(unittest.TestCase):
    def test_simple_kv(self):
        d = parse_yaml("a: 1\nb: hello\n")
        self.assertEqual(d, {"a": "1", "b": "hello"})

    def test_nested_map(self):
        d = parse_yaml("meta:\n  lang: zh-CN\n  fallback: en\n")
        self.assertEqual(d, {"meta": {"lang": "zh-CN", "fallback": "en"}})

    def test_flow_list(self):
        d = parse_yaml('tags: [a, "b", c]\n')
        self.assertEqual(d, {"tags": ["a", "b", "c"]})

    def test_block_list(self):
        d = parse_yaml("tags:\n  - a\n  - b\n")
        self.assertEqual(d, {"tags": ["a", "b"]})

    def test_quoted_scalar_preserves(self):
        d = parse_yaml('msg: "hello: world"\n')
        self.assertEqual(d["msg"], "hello: world")

    def test_comments_skipped(self):
        d = parse_yaml("# top comment\na: 1  # inline\nb: 2\n")
        self.assertEqual(d, {"a": "1", "b": "2"})

    def test_block_scalar(self):
        d = parse_yaml("note: |\n  line1\n  line2\n")
        self.assertIn("line1", d["note"])
        self.assertIn("line2", d["note"])

    def test_empty_input(self):
        self.assertEqual(parse_yaml(""), {})

    def test_malformed_does_not_raise(self):
        d = parse_yaml("a: 1\n  random_indented_no_parent\nb: 2\n")
        # parser is best-effort; should not crash
        self.assertIn("a", d)


class FallbackChainTest(unittest.TestCase):
    def test_zh_cn(self):
        self.assertEqual(_fallback_chain("zh-CN"), ["zh-CN", "zh", "en"])

    def test_en(self):
        self.assertEqual(_fallback_chain("en"), ["en"])

    def test_ja(self):
        self.assertEqual(_fallback_chain("ja"), ["ja", "en"])

    def test_unknown(self):
        # de -> en
        self.assertEqual(_fallback_chain("de"), ["de", "en"])


class DeepMergeTest(unittest.TestCase):
    def test_overwrite_scalar(self):
        a = {"x": 1, "y": 2}
        b = {"y": 3}
        self.assertEqual(_deep_merge(a, b), {"x": 1, "y": 3})

    def test_merge_nested(self):
        a = {"d": {"x": 1}}
        b = {"d": {"y": 2}}
        self.assertEqual(_deep_merge(a, b), {"d": {"x": 1, "y": 2}})


class LoadLocaleTest(unittest.TestCase):
    def test_load_zh_cn_dirs(self):
        loc = load_locale(PLUGIN_ROOT, None, "zh-CN")
        dirs = loc.get_dirs()
        self.assertEqual(dirs.get("concepts"), "概念")
        self.assertEqual(dirs.get("moc"), "MOC")

    def test_load_en_dirs(self):
        loc = load_locale(PLUGIN_ROOT, None, "en")
        dirs = loc.get_dirs()
        self.assertEqual(dirs.get("concepts"), "concepts")

    def test_load_ja_dirs(self):
        loc = load_locale(PLUGIN_ROOT, None, "ja")
        dirs = loc.get_dirs()
        self.assertEqual(dirs.get("entities"), "エンティティ")

    def test_unknown_lang_falls_back_to_en(self):
        loc = load_locale(PLUGIN_ROOT, None, "de")
        dirs = loc.get_dirs()
        # de has no file → fallback en
        self.assertEqual(dirs.get("concepts"), "concepts")

    def test_get_prompt_with_format(self):
        loc = load_locale(PLUGIN_ROOT, None, "zh-CN")
        s = loc.get_prompt("archive_pending", path="log/foo.md")
        self.assertIn("log/foo.md", s)

    def test_get_prompt_missing_returns_empty(self):
        loc = load_locale(PLUGIN_ROOT, None, "zh-CN")
        self.assertEqual(loc.get_prompt("nonexistent_key"), "")

    def test_chain(self):
        loc = load_locale(PLUGIN_ROOT, None, "zh-CN")
        self.assertEqual(loc.chain(), ["zh-CN", "zh", "en"])


class VaultOverrideTest(unittest.TestCase):
    def test_vault_override_wins(self):
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            (vault / "locales").mkdir()
            (vault / "locales" / "zh-CN.yml").write_text(
                "dirs:\n  concepts: 测试概念\n", encoding="utf-8"
            )
            loc = load_locale(PLUGIN_ROOT, vault, "zh-CN")
            self.assertEqual(loc.get_dirs().get("concepts"), "测试概念")
            # other dirs still inherit from plugin builtin
            self.assertEqual(loc.get_dirs().get("entities"), "实体")


class DetectVaultLangTest(unittest.TestCase):
    def test_default_when_missing(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(detect_vault_lang(Path(d)), "zh-CN")

    def test_reads_lang(self):
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            (vault / "_meta").mkdir()
            (vault / "_meta" / "version.json").write_text(
                '{"lang": "ja"}', encoding="utf-8"
            )
            self.assertEqual(detect_vault_lang(vault), "ja")

    def test_malformed_json(self):
        with tempfile.TemporaryDirectory() as d:
            vault = Path(d)
            (vault / "_meta").mkdir()
            (vault / "_meta" / "version.json").write_text("{not json", encoding="utf-8")
            self.assertEqual(detect_vault_lang(vault), "zh-CN")


class DetectVaultLangFallbackChainTest(unittest.TestCase):
    """env > _meta > config.lang > zh-CN."""

    def setUp(self):
        self._tmp_home = tempfile.TemporaryDirectory()
        self._tmp_vault = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp_home.name)
        self.vault = Path(self._tmp_vault.name)
        # Clear env + redirect HOME so real ~/.cortex/config.json is invisible.
        self._env = mock.patch.dict(
            os.environ, {"HOME": str(self.home)}, clear=False
        )
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

    def test_env_ignored_for_lang(self):
        """Per PRD: CORTEX_LANG env is no longer consulted; meta wins."""
        self._write_meta("ja")
        self._write_cfg("fr")
        os.environ["CORTEX_LANG"] = "en-US"
        # env is ignored; vault meta wins over config and env.
        self.assertEqual(detect_vault_lang(self.vault), "ja")

    def test_meta_wins_over_config(self):
        self._write_meta("ja")
        self._write_cfg("fr")
        self.assertEqual(detect_vault_lang(self.vault), "ja")

    def test_config_used_when_meta_missing(self):
        self._write_cfg("fr")
        self.assertEqual(detect_vault_lang(self.vault), "fr")

    def test_default_when_all_missing(self):
        self.assertEqual(detect_vault_lang(self.vault), "zh-CN")


class LocaleClassTest(unittest.TestCase):
    def test_get_dotted_key(self):
        loc = Locale(PLUGIN_ROOT, None, "zh-CN")
        self.assertEqual(loc.get("meta.lang"), "zh-CN")

    def test_get_default(self):
        loc = Locale(PLUGIN_ROOT, None, "zh-CN")
        self.assertIsNone(loc.get("totally.missing.key"))


if __name__ == "__main__":
    unittest.main()
