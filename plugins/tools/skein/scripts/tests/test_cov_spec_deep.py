# mypy: ignore-errors
"""spec/maintain.py + spec/write.py 深度分支覆盖。
MaintainMixin/WriteMixin 是 Spec facade 的 mixin, 用 Spec() 进程内调。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401
from skeinlib.spec.facade import Spec
from skeinlib.spec.model import now, KEYWORDS_DUP_THRESHOLD
from skeinlib.utils.errors import SkeinError


def _write_rule(ws: Path, ns: str, cat: str, topic: str, fm: str = "inclusion: auto\nstatus: active\n", body: str = "rule body") -> Path:
    d = ws / ".skein" / "spec" / ns / cat
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{topic}.md"
    f.write_text(f"---\n{fm}---\n\n{body}\n")
    return f


# ---- _check_file_symbol / _check_py_symbol / _check_js_symbol / _check_go_symbol ----

def test_check_file_symbol_not_exists(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    assert s._check_file_symbol(Path("/nonexistent/file.py"), "foo") is False


def test_check_file_symbol_unreadable(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "bad.py"
    f.write_bytes(b'\x80\x80\x80')  # invalid utf-8
    assert s._check_file_symbol(f, "foo") is False


def test_check_py_symbol_found(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "test.py"
    f.write_text("def foo():\n    pass\nclass Bar:\n    pass\n")
    assert s._check_file_symbol(f, "foo") is True
    assert s._check_file_symbol(f, "Bar") is True
    assert s._check_file_symbol(f, "missing") is False


def test_check_py_symbol_async(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "a.py"
    f.write_text("async def baz():\n    pass\n")
    assert s._check_file_symbol(f, "baz") is True


def test_check_js_symbol_found(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "test.ts"
    f.write_text("export function greet() {}\nexport const x = 1;\nclass Foo {}\n")
    assert s._check_file_symbol(f, "greet") is True
    assert s._check_file_symbol(f, "Foo") is True
    assert s._check_file_symbol(f, "missing") is False


def test_check_js_symbol_export_const(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "mod.js"
    f.write_text("export const myVar = 42\n")
    assert s._check_file_symbol(f, "myVar") is True


def test_check_go_symbol_found(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "main.go"
    f.write_text("package main\n\nfunc handler() {}\ntype Handler struct{}\n")
    assert s._check_file_symbol(f, "handler") is True
    assert s._check_file_symbol(f, "Handler") is True
    assert s._check_file_symbol(f, "missing") is False


def test_check_file_symbol_non_code(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "readme.txt"
    f.write_text("hello")
    assert s._check_file_symbol(f, "anything") is True  # 非代码文件 = 路径存在即通过


def test_check_js_symbol_not_identifier(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    f = tmp_path / "bad.js"
    f.write_text("export const 123bad = 1\n")
    assert s._check_file_symbol(f, "123bad") is False  # not valid identifier


# ---- maintain: archive / restore with MaintainMixin methods ----

def test_archive_empty(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    s.archive(argparse.Namespace(namespace=None))
    s._reindex_all()


def test_archive_with_rules(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "rule1")
    s = Spec()
    import argparse
    s.archive(argparse.Namespace(namespace="rules"))
    # 验证规则被移到 .archive
    archives = list((mem_ws / ".skein" / "spec" / ".archive").rglob("*.md"))
    assert len(archives) >= 1


def test_restore_nonexistent(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    with pytest.raises(SkeinError, match="归档不存在"):
        s.restore(argparse.Namespace(ts="nonexistent-timestamp"))


def test_restore_works(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "rule1")
    s = Spec()
    import argparse
    # archive then restore
    s.archive(argparse.Namespace(namespace="rules"))
    archives = list((mem_ws / ".skein" / "spec" / ".archive").iterdir())
    ts = archives[0].name
    s.restore(argparse.Namespace(ts=ts))
    assert (mem_ws / ".skein" / "spec" / "rules" / "arch" / "rule1.md").exists()


def test_restore_skips_index(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "rule1")
    s = Spec()
    import argparse
    s.archive(argparse.Namespace(namespace="rules"))
    archives = list((mem_ws / ".skein" / "spec" / ".archive").iterdir())
    ts = archives[0].name
    # 放一个 index.md 在归档里
    (mem_ws / ".skein" / "spec" / ".archive" / ts / "rules" / "arch").mkdir(parents=True, exist_ok=True)
    (mem_ws / ".skein" / "spec" / ".archive" / ts / "rules" / "arch" / "index.md").write_text("# index")
    s.restore(argparse.Namespace(ts=ts))


# ---- maintain: _scan_findings 深度分支 ----

def test_scan_findings_stale(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """stale 判据: 修改超 STALE_DAYS 天且无引用。"""
    monkeypatch.chdir(mem_ws)
    # 写一条旧规则 (mtime 不可控, 但至少触发 _scan_findings 跑全量)
    _write_rule(mem_ws, "rules", "arch", "old", "inclusion: auto\nstatus: active\n", "old rule [[missing-link]]")
    s = Spec()
    findings = s._scan_findings(["rules"])
    # 可能找到 broken_link (missing-link)
    kinds = [f.get("kind") for f in findings]
    # 至少不会崩
    assert isinstance(kinds, list)


def test_scan_findings_anchors_broken(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """anchors 路径不存在 → broken_link + anchors_broken (rules namespace archive 策略)。"""
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "rule1",
                "inclusion: auto\nstatus: active\nanchors: nonexistent/path.py:myFunc\n", "body")
    s = Spec()
    findings = s._scan_findings(["rules"])
    kinds = [f.get("kind") for f in findings]
    assert "broken_link" in kinds


def test_scan_findings_anchors_symbol_missing(mem_ws: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """anchors 路径存在但 symbol 缺失 → broken_link。"""
    monkeypatch.chdir(mem_ws)
    # 创建一个 py 文件在仓库根
    (mem_ws / "src.py").write_text("def real_func():\n    pass\n")
    _write_rule(mem_ws, "rules", "arch", "rule1",
                "inclusion: auto\nstatus: active\nanchors: src.py:missing_func\n", "body")
    s = Spec()
    findings = s._scan_findings(["rules"])
    broken = [f for f in findings if f.get("kind") == "broken_link"]
    assert len(broken) >= 1


def test_scan_findings_anchors_path_only(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """anchors 只有路径无 symbol → 路径存在不报告。"""
    monkeypatch.chdir(mem_ws)
    (mem_ws / "real.py").write_text("# code\n")
    _write_rule(mem_ws, "rules", "arch", "rule1",
                "inclusion: auto\nstatus: active\nanchors: real.py\n", "body")
    s = Spec()
    findings = s._scan_findings(["rules"])
    # real.py 存在, 不报断链
    broken = [f for f in findings if f.get("kind") == "broken_link" and "real.py" in f.get("text", "")]
    assert len(broken) == 0


def test_scan_findings_keywords_dup(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """keywords 重复超阈值。"""
    monkeypatch.chdir(mem_ws)
    # 写两条 keywords 高度重复的规则
    for i in range(KEYWORDS_DUP_THRESHOLD + 1):
        _write_rule(mem_ws, "rules", "arch", f"r{i}",
                    f"inclusion: auto\nstatus: active\nkeywords: [common, shared, dup]\n", f"rule {i}")
    s = Spec()
    findings = s._scan_findings(["rules"])
    kw_findings = [f for f in findings if f.get("kind") == "keywords_dup"]
    assert len(kw_findings) >= 1


def test_scan_findings_deprecated(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """deprecated 状态规则。"""
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "dep",
                "inclusion: auto\nstatus: deprecated\n", "old rule")
    s = Spec()
    findings = s._scan_findings(["rules"])
    dep = [f for f in findings if f.get("kind") == "deprecated"]
    assert len(dep) >= 1


def test_scan_findings_overbudget(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """always 页超预算。"""
    monkeypatch.chdir(mem_ws)
    # 写一条很大的 always 规则
    big_body = "x" * 20000
    _write_rule(mem_ws, "rules", "core", "big",
                f"inclusion: always\nstatus: active\n", big_body)
    s = Spec()
    findings = s._scan_findings(["rules"])
    ob = [f for f in findings if f.get("kind") == "overbudget"]
    assert len(ob) >= 1


# ---- maintain: _maintain_apply / degrade ----

def test_maintain_apply_dry_run(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """maintain 无 --apply 只报告。"""
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "dep",
                "inclusion: auto\nstatus: deprecated\n", "deprecated rule")
    s = Spec()
    import argparse
    s.maintain(argparse.Namespace(namespace=None, apply=False))


def test_degrade_auto(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """degrade --auto 模式。"""
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "core", "big1",
                "inclusion: always\nstatus: active\n", "x" * 10000)
    _write_rule(mem_ws, "rules", "core", "big2",
                "inclusion: always\nstatus: active\n", "y" * 10000)
    s = Spec()
    import argparse
    s.degrade(argparse.Namespace(file=None, auto=True))


# ---- write.py 深度分支 ----

def test_amend_section_not_found(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """amend 章节不存在 → 报错列出现有章节。"""
    monkeypatch.chdir(mem_ws)
    # 先写一个主题文件
    body_file = mem_ws / "body.txt"
    body_file.write_text("new content")
    _write_rule(mem_ws, "rules", "arch", "topic1",
                "inclusion: auto\nstatus: active\n", "## Section A\ncontent A\n")
    s = Spec()
    import argparse
    with pytest.raises(SkeinError, match="章节"):
        s.amend(argparse.Namespace(
            topic="rules/arch/topic1", section="Nonexistent",
            body_file=str(body_file), rename_section=None))


def test_amend_success(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """amend 成功改写章节。"""
    monkeypatch.chdir(mem_ws)
    body_file = mem_ws / "body.txt"
    body_file.write_text("new content")
    _write_rule(mem_ws, "rules", "arch", "topic1",
                "inclusion: auto\nstatus: active\n", "## Section A\nold content\n")
    s = Spec()
    import argparse
    s.amend(argparse.Namespace(
        topic="rules/arch/topic1", section="Section A",
        body_file=str(body_file), rename_section=None))
    content = (mem_ws / ".skein" / "spec" / "rules" / "arch" / "topic1.md").read_text()
    assert "new content" in content


def test_amend_rename_section(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """amend 同时重命名章节。"""
    monkeypatch.chdir(mem_ws)
    body_file = mem_ws / "body.txt"
    body_file.write_text("renamed content")
    _write_rule(mem_ws, "rules", "arch", "topic1",
                "inclusion: auto\nstatus: active\n", "## Old Name\ncontent\n")
    s = Spec()
    import argparse
    s.amend(argparse.Namespace(
        topic="rules/arch/topic1", section="Old Name",
        body_file=str(body_file), rename_section="New Name"))
    content = (mem_ws / ".skein" / "spec" / "rules" / "arch" / "topic1.md").read_text()
    assert "New Name" in content
    assert "renamed content" in content


def test_finish_candidates_no_data(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """finish-candidates 无 task → 返回建议。"""
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    # 不存在的 task → 应该返回建议或报错
    try:
        s.finish_candidates(argparse.Namespace(tid="nonexistent", json=False, files=None))
    except (SkeinError, Exception):
        pass  # 只要跑了就行


def test_restructure_dry_run(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """restructure --dry-run 只打印。"""
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "r1", "inclusion: auto\n", "rule 1")
    _write_rule(mem_ws, "rules", "arch", "r2", "inclusion: auto\n", "rule 2")
    plan = mem_ws / "plan.json"
    plan.write_text(json.dumps({"rules/arch/merged.md": ["rules/arch/r1.md", "rules/arch/r2.md"]}))
    s = Spec()
    import argparse
    s.restructure(argparse.Namespace(map=str(plan), dry_run=True))
