"""_task_detail research 字段回归 — st1 验收: research 目录多篇笔记进 dict, 空目录不崩。

直接 import skein.py (顶层仅 stdlib + hooklib, 无重依赖)。Skein() 构造走 git rev-parse,
故 os.chdir 到 ws fixture 仓根后实例化, 造 task/<id>/research/*.md 后断言返回结构。
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest  # type: ignore[import-not-found]

_SKEIN = Path(__file__).resolve().parent.parent / "skein.py"
_spec = importlib.util.spec_from_file_location("skein_detail", _SKEIN)
assert _spec is not None and _spec.loader is not None
sk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sk)


def _new_task(root: Path, tid: str) -> Path:
    tdir = root / ".skein" / "task" / tid
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "task.json").write_text(
        '{"id": "%s", "name": "t", "subtasks": [], "contracts": []}' % tid,
        encoding="utf-8",
    )
    return tdir


def test_research_dict_has_multi_notes(ws: Path) -> None:
    os.chdir(ws)
    tdir = _new_task(ws, "spec-memory-extend")
    rdir = tdir / "research"
    rdir.mkdir()
    for nm in ("00-summary.md", "01-a.md", "05-e.md"):
        (rdir / nm).write_text("# %s\nbody" % nm, encoding="utf-8")
    board = sk.Skein()
    d = board._task_detail("spec-memory-extend")
    assert d is not None
    assert d["research"] == {
        "00-summary.md": "# 00-summary.md\nbody",
        "01-a.md": "# 01-a.md\nbody",
        "05-e.md": "# 05-e.md\nbody",
    }


def test_research_empty_when_no_dir(ws: Path) -> None:
    os.chdir(ws)
    _new_task(ws, "no-research")
    board = sk.Skein()
    d = board._task_detail("no-research")
    assert d is not None
    assert d["research"] == {}
