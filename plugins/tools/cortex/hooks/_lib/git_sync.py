"""Vault git auto-sync — opt-in via _meta/version.json.

Pure stdlib + subprocess git CLI. No PyGit2/dulwich/gitpython.

Behavior:
- 默认 opt-in 严格: 未启用直接 skip
- has_changes 检测先于 commit, 防 commit storm
- 任何异常 fail-soft 返 (False, info), 不抛 (不阻塞 Stop hook)
- timezone: UTC, 跨机一致
- 禁 shell=True
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


COMMIT_TIMEOUT = 10
PUSH_TIMEOUT = 30
GIT_TIMEOUT = 30


def _run_git(args: list[str], cwd: Path, timeout: int = GIT_TIMEOUT) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        timeout=timeout,
        capture_output=True,
        text=True,
    )


def read_vault_config(vault: Path) -> dict:
    """读 _meta/version.json. 缺/坏则返 {}."""
    path = vault / "_meta" / "version.json"
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def is_git_repo(vault: Path) -> bool:
    """vault/.git 存在 + git rev-parse 成功."""
    if not (vault / ".git").exists():
        return False
    try:
        cp = _run_git(["rev-parse", "--git-dir"], cwd=vault, timeout=5)
        return cp.returncode == 0
    except Exception:
        return False


def is_auto_commit_enabled(vault: Path) -> bool:
    return read_vault_config(vault).get("auto_commit", False) is True


def is_auto_push_enabled(vault: Path) -> bool:
    return read_vault_config(vault).get("auto_push", False) is True


def has_changes(vault: Path) -> bool:
    """git status --porcelain 非空 = 有改动."""
    try:
        cp = _run_git(["status", "--porcelain"], cwd=vault, timeout=10)
        if cp.returncode != 0:
            return False
        return bool(cp.stdout.strip())
    except Exception:
        return False


def _default_message() -> str:
    return "auto: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def auto_commit(vault: Path, message: Optional[str] = None) -> tuple[bool, str]:
    """主入口.

    返回 (ok, info). 见模块 docstring 行为说明.
    """
    try:
        if not is_git_repo(vault):
            return (True, "not a git repo, skipped")
        if not is_auto_commit_enabled(vault):
            return (True, "auto_commit disabled, skipped")
        if not has_changes(vault):
            return (True, "no changes")

        msg = message or os.environ.get("CORTEX_GIT_MESSAGE") or _default_message()

        try:
            cp_add = _run_git(["add", "-A"], cwd=vault, timeout=COMMIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            return (False, "timeout")
        if cp_add.returncode != 0:
            return (False, (cp_add.stderr or "git add failed").strip())

        try:
            cp_commit = _run_git(["commit", "-m", msg], cwd=vault, timeout=COMMIT_TIMEOUT)
        except subprocess.TimeoutExpired:
            return (False, "timeout")
        if cp_commit.returncode != 0:
            return (False, (cp_commit.stderr or "git commit failed").strip())

        info = f"committed: {msg}"

        if is_auto_push_enabled(vault):
            try:
                cp_push = _run_git(["push", "origin", "HEAD"], cwd=vault, timeout=PUSH_TIMEOUT)
            except subprocess.TimeoutExpired:
                return (False, "push timeout")
            except Exception as e:
                return (False, f"push error: {e!r}")
            if cp_push.returncode != 0:
                return (False, (cp_push.stderr or "git push failed").strip())
            info += "; pushed"

        return (True, info)
    except Exception as e:
        return (False, repr(e))


def _resolve_vault(arg: Optional[str]) -> Optional[Path]:
    """argv > ~/.cortex/config.json > None (不猜).

    Env var lookup removed per PRD (config-only). Callers pass vault
    explicitly as argv; config.json is consulted as a fallback so that
    standalone invocations from cron / wrappers Just Work.
    """
    if arg:
        return Path(arg).expanduser().resolve()
    try:
        # Late import: keep this module importable without hooks/_lib on path.
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from cortex_config import get_vault  # type: ignore
        v = get_vault()
        if v:
            return v.expanduser().resolve()
    except Exception:
        pass
    return None


def main(argv: list[str]) -> int:
    """CLI: git_sync.py auto <vault> | git_sync.py status <vault>."""
    if len(argv) < 2:
        sys.stderr.write("usage: git_sync.py {auto|status} <vault_path>\n")
        return 2
    cmd = argv[1]
    vault_arg = argv[2] if len(argv) >= 3 else None
    vault = _resolve_vault(vault_arg)
    if vault is None:
        sys.stderr.write("vault not resolved (pass as argv or set 'vault' in ~/.cortex/config.json)\n")
        return 2

    if cmd == "auto":
        ok, info = auto_commit(vault)
        sys.stdout.write(f"{'ok' if ok else 'fail'}: {info}\n")
        return 0 if ok else 1
    if cmd == "status":
        sys.stdout.write(
            f"vault={vault}\n"
            f"is_git_repo={is_git_repo(vault)}\n"
            f"auto_commit={is_auto_commit_enabled(vault)}\n"
            f"auto_push={is_auto_push_enabled(vault)}\n"
            f"has_changes={has_changes(vault)}\n"
        )
        return 0
    sys.stderr.write(f"unknown cmd: {cmd}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
