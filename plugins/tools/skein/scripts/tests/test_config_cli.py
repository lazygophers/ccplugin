"""config 命令测试 — skein.py config get/set [key] [value]。

经 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
CONFIG_DEFAULTS 8 键 (max_active/auto_commit/use_worktree/worktree_root/retain_days/
web_serve/board_open/spec_core_budget)。报错用例传 check=False 断 returncode + stderr 文案。
覆盖 (8 用例):
  1. get 全部: 8 行 key=val, 含 max_active=2。
  2. get 单键: max_active → "2"。
  3. get 未知键: 拒 (returncode!=0, stderr 含「未知配置键」)。
  4. set + 回读: set max_active 3 → get 得 "3"。
  5. set bool coerce: set auto_commit false → get 得 "False"。
  6. set 未知键: 拒 (非静默, returncode!=0, stderr 含「未知配置键」)。
  7. set 类型不合: set max_active abc → 拒 (stderr 含「类型不合」/「值类型」)。
  8. set 保留其他键: set max_active 5 后 retain_days 仍默认值。
"""
from __future__ import annotations

from pathlib import Path

from conftest import SkeinCli


# ---------- 1. get 全部 ----------
def test_get_all(skein_cli: SkeinCli, ws: Path) -> None:
    """config get 无 key → 8 行 key=val, 含 max_active=2。"""
    r = skein_cli(ws, "config", "get")
    lines = [ln for ln in r.stdout.strip().splitlines() if "=" in ln]
    assert len(lines) == 8, f"应 8 行 key=val, 得 {len(lines)}: {lines}"
    assert "max_active=2" in lines, f"缺 max_active=2: {lines}"


# ---------- 2. get 单键 ----------
def test_get_single(skein_cli: SkeinCli, ws: Path) -> None:
    """config get max_active → "2"。"""
    r = skein_cli(ws, "config", "get", "max_active")
    assert r.stdout.strip() == "2", f"单键值错: {r.stdout!r}"


# ---------- 3. get 未知键 ----------
def test_get_unknown_key(skein_cli: SkeinCli, ws: Path) -> None:
    """config get nope → 拒 (returncode!=0, stderr 含未知配置键)。"""
    r = skein_cli(ws, "config", "get", "nope", check=False)
    assert r.returncode != 0, f"未知键未拒: rc={r.returncode}"
    assert "未知配置键" in r.stderr, f"stderr 文案不符: {r.stderr!r}"


# ---------- 4. set + 回读 ----------
def test_set_and_readback(skein_cli: SkeinCli, ws: Path) -> None:
    """config set max_active 3 成功; 再 get → "3"。"""
    skein_cli(ws, "config", "set", "max_active", "3")
    r = skein_cli(ws, "config", "get", "max_active")
    assert r.stdout.strip() == "3", f"set 后回读错: {r.stdout!r}"


# ---------- 5. set bool coerce ----------
def test_set_bool_coerce(skein_cli: SkeinCli, ws: Path) -> None:
    """config set auto_commit false; get → "False" (Python bool str)。"""
    skein_cli(ws, "config", "set", "auto_commit", "false")
    r = skein_cli(ws, "config", "get", "auto_commit")
    assert r.stdout.strip() == "False", f"bool coerce 错: {r.stdout!r}"


# ---------- 6. set 未知键 ----------
def test_set_unknown_key_errors(skein_cli: SkeinCli, ws: Path) -> None:
    """config set nope 1 → 拒 (非静默, returncode!=0, stderr 含未知配置键)。"""
    r = skein_cli(ws, "config", "set", "nope", "1", check=False)
    assert r.returncode != 0, f"未知键 set 未拒: rc={r.returncode}"
    assert "未知配置键" in r.stderr, f"stderr 文案不符: {r.stderr!r}"


# ---------- 7. set 类型不合 ----------
def test_set_type_mismatch(skein_cli: SkeinCli, ws: Path) -> None:
    """config set max_active abc → 拒 (stderr 含类型不合/值类型)。"""
    r = skein_cli(ws, "config", "set", "max_active", "abc", check=False)
    assert r.returncode != 0, f"类型不合未拒: rc={r.returncode}"
    assert "类型不合" in r.stderr or "值类型" in r.stderr, f"stderr 文案不符: {r.stderr!r}"


# ---------- 8. set 保留其他键 ----------
def test_set_preserves_other_keys(skein_cli: SkeinCli, ws: Path) -> None:
    """set max_active 5 后, retain_days 仍为默认值 7 (未被抹)。"""
    skein_cli(ws, "config", "set", "max_active", "5")
    r = skein_cli(ws, "config", "get", "retain_days")
    assert r.stdout.strip() == "7", f"其他键被抹: retain_days={r.stdout!r}"
