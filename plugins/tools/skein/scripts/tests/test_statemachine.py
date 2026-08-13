"""skein task 生命周期状态机测试 — 合法/非法/幂等转换全覆盖。

通过 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离临时仓),
覆盖 task 状态机: 待处理(pending) ⇄ 调研中(research) → [confirm, 吸收原 start] → 进行中(active)
→ [check] → 检查中(check) → [finishing, 占 gate 槽] → 收尾中(finishing) → [finish] → 已完成(done) → 归档。

待处理→调研中 经 research (须先登记 ≥1 个 --phase research 的 subtask); 调研中→待处理 经 plan
(须 research subtask 全 done); 待处理→进行中 经 confirm (吸收原 start: doctor 体检 + 建 worktree,
一步直接开工, 不再有「就绪」中间态)。非法转换断言被拒 (exit 1 + 中文态校验信息); 幂等转换断言
当前真实行为。
状态常量来自 skeinlib.model (中文落盘): TaskStatus.PENDING/TaskStatus.RESEARCH/TaskStatus.ACTIVE/TaskStatus.CHECK/TaskStatus.FINISHING/TaskStatus.DONE。
task/subtask id 全用描述性 slug, 规避 skein CODE_ID_RE (^[a-z]{1,4}\\d+$) 对代号式 id 的拒绝。"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

from skeinlib.task.model import TaskStatus

SkeinCli = Callable[..., subprocess.CompletedProcess[str]]

SID = "sub-build"  # subtask sid (描述性, 规避代号式校验)


def _mk(skein_cli: SkeinCli, ws: Path, tid: str = "feat-x", *,
        sub: bool = False, active: bool = False) -> str:
    """造 task。sub=附 1 subtask + 填实 prd (满足 confirm 前置); active=再 confirm 推到进行中
    (confirm 吸收 start, 直接建 worktree 开工)。"""
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    if sub or active:
        skein_cli(ws, "subtask", "add", tid, SID, "--name", "S", "--desc", "d", "--estimate", "1")
        _fill_prd(ws, tid)  # confirm 前置 prd 门: 填实占位免被拒
    if active:
        skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
        skein_cli(ws, "confirm", tid, "--approved")  # 待处理→进行中 用户确认门 (吸收 start)
    return tid


def _fill_prd(ws: Path, tid: str) -> None:
    """写一份规范 prd.md + design.md (全 7 章齐 + 无 TODO 占位), 过 confirm 的 _validate_prd + _validate_seam 门。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n"
        "## 目标\n- 解决 X 问题\n\n"
        "## 边界\n- 范围内: a\n\n"
        "## User Stories\n1. As a user, I want X, so that Y\n\n"
        "## 验收标准\n- 用例通过\n\n"
        "## 验证方式\n- 跑 pytest, 全绿即 pass\n\n"
        "## Testing Decisions\n- 只测外部行为\n\n"
        "## 索引\n- design.md\n")
    (ws / ".skein" / "task" / tid / "design.md").write_text(
        f"# {tid} — 详细设计\n\n"
        "## 测试接缝 (seam)\n- [x] API 层\n")


def _status_of(skein_cli: SkeinCli, ws: Path, tid: str) -> str:
    """从 skein list JSON 取 task 态; 不存在返 <missing>。"""
    data = json.loads(skein_cli(ws, "list").stdout)
    for t in data.get("tasks", []):
        if t["id"] == tid:
            return str(t["status"])
    return "<missing>"


# ---------- 合法转换全链 ----------

def test_create_pending(skein_cli: SkeinCli, ws: Path) -> None:
    """create → pending: 新 task 落盘态为待处理。"""
    r = skein_cli(ws, "create", "feat-add", "--name", "feat-add", "--desc", "d")
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, "feat-add") == TaskStatus.PENDING


def test_research_to_researching(skein_cli: SkeinCli, ws: Path) -> None:
    """research: 待处理 → 调研中 (须先登记 ≥1 个 research subtask)。"""
    tid = "feat-research"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "sub-r", "--name", "R", "--desc", "d",
              "--estimate", "1", "--phase", "research")
    r = skein_cli(ws, "research", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.RESEARCH


def test_plan_back_to_pending(skein_cli: SkeinCli, ws: Path) -> None:
    """plan: 调研中 → 待处理 (须 research subtask 全 done)。"""
    tid = "feat-plan"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "sub-r", "--name", "R", "--desc", "d",
              "--estimate", "1", "--phase", "research")
    skein_cli(ws, "research", tid)
    skein_cli(ws, "subtask", "done", tid, "sub-r")
    r = skein_cli(ws, "plan", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING


def test_confirm_active_builds_worktree(skein_cli: SkeinCli, ws: Path) -> None:
    """confirm(吸收 start, 须 --approved) → active: 建 worktree + 状态直接切进行中。"""
    skein_cli(ws, "config", "set", "worktree.enabled", "true")  # worktree 默认 false，测试需显式启用
    tid = _mk(skein_cli, ws, sub=True)
    skein_cli(ws, "estimate", tid, "--set", "1")
    r = skein_cli(ws, "confirm", tid, "--approved")
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE
    assert (ws / ".worktrees" / f"skein-{tid}").exists(), "worktree 未建"


def test_check_to_checking(skein_cli: SkeinCli, ws: Path) -> None:
    """check: active → check(检查中)。"""
    tid = _mk(skein_cli, ws, active=True)
    r = skein_cli(ws, "check", tid)
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, tid) == TaskStatus.CHECK


def test_finishing_to_finishing(skein_cli: SkeinCli, ws: Path) -> None:
    """finishing: 检查中 → 收尾中 (占 gate 槽)。"""
    tid = _mk(skein_cli, ws, active=True)
    skein_cli(ws, "check", tid)
    r = skein_cli(ws, "finishing", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.FINISHING


def test_finish_done_merges_and_destroys_worktree(skein_cli: SkeinCli, ws: Path) -> None:
    """finish(仅收尾中可调): 收尾中 → done, merge 回主仓 + 销 worktree。"""
    tid = _mk(skein_cli, ws, active=True)
    skein_cli(ws, "check", tid)
    skein_cli(ws, "finishing", tid)
    r = skein_cli(ws, "finish", tid)
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.DONE
    assert not (ws / ".worktrees" / f"skein-{tid}").exists(), "worktree 未销"


def test_finish_autoclean_removes_from_board(skein_cli: SkeinCli, ws: Path) -> None:
    """retain_days=0: finish 后自动归档, list 不再列出。"""
    cfg = ws / ".skein/config.yaml"
    cfg.write_text(cfg.read_text().replace("retain_days: 7", "retain_days: 0"))
    tid = _mk(skein_cli, ws, active=True)
    skein_cli(ws, "check", tid)
    skein_cli(ws, "finishing", tid)
    r = skein_cli(ws, "finish", tid)
    assert r.returncode == 0
    assert _status_of(skein_cli, ws, tid) == "<missing>"


def test_full_chain_create_to_finish(skein_cli: SkeinCli, ws: Path) -> None:
    """全链路: create → confirm(进行中) → check → finishing → finish。"""
    tid = _mk(skein_cli, ws, "feat-chain", active=True)
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE
    skein_cli(ws, "check", tid)
    assert _status_of(skein_cli, ws, tid) == TaskStatus.CHECK
    skein_cli(ws, "finishing", tid)
    assert _status_of(skein_cli, ws, tid) == TaskStatus.FINISHING
    skein_cli(ws, "finish", tid)
    assert _status_of(skein_cli, ws, tid) == TaskStatus.DONE


# ---------- 非法转换 (应拒) ----------

def test_confirm_already_active_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: confirm 一个已 active 的 task (应拒, 退出码 1)。"""
    tid = _mk(skein_cli, ws, active=True)
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "只能 confirm 待处理" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE


def test_confirm_during_research_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: 调研中态直接 confirm (应拒, 提示先 plan)。"""
    tid = "feat-mid-research"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "sub-r", "--name", "R", "--desc", "d",
              "--estimate", "1", "--phase", "research")
    skein_cli(ws, "research", tid)
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "先" in (r.stdout + r.stderr) and "plan" in (r.stdout + r.stderr)
    assert _status_of(skein_cli, ws, tid) == TaskStatus.RESEARCH


def test_confirm_force_skips_planning_and_research_gates(skein_cli: SkeinCli, ws: Path) -> None:
    """--force 允许未规划 pending 与未收敛 research 开工, 但仍执行完整激活动作。"""
    pending = _mk(skein_cli, ws, "feat-force-pending")
    r = skein_cli(ws, "confirm", pending, "--approved", "--force")
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, pending) == TaskStatus.ACTIVE
    task = json.loads((ws / ".skein" / "task" / pending / "task.json").read_text())
    assert task["timeline"][-1]["note"] == "--force: 看板强制操作, 跳过前置门"

    research = "feat-force-research"
    skein_cli(ws, "create", research, "--name", research, "--desc", "d")
    skein_cli(ws, "subtask", "add", research, "sub-r", "--name", "R", "--desc", "d",
              "--estimate", "1", "--phase", "research")
    skein_cli(ws, "research", research)
    r = skein_cli(ws, "confirm", research, "--approved", "--force")
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, research) == TaskStatus.ACTIVE


def test_confirm_force_on_active_is_idempotent(skein_cli: SkeinCli, ws: Path) -> None:
    """看板强制确认已开工 task: 目标态已达成, 幂等成功且不重复建 worktree。"""
    tid = _mk(skein_cli, ws, "feat-force-active", active=True)
    before = json.loads((ws / ".skein" / "task" / tid / "task.json").read_text())["worktrees"]
    r = skein_cli(ws, "confirm", tid, "--approved", "--force", check=False)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "只能 confirm 待处理" not in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE
    after = json.loads((ws / ".skein" / "task" / tid / "task.json").read_text())["worktrees"]
    assert after == before


def test_plan_rejects_unfinished_research(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: research subtask 未全 done 时 plan 被拒。"""
    tid = "feat-research-undone"
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "sub-r", "--name", "R", "--desc", "d",
              "--estimate", "1", "--phase", "research")
    skein_cli(ws, "research", tid)
    r = skein_cli(ws, "plan", tid, check=False)
    assert r.returncode == 1
    assert "未全完成" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.RESEARCH


def test_research_without_research_subtask_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: 无 research subtask 的 task 发起调研 (应拒)。"""
    tid = _mk(skein_cli, ws, sub=True)  # 只有 exec(默认) subtask
    r = skein_cli(ws, "research", tid, check=False)
    assert r.returncode == 1
    assert "无 research subtask" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING


def test_finish_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: finish 一个未收尾中的 pending task (应拒)。"""
    tid = _mk(skein_cli, ws)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1
    assert "只能 finish 收尾中" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING


def test_finish_force_skips_state_gate_but_completes(skein_cli: SkeinCli, ws: Path) -> None:
    """--force 允许 pending task 跳过状态/gate 门, 仍落完整完成态。"""
    tid = _mk(skein_cli, ws, "feat-force-finish")
    r = skein_cli(ws, "finish", tid, "--force")
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.DONE
    task = json.loads((ws / ".skein" / "task" / tid / "task.json").read_text())
    assert task["finished"]
    assert task["checked_end"]
    assert task["timeline"][-1]["note"] == "--force: 看板强制操作, 跳过前置门"


def test_finish_active_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: finish 一个进行中 (未经 check/finishing) 的 task (应拒 — finish 仅收尾中可调)。"""
    tid = _mk(skein_cli, ws, active=True)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1
    assert "只能 finish 收尾中" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE


def test_finishing_active_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: finishing 一个进行中 (未 check) 的 task (应拒)。"""
    tid = _mk(skein_cli, ws, active=True)
    r = skein_cli(ws, "finishing", tid, check=False)
    assert r.returncode == 1
    assert "只能对检查中 task 收尾" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE


def test_confirm_no_subtask_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: confirm 无 subtask 的 task (subtask 门在 confirm, 应拒, 留待处理)。"""
    tid = _mk(skein_cli, ws)
    skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "无 subtask" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING


def test_confirm_no_estimate_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: confirm 未填预计工时的 task (estimate 硬门, 应拒, 留待处理)。"""
    tid = _mk(skein_cli, ws, sub=True)  # 有 subtask+prd, 只差 estimate
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "预计工时未填" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING
    # 填实后同一条 confirm 应放行 (直接进 active)
    skein_cli(ws, "estimate", tid, "--set", "1")
    skein_cli(ws, "confirm", tid, "--approved")
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE


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
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "低于 subtask 合计 5" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING
    # 补到含 plan/check 自身开销即放行
    skein_cli(ws, "estimate", tid, "--set", "6")
    skein_cli(ws, "confirm", tid, "--approved")
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE


def test_confirm_prd_placeholder_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: confirm 时 prd.md 残留 `- [ ] TODO` 占位 (模板初始态, 说明未填实, 应拒)。"""
    tid = _mk(skein_cli, ws, sub=True)
    skein_cli(ws, "estimate", tid, "--set", "1")
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- [ ] TODO: 填目标\n\n"
        "## 边界\n- 边界内容\n\n## User Stories\n1. As a u, I want x\n\n"
        "## 验收标准\n- 用例通过\n\n## 验证方式\n- 跑 pytest\n\n"
        "## Testing Decisions\n- 测外部行为\n\n## 索引\n- design.md\n")
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    assert "prd 未就绪" in r.stdout + r.stderr
    assert "TODO" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING


def test_confirm_prd_checked_placeholder_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: 占位被勾成 `- [x] TODO` — 勾选不等于填实, 同样应拒 (防 plan 期预勾绕门)。"""
    tid = _mk(skein_cli, ws, sub=True)
    skein_cli(ws, "estimate", tid, "--set", "1")
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- [x] TODO: 填目标\n\n"
        "## 边界\n- 边界内容\n\n## User Stories\n1. As a u, I want x\n\n"
        "## 验收标准\n- [X] TODO: 填验收标准\n\n## 验证方式\n- 跑 pytest\n\n"
        "## Testing Decisions\n- 测外部行为\n\n## 索引\n- design.md\n")
    r = skein_cli(ws, "confirm", tid, "--approved", check=False)
    assert r.returncode == 1
    out = r.stdout + r.stderr
    assert "prd 未就绪" in out
    assert "2 处" in out, f"勾选态占位应全数计入: {out}"
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING


def test_confirm_prd_ok_passes(skein_cli: SkeinCli, ws: Path) -> None:
    """合法: prd.md 章节齐 + 无占位 → confirm 正常进 active。"""
    tid = _mk(skein_cli, ws, sub=True)  # _mk 内已 _fill_prd
    skein_cli(ws, "estimate", tid, "--set", "1")
    r = skein_cli(ws, "confirm", tid, "--approved")
    assert r.returncode == 0, r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.ACTIVE


def test_op_on_missing_task_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: 对不存在的 task 操作 — confirm/finish/check 经 _load 拒 (exit 1)。"""
    for cmd in ("confirm", "finish", "check"):
        args = [cmd, "ghost-task"] + (["--approved"] if cmd == "confirm" else [])
        r = skein_cli(ws, *args, check=False)
        assert r.returncode == 1, f"{cmd} 对不存在 task 应 exit 1"
        assert "task 不存在" in r.stdout + r.stderr, f"{cmd} 应报 task 不存在"


def test_check_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """非法: check 一个 pending task (仅 active 能进检查, 应拒)。"""
    tid = _mk(skein_cli, ws, sub=True)
    r = skein_cli(ws, "check", tid, check=False)
    assert r.returncode == 1
    assert "只有进行中" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.PENDING


# ---------- 幂等 / 边界 ----------

def test_create_duplicate_id_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """幂等边界: create 同名重复 id (应拒 — 含已归档也不可复用)。"""
    skein_cli(ws, "create", "feat-dup", "--name", "feat-dup", "--desc", "d")
    r = skein_cli(ws, "create", "feat-dup", "--name", "feat-dup", "--desc", "d", check=False)
    assert r.returncode == 1
    assert "id 已占用" in r.stdout + r.stderr


def test_finish_after_done_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """幂等边界: finish 后再 finish (done 非收尾中, 应拒)。"""
    tid = _mk(skein_cli, ws, active=True)
    skein_cli(ws, "check", tid)
    skein_cli(ws, "finishing", tid)
    skein_cli(ws, "finish", tid)
    r = skein_cli(ws, "finish", tid, check=False)
    assert r.returncode == 1
    assert "只能 finish 收尾中" in r.stdout + r.stderr
    assert _status_of(skein_cli, ws, tid) == TaskStatus.DONE


def test_subtask_add_duplicate_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """幂等边界: subtask add 同 sid 重复 (应拒)。"""
    tid = _mk(skein_cli, ws, sub=True)
    r = skein_cli(ws, "subtask", "add", tid, SID, "--name", "S", "--desc", "d", "--estimate", "1", check=False)
    assert r.returncode == 1
    assert "subtask 已存在" in r.stdout + r.stderr
