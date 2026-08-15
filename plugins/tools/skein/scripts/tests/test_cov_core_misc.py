"""补充 core 模块覆盖率缺口 - workspace / artifacts / query / admin。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401
from skeinlib.core.commands import Skein  # noqa: E402
from skeinlib.task.model import TaskStatus, SubtaskStatus  # noqa: E402
from skeinlib.utils.errors import SkeinError  # noqa: E402


def _skein(ws: Path, monkeypatch: pytest.MonkeyPatch) -> Skein:
    monkeypatch.chdir(ws)
    return Skein()


def _ns(**kw: Any) -> argparse.Namespace:
    return argparse.Namespace(**kw)


def _create(sk: Skein, tid: str, **over: Any) -> dict[str, Any]:
    a = _ns(id=tid, name=tid, desc="d", deps="",
            repos=None, estimate=None, priority=None, like=None)
    for k, v in over.items():
        setattr(a, k, v)
    return sk.lifecycle.create(a)


def _add_sub(sk: Skein, tid: str, sid: str, **over: Any) -> dict[str, Any]:
    a = _ns(action="add", tid=tid, sid=sid, name=sid, desc="d", estimate="1",
            deps="", check="", skills="", repo=None)
    for k, v in over.items():
        setattr(a, k, v)
    return sk.scheduler.subtask(a)


def _add_research(sk: Skein, tid: str, sid: str, **over: Any) -> dict[str, Any]:
    a = _ns(action="add", tid=tid, sid=sid, name=sid, desc="d", estimate="1",
            deps="", check="", note=None)
    for k, v in over.items():
        setattr(a, k, v)
    return sk.scheduler.research(a)


def _fill_prd(ws: Path, tid: str) -> None:
    d = ws / ".skein" / "task" / tid
    (d / "prd.md").write_text("---\ndesc: 解决 X 问题\nboundary:\n  should:\n  - 范围内a\n  should_not: []\nestimate: 1\nacceptance:\n  - 用例通过\n---\n", encoding="utf-8")
    (d / "design.md").write_text(
        f"# {tid} — 详细设计\n\n## 测试接缝 (seam)\n- [x] API 层\n", encoding="utf-8")


def _confirm(sk: Skein, ws: Path, tid: str) -> dict[str, Any]:
    _fill_prd(ws, tid)
    sk.lifecycle.estimate(_ns(id=tid, set="8"))
    return sk.lifecycle.confirm(_ns(id=tid, approved=True, unattended=False, summary=False))


def _load(ws: Path, tid: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (ws / ".skein" / "task" / tid / "task.json").read_text(encoding="utf-8"))
    return data


# ── workspace: hooks_cfg / config / _dep_unfinished ─────────────────────────────
def test_workspace_config_raises_on_uninitialized(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """未初始化时 config() 抛错。"""
    monkeypatch.chdir(ws)
    # 删除 .skein 模拟未初始化
    import shutil
    skein_dir = ws / ".skein"
    if skein_dir.exists():
        shutil.rmtree(skein_dir)
    sk = Skein()
    with pytest.raises(SkeinError, match="未初始化"):
        sk.config()


def test_workspace_hooks_cfg_returns_empty_on_missing_config(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """配置文件缺失时 _hooks_cfg 返回空字典。"""
    monkeypatch.chdir(ws)
    sk = Skein()
    # 删除 config.yaml
    cfg = ws / ".skein" / "config.yaml"
    cfg.unlink()
    assert sk._hooks_cfg() == {}


def test_workspace_dep_unfinished_returns_false_for_archived(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_dep_unfinished 对已归档的依赖返回 False (视为完成)。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    # 完成并归档 task
    t = _load(ws, "base-api")
    t["status"] = TaskStatus.DONE
    import skeinlib.core.workspace as ws_module
    ws_module.Workspace().store.save(t)
    # 模拟归档移动
    import shutil
    task_dir = ws / ".skein" / "task" / "base-api"
    archive_dir = ws / ".skein" / "task" / "archive" / "base-api"
    archive_dir.parent.mkdir(parents=True, exist_ok=True)
    if task_dir.exists():
        shutil.move(str(task_dir), str(archive_dir))
    assert sk._dep_unfinished("base-api") is False


def test_workspace_dep_unfinished_returns_false_for_unknown(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_dep_unfinished 对不存在的依赖返回 False (不阻塞)。"""
    sk = _skein(ws, monkeypatch)
    assert sk._dep_unfinished("ghost-task") is False


def test_workspace_sub_raises_on_unknown_sid(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_sub 对不存在的 subtask 抛错。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    t = _load(ws, "feat-x")
    with pytest.raises(SkeinError, match="subtask 不存在"):
        sk._sub(t, "ghost-sid")


# ── artifacts: prd / design ───────────────────────────────────────────



def test_artifacts_design_seam_write(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """design seam 写入测试接缝条目。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    out = sk.artifacts.design(_ns(id="feat-x", action="seam",
                                     list="- [ ] API 层\n- [ ] UI 层"))
    assert out["items"] == 2





def test_artifacts_design_unknown_action(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """design 拒绝未知 action。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    with pytest.raises(SkeinError, match="未知 design 动作"):
        sk.artifacts.design(_ns(id="feat-x", action="unknown"))



def test_query_ready_filters_by_deps(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ready 只出待处理且前置全完成的 task。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    _create(sk, "feat-x")
    sk.lifecycle.deps(_ns(id="feat-x", set="base-api"))
    out = sk.query.ready(_ns())
    assert [t["id"] for t in out["tasks"]] == ["base-api"]


def test_query_list_with_open_status(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """list --status=open = plan 阶段 (仅待处理); unfinished = 全部未完成。"""
    import skeinlib.core.workspace as ws_module
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _create(sk, "feat-done")
    _create(sk, "feat-plan")
    t = _load(ws, "feat-x")
    t["status"] = TaskStatus.ACTIVE
    ws_module.Workspace().store.save(t)
    t = _load(ws, "feat-done")
    t["status"] = TaskStatus.DONE
    ws_module.Workspace().store.save(t)
    # open 只剩待处理 (active/done 均不在)
    assert {x["id"] for x in sk.query.list_(_ns(status="open"))["tasks"]} == {"feat-plan"}
    # unfinished = 非done 全部
    assert {x["id"] for x in sk.query.list_(_ns(status="unfinished"))["tasks"]} == {"feat-x", "feat-plan"}
    # 阶段别名: plan/exec 与 pending/active 同义
    assert {x["id"] for x in sk.query.list_(_ns(status="plan"))["tasks"]} == {"feat-plan"}
    assert {x["id"] for x in sk.query.list_(_ns(status="exec"))["tasks"]} == {"feat-x"}


def test_query_list_with_all_status(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """list --status=all 不筛选状态。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _create(sk, "feat-y")
    out = sk.query.list_(_ns(status="all"))
    assert len(out["tasks"]) == 2


def test_query_list_with_comma_statuses(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """list --status 支持逗号分隔的多状态。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _create(sk, "feat-y")
    t = _load(ws, "feat-y")
    t["status"] = TaskStatus.ACTIVE
    import skeinlib.core.workspace as ws_module
    ws_module.Workspace().store.save(t)
    out = sk.query.list_(_ns(status="pending,active"))
    assert {t["id"] for t in out["tasks"]} == {"feat-x", "feat-y"}


def test_query_status_with_unknown_sid(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """status --sid 指向不存在的 subtask 时报错并列出现有 sid。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="subtask 不存在.*现有.*sub-a"):
        sk.query.status(_ns(tid="feat-x", sid="ghost"))


def test_query_brief_includes_repos_when_wt_enabled(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_brief 在 worktree 启用时包含 repos 字段。"""
    # 启用 worktree
    cfg = ws / ".skein" / "config.yaml"
    txt = cfg.read_text(encoding="utf-8")
    cfg.write_text(txt.replace("enabled: false", "enabled: true"))
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _confirm(sk, ws, "feat-x")
    brief = sk.query.status(_ns(tid="feat-x", sid=None))["task"]
    assert "repos" in brief


# ── admin: init / config / board ─────────────────────────────────────────────────
def test_admin_init_creates_directories_and_config(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """init 创建必需目录和配置文件。"""
    monkeypatch.chdir(ws)
    sk = Skein()
    out = sk.admin.init(_ns())
    assert out["initialized"] is True
    assert (ws / ".skein").exists()
    assert (ws / ".skein" / "config.yaml").exists()


def test_admin_config_reset(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config reset 重置为默认配置。"""
    sk = _skein(ws, monkeypatch)
    out = sk.admin.config_cmd(_ns(action="reset", json=False))
    assert out["reset"] is True
    assert "config" in out


def test_admin_config_with_json_flag(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config 不带 action 时返回完整配置，json=True 返回 JSON 形态。"""
    sk = _skein(ws, monkeypatch)
    out = sk.admin.config_cmd(_ns(action=None, json=True))
    assert isinstance(out, dict)
    assert "pools" in out


def test_admin_config_set_unknown_key(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """config set 拒绝非法键。"""
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError, match="未知配置键"):
        sk.admin.config_cmd(_ns(action="set", key="unknown.key", value="1"))


def test_admin_board_regenerates_board(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """board 重新生成看板。"""
    sk = _skein(ws, monkeypatch)
    out = sk.admin.board(_ns())
    assert "updated" in out
    assert (ws / ".skein" / "task.md").exists()


def test_admin_clean_with_days(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """clean 可指定天数。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    out = sk.admin.clean(_ns(days=1))
    assert "days" in out


def test_admin_clean_without_days_uses_config(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """clean 不指定天数时使用配置的 retain_days。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    out = sk.admin.clean(_ns(days=None))
    assert "days" in out


# ── lifecycle 边界情况 ────────────────────────────────────────────────────────
def test_confirm_research_blocked(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """confirm 时调研中态被拒绝，需先 plan。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_research(sk, "feat-x", "sub-r")
    sk.lifecycle.research(_ns(id="feat-x"))
    with pytest.raises(SkeinError, match="调研中.*先.*plan"):
        sk.lifecycle.confirm(_ns(id="feat-x", approved=True))


def test_rename_subtask_id_collision(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """改 subtask id 时与现有 sid 冲突报错。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b")
    with pytest.raises(SkeinError, match="sid 已占用"):
        sk.lifecycle.rename(_ns(tid="feat-x", sid="sub-a", id="sub-b", name=None))


def test_del_task_with_missing_worktree_file(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """删除在途 task 时 worktree 文件缺失的处理。"""
    # 启用 worktree
    cfg = ws / ".skein" / "config.yaml"
    txt = cfg.read_text(encoding="utf-8")
    cfg.write_text(txt.replace("enabled: false", "enabled: true"))

    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _confirm(sk, ws, "feat-x")

    # 先让 task 离开在途态，避免 worktree 清理问题
    import skeinlib.core.workspace as ws_module
    t = _load(ws, "feat-x")
    t["status"] = TaskStatus.DONE
    ws_module.Workspace().store.save(t)

    # 手动删除 worktree 目录模拟外部删除
    wt = ws / ".worktrees" / "skein-feat-x"
    if wt.exists():
        import shutil
        shutil.rmtree(wt)

    # 删除 task 应该能处理缺失的 worktree
    out = sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid=None, dry_run=False))
    assert out["deleted"] is True


def test_status_overview_json_and_rich(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                       capsys: pytest.CaptureFixture[str]) -> None:
    """顶层 skein status: JSON 形态 (池/执行中/统计) + rich 自打印返回 None。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b", deps="sub-a")
    import skeinlib.core.workspace as ws_module
    t = _load(ws, "feat-x")
    t["status"] = TaskStatus.ACTIVE
    t["subtasks"][0]["status"] = SubtaskStatus.RUNNING
    t["subtasks"][0]["started"] = 1_700_000_000
    ws_module.Workspace().store.save(t)

    out = sk.query.status_overview(_ns(pretty=False))
    assert out is not None  # pretty=False → JSON dict (mypy: status_overview 返回 dict | None)
    assert out["pool"]["work"] == {"running": 1, "capacity": 2}
    assert out["pool"]["gate"]["running"] == 0
    assert out["tasks"]["by_status"] == {TaskStatus.ACTIVE: 1}
    assert [r["sid"] for r in out["running_subtasks"]] == ["sub-a"]
    assert out["running_subtasks"][0]["tid"] == "feat-x"
    assert out["ready_pending"] == 0  # sub-b 依赖 sub-a 未 done → 不算就绪
    assert out["active_tasks"][0]["id"] == "feat-x"
    # feat-x 已 active → 不在 plan_tasks; 建一个带依赖阻塞的 pending task 验证
    _create(sk, "feat-next", deps="feat-x")
    assert [t["id"] for t in out["plan_tasks"]] == []  # 快照在 feat-next 建立前
    out2 = sk.query.status_overview(_ns(pretty=False))
    assert out2 is not None
    # JSON 形态精简: task 只留 id/name/status
    assert out2["plan_tasks"] == [{"id": "feat-next", "name": "feat-next",
                                   "status": TaskStatus.PENDING}]
    assert set(out2["running_subtasks"][0]) == {"tid", "sid", "name", "status"}
    assert set(out2["active_tasks"][0]) == {"id", "name", "status"}

    # --pretty: 自打印 + 返回 None (cli 不再打 JSON)
    capsys.readouterr()
    assert sk.query.status_overview(_ns(pretty=True)) is None
    rich_out = capsys.readouterr().out
    assert "SKEIN 运行态" in rich_out and "sub-a" in rich_out
    assert "plan 中" in rich_out and "feat-next" in rich_out
