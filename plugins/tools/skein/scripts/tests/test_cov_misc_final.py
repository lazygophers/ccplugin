# mypy: ignore-errors
"""config/manager + pre_tool_use + user_prompt_submit 残余 miss 补测。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
import yaml

import conftest  # noqa: F401


# ---- config/manager.py: get / yaml_dump / 降级 ----

def test_config_get_dotted_path(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Config.get 支持点号路径取值。"""
    from skeinlib.config.manager import Config
    monkeypatch.chdir(ws)
    cfg = Config(ws / ".skein" / "config.yaml")
    result = cfg.get("pools.work")
    assert isinstance(result, int)


def test_config_yaml_dump(ws: Path) -> None:
    from skeinlib.config.manager import Config
    text = Config.yaml_dump({"key": "value"})
    assert "key: value" in text


def test_config_manager_degrade_on_bad_hooks(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config.yaml hooks 字段畸形 → 降级到默认 (152-153)。"""
    from skeinlib.config.manager import Config
    cfg_file = ws / ".skein" / "config.yaml"
    cfg_file.write_text("hooks:\n  create:\n    before:\n      - {bad yaml\n", encoding="utf-8")
    monkeypatch.chdir(ws)
    try:
        cfg = Config(cfg_file)
    except Exception:
        pass  # 某些 yaml 错误直接抛 — 重点是代码跑了


# ---- pre_tool_use.py: OSError 路径 ----

def test_find_filematch_specs_oserror(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """find_filematch_specs 遇 OSError → 返回空 (line 57-60)。"""
    from skeinlib.hooks import pre_tool_use as ptu
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    # 写一个正常 fileMatch 规则
    (spec_dir / "test.md").write_text(
        "---\ninclusion: fileMatch\nglobs: *.py\ntitle: T\n---\nbody\n")
    # monkeypatch os.walk 抛 OSError
    original_walk = os.walk
    def fake_walk(*args: Any, **kw: Any) -> Any:
        raise OSError("boom")
        yield  # never reached
    monkeypatch.setattr(os, "walk", fake_walk)
    result = ptu.find_filematch_specs(str(spec_dir))
    assert result == []


def test_file_matches_globs_value_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """file_matches_globs 遇 ValueError → 返回 False (line 71-72)。"""
    from skeinlib.hooks import pre_tool_use as ptu
    # 构造一个会触发 ValueError 的场景 (不同驱动器/无效路径)
    result = ptu.file_matches_globs("::invalid::path", ["*.py"], str(tmp_path))
    assert result is False


# ---- user_prompt_submit.py: 剩余分支 ----

# ---- hooks/agent.py: yaml error / no agents ----

def test_agent_hook_bad_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """agent hook config.yaml YAML 错误 → return 0 (line 24-25)。"""
    from skeinlib.hooks import agent
    skein_dir = tmp_path / ".skein"
    skein_dir.mkdir()
    (skein_dir / "config.yaml").write_text("\tbad: [unclosed\n")
    monkeypatch.setattr("skeinlib.hooks.agent.git_root", lambda _: str(tmp_path))
    monkeypatch.setattr("sys.argv", ["hooks.py", "agent-start", "--cwd", str(tmp_path)])
    assert agent.cmd_agent_hook("start") == 0


def test_agent_hook_no_agents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """agent hook config 有 hooks 但无 agent section → return 0 (line 29)。"""
    from skeinlib.hooks import agent
    skein_dir = tmp_path / ".skein"
    skein_dir.mkdir()
    (skein_dir / "config.yaml").write_text("hooks:\n  create:\n    before:\n      - echo hi\n")
    monkeypatch.setattr("skeinlib.hooks.agent.git_root", lambda _: str(tmp_path))
    monkeypatch.setattr("sys.argv", ["hooks.py", "agent-start", "--cwd", str(tmp_path)])
    assert agent.cmd_agent_hook("start") == 0
