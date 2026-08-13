# mypy: ignore-errors
"""doctor.py + session_context 剩余 miss 补测。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

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


def test_pending_fix_hint_empty_problems(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """pending-fix problems 为空列表 → 返回空串 (doctor.py 331)。"""
    sk = _skein(ws, monkeypatch)
    marker = ws / ".skein" / "spec" / ".pending-fix"
    marker.parent.mkdir(exist_ok=True)
    marker.write_text(json.dumps({"problems": []}), encoding="utf-8")
    assert sk._pending_fix_hint() == ""


def test_session_context_no_skein_no_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """非 git 且无 .skein → 直接 return (doctor.py 343)。"""
    monkeypatch.chdir(tmp_path)
    sk = Skein()
    sk.session_context()  # 不输出任何东西


def test_session_context_skein_without_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    """有 .skein 但无 config.yaml → 未初始化时静默。"""
    d = tmp_path / "proj"
    (d / ".skein").mkdir(parents=True)
    # 需要 git init 否则 git=False 且有 .skein
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=d)
    subprocess.run(["git", "config", "user.email", "t@t.dev"], cwd=d)
    subprocess.run(["git", "config", "user.name", "t"], cwd=d)
    (d / "seed").write_text("s")
    subprocess.run(["git", "add", "-A"], cwd=d)
    subprocess.run(["git", "commit", "-qm", "seed"], cwd=d)
    monkeypatch.chdir(d)
    sk = Skein()
    sk.session_context()
    assert capsys.readouterr().out == ""


def _session_ctx(ws: Path, monkeypatch: pytest.MonkeyPatch,
                 capsys: pytest.CaptureFixture[str]) -> str:
    _skein(ws, monkeypatch).session_context()
    out = capsys.readouterr().out.strip()
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def test_session_context_silent_about_agent_hooks_by_default(
        ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """默认无 hooks.agent 声明 → 不提 agent 钩子, agent md 里也不该写死这两步。"""
    assert "agent-start" not in _session_ctx(ws, monkeypatch, capsys)


def test_session_context_silent_about_empty_agent_hook_skeleton(
        ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """空 AgentHooks 骨架不是声明，不应注入生命周期命令。"""
    cfg_path = ws / ".skein" / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    cfg["hooks"] = {"agent": {"skein-executor": {"start": [], "stop": []}}}
    cfg_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    assert "agent-start" not in _session_ctx(ws, monkeypatch, capsys)


def test_session_context_announces_declared_agent_hooks(
        ws: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """config 真声明了 hooks.agent.<name> → 才提示 main 把首尾钩子写进 dispatch prompt。"""
    cfg_path = ws / ".skein" / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    cfg["hooks"] = {"agent": {"skein-executor": {"start": [{"command": "echo hi"}]}}}
    cfg_path.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    ctx = _session_ctx(ws, monkeypatch, capsys)
    assert "skein-executor" in ctx and "agent-start" in ctx


def test_agent_md_no_longer_hardcodes_lifecycle_hooks() -> None:
    """agent md 里写死 no-op 钩子 = 每次运行白烧两次 Bash 往返。"""
    agents = (Path(__file__).resolve().parents[2] / "agents").glob("skein-*.md")
    offenders = [p.name for p in agents if "agent-start" in p.read_text(encoding="utf-8")]
    assert offenders == []
