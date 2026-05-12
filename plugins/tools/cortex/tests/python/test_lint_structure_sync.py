"""Tests for lint constructive sync rules: structure/seed/meta missing."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))

from lint.run import (  # noqa: E402
    _check_meta_missing,
    _check_seed_missing,
    _check_structure_missing,
    _fix_meta_missing,
    _fix_seed_missing,
    _fix_structure_missing,
    apply_fixes,
)


def _bootstrap_vault(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / ".obsidian").mkdir(exist_ok=True)
    (root / "_meta").mkdir(exist_ok=True)
    (root / "_meta" / "version.json").write_text(
        json.dumps({"preset": "lyt", "lang": "zh-CN"}), encoding="utf-8"
    )
    return root


def test_structure_missing_empty_vault(tmp_path):
    v = _bootstrap_vault(tmp_path)
    findings = _check_structure_missing(v, PLUGIN)
    assert len(findings) > 0
    assert all(f["rule"] == "structure-missing" for f in findings)
    files = {f["file"] for f in findings}
    # spot-check key namespaces
    assert "知识库" in files
    assert "记忆体系/L0-核心" in files


def test_seed_missing_empty_vault(tmp_path):
    v = _bootstrap_vault(tmp_path)
    findings = _check_seed_missing(v, PLUGIN)
    assert findings, "expect seed-missing findings on empty vault"
    assert all(f["rule"] == "seed-missing" for f in findings)
    files = {f["file"] for f in findings}
    assert "主页.md" in files


def test_meta_missing_empty_vault(tmp_path):
    v = _bootstrap_vault(tmp_path)
    findings = _check_meta_missing(v, PLUGIN)
    rules = {f["rule"] for f in findings}
    files = {f["file"] for f in findings}
    assert "meta-missing" in rules
    assert "_meta/memory-policy.yaml" in files
    assert "_meta/triggers.yaml" in files
    assert "_meta/template-manifest.json" in files


def test_structure_present_no_findings_for_existing(tmp_path):
    v = _bootstrap_vault(tmp_path)
    for d in ["知识库/项目", "知识库/来源", "记忆体系/L0-核心", "仪表盘", "归档"]:
        (v / d).mkdir(parents=True, exist_ok=True)
    findings = _check_structure_missing(v, PLUGIN)
    files = {f["file"] for f in findings}
    assert "知识库/项目" not in files
    assert "记忆体系/L0-核心" not in files


def test_fix_structure_creates_dir(tmp_path):
    v = _bootstrap_vault(tmp_path)
    finding = {"file": "知识库/项目"}
    assert _fix_structure_missing(finding, v, PLUGIN, tmp_path / "_bak")
    assert (v / "知识库" / "项目").is_dir()


def test_fix_meta_copies(tmp_path):
    v = _bootstrap_vault(tmp_path)
    finding = {"file": "_meta/triggers.yaml"}
    assert _fix_meta_missing(finding, v, PLUGIN, tmp_path / "_bak")
    assert (v / "_meta" / "triggers.yaml").exists()


def test_fix_meta_skips_existing(tmp_path):
    v = _bootstrap_vault(tmp_path)
    (v / "_meta" / "triggers.yaml").write_text("user content", encoding="utf-8")
    finding = {"file": "_meta/triggers.yaml"}
    assert not _fix_meta_missing(finding, v, PLUGIN, tmp_path / "_bak")
    assert (v / "_meta" / "triggers.yaml").read_text(encoding="utf-8") == "user content"


def test_fix_seed_renders_placeholders(tmp_path):
    v = _bootstrap_vault(tmp_path)
    # ensure parent dir exists
    (v / "知识库" / "项目").mkdir(parents=True, exist_ok=True)
    finding = {"file": "知识库/项目/_index.md"}
    assert _fix_seed_missing(finding, v, PLUGIN, tmp_path / "_bak")
    p = v / "知识库" / "项目" / "_index.md"
    assert p.exists()
    text = p.read_text(encoding="utf-8")
    # No placeholders left for the 5 known tokens
    for token in ("{{TITLE}}", "{{CURRENT_PATH}}", "{{LAST_UPDATED}}",
                  "{{UPDATED}}", "{{CREATED}}"):
        assert token not in text, f"placeholder {token} not rendered"


def test_apply_fixes_full_sync(tmp_path):
    """End-to-end: empty vault + apply_fixes → directories + seed + meta populated."""
    v = _bootstrap_vault(tmp_path)
    findings = (
        _check_structure_missing(v, PLUGIN)
        + _check_meta_missing(v, PLUGIN)
        + _check_seed_missing(v, PLUGIN)
    )
    backup = tmp_path / "_bak"
    backup.mkdir()
    n = apply_fixes(v, findings, backup, plugin_root=PLUGIN)
    assert n > 0
    # Key dirs created
    assert (v / "知识库" / "项目").is_dir()
    assert (v / "记忆体系" / "L0-核心").is_dir()
    assert (v / "仪表盘").is_dir()
    # Key seed / meta files written
    assert (v / "主页.md").exists()
    assert (v / "_meta" / "memory-policy.yaml").exists()
    assert (v / "_meta" / "triggers.yaml").exists()
    # Re-scan: no more missing
    assert _check_structure_missing(v, PLUGIN) == []
    assert _check_meta_missing(v, PLUGIN) == []
    assert _check_seed_missing(v, PLUGIN) == []
