"""插件清单规范测试。"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT_DIR / ".claude-plugin" / "plugin.json"
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"


def _load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_version_matches_pyproject() -> None:
    # Arrange
    manifest = _load_manifest()
    with PYPROJECT_PATH.open("rb") as f:
        pyproject = tomllib.load(f)

    # Act
    manifest_version = manifest["version"]
    project_version = pyproject["project"]["version"]

    # Assert
    assert manifest_version == project_version


def test_manifest_hooks_use_project_relative_runner() -> None:
    # Arrange
    manifest = _load_manifest()
    required_events = {
        "SessionStart",
        "SessionEnd",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "Stop",
    }

    # Act
    hooks = manifest.get("hooks", {})

    # Assert
    assert required_events.issubset(hooks.keys())
    for event in required_events:
        event_hooks = hooks[event]
        assert event_hooks
        for hook_group in event_hooks:
            for hook in hook_group.get("hooks", []):
                command = hook.get("command", "")
                assert command.startswith("PLUGIN_NAME=memory ")
                assert "uv run --directory ${CLAUDE_PLUGIN_ROOT}" in command
                assert "./scripts/main.py hooks" in command


def test_manifest_name_and_skills_dir_are_valid() -> None:
    # Arrange
    manifest = _load_manifest()

    # Act
    plugin_name = manifest.get("name", "")
    skills_dir = ROOT_DIR / "skills.bak"

    # Assert
    assert re.fullmatch(r"[a-z0-9][a-z0-9-]*", plugin_name)
    assert manifest.get("skills.bak") == "./skills.bak/"
    assert skills_dir.exists()
    assert any(skills_dir.glob("*/SKILL.md"))


@pytest.mark.skipif(shutil.which("claude") is None, reason="claude CLI not installed")
def test_manifest_is_valid_for_claude_cli() -> None:
    # Arrange
    command = ["claude", "plugin", "validate", str(MANIFEST_PATH)]

    # Act
    result = subprocess.run(command, cwd=ROOT_DIR, capture_output=True, text=True)

    # Assert
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, combined_output
    assert "Validation passed" in combined_output
