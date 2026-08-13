# mypy: ignore-errors
"""write.py finish_candidates + _print_finish_candidates_result 覆盖。
构造真 task 目录, 走 Spec().finish_candidates 进程内。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401
from skeinlib.spec.facade import Spec
from skeinlib.spec.write import WriteMixin, FinishCandidatesResult, AnchorHit, KeywordCandidate
from skeinlib.utils.errors import SkeinError


def _write_rule(ws: Path, ns: str, cat: str, topic: str, fm: str = "inclusion: auto\nstatus: active\n",
                body: str = "rule body") -> Path:
    d = ws / ".skein" / "spec" / ns / cat
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{topic}.md"
    f.write_text(f"---\n{fm}---\n\n{body}\n")
    return f


def _make_task(ws: Path, tid: str, prd: str = "# PRD\nGoal: do X\n") -> Path:
    tdir = ws / ".skein" / "task" / tid
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "task.json").write_text(json.dumps({"id": tid, "status": "active", "subtasks": []}))
    (tdir / "prd.md").write_text(prd)
    return tdir


# ---- _print_finish_candidates_result (纯输出函数) ----

def test_print_finish_candidates_empty(monkeypatch: pytest.MonkeyPatch,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir("/tmp")
    s = Spec()
    result = FinishCandidatesResult(tid="t1")
    s._print_finish_candidates_result(result)
    out = capsys.readouterr().out
    assert "无候选" in out


def test_print_finish_candidates_with_hits(monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir("/tmp")
    s = Spec()
    result = FinishCandidatesResult(
        tid="t1",
        files=["src/a.py", "src/b.py"],
        keywords=["auth", "login"],
        anchor_hits=[AnchorHit(file="src/a.py", anchor="src/a.py:login", rule="product/auth")],
        weak_candidates=[KeywordCandidate(rule="product/auth", title="Auth",
                                          keywords="login,auth", matched_keywords=["auth"])],
    )
    s._print_finish_candidates_result(result)
    out = capsys.readouterr().out
    assert "Anchor" in out
    assert "src/a.py" in out
    assert "关键词召回" in out


def test_print_finish_candidates_many_files(monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir("/tmp")
    s = Spec()
    result = FinishCandidatesResult(
        tid="t1",
        files=[f"file{i}.py" for i in range(15)],
    )
    s._print_finish_candidates_result(result)
    out = capsys.readouterr().out
    assert "还有 5 个文件" in out


def test_print_finish_candidates_with_message(monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir("/tmp")
    s = Spec()
    result = FinishCandidatesResult(
        tid="t1",
        message="新功能域",
        suggestion="建议新建 product wiki 页",
    )
    s._print_finish_candidates_result(result)
    out = capsys.readouterr().out
    assert "新功能域" in out
    assert "建议" in out


# ---- finish_candidates 进程内 ----

def test_finish_candidates_no_task_dir(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    with pytest.raises(SkeinError, match="任务目录不存在"):
        s.finish_candidates(argparse.Namespace(tid="no-such-task", json=False, files=None))


def test_finish_candidates_with_task(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    _write_rule(mem_ws, "product", "wiki", "authpage",
                fm="inclusion: auto\nstatus: active\nanchors: src/auth.py\n",
                body="## Login\nAuth rule\n")
    _make_task(mem_ws, "feat-auth", prd="# PRD\n实现 login 功能\nGoal: auth login\n")
    s = Spec()
    import argparse
    s.finish_candidates(argparse.Namespace(tid="feat-auth", json=False, files=None))


def test_finish_candidates_json(mem_ws: Path, monkeypatch: pytest.MonkeyPatch,
                                 capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.chdir(mem_ws)
    _make_task(mem_ws, "task1", prd="# PRD\nFeature X\n")
    s = Spec()
    import argparse
    s.finish_candidates(argparse.Namespace(tid="task1", json=True, files=None))
    out = capsys.readouterr().out
    # json 模式输出 JSON
    assert out.strip().startswith("{") or "candidates" in out.lower()


def test_finish_candidates_with_files(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """finish-candidates --files 手动注入文件列表。"""
    monkeypatch.chdir(mem_ws)
    (mem_ws / "src").mkdir(exist_ok=True)
    (mem_ws / "src" / "code.py").write_text("# code\n")
    _write_rule(mem_ws, "product", "wiki", "codepage",
                fm="inclusion: auto\nstatus: active\nanchors: src/code.py\n",
                body="## Code Rule\nDo X\n")
    _make_task(mem_ws, "feat-x", prd="# PRD\nFeature X\n")
    s = Spec()
    import argparse
    s.finish_candidates(argparse.Namespace(tid="feat-x", json=False, files="src/code.py"))


# ---- write.py _require_namespace ----

def test_require_namespace_missing(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    with pytest.raises(SkeinError, match="namespace"):
        s._require_namespace(argparse.Namespace(namespace=None), with_inclusion=True)


def test_require_namespace_with_inclusion(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    ns, inc = s._require_namespace(
        argparse.Namespace(namespace="rules", inclusion="always"), with_inclusion=True)
    assert ns == "rules"
    assert inc == "always"


def test_require_namespace_default_inclusion(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    ns, inc = s._require_namespace(
        argparse.Namespace(namespace="rules", inclusion=None), with_inclusion=True)
    assert ns == "rules"
    assert inc == "auto"


def test_require_namespace_without_inclusion(mem_ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(mem_ws)
    s = Spec()
    import argparse
    ns, inc = s._require_namespace(
        argparse.Namespace(namespace="rules", inclusion=None), with_inclusion=False)
    assert ns == "rules"
    assert inc is None
