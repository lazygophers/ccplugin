"""config 命令测试 — skein.py config [set <key> <value> | reset]。

经 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
CONFIG_DEFAULTS 8 键 (max_active/auto_commit/use_worktree/worktree_root/retain_days/
web_serve/board_open/spec_core_budget)。报错用例传 check=False 断 returncode + stderr 文案。
无参 `config` 展示全部生效配置 (每行 key=value); 单键回读经无参输出按行 grep。
覆盖:
  1. 无参展示: 8 行 key=val, 含 max_active=2。
  2. set + 回读: set max_active 3 → 无参回读含 max_active=3。
  3. set bool coerce: set auto_commit false → 回读含 auto_commit=False。
  4. set 未知键: 拒 (returncode!=0, stderr 含「未知配置键」)。
  5. set 类型不合: set max_active abc → 拒 (stderr 含「类型不合」/「值类型」)。
  6. set 保留其他键: set max_active 5 后 retain_days 仍默认值。
  7. reset: set 非默认值后 reset → 回读为默认值。
  8. get 已删: config get → 拒 (invalid choice)。
  9. --json: 无参 config --json → 合法 JSON dict, 含 8 键, use_worktree 为 bool。
"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SkeinCli


def _readback(skein_cli: SkeinCli, ws: Path, key: str) -> str | None:
    """无参 config 展示全部, 从输出按行取 key=value 的 value (无则 None)。"""
    r = skein_cli(ws, "config")
    for ln in r.stdout.strip().splitlines():
        if ln.startswith(f"{key}="):
            return ln.split("=", 1)[1]
    return None


# ---------- 1. 无参展示全部 ----------
def test_show_all(skein_cli: SkeinCli, ws: Path) -> None:
    """config 无参 → 8 行 key=val, 含 max_active=2。"""
    r = skein_cli(ws, "config")
    lines = [ln for ln in r.stdout.strip().splitlines() if "=" in ln]
    assert len(lines) == 8, f"应 8 行 key=val, 得 {len(lines)}: {lines}"
    assert "max_active=2" in lines, f"缺 max_active=2: {lines}"


# ---------- 2. set + 回读 ----------
def test_set_and_readback(skein_cli: SkeinCli, ws: Path) -> None:
    """config set max_active 3 成功; 无参回读 → "3"。"""
    skein_cli(ws, "config", "set", "max_active", "3")
    assert _readback(skein_cli, ws, "max_active") == "3", "set 后回读错"


# ---------- 3. set bool coerce ----------
def test_set_bool_coerce(skein_cli: SkeinCli, ws: Path) -> None:
    """config set auto_commit false; 回读 → "False" (Python bool str)。"""
    skein_cli(ws, "config", "set", "auto_commit", "false")
    assert _readback(skein_cli, ws, "auto_commit") == "False", "bool coerce 错"


# ---------- 4. set 未知键 ----------
def test_set_unknown_key_errors(skein_cli: SkeinCli, ws: Path) -> None:
    """config set nope 1 → 拒 (非静默, returncode!=0, stderr 含未知配置键)。"""
    r = skein_cli(ws, "config", "set", "nope", "1", check=False)
    assert r.returncode != 0, f"未知键 set 未拒: rc={r.returncode}"
    assert "未知配置键" in r.stderr, f"stderr 文案不符: {r.stderr!r}"


# ---------- 5. set 类型不合 ----------
def test_set_type_mismatch(skein_cli: SkeinCli, ws: Path) -> None:
    """config set max_active abc → 拒 (stderr 含类型不合/值类型)。"""
    r = skein_cli(ws, "config", "set", "max_active", "abc", check=False)
    assert r.returncode != 0, f"类型不合未拒: rc={r.returncode}"
    assert "类型不合" in r.stderr or "值类型" in r.stderr, f"stderr 文案不符: {r.stderr!r}"


# ---------- 6. set 保留其他键 ----------
def test_set_preserves_other_keys(skein_cli: SkeinCli, ws: Path) -> None:
    """set max_active 5 后, retain_days 仍为默认值 7 (未被抹)。"""
    skein_cli(ws, "config", "set", "max_active", "5")
    assert _readback(skein_cli, ws, "retain_days") == "7", "其他键被抹"


# ---------- 7. reset ----------
def test_reset(skein_cli: SkeinCli, ws: Path) -> None:
    """set max_active 9 → config reset → 回读为默认值 2。"""
    skein_cli(ws, "config", "set", "max_active", "9")
    assert _readback(skein_cli, ws, "max_active") == "9", "set 未生效"
    skein_cli(ws, "config", "reset")
    assert _readback(skein_cli, ws, "max_active") == "2", "reset 未回默认"


# ---------- 8. get 子命令已删 ----------
def test_get_removed(skein_cli: SkeinCli, ws: Path) -> None:
    """config get → 拒 (invalid choice, get 子命令已删)。"""
    r = skein_cli(ws, "config", "get", check=False)
    assert r.returncode != 0, f"get 未拒: rc={r.returncode}"


# ---------- 9. --json 输出 ----------
def test_show_json(skein_cli: SkeinCli, ws: Path) -> None:
    """config --json → 合法 JSON dict, 含 8 键, use_worktree 为 bool (供 jq 解析)。"""
    r = skein_cli(ws, "config", "--json")
    data = json.loads(r.stdout.strip())
    assert len(data) == 8, f"应 8 键, 得 {len(data)}: {list(data)}"
    assert isinstance(data["use_worktree"], bool), f"use_worktree 非 bool: {data['use_worktree']!r}"
    assert data["max_active"] == 2, f"max_active 非默认 2: {data['max_active']}"


def test_json_reflects_set(skein_cli: SkeinCli, ws: Path) -> None:
    """set use_worktree false 后 config --json → use_worktree=false (jq 可解析禁用态)。"""
    skein_cli(ws, "config", "set", "use_worktree", "false")
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data["use_worktree"] is False, f"set 后 json 未反映: {data['use_worktree']!r}"
