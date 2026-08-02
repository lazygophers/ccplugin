"""config 命令测试 — skein.py config [set <key> <value> | reset]。

经 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
CONFIG_DEFAULTS 10 叶 (pools.work/pools.gate/auto_commit/retain_days/worktree.enabled/worktree.root/
web.serve/web.board_open/spec.core_budget/spec.always_budget)。
报错用例传 check=False 断 returncode + stderr 文案。

全部命令输出结构化 JSON (扁平或嵌套):
  - config 无参 → flat JSON dict (点号路径做 key, 跳过 hooks)
  - config --json → 嵌套 JSON dict (含 hooks)
  - config set → {"key": ..., "value": ...}
  - config reset → {"reset": true, "config": {...}}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import SkeinCli

import sys as _sys  # noqa: E402

_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skeinlib.config import CONFIG_DEFAULTS as _DEFAULTS  # noqa: E402  单一真值源, 禁在测试里硬编码默认值
from skeinlib.config import HooksConfig  # noqa: E402

# hooks 阶段名 (alias 形式) — 从 HooksConfig model_fields alias 取
_STAGES = tuple(
    info.alias or name
    for name, info in HooksConfig.model_fields.items()
)


def _flat(skein_cli: SkeinCli, ws: Path) -> dict[str, Any]:
    """config 无参 → flat JSON dict (点号路径做 key)。"""
    data: dict[str, Any] = json.loads(skein_cli(ws, "config").stdout)
    return data


def _readback(skein_cli: SkeinCli, ws: Path, path: str) -> str | None:
    """从 flat JSON 输出取 path 对应的 value (无则 None)。"""
    data = _flat(skein_cli, ws)
    if path in data:
        v = data[path]
        return str(v)
    return None


# ---------- 1. 无参展示全部 ----------
def test_show_all(skein_cli: SkeinCli, ws: Path) -> None:
    """config 无参 → flat JSON dict, 10 叶 (跳过 hooks), 含 pools.work=2 与 worktree.enabled=False。"""
    data = _flat(skein_cli, ws)
    assert len(data) == 10, f"应 10 叶, 得 {len(data)}: {data}"
    assert data.get("pools.work") == 2, f"缺 pools.work=2: {data}"
    assert data.get("worktree.enabled") is False, f"缺 worktree.enabled=False: {data}"


# ---------- 0. hooks 空骨架在 CONFIG_DEFAULTS 内 ----------
def test_hooks_skeleton_present(skein_cli: SkeinCli, ws: Path) -> None:
    """hooks 空骨架进 CONFIG_DEFAULTS: init 写出占位键, --json 含它且为 dict。"""
    assert "hooks" in _DEFAULTS, "CONFIG_DEFAULTS 应含 hooks 完整骨架"
    h = _DEFAULTS["hooks"]
    assert h["check"] == {"before": [], "after": []}, "阶段骨架应含空 before/after"
    assert "hooks" in (ws / ".skein" / "config.yaml").read_text()
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert isinstance(data.get("hooks"), dict), f"hooks 应读回 dict, 得 {type(data.get('hooks'))}"


# ---------- 2. set + 回读 (点号路径) ----------
def test_set_and_readback(skein_cli: SkeinCli, ws: Path) -> None:
    """config set pools.work 3 成功; 回读 → 3。"""
    skein_cli(ws, "config", "set", "pools.work", "3")
    assert _readback(skein_cli, ws, "pools.work") == "3", "set 后回读错"


def test_set_nested_path_and_readback(skein_cli: SkeinCli, ws: Path) -> None:
    """config set worktree.enabled false (新点号路径) 成功; 回读 → False。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "false")
    assert _readback(skein_cli, ws, "worktree.enabled") == "False", "点号路径 set 后回读错"


def test_set_nested_path_json_output(skein_cli: SkeinCli, ws: Path) -> None:
    """config set spec.always_budget 9000 → --json 嵌套结构反映新值。"""
    skein_cli(ws, "config", "set", "spec.always_budget", "9000")
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data["spec"]["always_budget"] == 9000, f"嵌套 json 未反映: {data['spec']}"


# ---------- 3. set bool coerce ----------
def test_set_bool_coerce(skein_cli: SkeinCli, ws: Path) -> None:
    """config set auto_commit false; 回读 → False (Python bool str)。"""
    skein_cli(ws, "config", "set", "auto_commit", "false")
    assert _readback(skein_cli, ws, "auto_commit") == "False", "bool coerce 错"


# ---------- 4. set 未知键 ----------
def test_set_unknown_key_errors(skein_cli: SkeinCli, ws: Path) -> None:
    """config set nope 1 → 拒 (非静默, returncode!=0, stderr 含未知配置键 + 合法路径列表)。"""
    r = skein_cli(ws, "config", "set", "nope", "1", check=False)
    assert r.returncode != 0, f"未知键 set 未拒: rc={r.returncode}"
    assert "未知配置键" in r.stderr, f"stderr 文案不符: {r.stderr!r}"
    assert "worktree.enabled" in r.stderr, f"stderr 未列合法路径: {r.stderr!r}"


def test_set_unknown_nested_path_errors(skein_cli: SkeinCli, ws: Path) -> None:
    """config set worktree.nope 1 (合法分组+非法叶) → 同样拒。"""
    r = skein_cli(ws, "config", "set", "worktree.nope", "1", check=False)
    assert r.returncode != 0, f"未知路径 set 未拒: rc={r.returncode}"
    assert "未知配置键" in r.stderr, f"stderr 文案不符: {r.stderr!r}"


# ---------- 5. set 类型不合 ----------
def test_set_type_mismatch(skein_cli: SkeinCli, ws: Path) -> None:
    """config set pools.work abc → 拒 (stderr 含类型不合/值类型)。"""
    r = skein_cli(ws, "config", "set", "pools.work", "abc", check=False)
    assert r.returncode != 0, f"类型不合未拒: rc={r.returncode}"
    assert "类型不合" in r.stderr or "值类型" in r.stderr, f"stderr 文案不符: {r.stderr!r}"


# ---------- 6. set 保留其他键 ----------
def test_set_preserves_other_keys(skein_cli: SkeinCli, ws: Path) -> None:
    """set pools.work 5后, retain_days 仍为默认值 7 (未被抹)。"""
    skein_cli(ws, "config", "set", "pools.work", "5")
    assert _readback(skein_cli, ws, "retain_days") == "7", "其他键被抹"


def test_set_nested_preserves_sibling_leaf(skein_cli: SkeinCli, ws: Path) -> None:
    """set worktree.root 后, 同组 worktree.enabled 仍为默认值 (分组内其他叶不被抹)。"""
    skein_cli(ws, "config", "set", "worktree.root", ".wt2")
    assert _readback(skein_cli, ws, "worktree.enabled") == "False", "同组其他叶被抹"


# ---------- 7. reset ----------
def test_reset(skein_cli: SkeinCli, ws: Path) -> None:
    """set pools.work 9 → config reset → 回读为默认值 2。"""
    skein_cli(ws, "config", "set", "pools.work", "9")
    assert _readback(skein_cli, ws, "pools.work") == "9", "set 未生效"
    skein_cli(ws, "config", "reset")
    assert _readback(skein_cli, ws, "pools.work") == "2", "reset 未回默认"


# ---------- 8. get 子命令已删 ----------
def test_get_removed(skein_cli: SkeinCli, ws: Path) -> None:
    """config get → 拒 (invalid choice, get 子命令已删)。"""
    r = skein_cli(ws, "config", "get", check=False)
    assert r.returncode != 0, f"get 未拒: rc={r.returncode}"


# ---------- 9. --json 输出 (嵌套结构) ----------
def test_show_json(skein_cli: SkeinCli, ws: Path) -> None:
    """config --json → 合法嵌套 JSON dict, worktree.enabled 为 bool (供 jq 解析)。"""
    r = skein_cli(ws, "config", "--json")
    data = json.loads(r.stdout.strip())
    assert isinstance(data["worktree"]["enabled"], bool), f"worktree.enabled 非 bool: {data['worktree']!r}"
    assert data["pools"]["work"] == 2, f"pools.work 非默认 2: {data['pools']}"
    assert data["spec"]["always_budget"] == _DEFAULTS["spec"]["always_budget"], \
        f"spec.always_budget 非默认: {data['spec']}"


def test_json_reflects_set(skein_cli: SkeinCli, ws: Path) -> None:
    """set worktree.enabled false 后 config --json → worktree.enabled=false (jq 可解析禁用态)。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "false")
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data["worktree"]["enabled"] is False, f"set 后 json 未反映: {data['worktree']!r}"


# ---------- 11. 扁平 config.yaml 缺失键回填 ----------
def test_flat_config_missing_keys_backfilled(skein_cli: SkeinCli, ws: Path) -> None:
    """既有全扁平 config.yaml (无 pools 键) 只读 → pools 真缺失, 按正常缺键回填规则
    补上默认值并回写磁盘。"""
    cfg = ws / ".skein" / "config.yaml"
    flat = (
        "auto_commit: false\n"
        "retain_days: 7\n"
    )
    cfg.write_text(flat)
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data == {
        "auto_commit": False, "retain_days": 7,
        "pools": {"work": 2, "gate": 3},
        "worktree": {"enabled": False, "root": ".worktrees"},
        "web": {"serve": True, "board_open": True},
        "spec": {"core_budget": 400, "always_budget": 517},
        "hooks": {s: {"before": [], "after": []} for s in _STAGES} | {"agent": {}},
    }, f"缺键回填不符: {data}"
    text = cfg.read_text()
    assert "pools:\n  work: 2\n  gate: 3\n" in text, f"真缺失的 pools 应被回填写盘: {text!r}"
