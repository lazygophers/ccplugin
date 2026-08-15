# mypy: ignore-errors
"""write.py 剩余 miss + serve.py 进程内可达 miss 补测。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401
from skeinlib.spec.facade import Spec
from skeinlib.utils.errors import SkeinError


def _write_rule(ws: Path, ns: str, cat: str, topic: str, fm: str = "inclusion: auto\nstatus: active\n",
                body: str = "rule body") -> Path:
    d = ws / ".skein" / "spec" / ns / cat
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{topic}.md"
    f.write_text(f"---\n{fm}---\n\n{body}\n")
    return f


# ---- write.py: append_rule with globs/anchors merge ----

def test_sediment_merges_globs_and_anchors(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """已有文件带 globs/anchors → 追加时保留已有值 (line 117)。"""
    monkeypatch.chdir(mem_ws)
    s = Spec()
    # 第一条: 带 globs + anchors
    body_a = mem_ws / "body-a.md"
    body_a.write_text("Rule A body")
    s.sediment(argparse.Namespace(
        namespace="rules", inclusion="fileMatch", category="arch", topic="merge1",
        title="Rule A", keywords="kw1", status="active", body_file=str(body_a),
        globs="*.py", anchors="src/code.py:func1"))
    # 第二条: 不带 globs/anchors → 应保留第一条的值
    body_b = mem_ws / "body-b.md"
    body_b.write_text("Rule B body")
    s.sediment(argparse.Namespace(
        namespace="rules", inclusion="fileMatch", category="arch", topic="merge1",
        title="Rule B", keywords="kw2", status="active", body_file=str(body_b),
        globs=None, anchors=None))
    content = (mem_ws / ".skein" / "spec" / "rules" / "arch" / "merge1.md").read_text()
    assert "globs: *.py" in content
    assert "anchors: src/code.py:func1" in content


# ---- write.py: amend error paths ----

def test_amend_bad_topic_format(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """amend --topic 格式不对 (缺 namespace)。"""
    monkeypatch.chdir(mem_ws)
    s = Spec()
    body = mem_ws / "b.txt"
    body.write_text("x")
    with pytest.raises(SkeinError, match="无效的 --topic"):
        s.amend(argparse.Namespace(topic="only-two-parts", section="S",
                                    body_file=str(body), rename_section=None))


def test_amend_nonexistent_file(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """amend 主题文件不存在。"""
    monkeypatch.chdir(mem_ws)
    s = Spec()
    body = mem_ws / "b.txt"
    body.write_text("x")
    with pytest.raises(SkeinError, match="主题文件不存在"):
        s.amend(argparse.Namespace(topic="rules/arch/nope", section="S",
                                    body_file=str(body), rename_section=None))


# ---- write.py: finish_candidates with anchor hits ----

def test_finish_candidates_anchor_match(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """finish-candidates anchors 反查命中。"""
    monkeypatch.chdir(mem_ws)
    (mem_ws / "src").mkdir(exist_ok=True)
    (mem_ws / "src" / "auth.py").write_text("def login():\n    pass\n")
    _write_rule(mem_ws, "product", "auth", "loginpage",
                fm="inclusion: auto\nstatus: active\nanchors: src/auth.py:login\n",
                body="## Login\nLogin auth\n")
    tdir = mem_ws / ".skein" / "task" / "feat-login"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(json.dumps({"id": "feat-login", "status": "active", "subtasks": []}))
    (tdir / "prd.md").write_text("---\ndesc: 解决 X 问题\nboundary:\n  should:\n  - 范围内a\n  should_not: []\nestimate: 1\nacceptance:\n  - 用例通过\n---\n", encoding="utf-8")
    s = Spec()
    s.finish_candidates(argparse.Namespace(tid="feat-login", json=True, files="src/auth.py"))


def test_finish_candidates_no_anchors_keyword_recall(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """finish-candidates 无 anchors 命中 → 关键词召回。"""
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "product", "auth", "loginpage",
                fm="inclusion: auto\nstatus: active\nkeywords: [login, auth]\n",
                body="## Login\nLogin rule\n")
    tdir = mem_ws / ".skein" / "task" / "feat-x"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(json.dumps({"id": "feat-x", "status": "active", "subtasks": []}))
    (tdir / "prd.md").write_text("---\ndesc: 解决 X 问题\nboundary:\n  should:\n  - 范围内a\n  should_not: []\nestimate: 1\nacceptance:\n  - 用例通过\n---\n", encoding="utf-8")
    s = Spec()
    s.finish_candidates(argparse.Namespace(tid="feat-x", json=True, files=None))


# ---- write.py: _collect_merge_targets / restructure ----

def test_restructure_with_content(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """restructure 合并文件 (非 dry-run)。"""
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "rules", "arch", "r1", body="## A\nrule A\n")
    _write_rule(mem_ws, "rules", "arch", "r2", body="## B\nrule B\n")
    plan = mem_ws / "plan.json"
    plan.write_text(json.dumps({"rules/arch/merged.md": ["rules/arch/r1.md", "rules/arch/r2.md"]}))
    s = Spec()
    s.restructure(argparse.Namespace(map=str(plan), dry_run=False))
    assert (mem_ws / ".skein" / "spec" / "rules" / "arch" / "merged.md").exists()


# ---- serve.py: 进程内可覆盖的行 ----

def test_serve_pkg_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    """pkg_manager 返回可用包管理器或 None。"""
    from skeinlib.web import serve
    result = serve.pkg_manager()
    assert result is None or isinstance(result, str)


def test_serve_debug_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from skeinlib.web import serve
    monkeypatch.delenv("SKEIN_DEBUG", raising=False)
    assert serve.debug_enabled(None) is False
    monkeypatch.setenv("SKEIN_DEBUG", "1")
    assert serve.debug_enabled(None) is True
