"""Tests for cortex/scripts/cli/refresh_projects.py (PR2)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
CLI = PLUGIN_ROOT / "scripts" / "cli" / "refresh_projects.py"
CLI_DIR = PLUGIN_ROOT / "scripts" / "cli"
sys.path.insert(0, str(CLI_DIR))

import refresh_projects as rp  # noqa: E402


# ─────────── helpers ───────────


def _make_repo(
    vault: Path,
    host: str,
    org: str,
    repo: str,
    *,
    source_url: str,
    source_type: str = "github",
    last_commit_sha: str | None = None,
    content_hash: str | None = None,
) -> Path:
    d = vault / "知识库" / "项目" / host / org / repo
    d.mkdir(parents=True, exist_ok=True)
    fm_lines = [
        "---",
        f"source_url: {source_url}",
        f"source_type: {source_type}",
    ]
    if last_commit_sha:
        fm_lines.append(f"last_commit_sha: {last_commit_sha}")
    if content_hash:
        fm_lines.append(f"content_hash: {content_hash}")
    fm_lines += ["---", "", f"# {org}/{repo}", ""]
    (d / "_index.md").write_text("\n".join(fm_lines), encoding="utf-8")
    return d


# ─────────── scan_projects (4) ───────────


def test_scan_projects_empty(tmp_path: Path) -> None:
    projects, warnings = rp.scan_projects(tmp_path)
    assert projects == []
    assert warnings == []


def test_scan_projects_parses_index_md(tmp_path: Path) -> None:
    _make_repo(
        tmp_path,
        "github.com",
        "foo",
        "bar",
        source_url="https://github.com/foo/bar",
        last_commit_sha="abc123",
    )
    projects, warnings = rp.scan_projects(tmp_path)
    assert len(projects) == 1
    p = projects[0]
    assert p["host"] == "github.com"
    assert p["org"] == "foo"
    assert p["repo"] == "bar"
    assert p["source_url"] == "https://github.com/foo/bar"
    assert p["last_commit_sha"] == "abc123"
    assert warnings == []


def test_scan_projects_scope_single_repo(tmp_path: Path) -> None:
    _make_repo(
        tmp_path, "github.com", "foo", "bar", source_url="https://github.com/foo/bar"
    )
    _make_repo(
        tmp_path, "github.com", "foo", "baz", source_url="https://github.com/foo/baz"
    )
    _make_repo(
        tmp_path, "github.com", "other", "x", source_url="https://github.com/other/x"
    )
    projects, _ = rp.scan_projects(tmp_path, scope="github.com/foo/bar")
    assert len(projects) == 1
    assert projects[0]["repo"] == "bar"

    projects, _ = rp.scan_projects(tmp_path, scope="github.com/foo")
    assert len(projects) == 2
    assert {p["repo"] for p in projects} == {"bar", "baz"}


def test_scan_skip_project_no_source_url(tmp_path: Path) -> None:
    d = tmp_path / "知识库" / "项目" / "github.com" / "foo" / "bar"
    d.mkdir(parents=True)
    (d / "_index.md").write_text("---\nfoo: 1\n---\n", encoding="utf-8")
    projects, warnings = rp.scan_projects(tmp_path)
    assert projects == []
    assert any("no source_url" in w for w in warnings)


# ─────────── refresh_git (2) ───────────


def test_refresh_git_no_change(tmp_path: Path) -> None:
    _make_repo(
        tmp_path,
        "github.com",
        "foo",
        "bar",
        source_url="https://github.com/foo/bar",
        last_commit_sha="aaa",
    )
    projects, _ = rp.scan_projects(tmp_path)
    p = projects[0]

    def fake_run_git(args, cwd=None, timeout=None):
        if args[0] == "clone":
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:2] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(args, 0, "aaa\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    with mock.patch.object(rp, "run_git", side_effect=fake_run_git):
        r = rp.refresh_git_project(p, tmp_path, dry_run=False)
    assert r["status"] == "skip"
    assert r["files_changed"] == 0


def test_refresh_git_sha_changed(tmp_path: Path) -> None:
    repo_dir = _make_repo(
        tmp_path,
        "github.com",
        "foo",
        "bar",
        source_url="https://github.com/foo/bar",
        last_commit_sha="aaa",
    )
    projects, _ = rp.scan_projects(tmp_path)
    p = projects[0]

    # Create fake clone tmp content via run_git side_effect that also writes a file.
    calls = {"n": 0}

    def fake_run_git(args, cwd=None, timeout=None):
        if args[0] == "clone":
            # args = ["clone", "--depth=50", url, dest]
            dest = Path(args[-1])
            dest.mkdir(parents=True, exist_ok=True)
            (dest / "src").mkdir(exist_ok=True)
            (dest / "src" / "a.py").write_text("print(1)\n")
            (dest / "src" / "b.py").write_text("print(2)\n")
            return subprocess.CompletedProcess(args, 0, "", "")
        if args[:2] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(args, 0, "bbb\n", "")
        if args[0] == "diff":
            return subprocess.CompletedProcess(args, 0, "src/a.py\nsrc/b.py\n", "")
        calls["n"] += 1
        return subprocess.CompletedProcess(args, 0, "", "")

    with mock.patch.object(rp, "run_git", side_effect=fake_run_git):
        r = rp.refresh_git_project(p, tmp_path, dry_run=False)
    assert r["status"] == "updated", r
    assert r["files_changed"] == 2
    assert r["last_commit_sha"] == "bbb"
    # 写入两份 src 的 .md
    assert (repo_dir / "源" / "src" / "a.py.md").is_file()
    assert (repo_dir / "源" / "src" / "b.py.md").is_file()


# ─────────── refresh_website (2) ───────────


def test_refresh_website_hash_match(tmp_path: Path) -> None:
    import hashlib

    page_url = "https://example.com/page"
    body = "<html>hello</html>"
    expected = hashlib.sha256(body.encode("utf-8")).hexdigest()
    repo_dir = _make_repo(
        tmp_path,
        "example.com",
        "_site",
        "example",
        source_url="https://example.com/",
        source_type="website",
    )
    # 已存页 frontmatter 含 source_url + content_hash
    (repo_dir / "page.md").write_text(
        "---\n"
        f"source_url: {page_url}\n"
        "source_type: website\n"
        f"content_hash: {expected}\n"
        "---\n\n" + body,
        encoding="utf-8",
    )
    projects, _ = rp.scan_projects(tmp_path)
    p = projects[0]

    class FakeSecurity:
        @staticmethod
        def is_safe(_url):
            return (True, "")

    class FakeSanitize:
        @staticmethod
        def sanitize(s):
            return s

    class FakeMasking:
        @staticmethod
        def mask(s):
            return (s, [])

    def fake_loader(name, _mod):
        return {
            "url_security.py": FakeSecurity,
            "html_sanitize.py": FakeSanitize,
            "masking.py": FakeMasking,
        }[name]

    with mock.patch.object(rp, "load_filter_module", side_effect=fake_loader):
        with mock.patch.object(rp, "discover_urls", return_value=[page_url]):
            with mock.patch.object(
                rp, "fetch_bytes", return_value=(body.encode("utf-8"), "text/html")
            ):
                r = rp.refresh_website_project(p, tmp_path, dry_run=False)
    assert r["status"] == "skip"
    assert r["files_changed"] == 0
    assert r["files_new"] == 0


def test_refresh_website_hash_changed(tmp_path: Path) -> None:
    page_url = "https://example.com/page"
    repo_dir = _make_repo(
        tmp_path,
        "example.com",
        "_site",
        "example",
        source_url="https://example.com/",
        source_type="website",
    )
    (repo_dir / "page.md").write_text(
        "---\n"
        f"source_url: {page_url}\n"
        "source_type: website\n"
        "content_hash: OLDHASH\n"
        "---\n\nold body",
        encoding="utf-8",
    )
    projects, _ = rp.scan_projects(tmp_path)
    p = projects[0]

    class FakeSecurity:
        @staticmethod
        def is_safe(_u):
            return (True, "")

    class FakeSanitize:
        @staticmethod
        def sanitize(s):
            return s

    class FakeMasking:
        @staticmethod
        def mask(s):
            return (s, [])

    def fake_loader(name, _mod):
        return {
            "url_security.py": FakeSecurity,
            "html_sanitize.py": FakeSanitize,
            "masking.py": FakeMasking,
        }[name]

    with mock.patch.object(rp, "load_filter_module", side_effect=fake_loader):
        with mock.patch.object(rp, "discover_urls", return_value=[page_url]):
            with mock.patch.object(
                rp,
                "fetch_bytes",
                return_value=(b"<html>NEW BODY</html>", "text/html"),
            ):
                r = rp.refresh_website_project(p, tmp_path, dry_run=False)
    assert r["status"] == "updated"
    # 重写后 hash 与 OLDHASH 不一致
    written = (repo_dir / "page.md").read_text(encoding="utf-8")
    assert "OLDHASH" not in written
    assert "NEW BODY" in written


# ─────────── CLI integration: dry-run + JSON schema (3) ───────────


def _run_cli(args: list[str]) -> tuple[int, dict]:
    res = subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        timeout=20,
    )
    payload: dict
    try:
        payload = (
            json.loads(res.stdout.strip().splitlines()[-1])
            if res.stdout.strip()
            else {}
        )
    except json.JSONDecodeError:
        payload = {"_raw": res.stdout}
    return res.returncode, payload


def test_dry_run_empty_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    rc, out = _run_cli(["--vault", str(tmp_path), "--dry-run"])
    assert rc == 0, out
    assert out.get("projects_scanned") == 0
    assert out.get("results") == []


def test_dry_run_does_not_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    repo_dir = _make_repo(
        tmp_path,
        "github.com",
        "foo",
        "bar",
        source_url="https://github.com/foo/bar",
        last_commit_sha="aaa",
    )
    before = sorted(p.name for p in repo_dir.iterdir())
    rc, out = _run_cli(["--vault", str(tmp_path), "--dry-run"])
    assert rc == 0, out
    after = sorted(p.name for p in repo_dir.iterdir())
    assert before == after
    # Result entry exists, marked dry_run.
    assert out["projects_scanned"] == 1
    assert out["results"][0]["status"] == "dry_run"


def test_json_summary_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    rc, out = _run_cli(["--vault", str(tmp_path), "--dry-run"])
    assert rc == 0
    for key in (
        "projects_scanned",
        "projects_updated",
        "files_changed",
        "files_new",
        "errors",
        "warnings",
        "results",
    ):
        assert key in out, f"missing key {key} in {out}"


def test_help_works() -> None:
    res = subprocess.run(
        [sys.executable, str(CLI), "--help"], capture_output=True, text=True, timeout=10
    )
    assert res.returncode == 0
    assert "usage" in res.stdout.lower()
