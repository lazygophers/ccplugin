"""Tests for lint/run.py."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import PLUGIN_ROOT, add_paths, make_vault, write_md

add_paths()

import run as lint_run  # noqa: E402

SCRIPT = PLUGIN_ROOT / "scripts" / "lint" / "run.py"


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
                vault / "知识库" / "领域" / "demo.md",
                {"type": "concept", "title": "demo", "created": "2026-05-11",
                 "tags": ["x"]},
                "# demo\n\nbody\n",
            )
            rc, rep = run_lint(vault)
            self.assertEqual(rc, 0)
            # demo.md itself should not have a fm-missing-type / dead-wikilink finding
            for f in rep["errors"]:
                self.assertNotEqual(f["file"], "知识库/领域/demo.md", msg=str(f))

    def test_rule1_fm_missing_type(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "知识库" / "领域" / "x.md",
                     {"title": "x", "created": "2026-05-11"}, "# x\n")
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-type", rules_hit(rep))

    def test_rule2_fm_missing_created(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "知识库" / "领域" / "x.md", {"type": "concept", "title": "x"},
                     "# x\n")
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-created", rules_hit(rep))

    def test_rule_fm_duplicate_tags(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["a", "b", "a", "c", "b"]},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("fm-duplicate-tags", rules_hit(rep))

    def test_rule_fm_banned_fields(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["go"], "preset": "lyt"},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("fm-banned-fields", rules_hit(rep))

    def test_rule_fm_banned_fields_autofix(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "知识库" / "领域" / "x.md"
            write_md(
                p,
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["go"], "preset": "lyt"},
                "# x\n",
            )
            run_lint(vault, "--fix")
            text = p.read_text(encoding="utf-8")
            import re as _re
            import yaml as _yaml
            m = _re.match(r"^---\n(.*?)\n---", text, _re.S)
            fm = _yaml.safe_load(m.group(1))
            self.assertNotIn("preset", fm)

    def test_rule_fm_missing_tags(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11"},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-tags", rules_hit(rep))

    def test_rule_fm_missing_tags_autofix(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "知识库" / "领域" / "x.md"
            # 提供足够 fm + 正文派生信息, autofix 应能补到 ≥10
            write_md(
                p,
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "lang": "zh-CN", "host": "example.com", "org": "demo",
                 "repo": "demo-repo", "source_url": "https://example.com/x",
                 "maturity": "draft", "score": 3},
                "# 标题甲\n\n## 子标题乙\n\n这是一段中文正文 关于 数据库 索引 优化。\n"
                "包含 PostgreSQL 与 MySQL 比较。MoreContent SomePhrase\n",
            )
            run_lint(vault, "--fix")
            text = p.read_text(encoding="utf-8")
            import re as _re
            import yaml as _yaml
            m = _re.match(r"^---\n(.*?)\n---", text, _re.S)
            fm = _yaml.safe_load(m.group(1))
            self.assertIn("tags", fm)
            self.assertIsInstance(fm["tags"], list)
            self.assertGreaterEqual(len(fm["tags"]), 10)

    def test_rule_fm_banned_tags(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["go", "meta", "index"]},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("fm-banned-tags", rules_hit(rep))

    def test_rule_fm_banned_tags_autofix(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "知识库" / "领域" / "x.md"
            write_md(
                p,
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["go", "meta", "index", "channel"]},
                "# x\n",
            )
            run_lint(vault, "--fix")
            text = p.read_text(encoding="utf-8")
            import re as _re
            import yaml as _yaml
            m = _re.match(r"^---\n(.*?)\n---", text, _re.S)
            fm = _yaml.safe_load(m.group(1))
            tg = fm["tags"]
            for banned in ("meta", "index"):
                self.assertNotIn(banned, tg)
            self.assertIn("go", tg)
            self.assertIn("channel", tg)

    def test_rule_fm_duplicate_tags_autofix(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "知识库" / "领域" / "x.md"
            write_md(
                p,
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["a", "b", "a", "c", "b"]},
                "# x\n",
            )
            run_lint(vault, "--fix")
            text = p.read_text(encoding="utf-8")
            # parse fm
            import re as _re
            import yaml as _yaml
            m = _re.match(r"^---\n(.*?)\n---", text, _re.S)
            fm = _yaml.safe_load(m.group(1))
            tg = fm["tags"]
            # dedup'd; schema 可能追加 required tag, 只检测顺序保持 + 去重
            for v in ("a", "b", "c"):
                self.assertEqual(tg.count(v), 1)

    def test_rule3_dead_wikilink(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11"},
                "[[Nonexistent]]\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("dead-wikilink", rules_hit(rep))

    def test_rule4_orphan_page(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "lonely.md",
                {"type": "concept", "title": "lonely", "created": "2026-05-11"},
                "# lonely\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("orphan-page", rules_hit(rep))

    def test_rule5_duplicate_alias(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "知识库" / "领域" / "a.md",
                     {"type": "concept", "title": "Same", "created": "2026-05-11",
                      "tags": ["t"]}, "# Same\n")
            write_md(vault / "知识库" / "领域" / "b.md",
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
            (vault / "知识库" / "领域").mkdir(parents=True)
            write_md(vault / "知识库" / "领域" / "x.md",
                     {"type": "concept", "title": "x",
                      "created": "2026-05-11", "tags": ["t"]}, "x")
            (vault / "index.md").write_text("# index\n", encoding="utf-8")
            rc, rep = run_lint(vault)
            self.assertIn("index-missing-section", rules_hit(rep))

    def test_rule9_title_h1_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(vault / "知识库" / "领域" / "x.md",
                     {"type": "concept", "title": "Real Title",
                      "created": "2026-05-11", "tags": ["t"]},
                     "# Wrong H1\n")
            rc, rep = run_lint(vault)
            self.assertIn("title-h1-mismatch", rules_hit(rep))

    def test_rule10_filename_illegal(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            bad = vault / "知识库" / "领域" / "bad?name.md"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_text("---\ntype: concept\ntitle: x\ncreated: 2026-05-11\ntags: [t]\n---\n# x\n", encoding="utf-8")
            rc, rep = run_lint(vault)
            self.assertIn("filename-illegal", rules_hit(rep))

    def test_rule11_block_id_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            for n in ("a", "b"):
                write_md(
                    vault / "知识库" / "领域" / f"{n}.md",
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
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x",
                 "created": "2026-05-11", "tags": ["t"]},
                "# x\n\n> [!unknownweird] something\n> body\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("callout-unknown-type", rules_hit(rep))

    def test_rule13_legacy_log_dir_is_structure_violation(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            bad = vault / "log" / "2026-05" / "anything.md"
            bad.parent.mkdir(parents=True, exist_ok=True)
            bad.write_text("---\ntype: log\ntitle: x\ncreated: 2026-05-11\n---\n# x\n", encoding="utf-8")
            rc, rep = run_lint(vault)
            self.assertIn("vault-structure-violation", rules_hit(rep))

    def test_rule14_i18n_lang_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d), lang="zh-CN")
            write_md(
                vault / "知识库" / "领域" / "x.md",
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

    # --- fm-missing-tags ≥10 强制规则 (新行为) ---

    def test_rule_fm_missing_tags_field_absent(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11"},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-tags", rules_hit(rep))

    def test_rule_fm_missing_tags_too_few(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            write_md(
                vault / "知识库" / "领域" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["a", "b", "c"]},
                "# x\n",
            )
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-tags", rules_hit(rep))

    def test_rule_fm_missing_tags_autofix_derives_from_fm_and_body(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "知识库" / "领域" / "x.md"
            write_md(
                p,
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "lang": "zh-CN", "host": "example.com", "org": "demo",
                 "repo": "demo-repo", "maturity": "draft", "score": 3,
                 "source_url": "https://example.com/x"},
                "# 一个标题\n\n## 子主题\n\n这里 介绍 数据库 索引 优化 方案。SomeWord OtherTerm\n",
            )
            run_lint(vault, "--fix")
            text = p.read_text(encoding="utf-8")
            import re as _re
            import yaml as _yaml
            m = _re.match(r"^---\n(.*?)\n---", text, _re.S)
            fm = _yaml.safe_load(m.group(1))
            self.assertGreaterEqual(len(fm.get("tags") or []), 10)

    def test_rule_fm_missing_tags_autofix_rejects_placeholders(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "知识库" / "领域" / "x.md"
            write_md(
                p,
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "lang": "zh-CN", "host": "example.com", "org": "demo",
                 "repo": "demo-repo", "maturity": "draft", "score": 3,
                 "source_url": "https://example.com/x"},
                "# 一个标题\n\n## 子主题\n\n这里 介绍 数据库 索引 优化。SomeWord OtherTerm\n",
            )
            run_lint(vault, "--fix")
            text = p.read_text(encoding="utf-8")
            import re as _re
            import yaml as _yaml
            m = _re.match(r"^---\n(.*?)\n---", text, _re.S)
            fm = _yaml.safe_load(m.group(1))
            tags = fm.get("tags") or []
            for t in tags:
                self.assertNotRegex(
                    str(t),
                    r"<.*?>|placeholder|TODO|待填|TBD|FIXME",
                    msg=f"autofix 不应写占位符: {t}",
                )

    def test_rule_fm_missing_tags_autofix_cant_fill_keeps_warn(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            p = vault / "知识库" / "领域" / "x.md"
            # 极简 fm + 极简 body, 派生不到 10 个
            write_md(
                p,
                {"type": "concept", "title": "x", "created": "2026-05-11"},
                "# x\n",
            )
            run_lint(vault, "--fix")
            # 再跑一次 lint, 应仍有 fm-missing-tags warning
            rc, rep = run_lint(vault)
            self.assertIn("fm-missing-tags", rules_hit(rep))

    def test_lint_skip_short_circuits_all_checks(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            # 写一个缺各种 fm + 含 dead wikilink 的页, 但加 lint-skip
            p = vault / "知识库" / "领域" / "tpl.md"
            write_md(
                p,
                {"lint-skip": True, "type": "concept", "title": "tpl",
                 "created": "2026-05-11"},
                "# tpl\n\n[[non-existent-target]]\n",
            )
            rc, rep = run_lint(vault)
            # 该文件不应出现在 findings 内
            for f in rep.get("errors", []) + rep.get("warnings", []):
                self.assertNotEqual(f["file"], "知识库/领域/tpl.md", msg=str(f))


class AutofixTest(unittest.TestCase):
    def test_fix_missing_type(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            f = vault / "知识库" / "领域" / "x.md"
            write_md(f, {"title": "x", "created": "2026-05-11", "tags": ["t"]},
                     "# x\n")
            rc, rep = run_lint(vault, "--fix")
            self.assertEqual(rc, 0)
            self.assertGreater(rep["summary"]["fixed"], 0)
            text = f.read_text(encoding="utf-8")
            self.assertIn("type:", text)
            # backup dir is created OUTSIDE the vault
            # (~/.cache/cortex/lint-backup/<vault-hash>/<ts>/), never inside.
            self.assertFalse((vault / "_meta" / ".cortex-backup").exists())
            import hashlib
            vh = hashlib.sha256(str(vault.resolve()).encode()).hexdigest()[:8]
            backup_root = Path.home() / ".cache" / "cortex" / "lint-backup" / vh
            self.assertTrue(backup_root.is_dir())
            # at least one ts subdir
            self.assertTrue(any(backup_root.iterdir()))

    def test_fix_h1_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            vault = make_vault(Path(d))
            f = vault / "知识库" / "领域" / "x.md"
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
            # `concepts` at vault root is illegal in any preset (flat-layout
            # sub-namespace dirs must live under 知识库/). With lang=en the
            # i18n rule no longer recognizes it as legal top-level.
            write_md(
                vault / "concepts" / "x.md",
                {"type": "concept", "title": "x", "created": "2026-05-11",
                 "tags": ["t"]},
                "# x\n",
            )
            rc, rep = run_lint(vault, "--lang", "en")
            # 现在统一: concepts 应在 知识库/ 下, root 出现属结构违规
            self.assertIn("vault-structure-violation", rules_hit(rep))


class LoadVaultLangFallbackChainTest(unittest.TestCase):
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

    def test_env_ignored_for_lang(self):
        """Per PRD: CORTEX_LANG env is no longer consulted; meta wins."""
        self._write_meta("ja")
        self._write_cfg("fr")
        os.environ["CORTEX_LANG"] = "en-US"
        self.assertEqual(lint_run._load_vault_lang(self.vault), "ja")

    def test_meta_wins_over_config(self):
        self._write_meta("ja")
        self._write_cfg("fr")
        self.assertEqual(lint_run._load_vault_lang(self.vault), "ja")

    def test_config_used_when_meta_missing(self):
        self._write_cfg("fr")
        self.assertEqual(lint_run._load_vault_lang(self.vault), "fr")

    def test_default_when_all_missing(self):
        self.assertEqual(lint_run._load_vault_lang(self.vault), "zh-CN")


if __name__ == "__main__":
    unittest.main()
