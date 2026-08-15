"""task.json timeline 行为测试 — 走 `skein_cli` 跑真命令, 读回 task.json 断言。

覆盖 (对应 wire-task/wire-sub 落地后的时间线):
1. 追加语义: 每次生命周期动作只 append 一条, 已有条目原样不变(不改写/不删)。
2. rollback 判定: task 级 (research→plan 回退) / subtask 级 (fail 后重 start 视为回滚)。
3. 多轮 check: `check` 已在检查中态时幂等, 不重复 append。
4. 老数据容错: task.json 缺 "timeline" 字段(模拟迁移前老数据)时不崩, 后续动作能正常补上。

🛑 禁 import skeinlib 内部函数(timeline.append / 状态枚举等) —— 只经 `skein_cli` 子进程操作,
断言只认 CLI 落盘的字面字符串, 黑盒验证真实行为(而非白盒验证实现细节)。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from conftest import SkeinCli

PRD = """# {tid} — PRD

## 目标
- [ ] timeline 测试

## 边界
- 不动别的

## 验收标准
- [ ] 追加不改写

"""

def _task(ws: Path, tid: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ws / ".skein" / "task" / tid / "task.json").read_text()))

def _write_task(ws: Path, tid: str, t: dict[str, Any]) -> None:
    (ws / ".skein" / "task" / tid / "task.json").write_text(json.dumps(t))

def _timeline(t: dict[str, Any]) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], t.get("timeline", []))

def _ready_task(ws: Path, skein_cli: SkeinCli, tid: str = "feat-tl") -> str:
    """结构上够格 confirm 的 task (复用 test_confirm_gate 的配方)。"""
    skein_cli(ws, "create", tid, "--name", "任务", "--desc", "d")
    skein_cli(ws, "subtask", "add", tid, "s1", "--name", "子一", "--desc", "d", "--estimate", "2")
    (ws / ".skein/task" / tid / "prd.md").write_text("---\ndesc: 解决 X 问题\nboundary:\n  should:\n  - 范围内a\n  should_not: []\nestimate: 1\nacceptance:\n  - 用例通过\n---\n", encoding="utf-8")
    (ws / ".skein/task" / tid / "design.md").write_text(
        f"# {tid} — 详细设计\n\n## 测试接缝 (seam)\n- [x] 复用 tests/test_statemachine.py\n")
    skein_cli(ws, "estimate", tid, "--set", "4")
    return tid

# ---------- 1. 追加语义: 只增不改 ----------
def test_timeline_append_only_grows(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _ready_task(ws, skein_cli)
    t = _task(ws, tid)
    tl = _timeline(t)
    assert len(tl) == 1, f"create 应写入唯一一条 task 事件: {tl}"
    assert tl[0]["kind"] == "task" and tl[0]["status"] == "pending" and tl[0]["rollback"] is False
    snapshot0 = dict(tl[0])

    skein_cli(ws, "confirm", tid, "--approved")
    t2 = _task(ws, tid)
    tl2 = _timeline(t2)
    assert len(tl2) == 2, f"confirm 应新追加一条, 而非改写: {tl2}"
    assert tl2[0] == snapshot0, "已有条目不该被后续动作改写"
    assert tl2[1]["status"] == "active" and tl2[1]["rollback"] is False

    skein_cli(ws, "check", tid)
    t3 = _task(ws, tid)
    tl3 = _timeline(t3)
    assert len(tl3) == 3, f"check 应再追加一条: {tl3}"
    assert tl3[:2] == tl2, "前两条不该因新动作被改动"
    assert tl3[2]["status"] == "check" and tl3[2]["rollback"] is False

# ---------- 2. rollback: task 级 (research → plan 回退) ----------
def test_timeline_rollback_task_level(skein_cli: SkeinCli, ws: Path) -> None:
    tid = "feat-research"
    skein_cli(ws, "create", tid, "--name", "任务", "--desc", "d")
    skein_cli(ws, "research", "add", tid, "r1", "--name", "调研一", "--desc", "d",
              "--estimate", "1", )
    skein_cli(ws, "research", tid)
    skein_cli(ws, "research", "done", tid, "r1")  # plan 门槛: research subtask 须全 done
    skein_cli(ws, "plan", tid)  # 调研中→待处理, 序号倒退 (research=1 → pending=0)
    t = _task(ws, tid)
    task_events = [e for e in _timeline(t) if e["kind"] == "task"]
    assert [(e["status"], e["rollback"]) for e in task_events] == [
        ("pending", False), ("research", False), ("pending", True),
    ], task_events

# ---------- 3. rollback: subtask 级 (fail 后重 start 视为回滚) ----------
def test_timeline_rollback_subtask_level(skein_cli: SkeinCli, ws: Path) -> None:
    # 先过 confirm 进「进行中」—— subtask start 要求 task 已在可调度态
    tid = _ready_task(ws, skein_cli, "feat-sub")
    skein_cli(ws, "confirm", tid, "--approved")

    skein_cli(ws, "subtask", "start", tid, "s1")
    skein_cli(ws, "subtask", "fail", tid, "s1", "--note", "boom")
    skein_cli(ws, "subtask", "start", tid, "s1")  # 失败后重 start = 回滚重跑
    skein_cli(ws, "subtask", "done", tid, "s1")

    t = _task(ws, tid)
    sub_events = [e for e in _timeline(t) if e["kind"] == "subtask" and e["sid"] == "s1"]
    assert [(e["status"], e["rollback"]) for e in sub_events] == [
        ("running", False),
        ("failed", False),
        ("running", True),   # 重 start: 序号 running(0) <= failed(1) → 回滚
        ("done", False),
    ], sub_events

# ---------- 4. 多轮 check: 已在检查中态时幂等, 不重复 append ----------
def test_timeline_multi_round_check_is_idempotent(skein_cli: SkeinCli, ws: Path) -> None:
    tid = _ready_task(ws, skein_cli, "feat-check")
    skein_cli(ws, "confirm", tid, "--approved")
    r1 = skein_cli(ws, "check", tid)
    d1 = json.loads(r1.stdout)
    assert d1.get("status") == "check" and not d1.get("idempotent")

    t_after_first = _task(ws, tid)
    check_events_1 = [e for e in _timeline(t_after_first) if e.get("status") == "check"]
    assert len(check_events_1) == 1

    r2 = skein_cli(ws, "check", tid)  # 再跑一次 (多轮 checker 自跑场景)
    d2 = json.loads(r2.stdout)
    assert d2.get("idempotent") is True, f"重复 check 应幂等: {d2}"

    t_after_second = _task(ws, tid)
    check_events_2 = [e for e in _timeline(t_after_second) if e.get("status") == "check"]
    assert len(check_events_2) == 1, f"幂等调用不该再追加一条: {check_events_2}"
    assert _timeline(t_after_second) == _timeline(t_after_first), "幂等调用不该改动 timeline"

# ---------- 5. 老数据容错: task.json 缺 "timeline" 字段不崩 ----------
def test_timeline_legacy_data_missing_field_tolerated(skein_cli: SkeinCli, ws: Path) -> None:
    # 先推到「进行中」再抹 timeline —— start 要求 task 可调度, 与本用例要验的老数据自愈无关
    tid = _ready_task(ws, skein_cli, "feat-legacy")
    skein_cli(ws, "confirm", tid, "--approved")
    t = _task(ws, tid)
    assert "timeline" in t
    del t["timeline"]  # 模拟 timeline 功能上线前的老 task.json
    _write_task(ws, tid, t)

    # 只读路径: status --json 不因缺字段崩, 原样回落空列表 (views.py 注释所述)
    r_status = skein_cli(ws, "status", tid, "--json")
    assert r_status.returncode == 0, f"老数据读 status 不该崩: {r_status.stderr}"
    status_data = json.loads(r_status.stdout)
    assert status_data.get("timeline", []) == [], f"缺字段应回落空列表: {status_data.get('timeline')}"

    # 写路径: 后续动作 (subtask add + start) 触发 timeline.append, 应自愈补回字段而非崩
    r_add = skein_cli(ws, "subtask", "add", tid, "s2", "--name", "子二", "--desc", "d", "--estimate", "1")
    assert r_add.returncode == 0, f"老数据下新增 subtask 不该崩: {r_add.stderr}"
    r_start = skein_cli(ws, "subtask", "start", tid, "s2")
    assert r_start.returncode == 0, f"老数据下 start 不该崩: {r_start.stderr}"

    t2 = _task(ws, tid)
    tl2 = _timeline(t2)
    assert len(tl2) == 1, f"老数据自愈后应正常追加新事件: {tl2}"
    assert tl2[0]["kind"] == "subtask" and tl2[0]["status"] == "running" and tl2[0]["sid"] == "s2"

if __name__ == "__main__":
    import tempfile

    from conftest import make_ws, run_skein
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "w"
            d.mkdir()
            fn(run_skein, make_ws(d))
    print("timeline 行为测试自检过")
