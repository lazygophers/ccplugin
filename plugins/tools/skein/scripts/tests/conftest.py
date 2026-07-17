"""共享 fixture — pytest tmp_path 隔离临时 git 仓 + skein/memory CLI 封装。

提炼自 test_skein.py 的 _init_ws/sk/git helper (line 47-54, 17-23)。每个测试拿独立
临时目录, 禁碰真实 .skein/。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

SCRIPTS: Path = Path(__file__).resolve().parent.parent
SKEIN: Path = SCRIPTS / "skein.py"
MEM: Path = SCRIPTS / "memory.py"

GitCmd = Callable[..., None]
SkeinCli = Callable[..., subprocess.CompletedProcess[str]]
MemCli = Callable[..., subprocess.CompletedProcess[str]]


@pytest.fixture
def git_cmd() -> GitCmd:
    """git 调用封装: git_cmd(cwd, *args) → subprocess.run(check=True)。"""
    def _git(cwd: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return _git


@pytest.fixture
def skein_cli() -> SkeinCli:
    """skein.py CLI 封装: skein_cli(cwd, *args, check=True) → CompletedProcess。"""
    def _sk(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SKEIN), *args], cwd=cwd,
                              capture_output=True, text=True, check=check)
    return _sk


@pytest.fixture
def mem_cli() -> MemCli:
    """memory.py CLI 封装: mem_cli(cwd, *args, inp=None) → CompletedProcess。"""
    def _mem(cwd: Path, *args: str, inp: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(MEM), *args], cwd=cwd,
                              capture_output=True, text=True, check=True, input=inp)
    return _mem


@pytest.fixture
def ws(tmp_path: Path, git_cmd: GitCmd, skein_cli: SkeinCli) -> Path:
    """造隔离临时 git 仓 + skein init, 返回仓库根 Path。每个测试独立 tmp_path。"""
    d = tmp_path
    git_cmd(d, "init", "-q")
    git_cmd(d, "config", "user.email", "t@t.dev")
    git_cmd(d, "config", "user.name", "t")
    (d / "seed.txt").write_text("s\n")
    git_cmd(d, "add", "-A")
    git_cmd(d, "commit", "-qm", "seed")
    skein_cli(d, "init")
    return d


@pytest.fixture
def mem_ws(tmp_path: Path, git_cmd: GitCmd, mem_cli: MemCli) -> Path:
    """造隔离临时 git 仓 + memory init (.skein/spec/core|recall 骨架), 供 memory.py 测试。"""
    d = tmp_path
    git_cmd(d, "init", "-q")
    git_cmd(d, "config", "user.email", "t@t.dev")
    git_cmd(d, "config", "user.name", "t")
    (d / "seed.txt").write_text("s\n")
    git_cmd(d, "add", "-A")
    git_cmd(d, "commit", "-qm", "seed")
    mem_cli(d, "init")
    return d
