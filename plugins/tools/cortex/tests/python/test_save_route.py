"""Test save._resolve_path routes for kind=project / domain (alias) / source."""
from __future__ import annotations

import datetime as _dt
import sys
import unittest
from pathlib import Path

CLI_DIR = Path(__file__).resolve().parent.parent.parent / "scripts" / "cli"
sys.path.insert(0, str(CLI_DIR))

import save  # noqa: E402


class ResolvePathTest(unittest.TestCase):
    def setUp(self) -> None:
        self.vault = Path("/tmp/cortex-test-vault")
        self.now = _dt.datetime(2026, 5, 13, 10, 30)

    def test_kind_project_github(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "project", "title": "foo", "host": "github.com", "org": "lazygophers", "repo": "ccplugin"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/项目/github.com/lazygophers/ccplugin/foo.md",
        )

    def test_kind_project_local_rel_home(self) -> None:
        # 本地项目: host/org/repo 接受任意字符串 (含相对 $HOME 路径段)
        target = save._resolve_path(
            self.vault,
            {"kind": "project", "title": "foo", "host": "persons", "org": "lyxamour", "repo": "ccplugin"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/项目/persons/lyxamour/ccplugin/foo.md",
        )

    def test_kind_project_fallback_local_segments(self) -> None:
        # host/org/repo 缺省 → 自动补 `_local`
        target = save._resolve_path(
            self.vault,
            {"kind": "project", "title": "foo", "host": "_local"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/项目/_local/_local/_local/foo.md",
        )

    def test_kind_domain_alias_routes_to_项目(self) -> None:
        # backward-compat alias: domain → project path
        target = save._resolve_path(
            self.vault,
            {"kind": "domain", "title": "bar", "host": "gitlab.com", "org": "g", "repo": "h"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/项目/gitlab.com/g/h/bar.md",
        )

    def test_kind_source_rejects_repo_host(self) -> None:
        with self.assertRaises(ValueError):
            save._resolve_path(
                self.vault,
                {"kind": "source", "title": "x", "host": "github.com"},
                self.now,
            )
        with self.assertRaises(ValueError):
            save._resolve_path(
                self.vault,
                {"kind": "source", "title": "x", "host": "gitlab.my-co.com"},
                self.now,
            )

    def test_kind_source_routes_to_收件箱(self) -> None:
        # 非 repo 来源统一落 收件箱/<host>-<slug>.md
        target = save._resolve_path(
            self.vault,
            {"kind": "source", "title": "post", "host": "example.com"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/收件箱/example.com-post.md",
        )

    def test_kind_source_paper_routes_to_收件箱(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "source", "title": "p", "host": "arxiv.org"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/收件箱/arxiv.org-p.md",
        )

    def test_kind_entity_default_domain_未分类(self) -> None:
        # --domain 缺 → 默认 领域/未分类/
        target = save._resolve_path(
            self.vault,
            {"kind": "entity", "title": "foo bar"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/领域/未分类/foo-bar.md",
        )

    def test_kind_entity_with_domain(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "entity", "title": "X", "domain": "技术"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/领域/技术/x.md",
        )

    def test_kind_concept_with_domain(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "concept", "title": "Y", "domain": "创作"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/领域/创作/y.md",
        )

    def test_kind_reflection_into_journal(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "reflection", "title": "我的反思"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/日记/日/2026-05/2026-05-13-反思-我的反思.md",
        )

    def test_kind_question_routes_to_收件箱(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "question", "title": "why"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/收件箱/why.md",
        )

    def test_kind_fleeting_routes_to_收件箱(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "fleeting", "title": "tmp"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/收件箱/tmp.md",
        )

    def test_kind_inbox_with_host(self) -> None:
        # inbox with host → 收件箱/<host>-<slug>.md
        target = save._resolve_path(
            self.vault,
            {"kind": "inbox", "title": "abc", "host": "example.com"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/收件箱/example.com-abc.md",
        )

    def test_kind_journal_only_day(self) -> None:
        # journal/log 仅日维度
        target = save._resolve_path(
            self.vault,
            {"kind": "journal", "title": "today"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/日记/日/2026-05/2026-05-13.md",
        )

    def test_kind_log_only_day(self) -> None:
        target = save._resolve_path(
            self.vault,
            {"kind": "log", "title": "today"},
            self.now,
        )
        self.assertEqual(
            str(target).split("cortex-test-vault/")[-1],
            "知识库/日记/日/2026-05/2026-05-13.md",
        )


class IngestFileLocalProjectTest(unittest.TestCase):
    """Test ingest_file._rel_home_to_host_org_repo for local project path strategy."""

    def setUp(self) -> None:
        # ingest_file lives next to save in cli/
        import ingest_file
        self.mod = ingest_file

    def test_3_segments_under_home(self) -> None:
        # mock Path.home() via monkeypatch is fragile; instead pass abs path
        # under the actual home so relative_to succeeds
        from pathlib import Path
        home = Path.home()
        host, org, repo, url = self.mod._rel_home_to_host_org_repo(home / "persons" / "lyxamour" / "ccplugin")
        self.assertEqual((host, org, repo), ("persons", "lyxamour", "ccplugin"))
        self.assertEqual(url, "file://$HOME/persons/lyxamour/ccplugin")

    def test_2_segments_pads_local(self) -> None:
        from pathlib import Path
        host, org, repo, _ = self.mod._rel_home_to_host_org_repo(Path.home() / "workspace" / "foo")
        self.assertEqual((host, org, repo), ("workspace", "_local", "foo"))

    def test_1_segment_pads_local(self) -> None:
        from pathlib import Path
        host, org, repo, _ = self.mod._rel_home_to_host_org_repo(Path.home() / "foo")
        self.assertEqual((host, org, repo), ("_local", "_local", "foo"))

    def test_outside_home_falls_back(self) -> None:
        from pathlib import Path
        host, org, repo, url = self.mod._rel_home_to_host_org_repo(Path("/tmp/somewhere"))
        self.assertEqual(host, "_local")
        self.assertEqual(org, "_local")
        self.assertEqual(repo, "somewhere")
        self.assertTrue(url.startswith("file:///tmp"))


if __name__ == "__main__":
    unittest.main()
