"""config 命令测试 — skein.py config [set <key> <value> | reset]。

经 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
CONFIG_DEFAULTS 10 叶 (pools.work/pools.gate/auto_commit/retain_days/worktree.enabled/worktree.root/
web.serve/web.board_open/spec.core_budget/spec.always_budget) —— c10 层级化: 带前缀的旧扁平键
(use_worktree/worktree_root/web_serve/board_open/spec_core_budget/spec_always_budget) 已分组为
worktree./web./spec. 三组; auto_commit/retain_days 本无前缀, 保持扁平; pools 无遗留扁平键映射
(旧 max_active 已删, 不留 fallback, 见 design.md §5)。
报错用例传 check=False 断 returncode + stderr 文案。
无参 `config` 展示全部生效配置, 扁平化为点号形式 (每行 path=value); 单键回读经无参输出按行 grep。
覆盖:
  1. 无参展示: 10 行 path=val, 含 pools.work=2 与 worktree.enabled=False。
  2. set + 回读 (点号路径): set worktree.enabled false → 无参回读含 worktree.enabled=False。
  3. set bool coerce: set auto_commit false → 回读含 auto_commit=False。
  4. set 未知键: 拒 (returncode!=0, stderr 含「未知配置键」)。
  5. set 类型不合: set pools.work abc → 拒 (stderr 含「类型不合」/「值类型」)。
  6. set 保留其他键: set pools.work 5 后 retain_days 仍默认值。
  7. reset: set 非默认值后 reset → 回读为默认值。
  8. get 已删: config get → 拒 (invalid choice)。
  9. --json: 无参 config --json → 合法嵌套 JSON dict, worktree.enabled 为 bool。
  10. 旧扁平键仍可读写 (deprecated fallback, 向后兼容既有脚本): set use_worktree false 仍生效,
      且写回磁盘仍是扁平键 (不代劳迁移嵌套)。
"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SkeinCli

import sys as _sys  # noqa: E402

_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skeinlib.config import CONFIG_DEFAULTS as _DEFAULTS  # noqa: E402  单一真值源, 禁在测试里硬编码默认值
from skeinlib.config import STAGE_NAMES as _STAGES  # noqa: E402  单一真值源, 禁在测试里硬编码阶段名


def _readback(skein_cli: SkeinCli, ws: Path, path: str) -> str | None:
    """无参 config 展示全部, 从输出按行取 path=value 的 value (无则 None)。"""
    r = skein_cli(ws, "config")
    for ln in r.stdout.strip().splitlines():
        if ln.startswith(f"{path}="):
            return ln.split("=", 1)[1]
    return None


# ---------- 1. 无参展示全部 ----------
def test_show_all(skein_cli: SkeinCli, ws: Path) -> None:
    """config 无参 → 10 行 path=val (点号扁平化), 含 pools.work=2 与 worktree.enabled=True。"""
    r = skein_cli(ws, "config")
    lines = [ln for ln in r.stdout.strip().splitlines() if "=" in ln]
    assert len(lines) == 10, f"应 10 行 path=val, 得 {len(lines)}: {lines}"
    assert "pools.work=2" in lines, f"缺 pools.work=2: {lines}"
    assert "worktree.enabled=False" in lines, f"缺 worktree.enabled=False: {lines}"


# ---------- 0. hooks 空骨架在 CONFIG_DEFAULTS 内, 但远程不可写 ----------
def test_hooks_skeleton_present_but_remote_denied(skein_cli: SkeinCli, ws: Path) -> None:
    """hooks 空骨架进 CONFIG_DEFAULTS: init 写出占位键, --json 含它且为 dict (非字符串);
    但它在 CFG_REMOTE_DENY 里 —— 值是 shell 命令, 允许远程写入等于开 RCE。"""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from skeinlib.config import CFG_REMOTE_DENY, CONFIG_DEFAULTS  # noqa: E402

    from skeinlib.config import STAGE_NAMES  # noqa: E402

    assert "hooks" in CONFIG_DEFAULTS, "CONFIG_DEFAULTS 应含 hooks 完整骨架"
    h = CONFIG_DEFAULTS["hooks"]
    assert set(h) == set(STAGE_NAMES) | {"agent"}, "骨架应列出全部阶段 + agent"
    assert h["check"] == {"before": [], "after": []}, "阶段骨架应含空 before/after"
    assert h["agent"]["*"] == {"start": [], "stop": []}, "agent 骨架应含通配 + 空 start/stop"
    assert "hooks" in CFG_REMOTE_DENY, "hooks 必须在远程拒写名单里 (值是 shell 命令)"
    assert "hooks" in (ws / ".skein" / "config.yaml").read_text()
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert isinstance(data.get("hooks"), dict), f"hooks 应读回 dict, 得 {type(data.get('hooks'))}"


# ---------- 2. set + 回读 (点号路径) ----------
def test_set_and_readback(skein_cli: SkeinCli, ws: Path) -> None:
    """config set pools.work 3 成功; 无参回读 → "3"。"""
    skein_cli(ws, "config", "set", "pools.work", "3")
    assert _readback(skein_cli, ws, "pools.work") == "3", "set 后回读错"


def test_set_nested_path_and_readback(skein_cli: SkeinCli, ws: Path) -> None:
    """config set worktree.enabled false (新点号路径) 成功; 无参回读 → "False"。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "false")
    assert _readback(skein_cli, ws, "worktree.enabled") == "False", "点号路径 set 后回读错"


def test_set_nested_path_json_output(skein_cli: SkeinCli, ws: Path) -> None:
    """config set spec.always_budget 9000 → --json 嵌套结构反映新值。"""
    skein_cli(ws, "config", "set", "spec.always_budget", "9000")
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data["spec"]["always_budget"] == 9000, f"嵌套 json 未反映: {data['spec']}"


# ---------- 3. set bool coerce ----------
def test_set_bool_coerce(skein_cli: SkeinCli, ws: Path) -> None:
    """config set auto_commit false; 回读 → "False" (Python bool str)。"""
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
    """set pools.work 5 后, retain_days 仍为默认值 7 (未被抹)。"""
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


# ---------- 10. 旧扁平键 deprecated fallback (向后兼容既有脚本) ----------
def test_legacy_flat_key_set_works_on_fresh_nested_init(skein_cli: SkeinCli, ws: Path) -> None:
    """新仓 (init 默认写嵌套 worktree.enabled=true) set use_worktree false (旧扁平键名) 仍要生效
    —— set 命令改的是盘上已存在的同组嵌套叶而非另加扁平键, 否则会被嵌套读取优先级遮蔽变相失效
    (大量既有测试如 test_worktree_disabled.py 靠这条在全新 ws 上用旧键名禁用 worktree)。"""
    skein_cli(ws, "config", "set", "use_worktree", "false")
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data["worktree"]["enabled"] is False, f"新仓上旧扁平键 set 未生效: {data['worktree']!r}"


def test_legacy_flat_key_set_still_works(skein_cli: SkeinCli, ws: Path) -> None:
    """既有全扁平仓 (init 默认写嵌套, 这里模拟旧仓覆写成纯扁平) set use_worktree false
    (旧扁平键名) 仍生效, --json 反映到新嵌套路径 worktree.enabled。"""
    cfg = ws / ".skein" / "config.yaml"
    cfg.write_text("max_active: 2\nauto_commit: true\nretain_days: 7\n"
                    "use_worktree: true\nworktree_root: .worktrees\n"
                    "web_serve: true\nboard_open: true\n"
                    "spec_core_budget: 1000\nspec_always_budget: 8000\n")
    skein_cli(ws, "config", "set", "use_worktree", "false")
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data["worktree"]["enabled"] is False, f"旧扁平键 set 未生效: {data['worktree']!r}"


def test_legacy_flat_key_written_flat_not_migrated(skein_cli: SkeinCli, ws: Path) -> None:
    """既有纯扁平仓 set use_worktree false 写盘仍是扁平键 (脚本不代劳迁移嵌套, 用户自己决定何时改)。"""
    cfg = ws / ".skein" / "config.yaml"
    cfg.write_text("max_active: 2\nauto_commit: true\nretain_days: 7\n"
                    "use_worktree: true\nworktree_root: .worktrees\n"
                    "web_serve: true\nboard_open: true\n"
                    "spec_core_budget: 1000\nspec_always_budget: 8000\n")
    skein_cli(ws, "config", "set", "use_worktree", "false")
    text = cfg.read_text()
    assert "use_worktree: false" in text, f"旧扁平键未原样写回扁平: {text!r}"
    assert "\nworktree:\n" not in text, f"不应被代劳迁移出嵌套 worktree 块: {text!r}"


def test_existing_flat_config_yaml_read_without_rewrite_to_nested(skein_cli: SkeinCli, ws: Path) -> None:
    """既有全扁平 config.yaml (6 个曾带前缀键全在, 另含已删的旧 `max_active`) 只读 →
    6 个曾带前缀键生效值正确且不被自动改写成嵌套 (零破坏); 残留的 `max_active` 静默忽略 (design.md
    §5: 无 legacy 映射, 不 fallback), `pools` 无嵌套键也无对应扁平键 → 真缺失, 按正常缺键回填规则
    补上默认值并回写磁盘 (与其他真缺失键回填行为一致, 不是「零破坏」例外)。"""
    cfg = ws / ".skein" / "config.yaml"
    flat = (
        "max_active: 3\n"
        "auto_commit: false\n"
        "use_worktree: false\n"
        "worktree_root: .worktrees\n"
        "retain_days: 7\n"
        "web_serve: true\n"
        "board_open: true\n"
        "spec_core_budget: 1000\n"
        "spec_always_budget: 12000\n"
    )
    cfg.write_text(flat)
    data = json.loads(skein_cli(ws, "config", "--json").stdout.strip())
    assert data == {
        "auto_commit": False, "retain_days": 7,
        "pools": {"work": 2, "gate": 3},  # 真缺失, 回填默认值 (旧 max_active 无 legacy 映射, 不继承)
        "worktree": {"enabled": False, "root": ".worktrees"},
        "web": {"serve": True, "board_open": True},
        "spec": {"core_budget": 1000, "always_budget": 12000},
        # 完整骨架来自 CONFIG_DEFAULTS 回填; 扁平仓无该键 → 得默认全空结构
        "hooks": {**{s: {"before": [], "after": []} for s in _STAGES},
                  "agent": {"*": {"start": [], "stop": []}}},
    }, f"扁平仓生效值不符: {data}"
    text = cfg.read_text()
    assert text.startswith(flat), "6 个曾带前缀键的既有扁平段应原样保留 (零破坏, 不代劳迁移)"
    assert "pools:\n  work: 2\n  gate: 3\n" in text, f"真缺失的 pools 应被回填写盘: {text!r}"
