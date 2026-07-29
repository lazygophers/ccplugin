"""skein task 生命周期状态机测试 — 合法/非法/幂等转换全覆盖。

通过 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离临时仓),
覆盖 task 状态机: 待处理(pending) → 就绪(ready) → 进行中(active) → 检查中(check) → 已完成(done) → 归档。
待处理→就绪 经 confirm 用户确认门 (验 prd + ≥1 subtask); 就绪→进行中 经 start。
非法转换断言被拒 (exit 1 + 中文态校验信息); 幂等转换断言当前真实行为。
状态常量来自 skein.py (中文落盘): S_PENDING/S_READY/S_ACTIVE/S_CHECK/S_DONE (skein.py:48-52)。
task/subtask id 全用描述性 slug, 规避 skein CODE_ID_RE (skein.py:66 ^[a-z]{1,4}\\d+$) 对代号式 id 的拒绝。"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

# 中文态常量 (与 skein.py:49-52 落盘值一致, 测试只读不 import skein 内部)
S_PENDING = "待处理"
S_READY = "就绪"
S_ACTIVE = "进行中"
S_CHECK = "检查中"
S_DONE = "已完成"

SkeinCli = Callable[..., subprocess.CompletedProcess[str]]

SID = "sub-build"  # subtask sid (描述性, 规避代号式校验)


def _mk(skein_cli: SkeinCli, ws: Path, tid: str = "feat-x", *,
        sub: bool = False, ready: bool = False) -> str:
    """造 task。sub=附 1 subtask + 填实 prd (满足 confirm/start 前置); ready=再 confirm 推到就绪 (可 start)。"""
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    if sub or ready:
        skein_cli(ws, "subtask", "add", tid, SID, "--name", "S", "--desc", "d", "--estimate", "1")
        _fill_prd(ws, tid)  # confirm/start 前置 prd 门: 填实占位免被拒
    if ready:
        skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
        skein_cli(ws, "confirm", tid)  # 待处理→就绪 用户确认门
    return tid


def _fill_prd(ws: Path, tid: str) -> None:
    """写一份规范 prd.md (章节齐 + 无 TODO 占位), 过 start 的 _validate_prd 门。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n"
        "## 目标\n- 解决 X 问题\n\n"
        "## 边界\n- 范围内: a\n\n"
        "## 验收标准\n- 用例通过\n\n"
        "## 索引\n- design.md\n")


def _status_of(skein_cli: SkeinCli, ws: Path, tid: str) -> str:
    """从 skein list 取 task 态 (列表行: <id>\\t<status>\\t<name>); 不存在返 <missing>。"""
    out = skein_cli(ws, "list").stdout
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == tid:
            return parts[1]
    return "<missing>"


# ---------- 合法转换全链 ----------

def test_create_pending(skein_cli: SkeinCli, ws: Path) -> None:
    """create → pending: 新 task 落盘态为待处理。"""
    r = skein_cli(ws, "create", "feat-add", "--name", "feat-add", "--desc", "d")
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, "feat-add") == S_PENDING


def test_start_active_builds_worktree(skein_cli: SkeinCli, ws: Path) -> None:
    """start(需先 confirm 到就绪) → active: 建 worktree + 状态切进行中。"""
    tid = _mk(skein_cli, ws, ready=True)
    r = skein_cli(ws, "start", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE
    assert (ws / ".worktrees" / f"skein-{tid}").exists(), "worktree 未建"


def test_check_to_checking(skein_cli: SkeinCli, ws: Path) -> None:
    """check: active → check(检查中)。"""
    tid = _mk(skein_cli, ws, ready=True)
    skein_cli(ws, "start", tid)
    r = skein_cli(ws, "check", tid)
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, tid) == S_CHECK


def test_finish_done_merges_and_destroys_worktree(skein_cli: SkeinCli, ws: Path) -> None:
    """finish: active → done, merge 回主仓 + 销 worktree。"""
    tid = _mk(skein_cli, ws, ready=True)
    skein_cli(ws, "start", tid)
    r = skein_cli(ws, "finish", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == S_DONE
    assert not (ws / ".worktrees" / f"skein-{tid}").exists(), "worktree 未销"


def test_archive_removes_from_board(skein_cli: SkeinCli, ws: Path) -> None:
    """archive: done task 移入归档, list 不再列出。"""
    tid = _mk(skein_cli, ws, ready=True)
    skein_cli(ws, "start", tid)
    skein_cli(ws, "finish", tid)
    r = skein_cli(ws, "archive", tid)
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, tid) == "<missing>"


def test_full_chain_create_to_archive(skein_cli: SkeinCli, ws: Path) -> None:
    """全链路: create → confirm(就绪) → start → check → finish → archive。"""
    tid = _mk(skein_cli, ws, "feat-chain", ready=True)
    assert _status_of(skein_cli, ws, tid) == S_READY
    skein_cli(ws, "start", tid)
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE
    skein_cli(ws, "check", tid)
    assert _status_of(skein_cli, ws, tid) == S_CHECK
    skein_cli(ws, "finish", tid)
    assert _status_of(skein_cli, ws, tid) == S_DONE
    skein_cli(ws, "archive", tid)
    assert _status_of(skein_cli, ws, tid) == "<missing>"


# ---------- 非法转换 (应拒) ----------

def test_start_already_active_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: start 一个已 active 的 task (应拒, 退出码 1)。"""
    tid = _mk(skein_cli, ws, ready=True)
    skein_cli(ws, "start", tid)
    r = skein_cli(ws, "start", tid, check=False)
    assert r.returncode == 1
    assert "只能 start 就绪" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE


def test_finish_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: finish 一个未 active 的 pending task (应拒)。"""
    tid = _mk(skein_cli, ws)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1
    assert "非在途 (进行中/检查中) 无法 finish" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING


def test_confirm_no_subtask_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: confirm 无 subtask 的 task (subtask 门在 confirm, 应拒, 留待处理)。"""
    tid = _mk(skein_cli, ws)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    r = skein_cli(ws, "confirm", tid, check=False)
    assert r.returncode == 1
    assert "无 subtask" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING


def test_confirm_no_estimate_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: confirm 未填预计工时的 task (estimate 硬门, 应拒, 留待处理)。"""
    tid = _mk(skein_cli, ws, sub=True)  # 有 subtask+prd, 只差 estimate
    r = skein_cli(ws, "confirm", tid, check=False)
    assert r.returncode == 1
    assert "预计工时未填" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING
    # 填实后同一条 confirm 应放行
    skein_cli(ws, "estimate", tid, "--set", "1")
    skein_cli(ws, "confirm", tid)
    assert _status_of(skein_cli, ws, tid) == S_READY


def test_subtask_add_requires_estimate(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: subtask add 缺 --estimate (必填, argparse 层拒, 退出码 2)。"""
    skein_cli(ws, "create", "feat-e", "--name", "n", "--desc", "d")
    r = skein_cli(ws, "subtask", "add", "feat-e", SID, "--name", "S", "--desc", "d", check=False)
    assert r.returncode == 2
    assert "--estimate" in r.stdout + r.stderr
    # 非正数同样拒 (方法层)
    r = skein_cli(ws, "subtask", "add", "feat-e", SID, "--name", "S", "--desc", "d",
                  "--estimate", "0", check=False)
    assert r.returncode == 1
    assert "正数" in r.stdout + r.stderr


def test_confirm_estimate_below_subtask_sum_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: task 工时低于 Σ subtask (自下而上累加硬门, 应拒)。"""
    tid = _mk(skein_cli, ws)  # 只 create, 自己控 subtask 工时
    skein_cli(ws, "subtask", "add", tid, "sub-a", "--name", "A", "--desc", "d", "--estimate", "3")
    skein_cli(ws, "subtask", "add", tid, "sub-b", "--name", "B", "--desc", "d", "--estimate", "2")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "4")  # < 3+2=5
    r = skein_cli(ws, "confirm", tid, check=False)
    assert r.returncode == 1
    assert "低于 subtask 合计 5" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING
    # 补到含 plan/check 自身开销即放行
    skein_cli(ws, "estimate", tid, "--set", "6")
    skein_cli(ws, "confirm", tid)
    assert _status_of(skein_cli, ws, tid) == S_READY


def test_start_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: start 未 confirm 的待处理 task (须先过 confirm 到就绪, 应拒)。"""
    tid = _mk(skein_cli, ws, sub=True)  # 有 subtask+prd 但未 confirm → 仍待处理
    r = skein_cli(ws, "start", tid, check=False)
    assert r.returncode == 1
    assert "只能 start 就绪" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING


def test_start_prd_placeholder_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: start 时 prd.md 残留 `- [ ] TODO` 占位 (模板初始态, 说明未填实, 应拒)。"""
    tid = _mk(skein_cli, ws, ready=True)  # 先 confirm 到就绪 → 重新写回带占位的模板态, 触 start prd double-check
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- [ ] TODO: 填目标\n\n"
        "## 边界\n- 边界内容\n\n## 验收标准\n- 用例通过\n\n## 索引\n- design.md\n")
    r = skein_cli(ws, "start", tid, check=False)
    assert r.returncode == 1
    assert "prd 未就绪" in r.stdout + r.stderr
    assert "TODO" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_READY  # start 被拒不回滚, 保持就绪


def test_start_prd_ok_passes(skein_cli: SkeinCli, ws: Path) -> None:
    """合法: prd.md 章节齐 + 无占位 → start 正常进 active。"""
    tid = _mk(skein_cli, ws, ready=True)  # _mk 内已 _fill_prd + confirm 到就绪
    r = skein_cli(ws, "start", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == S_ACTIVE


def test_op_on_missing_task_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: 对不存在的 task 操作 — start/finish/check 经 _load 拒 (exit 1)。

    注: archive 对不存在 task 静默 exit 0 (_archive 早退, 见 archive 幂等测试), 不在此断言。"""
    for cmd in ("start", "finish", "check"):
        r = skein_cli(ws, cmd, "ghost-task", check=False)
        assert r.returncode == 1, f"{cmd} 对不存在 task 应 exit 1"
        assert "task 不存在" in r.stdout + r.stderr, f"{cmd} 应报 task 不存在"


def test_check_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: check 一个 pending task (仅 active 能进检查, 应拒)。"""
    tid = _mk(skein_cli, ws, sub=True)
    r = skein_cli(ws, "check", tid, check=False)
    assert r.returncode == 1
    assert "只有进行中" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_PENDING


# ---------- 幂等 / 边界 ----------

def test_create_duplicate_id_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """幂等边界: create 同名重复 id (应拒 — 含已归档也不可复用)。"""
    skein_cli(ws, "create", "feat-dup", "--name", "feat-dup", "--desc", "d")
    r = skein_cli(ws, "create", "feat-dup", "--name", "feat-dup", "--desc", "d", check=False)
    assert r.returncode == 1
    assert "id 已占用" in r.stdout + r.stderr


def test_finish_after_done_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """幂等边界: finish 后再 finish (done 非 active, 应拒)。"""
    tid = _mk(skein_cli, ws, ready=True)
    skein_cli(ws, "start", tid)
    skein_cli(ws, "finish", tid)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1
    assert "非在途 (进行中/检查中) 无法 finish" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == S_DONE


def test_archive_already_archived_idempotent(skein_cli: SkeinCli, ws: Path) -> None:
    """幂等边界: archive 已归档 task — 当前实现静默返回 exit 0 (待确认: 应否报不存在)。

    archive 调 _archive (skein.py:715): src 不存在直接 return, 不报错。"""
    tid = _mk(skein_cli, ws, ready=True)
    skein_cli(ws, "start", tid)
    skein_cli(ws, "finish", tid)
    skein_cli(ws, "archive", tid)
    r = skein_cli(ws, "archive", tid, check=False)
    assert r.returncode == 0, "archive 已归档当前幂等返回 0 (见 _archive 早退)"
    assert _status_of(skein_cli, ws, tid) == "<missing>"


def test_subtask_add_duplicate_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """幂等边界: subtask add 同 sid 重复 (应拒)。"""
    tid = _mk(skein_cli, ws, sub=True)
    r = skein_cli(ws, "subtask", "add", tid, SID, "--name", "S", "--desc", "d", "--estimate", "1", check=False)
    assert r.returncode == 1
    assert "subtask 已存在" in r.stdout + r.stderr
