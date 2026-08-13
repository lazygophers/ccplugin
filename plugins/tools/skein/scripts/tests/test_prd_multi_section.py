"""PRD 多段写入与 CLI 错误提示契约。"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SkeinCli


def test_prd_write_accepts_multiple_sections(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "task", "create", "demo", "--name", "演示", "--desc", "多段写入")
    skein_cli(ws, "prd", "write", "demo",
              "--type", "goal", "--list", "目标一",
              "--type", "scope", "--list", "边界一")

    body = json.loads(skein_cli(ws, "prd", "read", "demo").stdout)["body"]
    assert "目标一" in body and "边界一" in body


def test_prd_and_subtask_help_match_supported_options(skein_cli: SkeinCli, ws: Path) -> None:
    prd_help = skein_cli(ws, "prd", "write", "--help").stdout
    assert "一次写多段" in prd_help

    subtask_help = skein_cli(ws, "subtask", "--help").stdout
    add_usage = next(line for line in subtask_help.splitlines() if "add   <tid> <sid>" in line)
    assert "[--check]" in add_usage and "[--phase]" in add_usage


def test_unknown_command_lists_available_commands(skein_cli: SkeinCli, ws: Path) -> None:
    result = skein_cli(ws, "subtask-add", "--help", check=False)

    assert result.returncode != 0
    assert "可用子命令:" in result.stdout + result.stderr


def test_unknown_option_lists_available_options(skein_cli: SkeinCli, ws: Path) -> None:
    result = skein_cli(ws, "task", "confirm", "demo", "--bogus", check=False)

    assert result.returncode != 0
    assert "可用选项:" in result.stdout + result.stderr
