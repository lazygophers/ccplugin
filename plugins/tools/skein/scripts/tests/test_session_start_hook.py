"""session-start hook 单测 — 只注 spec 待修告警 + 运行配置 (worktree/auto_commit) + 回复前缀。

agent 钩子段 / active task 段 / 任务判定规则段已删, 这里钉死它们不再回流。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import conftest  # noqa: F401
from conftest import HOOKS, SkeinCli

from skeinlib.hooks.session_start import _pending_fix_hint


def _run(cwd: Path) -> str:
    r = subprocess.run([sys.executable, str(HOOKS), "session-start"], cwd=cwd,
                       input=json.dumps({"cwd": str(cwd)}),
                       capture_output=True, text=True, check=True)
    out = r.stdout.strip()
    return str(json.loads(out)["hookSpecificOutput"]["additionalContext"]) if out else ""


def test_silent_when_uninitialized(tmp_path: Path) -> None:
    """未初始化 (无 .skein/config.yaml) 一律静默, 不劝进。"""
    assert _run(tmp_path) == ""


def test_injects_config_and_prefix(ws: Path) -> None:
    """恒注 Skein 配置块 (回复前缀规则 + worktree/auto_commit 一句话) 与回复前缀。"""
    ctx = _run(ws)
    assert "# **Skein 配置**" in ctx
    assert "- 每条回复以 `[skein]` 开头" in ctx
    assert "[skein|<tid" in ctx
    # 默认 (worktree 禁用 + auto_commit 启用) 的执行约束行
    assert "禁止使用 worktree 执行 task" in ctx
    assert "# SKEIN 运行配置" not in ctx, "旧配置块标题不该回流"
    assert "最大并行 subtask" not in ctx, "并行度行已删, 不该回流"
    assert "# 回复前缀 (强制)" not in ctx, "旧前缀段标题不该回流"


def test_dropped_sections_stay_out(ws: Path) -> None:
    """agent 钩子段 / active task 段 / 任务判定规则段已删, 钉死不回流。"""
    ctx = _run(ws)
    for banned in ("agent-start", "当前 active task", "任务判定规则", "跨≥2文件", "compaction"):
        assert banned not in ctx, f"已删段落回流: {banned}"


def test_pending_fix_hint_presented(ws: Path) -> None:
    """.pending-fix 有问题 → 注入告警 + specer 派遣建议。"""
    marker = ws / ".skein" / "spec" / ".pending-fix"
    marker.parent.mkdir(exist_ok=True)
    marker.write_text(json.dumps({"problems": [
        {"type": "stale"}, {"type": "stale"}, {"type": "broken_link"}]}), encoding="utf-8")
    ctx = _run(ws)
    assert "spec 问题待修" in ctx and "命中 3 项" in ctx and "stale(2)" in ctx
    assert "skein-specer" in ctx


def test_pending_fix_hint_empty_or_bad_json(ws: Path) -> None:
    """problems 空 / 坏 JSON → 无告警段。"""
    assert _pending_fix_hint(ws / ".skein" / "spec") == ""
    marker = ws / ".skein" / "spec" / ".pending-fix"
    marker.parent.mkdir(exist_ok=True)
    marker.write_text(json.dumps({"problems": []}), encoding="utf-8")
    assert _pending_fix_hint(ws / ".skein" / "spec") == ""
    marker.write_text("not json", encoding="utf-8")
    assert _pending_fix_hint(ws / ".skein" / "spec") == ""


def test_worktree_enabled_shows_root(skein_cli: SkeinCli, ws: Path) -> None:
    """启用态配置行带 worktree 存放目录路径。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")
    ctx = _run(ws)
    assert "启用 worktree 执行 task" in ctx
    assert ".worktrees" in ctx and "合并到源分支" in ctx
