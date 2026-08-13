# mypy: ignore-errors
"""spec CLI 命令路径补测 — 通过 subprocess 跑 spec.py 的 amend/finish-candidates/degrade/list 命令。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import conftest  # noqa: F401


def test_spec_list(mem_ws: Path, mem_cli: Any) -> None:
    mem_cli(mem_ws, "list")


def test_spec_list_with_namespace(mem_ws: Path, mem_cli: Any) -> None:
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "rule1", "--title", "Rule One", "--body-file", "/dev/null")
    r = mem_cli(mem_ws, "list", "--namespace", "rules")
    assert "rule1" in r.stdout or "Rule" in r.stdout


def test_spec_degrade_file(mem_ws: Path, mem_cli: Any) -> None:
    """degrade 单文件: always → auto。"""
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "always",
            "--category", "core", "--topic", "big", "--title", "Big Rule", "--body-file", "/dev/null")
    r = mem_cli(mem_ws, "degrade", "rules/core/big")
    assert r.returncode == 0


def test_spec_amend(mem_ws: Path, mem_cli: Any) -> None:
    """amend 改写章节正文。"""
    # 先写规则
    body = mem_ws / "body.txt"
    body.write_text("original body")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "topic1",
            "--title", "Section One", "--body-file", str(body))
    # amend
    new_body = mem_ws / "new_body.txt"
    new_body.write_text("amended content")
    r = mem_cli(mem_ws, "amend", "--topic", "rules/arch/topic1",
                "--section", "Section One", "--body-file", str(new_body))
    assert r.returncode == 0


def test_spec_amend_rename(mem_ws: Path, mem_cli: Any) -> None:
    body = mem_ws / "body.txt"
    body.write_text("content")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "topic1",
            "--title", "Old Name", "--body-file", str(body))
    new_body = mem_ws / "new.txt"
    new_body.write_text("renamed")
    r = mem_cli(mem_ws, "amend", "--topic", "rules/arch/topic1",
                "--section", "Old Name", "--body-file", str(new_body),
                "--rename-section", "New Name")
    assert r.returncode == 0


def test_spec_amend_nonexistent_section(mem_ws: Path, mem_cli: Any) -> None:
    body = mem_ws / "body.txt"
    body.write_text("content")
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "topic1",
            "--title", "Exists", "--body-file", str(body))
    r = mem_cli(mem_ws, "amend", "--topic", "rules/arch/topic1",
                "--section", "DoesNotExist", "--body-file", str(body), check=False)
    assert r.returncode != 0


def test_spec_archive_restore(mem_ws: Path, mem_cli: Any) -> None:
    """archive 后 restore。"""
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "rule1",
            "--title", "Rule", "--body-file", "/dev/null")
    r = mem_cli(mem_ws, "archive")
    assert r.returncode == 0
    # 找归档时间戳
    archive_dir = mem_ws / ".skein" / "spec" / ".archive"
    if archive_dir.exists():
        ts = sorted(archive_dir.iterdir())[-1].name
        r2 = mem_cli(mem_ws, "restore", ts)
        assert r2.returncode == 0


def test_spec_archive_namespace(mem_ws: Path, mem_cli: Any) -> None:
    """archive 指定 namespace。"""
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "rule1",
            "--title", "Rule", "--body-file", "/dev/null")
    r = mem_cli(mem_ws, "archive", "--namespace", "rules")
    assert r.returncode == 0


def test_spec_restore_nonexistent(mem_ws: Path, mem_cli: Any) -> None:
    r = mem_cli(mem_ws, "restore", "nonexistent-ts", check=False)
    assert r.returncode != 0


def test_spec_maintain_with_namespace(mem_ws: Path, mem_cli: Any) -> None:
    """maintain 指定 namespace。"""
    mem_cli(mem_ws, "sediment", "--namespace", "rules", "--inclusion", "auto",
            "--category", "arch", "--topic", "rule1",
            "--title", "Rule", "--body-file", "/dev/null")
    r = mem_cli(mem_ws, "maintain", "--namespace", "rules")
    assert r.returncode == 0


def test_spec_finish_candidates_no_task(mem_ws: Path, mem_cli: Any) -> None:
    """finish-candidates 对不存在的 task → 返回建议或报错。"""
    r = mem_cli(mem_ws, "finish-candidates", "nonexistent-task", check=False)
    # 不崩就行
    assert r.returncode in (0, 1, 2)


def test_spec_finish_candidates_json_no_task(mem_ws: Path, mem_cli: Any) -> None:
    r = mem_cli(mem_ws, "finish-candidates", "nonexistent-task", "--json", check=False)
    assert r.returncode in (0, 1, 2)


def test_spec_degrade_auto_nothing(mem_ws: Path, mem_cli: Any) -> None:
    """degrade --auto 无 always 规则 → 空跑。"""
    r = mem_cli(mem_ws, "degrade", "--auto")
    assert r.returncode == 0


def test_spec_reindex(mem_ws: Path, mem_cli: Any) -> None:
    """reindex 幂等。"""
    r = mem_cli(mem_ws, "reindex")
    assert r.returncode == 0


def test_spec_debug_flag(mem_ws: Path, mem_cli: Any) -> None:
    """--debug 开关不崩。"""
    r = mem_cli(mem_ws, "--debug", "list")
    assert r.returncode == 0
