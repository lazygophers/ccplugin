"""Tests for hooks/_lib/git_sync.py."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _helpers import add_paths

add_paths()

import git_sync  # noqa: E402


def _git(args, cwd, check=True):
    cp = subprocess.run(
        ["git", *args], cwd=str(cwd),
        capture_output=True, text=True,
    )
    if check and cp.returncode != 0:
        raise RuntimeError(f"git {args} failed: {cp.stderr}")
    return cp


def _init_repo(root: Path) -> None:
    # 用 -b main 显式分支; 老 git 不支持时回退
    cp = subprocess.run(
        ["git", "init", "-b", "main", str(root)],
        capture_output=True, text=True,
    )
    if cp.returncode != 0:
        subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(root), "checkout", "-b", "main"],
                       capture_output=True, text=True)
    # 只在 repo 内 set, 不污染全局
    _git(["config", "user.email", "test@cortex.local"], cwd=root)
    _git(["config", "user.name", "Cortex Test"], cwd=root)
    _git(["config", "commit.gpgsign", "false"], cwd=root)


def _write_config(vault: Path, **kwargs) -> None:
    meta = vault / "_meta"
    meta.mkdir(parents=True, exist_ok=True)
    data = {"version": "0.0.0", "lang": "zh-CN"}
    data.update(kwargs)
    (meta / "version.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


class GitSyncTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self._tmp.name) / "vault"
        self.vault.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_not_a_git_repo_skipped(self):
        _write_config(self.vault, auto_commit=True)
        ok, info = git_sync.auto_commit(self.vault)
        self.assertTrue(ok)
        self.assertIn("not a git repo", info)

    def test_auto_commit_disabled_skipped(self):
        _init_repo(self.vault)
        _write_config(self.vault, auto_commit=False)
        # 创点改动也不该 commit
        (self.vault / "note.md").write_text("# x\n", encoding="utf-8")
        ok, info = git_sync.auto_commit(self.vault)
        self.assertTrue(ok)
        self.assertIn("auto_commit disabled", info)

    def test_no_changes(self):
        _init_repo(self.vault)
        _write_config(self.vault, auto_commit=True)
        # 先 commit 初始 _meta 让 worktree clean
        _git(["add", "-A"], cwd=self.vault)
        _git(["commit", "-m", "init"], cwd=self.vault)
        ok, info = git_sync.auto_commit(self.vault)
        self.assertTrue(ok)
        self.assertEqual(info, "no changes")

    def test_commit_when_enabled_with_changes(self):
        _init_repo(self.vault)
        _write_config(self.vault, auto_commit=True)
        # 初始 baseline
        _git(["add", "-A"], cwd=self.vault)
        _git(["commit", "-m", "init"], cwd=self.vault)
        # 新改动
        (self.vault / "note.md").write_text("# hello\n", encoding="utf-8")
        ok, info = git_sync.auto_commit(self.vault, message="test commit")
        self.assertTrue(ok, f"info={info}")
        self.assertIn("committed", info)
        # HEAD 应有新 commit
        log = _git(["log", "--oneline"], cwd=self.vault).stdout
        self.assertIn("test commit", log)

    def test_push_unreachable_remote_returns_false(self):
        _init_repo(self.vault)
        _write_config(self.vault, auto_commit=True, auto_push=True)
        _git(["add", "-A"], cwd=self.vault)
        _git(["commit", "-m", "init"], cwd=self.vault)
        # 不存在的远端
        bad_remote = "file:///nonexistent/cortex-test-remote.git"
        _git(["remote", "add", "origin", bad_remote], cwd=self.vault)
        (self.vault / "note.md").write_text("# x\n", encoding="utf-8")
        ok, info = git_sync.auto_commit(self.vault, message="push test")
        # commit 成功但 push 失败 → (False, ...)
        self.assertFalse(ok)
        self.assertIsInstance(info, str)
        self.assertTrue(len(info) > 0)
        # 本地 commit 已落
        log = _git(["log", "--oneline"], cwd=self.vault).stdout
        self.assertIn("push test", log)

    def test_subprocess_timeout_returns_false(self):
        _init_repo(self.vault)
        _write_config(self.vault, auto_commit=True)
        _git(["add", "-A"], cwd=self.vault)
        _git(["commit", "-m", "init"], cwd=self.vault)
        (self.vault / "note.md").write_text("# x\n", encoding="utf-8")

        real_run = subprocess.run

        def fake_run(args, *a, **kw):
            # 仅在 git add 时模拟 timeout
            if isinstance(args, list) and len(args) >= 2 and args[0] == "git" and args[1] == "add":
                raise subprocess.TimeoutExpired(cmd=args, timeout=1)
            return real_run(args, *a, **kw)

        with mock.patch.object(git_sync.subprocess, "run", side_effect=fake_run):
            ok, info = git_sync.auto_commit(self.vault)
        self.assertFalse(ok)
        self.assertEqual(info, "timeout")


if __name__ == "__main__":
    unittest.main()
