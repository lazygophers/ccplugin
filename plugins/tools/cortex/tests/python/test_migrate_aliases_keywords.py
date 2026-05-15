"""Tests for migrate_aliases_keywords_to_v3 (PR2 一次性 v3 迁移)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
_MODULE_PATH = (
    PLUGIN_ROOT / "scripts" / "migrate" / "migrate_aliases_keywords_to_v3.py"
)

# 确保 cli/ 在 sys.path 上 (lib.frontmatter)
sys.path.insert(0, str(PLUGIN_ROOT / "scripts" / "cli"))


def _load_module():
    spec = importlib.util.spec_from_file_location("migrate_v3", _MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["migrate_v3"] = mod
    spec.loader.exec_module(mod)
    return mod


migrate_mod = _load_module()


def _make_vault(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / ".obsidian").mkdir(exist_ok=True)
    (root / "_meta").mkdir(exist_ok=True)
    (root / "_meta" / "version.json").write_text(
        '{"lang":"zh-CN"}', encoding="utf-8"
    )
    return root


def _write_md(path: Path, fm_lines: list[str], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "---\n" + "\n".join(fm_lines) + "\n---\n\n" + body
    path.write_text(text, encoding="utf-8")


def _read_fm(path: Path) -> dict:
    from lib.frontmatter import parse as fm_parse  # type: ignore

    return fm_parse(path.read_text(encoding="utf-8"))[0]


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    return _make_vault(tmp_path / "vault")


def test_missing_aliases_added(vault: Path) -> None:
    md = vault / "知识库" / "项目" / "github.com" / "foo" / "bar" / "认证.md"
    _write_md(
        md,
        ["type: project", "title: 认证模块", "keywords:", "  - existing"],
        "讲 RBAC 与 JWT 的实现。",
    )
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_changed"] == 1
    assert result["aliases_added"] == 1
    assert result["keywords_added"] == 0
    fm = _read_fm(md)
    assert fm.get("aliases")
    assert fm.get("keywords") == ["existing"]


def test_missing_keywords_added(vault: Path) -> None:
    md = vault / "知识库" / "领域" / "技术" / "log.md"
    _write_md(
        md,
        [
            "type: concept",
            "title: 日志系统",
            "aliases:",
            "  - logging",
            "  - log",
            "  - 日志",
        ],
        "## 概览\n\nlog 模块 design。",
    )
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_changed"] == 1
    assert result["aliases_added"] == 0
    assert result["keywords_added"] == 1
    fm = _read_fm(md)
    assert fm.get("keywords")


def test_both_missing_both_added(vault: Path) -> None:
    md = vault / "知识库" / "项目" / "github.com" / "x" / "y" / "API.md"
    _write_md(
        md,
        ["type: project", "title: API 网关"],
        "REST proxy 实现。",
    )
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_changed"] == 1
    assert result["aliases_added"] == 1
    assert result["keywords_added"] == 1
    fm = _read_fm(md)
    assert fm.get("aliases")
    assert fm.get("keywords")


def test_both_present_skip(vault: Path) -> None:
    md = vault / "知识库" / "领域" / "技术" / "x.md"
    _write_md(
        md,
        [
            "type: concept",
            "title: x",
            "aliases:",
            "  - a",
            "  - b",
            "  - c",
            "keywords:",
            "  - k1",
            "  - k2",
        ],
        "body",
    )
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_scanned"] == 1
    assert result["files_changed"] == 0


def test_non_target_path_skip(vault: Path) -> None:
    # 收件箱 跳过
    md1 = vault / "知识库" / "收件箱" / "x.md"
    _write_md(md1, ["type: inbox", "title: x"], "body")
    # 归档/ 跳过
    md2 = vault / "归档" / "old.md"
    _write_md(md2, ["type: log", "title: old"], "body")
    # _meta 跳过
    md3 = vault / "_meta" / "info.md"
    _write_md(md3, ["title: meta"], "body")
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_scanned"] == 0
    assert result["files_changed"] == 0


def test_l4_skip(vault: Path) -> None:
    md = vault / "记忆" / "L4-流水账" / "sessions" / "x.md"
    _write_md(md, ["type: log", "title: l4"], "body")
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_scanned"] == 0


def test_dry_run_no_write(vault: Path) -> None:
    md = vault / "知识库" / "项目" / "github.com" / "foo" / "bar" / "z.md"
    orig_fm_lines = ["type: project", "title: 认证 RBAC"]
    _write_md(md, orig_fm_lines, "JWT API 实现")
    before = md.read_text(encoding="utf-8")
    result = migrate_mod.migrate(vault, dry_run=True, backup=False)
    assert result["dry_run"] is True
    assert result["files_changed"] == 1
    after = md.read_text(encoding="utf-8")
    assert before == after, "dry_run 不该写盘"


def test_no_frontmatter_skip(vault: Path) -> None:
    md = vault / "知识库" / "项目" / "github.com" / "foo" / "bar" / "nofm.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text("# 无 frontmatter\n\nbody only", encoding="utf-8")
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_scanned"] == 1
    assert result["files_changed"] == 0


def test_json_schema(vault: Path) -> None:
    md = vault / "知识库" / "项目" / "github.com" / "a" / "b" / "x.md"
    _write_md(md, ["type: project", "title: 测试 test"], "log body")
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    for k in (
        "vault",
        "dry_run",
        "backup_path",
        "files_scanned",
        "files_changed",
        "aliases_added",
        "keywords_added",
        "errors",
    ):
        assert k in result, f"missing key: {k}"
    assert isinstance(result["errors"], list)


def test_backup_creates_tar(vault: Path, monkeypatch, tmp_path: Path) -> None:
    md = vault / "知识库" / "项目" / "github.com" / "a" / "b" / "x.md"
    _write_md(md, ["type: project", "title: 配置 config"], "API code")
    # 引导 /tmp → tmp_path (PathLib monkeypatch)
    import migrate_v3 as mod  # type: ignore

    fake_tmp = tmp_path / "tmpdir"
    fake_tmp.mkdir()

    orig_backup = mod._backup_vault

    def patched_backup(v: Path) -> Path:
        import tarfile

        out = fake_tmp / "cortex-migration-backup-v3-test.tar.gz"
        with tarfile.open(out, "w:gz") as tar:
            tar.add(str(v), arcname=v.name)
        return out

    monkeypatch.setattr(mod, "_backup_vault", patched_backup)
    try:
        result = mod.migrate(vault, dry_run=False, backup=True)
    finally:
        monkeypatch.setattr(mod, "_backup_vault", orig_backup)
    assert result["backup_path"]
    assert Path(result["backup_path"]).is_file()


def test_uses_stem_when_no_title(vault: Path) -> None:
    md = vault / "知识库" / "项目" / "github.com" / "a" / "b" / "config_loader.md"
    _write_md(md, ["type: project"], "load config")
    result = migrate_mod.migrate(vault, dry_run=False, backup=False)
    assert result["files_changed"] == 1
    fm = _read_fm(md)
    # keywords 应含 path stem
    kws = fm.get("keywords") or []
    assert any("config_loader" in str(k) for k in kws)
