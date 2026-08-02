"""skein task 生命周期状态机测试 — 合法/非法/幂等转换全覆盖。

覆盖 task 状态机: 待处理(pending) → 进行中(active) → 检查中(check) → 已完成(done) → 归档。
待处理→进行中 经 confirm 用户确认门 (验 prd + ≥1 subtask + estimate); confirm 即激活 (建 worktree + 占槽)。
非法转换断言被拒 (exit 1 + 中文态校验信息); 幂等转换断言当前真实行为。
状态常量来自 model.py (中文落盘): S_PENDING/S_ACTIVE/S_CHECK/S_DONE。"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

S_PENDING = "待处理"
S_ACTIVE = "进行中"
S_CHECK = "检查中"
S_DONE = "已完成"

SkeinCli = Callable[..., subprocess.CompletedProcess[str]]
SID = "sub-build"


def _mk(skein_cli: SkeinCli, ws: Path, tid: str = "feat-x", *,
        sub: bool = False, active: bool = False) -> str:
    """造 task。sub=附 1 subtask + 填实 prd; active=confirm --approved 直接激活。"""
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    if sub or active:
        skein_cli(ws, "subtask", "add", tid, SID, "--name", "S", "--desc", "d", "--estimate", "1")
        _fill_prd(ws, tid)
    if active:
        skein_cli(ws, "estimate", tid, "--set", "1")
        skein_cli(ws, "confirm", tid, "--approved")
    return tid


def _fill_prd(ws: Path, tid: str) -> None:
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- 解决 X 问题\n\n"
        "## 边界\n- 范围内: a\n\n## 验收标准\n- 用例通过\n\n## 索引\n- design.md\n")


def _status_of(skein_cli: SkeinCli, ws: Path, tid: str) -> str:
    out = skein_cli(ws, "list").stdout
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == tid:
            return parts[1]
    return "<missing>"


def test_create_pending(skein_cli: SkeinCli, ws: Path) -> None:
    r = skein_cli(ws, "create", "feat-add", "--name", "feat-add", "--desc", "d")
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, "feat-add") == S_PENDING


def test_confirm_active_builds_worktree(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, active=True)
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE
    assert (ws / ".worktrees" / f"skein-{tid}").exists()


def test_check_to_checking(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, active=True)
    r = skein_cli(ws, "check", tid)
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, tid) == S_CHECK


def test_finish_done_merges_and_destroys_worktree(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, active=True)
    r = skein_cli(ws, "finish", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == S_DONE
    assert not (ws / ".worktrees" / f"skein-{tid}").exists()


def test_archive_removes_from_board(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, active=True)
    skein_cli(ws, "finish", tid)
    r = skein_cli(ws, "archive", tid)
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, tid) == "<missing>"


def test_full_chain_create_to_archive(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, "feat-chain", active=True)
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE
    skein_cli(ws, "check", tid)
    assert _status_of(skein_cli, ws, tid) == S_CHECK
    skein_cli(ws, "finish", tid)
    assert _status_of(skein_cli, ws, tid) == S_DONE
    skein_cli(ws, "archive", tid)
    assert _status_of(skein_cli, ws, tid) == "<missing>"


def test_confirm_already_active_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, active=True)
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE


def test_finish_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1
    assert "非在途" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING


def test_confirm_no_subtask_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws)
    skein_cli(ws, "estimate", tid, "--set", "1")
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "无 subtask" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING


def test_confirm_no_estimate_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, sub=True)
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "预计工时" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING
    skein_cli(ws, "estimate", tid, "--set", "1")
    skein_cli(ws, "confirm", tid, "--approved")
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE


def test_subtask_add_requires_estimate(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "feat-e", "--name", "n", "--desc", "d")
    r = skein_cli(ws, "subtask", "add", "feat-e", SID, "--name", "S", "--desc", "d", check=False)
    assert r.returncode == 2
    r = skein_cli(ws, "subtask", "add", "feat-e", SID, "--name", "S", "--desc", "d",
                  "--estimate", "0", check=False)
    assert r.returncode == 1
    assert "正数" in r.stdout + r.stderr


def test_confirm_estimate_below_subtask_sum_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws)
    skein_cli(ws, "subtask", "add", tid, "sub-a", "--name", "A", "--desc", "d", "--estimate", "3")
    skein_cli(ws, "subtask", "add", tid, "sub-b", "--name", "B", "--desc", "d", "--estimate", "2")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "4")
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "低于 subtask 合计 5" in r.stdout + r.stderr
    skein_cli(ws, "estimate", tid, "--set", "6")
    skein_cli(ws, "confirm", tid, "--approved")
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE


def test_start_activates_pending(skein_cli: SkeinCli, ws: Path) -> None:
    """start 直接激活待处理 task (跳过人审门, 供调度器/已确认场景用)。"""
    tid = _mk(skein_cli, ws, sub=True)
    skein_cli(ws, "estimate", tid, "--set", "1")
    r = skein_cli(ws, "start", tid)  # start 直接 _activate, 无需 --approved
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE


def test_check_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, sub=True)
    r = skein_cli(ws, "check", tid, check=False)
    assert r.returncode == 1
    assert "只有进行中" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING


def test_create_duplicate_id_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "feat-dup", "--name", "feat-dup", "--desc", "d")
    r = skein_cli(ws, "create", "feat-dup", "--name", "feat-dup", "--desc", "d", check=False)
    assert r.returncode == 1
    assert "id 已占用" in r.stdout + r.stderr


def test_finish_after_done_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, active=True)
    skein_cli(ws, "finish", tid)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1
    assert "非在途" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_DONE


def test_archive_already_archived_idempotent(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, active=True)
    skein_cli(ws, "finish", tid)
    skein_cli(ws, "archive", tid)
    r = skein_cli(ws, "archive", tid, check=False)
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, tid) == "<missing>"


def test_subtask_add_duplicate_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _mk(skein_cli, ws, sub=True)
    r = skein_cli(ws, "subtask", "add", tid, SID, "--name", "S", "--desc", "d", "--estimate", "1", check=False)
    assert r.returncode == 1
    assert "subtask 已存在" in r.stdout + r.stderr
