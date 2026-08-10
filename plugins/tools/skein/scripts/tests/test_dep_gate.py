"""task 级前置依赖门归位测试 — 门在「取活」侧, 不在「审批」侧。

用户裁定的语义: `confirm` 只确认 planning 产物审批完成; 「能不能开干」由调度侧取 subtask
时判。故本文件两侧对拍:
  1. 前置未完成的 task 照样能 confirm (审批不被上游进度串行化);
  2. confirm 之后前置仍未完成时, `claim exec` / `flow run` / `subtask claim` /
     `subtask start` 一律不派它的 subtask (否则就成了"前置没完成也派 executor 干活")。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from conftest import SkeinCli
from skeinlib.task.model import SubtaskStatus, TaskStatus


def _task(ws: Path, tid: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ws / ".skein" / "task" / tid / "task.json").read_text()))


def _fill_prd(ws: Path, tid: str) -> None:
    """写满 confirm 的 prd + design 接缝门 (与 test_supertask 同一套模板)。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n"
        "## 边界\n- a\n\n## User Stories\n1. As a user, I want X\n\n"
        "## 验收标准\n- 通过\n\n## 验证方式\n- 跑 pytest\n\n"
        "## Testing Decisions\n- 复用现有单测\n\n## 索引\n- design.md\n")
    (ws / ".skein" / "task" / tid / "design.md").write_text(
        f"# {tid} — 详细设计\n\n## 测试接缝 (seam)\n- [x] API 层\n")


def _plan(skein_cli: SkeinCli, ws: Path, tid: str) -> None:
    """create + 1 subtask + prd/design + estimate = 一个 planning 就绪的 task。"""
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s1", "--name", "干活", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, tid)
    skein_cli(ws, "estimate", tid, "--set", "2")


def _confirm_json(skein_cli: SkeinCli, ws: Path, tid: str) -> dict[str, Any]:
    # confirm 的 stdout 先打 doctor 的「✅ 无违规」再打 JSON, 取最后一行
    r = skein_cli(ws, "confirm", tid)
    return cast(dict[str, Any], json.loads(r.stdout.strip().splitlines()[-1]))


def _setup_pair(skein_cli: SkeinCli, ws: Path) -> None:
    """up (前置) + down (依赖 up), 两者 planning 均就绪, up 已 active。"""
    _plan(skein_cli, ws, "up")
    _plan(skein_cli, ws, "down")
    skein_cli(ws, "task", "deps", "down", "up")
    skein_cli(ws, "confirm", "up")


# ---------- ① 审批侧: 前置未完成不再挡 confirm ----------
def test_confirm_allowed_while_dep_unfinished(skein_cli: SkeinCli, ws: Path) -> None:
    _setup_pair(skein_cli, ws)
    assert _task(ws, "up")["status"] != TaskStatus.DONE, "前置须处于未完成态, 否则本例无意义"

    out = _confirm_json(skein_cli, ws, "down")
    assert out["status"] == TaskStatus.ACTIVE, out
    assert _task(ws, "down")["status"] == TaskStatus.ACTIVE, "前置未完成的 task 也该能过审批门"


# ---------- ② 调度侧: confirm 后依旧不派活 ----------
def test_claim_skips_task_with_unfinished_dep(skein_cli: SkeinCli, ws: Path) -> None:
    """全局 claim 只认领前置已清的 up/s1, 绝不碰 down/s1。"""
    _setup_pair(skein_cli, ws)
    _confirm_json(skein_cli, ws, "down")

    claimed = json.loads(skein_cli(ws, "claim", "exec").stdout)["claimed"]
    assert [c["tid"] for c in claimed] == ["up"], f"前置未完成的 down 被派了活: {claimed}"
    assert _task(ws, "down")["subtasks"][0]["status"] == SubtaskStatus.PENDING


def test_flow_run_skips_task_with_unfinished_dep(skein_cli: SkeinCli, ws: Path) -> None:
    """`flow run --task down` 走同一条 `_schedulable` 门 → 空批, 报依赖阻塞。"""
    _setup_pair(skein_cli, ws)
    _confirm_json(skein_cli, ws, "down")

    result = json.loads(skein_cli(ws, "flow", "run", "--task", "down").stdout)["result"]
    assert result["exec"]["claimed"] == [], f"flow run 派了前置未完成的活: {result}"
    assert _task(ws, "down")["subtasks"][0]["status"] == SubtaskStatus.PENDING


def test_subtask_claim_and_start_blocked_by_task_dep(skein_cli: SkeinCli, ws: Path) -> None:
    """单 task 路径 (`subtask claim` / `subtask start`) 同样拦住 —— 否则是条绕过依赖的暗道。"""
    _setup_pair(skein_cli, ws)
    _confirm_json(skein_cli, ws, "down")

    data = json.loads(skein_cli(ws, "subtask", "claim", "down").stdout)
    assert data["ready"] == [], f"subtask claim 认领了前置未完成的活: {data}"
    assert data["reason"] == "dependencies_blocked", data

    r = skein_cli(ws, "subtask", "start", "down", "s1", check=False)
    assert r.returncode != 0 and "前置 task 未完成" in r.stderr, r.stderr
    assert _task(ws, "down")["subtasks"][0]["status"] == SubtaskStatus.PENDING


# ---------- ③ 前置完成后放行 ----------
def test_claim_resumes_after_dep_done(skein_cli: SkeinCli, ws: Path) -> None:
    _setup_pair(skein_cli, ws)
    _confirm_json(skein_cli, ws, "down")
    skein_cli(ws, "subtask", "done", "up", "s1")
    skein_cli(ws, "check", "up")
    skein_cli(ws, "finishing", "up")
    skein_cli(ws, "finish", "up")

    claimed = json.loads(skein_cli(ws, "claim", "exec").stdout)["claimed"]
    assert [c["tid"] for c in claimed] == ["down"], f"前置已完成仍不派活: {claimed}"
