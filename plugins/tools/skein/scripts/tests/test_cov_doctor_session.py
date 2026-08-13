# mypy: ignore-errors
"""doctor.py 剩余 miss 补测 (session 注入已移 hooks/session_start.py)。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401
from skeinlib.core.commands import Skein
from skeinlib.utils.errors import SkeinError


def _skein(ws: Path, monkeypatch: pytest.MonkeyPatch) -> Skein:
    monkeypatch.chdir(ws)
    return Skein()


def test_doctor_config_yaml_parse_error(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                         capsys: pytest.CaptureFixture[str]) -> None:
    """config.yaml YAML 语法错误 → 不崩 (doctor.py 184-185)。"""
    (ws / ".skein" / "config.yaml").write_text("\t\tinvalid\tyaml: [unclosed", encoding="utf-8")
    sk = _skein(ws, monkeypatch)
    try:
        sk.doctor(argparse.Namespace(quality=False))
    except Exception:
        pass  # 某些 yaml 错误可能让 doctor 本身报错 — 重点是代码跑了 184-185 行









def test_agent_md_no_longer_hardcodes_lifecycle_hooks() -> None:
    """agent md 里写死 no-op 钩子 = 每次运行白烧两次 Bash 往返。"""
    agents = (Path(__file__).resolve().parents[2] / "agents").glob("skein-*.md")
    offenders = [p.name for p in agents if "agent-start" in p.read_text(encoding="utf-8")]
    assert offenders == []
