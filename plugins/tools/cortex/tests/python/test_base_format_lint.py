"""Tests for lint rule: base-format-yaml.

.base 文件必须顶层 YAML object + 禁 markdown / Dataview DQL.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _helpers import add_paths

add_paths()

import run as lint_run  # noqa: E402


def _rules(findings: list[dict]) -> list[str]:
    return [f["rule"] for f in findings]


class BaseFormatYamlTest(unittest.TestCase):
    def test_base_yaml_valid(self):
        content = (
            "filters:\n"
            "  and:\n"
            '    - file.ext == "md"\n'
            "views:\n"
            "  - type: table\n"
            "    name: all\n"
        )
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(findings, [])

    def test_base_markdown_header(self):
        content = "# scode Bases\n\n## 项目\n- foo: bar\n"
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["rule"], "base-format-yaml")
        self.assertIn("markdown header", findings[0]["msg"])

    def test_base_dataview_dql_table(self):
        content = 'TABLE file, tags FROM "知识库/项目/foo"\nSORT file ASC\n'
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(len(findings), 1)
        self.assertIn("TABLE", findings[0]["msg"].upper())
        self.assertIn("Dataview", findings[0]["msg"])

    def test_base_dataview_dql_list(self):
        content = "LIST FROM #tag\n"
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(len(findings), 1)
        self.assertIn("LIST", findings[0]["msg"].upper())

    def test_base_yaml_invalid(self):
        # 不合法 YAML — mapping value 后再次冒号
        content = "key: : :\n  : invalid\n"
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(len(findings), 1)
        self.assertIn("YAML 解析失败", findings[0]["msg"])

    def test_base_yaml_list_top(self):
        content = "- item1\n- item2\n"
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(len(findings), 1)
        self.assertIn("dict", findings[0]["msg"])

    def test_base_yaml_no_schema_field(self):
        content = "foo: bar\nbaz: qux\n"
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(len(findings), 1)
        self.assertIn("Bases schema", findings[0]["msg"])

    def test_non_base_file_skip(self):
        content = "# This is markdown\n"
        findings = lint_run.check_base_format_yaml(Path("vault/test.md"), content)
        self.assertEqual(findings, [])

    def test_obsidian_dir_skip(self):
        content = "# Invalid header in .obsidian"
        findings = lint_run.check_base_format_yaml(
            Path("vault/.obsidian/foo.base"), content
        )
        self.assertEqual(findings, [])

    def test_archive_skip(self):
        content = 'TABLE FROM "..."\n'
        findings = lint_run.check_base_format_yaml(
            Path("vault/归档/old.base"), content
        )
        self.assertEqual(findings, [])

    def test_trash_skip(self):
        content = "# trash"
        findings = lint_run.check_base_format_yaml(
            Path("vault/.trash/dead.base"), content
        )
        self.assertEqual(findings, [])

    def test_base_valid_with_views_only(self):
        """只有 views 字段也是合法 (filters/views/formulas/properties 任一即可)."""
        content = "views:\n  - type: table\n    name: all\n"
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(findings, [])

    def test_base_dataview_group_by(self):
        """GROUP BY 多词关键字也命中."""
        content = 'TABLE FROM "x"\nGROUP BY tags\n'
        findings = lint_run.check_base_format_yaml(Path("vault/test.base"), content)
        self.assertEqual(len(findings), 1)
        # 第一行先命中 TABLE
        self.assertIn("Dataview", findings[0]["msg"])


if __name__ == "__main__":
    unittest.main()
