# mypy: ignore-errors
"""views.py 覆盖率补测 — 补 _view_* 各种分支。

重点:
  - _view_board_data 的 git 用户名读取失败分支
  - _view_dashboard / _view_queue 的各种分支
  - _view_search 的 spec 搜索命中
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from skeinlib.web.views import (_view_board_data, _view_dashboard, _view_queue,
                                _view_search, Snapshot)
from skeinlib.task.model import TaskStatus, SubtaskStatus



def test_view_board_data_git_user_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """git config 失败 → git_user 为 None (不抛异常)。"""

    def boom(*args: Any, **kw: Any) -> Any:
        raise OSError("git not found")

    monkeypatch.setattr("subprocess.run", boom)

    # 构造最小 Snapshot
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [],
        all_tasks_fn=lambda: [],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )
    data = _view_board_data(snap)

    # 验证 data 结构正确 (assignee 回退到 task.owner 或 None)
    assert "overview" in data
    assert "cards" in data


def test_view_board_data_elapsed_zero_for_pending(tmp_path: Path) -> None:
    """待处理 / 调研中 task 的 elapsed 为 0。"""
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [{"id": "p1", "status": TaskStatus.PENDING, "created": 1000}],
        all_tasks_fn=lambda: [{"id": "p1", "status": TaskStatus.PENDING, "created": 1000}],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )
    data = _view_board_data(snap)
    card = next(c for c in data["cards"] if c["id"] == "p1")
    assert card["elapsed"] == 0


def test_view_board_data_elapsed_rounds_to_minutes(tmp_path: Path) -> None:
    """elapsed 从秒数 round 到分钟 (不是 truncate)。"""
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [{"id": "a1", "status": TaskStatus.ACTIVE, "created": 1000, "started": 1000}],
        all_tasks_fn=lambda: [{"id": "a1", "status": TaskStatus.ACTIVE, "created": 1000, "started": 1000}],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )

    import skeinlib.task.model as _m
    import skeinlib.web.views as _v
    orig_model_now = _m.now
    orig_views_now = _v.now

    def fake_now() -> int:
        return 1600  # started 1000, now 1600 = 600s = 10m

    _m.now = fake_now
    _v.now = fake_now

    try:
        data = _view_board_data(snap)
        card = next(c for c in data["cards"] if c["id"] == "a1")
        assert card["elapsed"] == 10
    finally:
        _m.now = orig_model_now
        _v.now = orig_views_now


# ---- _view_dashboard: running/ready subtasks ---------------------------------

def test_view_dashboard_running_subs_no_started(tmp_path: Path) -> None:
    """running subtask 的 started 为 None → elapsed 为 None。"""
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [],
        all_tasks_fn=lambda: [{
            "id": "a1", "status": TaskStatus.ACTIVE,
            "subtasks": [{"sid": "s1", "status": SubtaskStatus.RUNNING, "started": None}]
        }],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )
    dash = _view_dashboard(snap)
    assert len(dash["runningSubs"]) == 1
    assert dash["runningSubs"][0]["elapsed"] is None


def test_view_dashboard_ready_subs_all_deps_done(tmp_path: Path) -> None:
    """ready_subtasks 只包含依赖全 done 的 pending subtask。"""
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [],
        all_tasks_fn=lambda: [{
            "id": "t1", "status": TaskStatus.ACTIVE,
            "subtasks": [
                {"sid": "s1", "status": SubtaskStatus.DONE, "depends_on": []},
                {"sid": "s2", "status": SubtaskStatus.PENDING, "depends_on": ["s1"]},
                {"sid": "s3", "status": SubtaskStatus.PENDING, "depends_on": ["s2"]},  # s2 未 done, 阻塞
            ]
        }],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )
    dash = _view_dashboard(snap)
    ready = dash["readySubs"]
    assert len(ready) == 1
    assert ready[0]["sid"] == "s2"


def test_view_dashboard_active_tasks_split_by_status(tmp_path: Path) -> None:
    """activeTasks / checkTasks 按 status 分流。"""
    task_data = [
        {"id": "a1", "status": TaskStatus.ACTIVE, "name": "A1", "desc": "active", "created": 1000, "started": 1000,
         "subtasks": [{"sid": "s1", "name": "S1", "status": "pending"}]},
        {"id": "c1", "status": TaskStatus.CHECK, "name": "C1", "desc": "check", "created": 1000,
         "subtasks": [{"sid": "s2", "name": "S2", "status": "done"}]},
    ]
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: task_data,  # snap.tasks 被视图使用
        all_tasks_fn=lambda: task_data,
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )
    dash = _view_dashboard(snap)
    assert len(dash["activeTasks"]) == 1
    assert dash["activeTasks"][0]["status"] == TaskStatus.ACTIVE
    assert len(dash["checkTasks"]) == 1
    assert dash["checkTasks"][0]["status"] == TaskStatus.CHECK


# ---- _view_queue: queue/running/ready -----------------------------------------

def test_view_queue_pending_queue_exists(tmp_path: Path) -> None:
    """pendingQueue 字段存在 (具体过滤逻辑由 _pending_queue 保证)。"""
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [],
        all_tasks_fn=lambda: [],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )

    queue = _view_queue(snap)
    # 验证 pendingQueue 字段存在
    assert "pendingQueue" in queue


def test_view_queue_running_subs_with_elapsed(tmp_path: Path) -> None:
    """runningSubtasks 带 elapsed (分钟)。"""
    import skeinlib.task.model as _m
    import skeinlib.web.views as _v
    orig_model_now = _m.now
    orig_views_now = _v.now

    def fake_now() -> int:
        return 1600

    _m.now = fake_now
    _v.now = fake_now

    try:
        snap = Snapshot(
            proj="TEST", wt_shown=False,
            tasks_fn=lambda: [],
            all_tasks_fn=lambda: [{
                "id": "a1", "status": TaskStatus.ACTIVE,
                "subtasks": [{"sid": "s1", "status": SubtaskStatus.RUNNING, "started": 1000}]
            }],
            tasks_dir=tmp_path / "tasks",
            archive_dir=tmp_path / "archive",
            spec_root=tmp_path / "spec",
        )
        queue = _view_queue(snap)
        assert len(queue["runningSubs"]) == 1
        assert queue["runningSubs"][0]["elapsed"] == 10  # (1600-1000)/60 = 10m
    finally:
        _m.now = orig_model_now
        _v.now = orig_views_now


# ---- _view_search: spec 搜索 --------------------------------------------------

def test_view_search_spec_hits(tmp_path: Path) -> None:
    """spec 搜索命中文件内容 (跳过 index.md)。"""
    spec_root = tmp_path / "spec"
    spec_root.mkdir(parents=True)
    rules = spec_root / "rules"
    rules.mkdir()
    (rules / "index.md").write_text("# Rules\n", encoding="utf-8")  # 应被跳过
    (rules / "naming.md").write_text("# 命名规范\n\n变量名要清晰。\n", encoding="utf-8")

    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [],
        all_tasks_fn=lambda: [],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=spec_root,
    )

    hits = _view_search(snap, "命名")
    assert any(h["kind"] == "spec" and "naming.md" in h["id"] for h in hits["hits"])
    assert not any("index.md" in h.get("id", "") for h in hits["hits"])


def test_view_search_empty_query(tmp_path: Path) -> None:
    """空查询直接回空数组, 不跑检索。"""
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: [],
        all_tasks_fn=lambda: [],
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )
    assert _view_search(snap, "")["hits"] == []
    assert _view_search(snap, "   ")["hits"] == []


def test_view_search_hits_subtasks(tmp_path: Path) -> None:
    """搜索命中 subtask 的 name/desc。"""
    task_data = [{
        "id": "t1", "name": "父任务", "desc": "父描述",
        "subtasks": [
            {"sid": "s1", "name": "子任务一", "desc": "子描述一"},
            {"sid": "s2", "name": "子任务二", "desc": "子描述二"},
        ]
    }]
    snap = Snapshot(
        proj="TEST", wt_shown=False,
        tasks_fn=lambda: task_data,  # snap.tasks 才是被搜索的
        all_tasks_fn=lambda: task_data,
        tasks_dir=tmp_path / "tasks",
        archive_dir=tmp_path / "archive",
        spec_root=tmp_path / "spec",
    )

    hits = _view_search(snap, "子描述")["hits"]
    assert len(hits) == 2
    assert all(h["kind"] == "subtask" for h in hits)
    assert "t1/s1" in hits[0]["id"]


