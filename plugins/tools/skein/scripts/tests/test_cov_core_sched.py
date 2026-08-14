"""core 三件套 (scheduling / lifecycle / query) 的进程内单元测试 — 补覆盖率缺口。

全部直接 `import` 实现层跑 (不起子进程): `ws` fixture 给隔离临时 git 仓, `monkeypatch.chdir`
进去后 `Skein()` 构造出真实工作区门面, 再拿 `argparse.Namespace` 直调各命令方法 —— 与 CLI
dispatch 走的是同一批入口 (见 cli.py 的 dispatch 表指向 `sk.lifecycle.* / sk.scheduler.* /
sk.query.*`), 只是省掉了进程启动。

状态串一律取 `skeinlib.task.model` 的 `TaskStatus` / `SubtaskStatus` 枚举 (落盘是英文枚举值,
中文只是看板展示名), 手写中文串会造出永假的死分支。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import run_git  # noqa: E402
from skeinlib.core.commands import Skein  # noqa: E402
from skeinlib.core.scheduling import (_dispatch_hints, _hint_prompt,  # noqa: E402
                                      _report_mismatches)
from skeinlib.task.model import SubtaskPhase, SubtaskStatus, TaskStatus  # noqa: E402
from skeinlib.utils.errors import SkeinError  # noqa: E402


# ── 工装 ─────────────────────────────────────────────────────────────────────
def _skein(ws: Path, monkeypatch: pytest.MonkeyPatch) -> Skein:
    """进入临时仓并构造门面 (Workspace 靠 cwd 的 git rev-parse 认根)。"""
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
            deps="", check="", skills="", phase=None, repo=None)
    for k, v in over.items():
        setattr(a, k, v)
    return sk.scheduler.subtask(a)


def _sub_act(sk: Skein, action: str, tid: str, sid: str = "", **over: Any) -> dict[str, Any]:
    a = _ns(action=action, tid=tid, sid=sid, passed="", note=None)
    for k, v in over.items():
        setattr(a, k, v)
    return sk.scheduler.subtask(a)


def _fill_prd(ws: Path, tid: str) -> None:
    """写齐 prd 六章 + design 接缝 (无 TODO 占位), 过 confirm 的 planning 硬门。"""
    d = ws / ".skein" / "task" / tid
    (d / "prd.md").write_text(
        f"# {tid} — PRD\n\n"
        "## 目标\n- 解决 X\n\n## 边界\n- 范围内: a\n\n"
        "## User Stories\n1. As a user, I want X, so that Y\n\n"
        "## 验收标准\n- 用例通过\n\n## 验证方式\n- 跑 pytest, 全绿即 pass\n\n"
        "## Testing Decisions\n- 只测外部行为\n\n## 索引\n- design.md\n", encoding="utf-8")
    (d / "design.md").write_text(
        f"# {tid} — 详细设计\n\n## 测试接缝 (seam)\n- [x] API 层\n", encoding="utf-8")


def _confirm(sk: Skein, ws: Path, tid: str, **over: Any) -> dict[str, Any]:
    """填齐 planning 硬门后过人审门 → 进行中。"""
    _fill_prd(ws, tid)
    sk.lifecycle.estimate(_ns(id=tid, set="8"))
    a = _ns(id=tid, approved=True, unattended=False, summary=False)
    for k, v in over.items():
        setattr(a, k, v)
    return sk.lifecycle.confirm(a)


def _active_task(sk: Skein, ws: Path, tid: str = "feat-x", sid: str = "sub-a",
                 **sub_over: Any) -> str:
    """建一个「进行中 + 1 个待处理 subtask」的 task。"""
    _create(sk, tid)
    _add_sub(sk, tid, sid, **sub_over)
    _confirm(sk, ws, tid)
    return tid


def _cfg_sub(ws: Path, old: str, new: str) -> None:
    p = ws / ".skein" / "config.yaml"
    txt = p.read_text(encoding="utf-8")
    assert old in txt, f"config.yaml 无 {old!r}, 工装失效"
    p.write_text(txt.replace(old, new, 1), encoding="utf-8")


def _enable_wt(ws: Path) -> None:
    _cfg_sub(ws, "enabled: false", "enabled: true")


def _load(ws: Path, tid: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(
        (ws / ".skein" / "task" / tid / "task.json").read_text(encoding="utf-8"))
    return data


def _write(ws: Path, t: dict[str, Any]) -> None:
    (ws / ".skein" / "task" / t["id"] / "task.json").write_text(
        json.dumps(t, ensure_ascii=False), encoding="utf-8")


# ── query.current / ready / status / list ────────────────────────────────────
def test_query_current_lists_only_active(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """current 只出在途 task; worktree 禁用时不带 worktree 列。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _create(sk, "feat-idle")  # 待处理, 不该出现
    out = sk.query.current(_ns())
    assert [t["id"] for t in out["tasks"]] == ["feat-x"]
    assert "worktree" not in out["tasks"][0]


def test_query_current_shows_worktree_col_when_enabled(ws: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """worktree.enabled=true 时 current 带 worktree 列。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.query.current(_ns())
    assert out["tasks"][0]["worktree"] == ".worktrees/skein-feat-x"


def test_query_ready_excludes_dep_unfinished(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """ready 只出「待处理且前置全完成」的 task。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    _create(sk, "feat-x", deps="base-api")
    ids = [t["id"] for t in sk.query.ready(_ns())["tasks"]]
    assert ids == ["base-api"], "前置未完成的 feat-x 不该进 ready"


def test_query_status_subtask_and_unknown_sid(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """status --sid 投影单个 subtask; 未知 sid 报错并列出现有 sid。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    out = sk.query.status(_ns(tid="feat-x", sid="sub-a"))
    assert out["subtask"]["sid"] == "sub-a"
    with pytest.raises(SkeinError, match="sub-a"):
        sk.query.status(_ns(tid="feat-x", sid="nope"))


def test_query_status_brief_counts_and_ready(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """不带 sid 走 _brief: 四态计数 + ready 判定 + priority 兜底。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    for sid in ("sub-a", "sub-b"):
        _add_sub(sk, "feat-x", sid)
    _confirm(sk, ws, "feat-x")
    _sub_act(sk, "done", "feat-x", "sub-a")
    brief = sk.query.status(_ns(tid="feat-x", sid=None))["task"]
    assert brief["subs"] == [1, 0, 1, 0], "done/running/pending/failed 计数"
    assert brief["ready"] is False, "已进行中的 task 不算 ready"
    assert brief["priority"] == "normal"


def test_query_list_status_filters(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """list --status: all 不筛 / open 排除已完成 / 具体态精确筛 / 非法态报错。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _create(sk, "feat-idle")
    all_ids = {t["id"] for t in sk.query.list_(_ns(status="all"))["tasks"]}
    assert all_ids == {"feat-x", "feat-idle"}
    assert {t["id"] for t in sk.query.list_(_ns(status="open"))["tasks"]} == all_ids
    only = sk.query.list_(_ns(status=TaskStatus.ACTIVE))["tasks"]
    assert [t["id"] for t in only] == ["feat-x"]
    with pytest.raises(SkeinError, match="未知 status"):
        sk.query.list_(_ns(status="进行中了没"))


# ── _dispatch_hints / _hint_prompt ───────────────────────────────────────────
def _wt_task(tid: str, wts: list[dict[str, Any]]) -> dict[str, Any]:
    return {"id": tid, "name": tid, "worktrees": wts, "worktree": wts[0]["wt"] if wts else None}


def test_hints_executor_carries_repo_and_workdir(tmp_path: Path) -> None:
    """单 worktree + 声明 repo 的 exec subtask: hint 带 workdir/repo/workdir_kind 与成品 prompt。"""
    t = _wt_task("feat-x", [{"repo": "svc", "wt": "svc/.worktrees/skein-feat-x"}])
    hints = _dispatch_hints(claimed=[{"tid": "feat-x", "sid": "sub-a", "repo": "svc",
                                      "phase": SubtaskPhase.EXEC}],
                            tasks={"feat-x": t}, root=tmp_path)
    assert hints[0]["agent"] == "skein:skein-executor"
    assert hints[0]["workdir_kind"] == "worktree"
    # hint 不含 isolation — Agent 工具只传 subagent_type + prompt，workdir 已在 prompt 里
    assert "isolation" not in hints[0]
    assert hints[0]["repo"] == "svc"
    assert hints[0]["workdir"] == str(tmp_path / "svc/.worktrees/skein-feat-x")
    p = json.loads(hints[0]["prompt"])
    assert p["worktree"] == "on" and p["sid"] == "sub-a" and p["repo"] == "svc"
    assert "subtask show feat-x sub-a" in p["action"]


def test_hints_research_phase_routes_to_researcher(tmp_path: Path) -> None:
    """phase=research 的 subtask 派 researcher (非 executor)。"""
    hints = _dispatch_hints(claimed=[{"tid": "feat-x", "sid": "sub-r",
                                      "phase": SubtaskPhase.RESEARCH}])
    assert hints[0]["agent"] == "skein:skein-researcher"


def test_hints_multi_repo_subtask_missing_repo(tmp_path: Path) -> None:
    """多 worktree 但 subtask 没声明 repo → 标 mismatch, 且不生成 prompt (无处可派)。"""
    t = _wt_task("feat-x", [{"repo": "a", "wt": "a/w"}, {"repo": "b", "wt": "b/w"}])
    hints = _dispatch_hints(claimed=[{"tid": "feat-x", "sid": "sub-a", "repo": None}],
                            tasks={"feat-x": t}, root=tmp_path)
    assert hints[0]["mismatch"] == "multi_repo_subtask_missing_repo"
    assert "prompt" not in hints[0]


def test_hints_invalid_workdir_when_repo_unknown(tmp_path: Path) -> None:
    """subtask 声明的 repo 没有对应 worktree → invalid_workdir + 原始错误文案。"""
    t = _wt_task("feat-x", [{"repo": "a", "wt": "a/w"}])
    hints = _dispatch_hints(claimed=[{"tid": "feat-x", "sid": "sub-a", "repo": "ghost"}],
                            tasks={"feat-x": t}, root=tmp_path)
    assert hints[0]["mismatch"] == "invalid_workdir"
    assert "ghost" in hints[0]["error"]


def test_hints_checker_multi_workdirs(tmp_path: Path) -> None:
    """多子 git 的 check: hint 给 workdirs[] 逐仓核查, prompt 内嵌 JSON 列表。"""
    t = _wt_task("feat-x", [{"repo": "a", "wt": "a/w"}, {"repo": "b", "wt": "b/w"}])
    hints = _dispatch_hints(checked=["feat-x"], tasks={"feat-x": t}, root=tmp_path)
    assert hints[0]["agent"] == "skein:skein-checker"
    assert hints[0]["workdirs"] == [str(tmp_path / "a/w"), str(tmp_path / "b/w")]
    assert json.loads(hints[0]["prompt"])["workdirs"] == hints[0]["workdirs"]


def test_hints_checker_multi_workdirs_error_aggregated(tmp_path: Path) -> None:
    """多 worktree 里有条目缺 repo → errors[] 汇总, 整条 hint 标 mismatch。"""
    t = _wt_task("feat-x", [{"repo": "a", "wt": "a/w"}, {"wt": "b/w"}])
    hints = _dispatch_hints(checked=["feat-x"], tasks={"feat-x": t}, root=tmp_path)
    assert hints[0]["mismatch"] == "invalid_workdir"
    assert len(hints[0]["errors"]) == 1


def test_hints_checker_single_worktree_never_mismatches(tmp_path: Path) -> None:
    """worktree ≤1 的 check hint 恒能解析出 workdir。

    钉的是 scheduling.py:116-119 那条 `except SkeinError` 分支不可达: 该路径必然
    `len(wts) <= 1`, 而 workdir_for 只在 `repo is None and len(wts) > 1` 时抛
    SkeinError —— 条件互斥。见报告「不可达分支」。
    """
    for wts in ([], [{"repo": ".", "wt": "w"}]):
        t = _wt_task("feat-x", wts)
        hints = _dispatch_hints(checked=["feat-x"], tasks={"feat-x": t}, root=tmp_path)
        assert "mismatch" not in hints[0]
        assert hints[0]["workdir"]


def test_hints_finisher_runs_at_repo_root(tmp_path: Path) -> None:
    """finishing 的 hint 固定在仓库根 (合并要在主仓做), workdir_kind=none。"""
    hints = _dispatch_hints(finishing=["feat-x"], tasks={"feat-x": _wt_task("feat-x", [])},
                            root=tmp_path)
    assert hints[0]["agent"] == "skein:skein-finisher"
    assert hints[0]["workdir_kind"] == "none"
    assert "isolation" not in hints[0]
    assert hints[0]["workdir"] == str(tmp_path)
    p = json.loads(hints[0]["prompt"])
    assert p["worktree"] == "off"  # 合并必须在主仓做, finisher 恒 off
    assert "task finish feat-x" in p["action"]


def test_hint_prompt_falls_back_to_unknown_workdir() -> None:
    """既无 workdir 也无 workdirs 时 prompt 用 <未知> 占位, 不 KeyError。"""
    p = json.loads(_hint_prompt({"agent": "skein:skein-checker", "tid": "feat-x"}))
    assert p["workdirs"] == ["<未知>"]


def test_hint_prompt_is_json_and_carries_worktree_switch(ws: Path,
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    """worktree 启用/禁用两种 config 下, prompt 都是可 json.loads 的单行 JSON,
    `worktree` 字段分别为 on/off —— 显式下发, 不留给 agent 从路径形态反推。"""
    for enabled, want in ((True, "on"), (False, "off")):
        if enabled:
            _cfg_sub(ws, "enabled: false", "enabled: true")
        else:
            _cfg_sub(ws, "enabled: true", "enabled: false")
        sk = _skein(ws, monkeypatch)
        tid = f"feat-{want}"
        _active_task(sk, ws, tid, sid="sub-a")
        hint = sk.scheduler.subtask(_ns(action="claim", tid=tid))["next"][0]
        assert "\n" not in hint["prompt"]
        p = json.loads(hint["prompt"])
        assert p["worktree"] == want, p
        assert p["tid"] == tid and p["sid"] == "sub-a" and p["workdir"]


# ── _report_mismatches ───────────────────────────────────────────────────────
def test_report_mismatches_flags_orphan_research_report(ws: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    """调研报告已落盘但 research subtask 还没收尾 → 报 mismatch 供 main 介入。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-r", phase=SubtaskPhase.RESEARCH)
    sk.lifecycle.research(_ns(id="feat-x"))
    rd = ws / ".skein" / "task" / "feat-x" / "research"
    rd.mkdir(parents=True, exist_ok=True)
    (rd / "sub-r.md").write_text("# 调研结论\n", encoding="utf-8")
    assert _report_mismatches(sk) == [{"tid": "feat-x", "sid": "sub-r",
                                       "reason": "research_report_exists_subtask_not_finished"}]
    # subtask done 后不再报
    _sub_act(sk, "done", "feat-x", "sub-r")
    assert _report_mismatches(sk) == []


# ── _ready / _global_ready / 空批原因 ────────────────────────────────────────
def test_subtask_ready_blocked_by_task_deps(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """前置 task 未完成 → 该 task 整体不出活 (依赖门在取活时判)。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    _active_task(sk, ws, "feat-x")
    t = _load(ws, "feat-x")
    t["deps"] = ["base-api"]
    _write(ws, t)
    out = _sub_act(sk, "ready", "feat-x")
    assert out["ready"] == []
    assert out["reason"] == "dependencies_blocked"


def test_global_ready_skips_running_and_done(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """非 pending/failed 的 subtask 不进全局候选池 (running 只占槽)。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    for sid in ("sub-a", "sub-b"):
        _add_sub(sk, "feat-x", sid)
    _confirm(sk, ws, "feat-x")
    _sub_act(sk, "done", "feat-x", "sub-a")
    batch = sk.scheduler._global_ready()
    assert [s["sid"] for _, s in batch] == ["sub-b"]


def test_empty_batch_reason_work_pool_full(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """running 占满 work 池 → 空批原因 work_pool_full (文案含 running/上限)。"""
    _cfg_sub(ws, "work: 2", "work: 1")
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    for sid in ("sub-a", "sub-b"):
        _add_sub(sk, "feat-x", sid)
    _confirm(sk, ws, "feat-x")
    _sub_act(sk, "start", "feat-x", "sub-a")
    info = sk.scheduler._empty_batch_info()
    assert info["reason"] == "work_pool_full"
    assert "1/1" in sk.scheduler._empty_batch_msg()


def test_empty_batch_reason_no_pending(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """全部 subtask 已 done → no_pending_subtask。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "done", "feat-x", "sub-a")
    assert sk.scheduler._empty_batch_info()["reason"] == "no_pending_subtask"
    assert "无待处理 subtask" in sk.scheduler._empty_batch_msg()


def test_empty_batch_reason_task_dep_blocked(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """有 pending subtask 但前置 task 没完成 → task_dep_blocked。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    _active_task(sk, ws, "feat-x")
    t = _load(ws, "feat-x")
    t["deps"] = ["base-api"]
    _write(ws, t)
    assert sk.scheduler._empty_batch_info()["reason"] == "task_dep_blocked"
    assert "前置 task 未完成" in sk.scheduler._empty_batch_msg()


def test_empty_batch_reason_subtask_dep_blocked(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """depends_on 指向的 subtask 还在跑 → subtask_dep_blocked。"""
    _cfg_sub(ws, "work: 2", "work: 1")
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b", deps="sub-a")
    _confirm(sk, ws, "feat-x")
    t = _load(ws, "feat-x")
    t["subtasks"][0]["status"] = SubtaskStatus.PENDING
    _write(ws, t)
    # sub-a pending、sub-b 依赖 sub-a: 槽没满但 sub-b 被 depends_on 卡住
    _cfg_sub(ws, "work: 1", "work: 2")
    t = _load(ws, "feat-x")
    t["subtasks"][0]["status"] = SubtaskStatus.RUNNING
    t["subtasks"][0]["sid"] = "sub-a"
    _write(ws, t)
    info = sk.scheduler._empty_batch_info()
    assert info["reason"] == "subtask_dep_blocked"
    assert "依赖" in sk.scheduler._empty_batch_msg()


def test_empty_batch_reason_dep_failed(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """依赖链上有 FAILED subtask → dep_failed, 并列出失败 sid。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b", deps="sub-a")
    _confirm(sk, ws, "feat-x")
    _sub_act(sk, "start", "feat-x", "sub-a")
    _sub_act(sk, "fail", "feat-x", "sub-a", note="炸了")
    info = sk.scheduler._empty_batch_info()
    assert info["reason"] == "dep_failed"
    assert info["failed_deps"] == ["sub-a"]
    assert "sub-a" in sk.scheduler._empty_batch_msg()


# ── claim exec / check / flow ────────────────────────────────────────────────
def test_claim_exec_preview_task_filter_no_ready(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--dry-run --task 指向没有就绪活的 task → empty.reason=task_filter_no_ready。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    data = sk.scheduler.claim(_ns(phase="exec", dry_run=True, task="other-task"))["exec"]
    assert data["count"] == 0
    assert data["empty"] == {"reason": "task_filter_no_ready", "task": "other-task"}


def test_claim_exec_preview_reports_invalid_workdir(ws: Path,
                                                    monkeypatch: pytest.MonkeyPatch) -> None:
    """subtask 的 repo 在 task worktrees 里找不到 → 预览条目和 mismatches 双双标出。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    t = _load(ws, "feat-x")
    t["worktrees"] = [{"repo": "a", "wt": "a/w", "branch": "skein/feat-x", "merged": False}]
    t["subtasks"][0]["repo"] = "ghost"
    _write(ws, t)
    data = sk.scheduler.claim(_ns(phase="exec", dry_run=True, task=None))["exec"]
    assert data["ready"][0]["mismatch"] == "invalid_workdir"
    assert data["mismatches"][0]["reason"] == "invalid_workdir"


def test_claim_exec_no_ready_returns_empty_reason(ws: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """真认领但无活可派 → claimed 空 + 结构化空批原因。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    out = sk.scheduler.claim(_ns(phase="exec", dry_run=False, task=None))
    assert out["count"] == 0
    assert out["reason"]["reason"] == "no_pending_subtask"


def test_claim_exec_task_filter_no_ready(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--task 过滤后没剩下活 → reason=task_filter_no_ready (字符串形态)。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.scheduler.claim(_ns(phase="exec", dry_run=False, task="nope"))
    assert out["reason"] == "task_filter_no_ready"


def test_claim_exec_marks_running_and_gives_hints(ws: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """认领整批标 running + 落 started 时刻 + 回派发提示。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.scheduler.claim(_ns(phase="exec", dry_run=False, task="feat-x"))
    assert out["count"] == 1
    assert out["next"][0]["agent"] == "skein:skein-executor"
    s = _load(ws, "feat-x")["subtasks"][0]
    assert s["status"] == SubtaskStatus.RUNNING and s["started"]


def test_claim_exec_dry_run_via_claim_exec_path(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`_claim_exec` 内部再撞上 dry_run 也要退回预览 (不改状态)。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.scheduler._claim_exec(_ns(dry_run=True, task=None))
    assert out["claim_command"] == "skein claim exec"
    assert _load(ws, "feat-x")["subtasks"][0]["status"] == SubtaskStatus.PENDING


def test_claim_no_phase_returns_both_pools(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """不传 phase = exec + check 各取一次, 供主循环一次看两池。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.scheduler.claim(_ns(phase=None, dry_run=False, task=None))
    assert set(out) == {"exec", "check"}
    assert out["exec"]["count"] == 1


def test_claim_dry_run_no_phase_previews_both(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--dry-run 不传 phase: 两池都只读预览。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.scheduler.claim(_ns(phase=None, dry_run=True, task=None))
    assert out["dry_run"] is True and out["phase"] == "all"
    assert out["check"]["empty"]["reason"] == "no_check_or_finishing_ready"


def test_claim_check_empty(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """没有可验收/可收尾的 task → check 认领空批。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.scheduler.claim(_ns(phase="check", dry_run=False, task=None))
    assert out["checked"] == [] and out["empty"]["reason"] == "no_check_or_finishing_ready"


def test_claim_check_dry_run_preview(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """全 subtask done 的进行中 task 在预览里排队进「检查中」, 但状态不动。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "done", "feat-x", "sub-a")
    out = sk.scheduler.claim(_ns(phase="check", dry_run=True, task=None))["check"]
    assert out["to_check"][0]["next_status"] == TaskStatus.CHECK
    assert _load(ws, "feat-x")["status"] == TaskStatus.ACTIVE


def test_claim_check_advances_to_check_then_finishing(ws: Path,
                                                      monkeypatch: pytest.MonkeyPatch) -> None:
    """两路: 进行中→检查中, 再来一次 检查中→收尾中 (占 gate 槽)。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "done", "feat-x", "sub-a")
    first = sk.scheduler.claim(_ns(phase="check", dry_run=False, task=None))
    assert first["checked"] == ["feat-x"]
    assert _load(ws, "feat-x")["status"] == TaskStatus.CHECK
    second = sk.scheduler.claim(_ns(phase="check", dry_run=False, task=None))
    assert second["finishing"] == ["feat-x"]
    assert second["next"][0]["agent"] == "skein:skein-finisher"
    assert _load(ws, "feat-x")["status"] == TaskStatus.FINISHING


def test_claim_check_reports_finishing_error_when_gate_full(
        ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """gate 池满 → 该 task 留在检查中, 错误进 errors[] 而非中断整批。"""
    _cfg_sub(ws, "gate: 3", "gate: 1")
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "done", "feat-x", "sub-a")
    sk.lifecycle.check(_ns(id="feat-x"))
    _active_task(sk, ws, "feat-y", "sub-y")
    _sub_act(sk, "done", "feat-y", "sub-y")
    sk.lifecycle.check(_ns(id="feat-y"))  # 两个都在检查中 → gate 已被对方占满
    out = sk.scheduler.claim(_ns(phase="check", dry_run=False, task=None))
    assert out["finishing"] == []
    assert {e["action"] for e in out["errors"]} == {"finishing"}


def test_check_candidates_skips_task_without_subtask(ws: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    """普通 task 没有 subtask 时不进 check 候选 (空 task 不算全 done)。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    t = _load(ws, "feat-x")
    t["subtasks"] = []
    _write(ws, t)
    assert sk.scheduler._check_candidates() == ([], [])


def test_flow_wraps_claim(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """flow = 一次调度 tick, 把 claim 结果原样包进 result。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.scheduler.flow(_ns(task=None, dry_run=True))
    assert out["action"] == "flow run" and out["dry_run"] is True
    assert out["result"]["exec"]["count"] == 1


# ── subtask 子命令 ───────────────────────────────────────────────────────────
def test_subtask_add_rejects_duplicate_sid(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="已存在"):
        _add_sub(sk, "feat-x", "sub-a")


def test_subtask_add_repo_must_be_declared(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--repo 必须在 task repos 里声明过; 多 repo 时又必须显式给 --repo。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    with pytest.raises(SkeinError, match="未声明 repo"):
        _add_sub(sk, "feat-x", "sub-a", repo="svc")
    t = _load(ws, "feat-x")
    t["repos"] = ["a", "b"]
    _write(ws, t)
    with pytest.raises(SkeinError, match="必须声明 --repo"):
        _add_sub(sk, "feat-x", "sub-a")


def test_subtask_add_rejects_nonpositive_estimate(ws: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    with pytest.raises(SkeinError, match="须为正数"):
        _add_sub(sk, "feat-x", "sub-a", estimate="0")


def test_subtask_list_and_show(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a", check="第一条; 第二条")
    listed = _sub_act(sk, "list", "feat-x")["subtasks"]
    assert listed[0]["sid"] == "sub-a" and listed[0]["estimate"] == 1
    shown = _sub_act(sk, "show", "feat-x", "sub-a")["subtask"]
    assert shown["acceptance"] == ["第一条", "第二条"]


def test_subtask_claim_reports_invalid_workdir(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """单 task claim 路径同样要把 workdir 解析失败标成 mismatch, 而不是整条命令炸掉。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    t = _load(ws, "feat-x")
    t["worktrees"] = [{"repo": "a", "wt": "a/w", "branch": "skein/feat-x", "merged": False},
                      {"repo": "b", "wt": "b/w", "branch": "skein/feat-x", "merged": False}]
    _write(ws, t)
    out = _sub_act(sk, "claim", "feat-x")
    assert out["claimed"][0]["mismatch"] == "invalid_workdir"
    assert out["mismatches"][0]["sid"] == "sub-a"


def test_subtask_start_requires_active_task(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """待处理 task 的 subtask 不能 start — 否则绕过 confirm 人审门。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="过人审门"):
        _sub_act(sk, "start", "feat-x", "sub-a")


def test_subtask_start_blocked_by_task_deps(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """单点 start 也要过 task 级依赖门 (与调度侧同一条规则)。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    _active_task(sk, ws, "feat-x")
    t = _load(ws, "feat-x")
    t["deps"] = ["base-api"]
    _write(ws, t)
    with pytest.raises(SkeinError, match="前置 task 未完成"):
        _sub_act(sk, "start", "feat-x", "sub-a")


def test_subtask_start_in_research_only_research_phase(ws: Path,
                                                       monkeypatch: pytest.MonkeyPatch) -> None:
    """调研中 task 只放行 phase=research 的 subtask。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-r", phase=SubtaskPhase.RESEARCH)
    _add_sub(sk, "feat-x", "sub-a")
    sk.lifecycle.research(_ns(id="feat-x"))
    with pytest.raises(SkeinError, match="只能 start phase=research"):
        _sub_act(sk, "start", "feat-x", "sub-a")
    assert _sub_act(sk, "start", "feat-x", "sub-r")["status"] == SubtaskStatus.RUNNING


def test_subtask_start_rejects_wrong_status_and_undone_deps(
        ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """已 running 的不能再 start; depends_on 未完成的也拦。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b", deps="sub-a")
    _confirm(sk, ws, "feat-x")
    _sub_act(sk, "start", "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="只能 start 待处理/失败"):
        _sub_act(sk, "start", "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="依赖未完成"):
        _sub_act(sk, "start", "feat-x", "sub-b")


def test_subtask_start_rejects_when_pool_full(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """单 task 内 running 数达 pools.work → 拒绝再 start。"""
    _cfg_sub(ws, "work: 2", "work: 1")
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b")
    _confirm(sk, ws, "feat-x")
    _sub_act(sk, "start", "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="并发已满"):
        _sub_act(sk, "start", "feat-x", "sub-b")


def test_subtask_check_marks_acceptance(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """check --passed: all/none/序号列表 三种写法 + 越界报错。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a", check="一; 二; 三")
    assert _sub_act(sk, "check", "feat-x", "sub-a", passed="all")["accepted"] == 3
    assert _sub_act(sk, "check", "feat-x", "sub-a", passed="none")["accepted"] == 0
    out = _sub_act(sk, "check", "feat-x", "sub-a", passed="1,3")
    # pending 档的 pct 是「状态区间 [0,5] 内按验收完成度线性插值」, 2/3 → int(5*2/3)=3
    assert out["accepted"] == 2 and out["pct"] == 3
    with pytest.raises(SkeinError, match="越界"):
        _sub_act(sk, "check", "feat-x", "sub-a", passed="9")


def test_subtask_check_rejects_check_flag_and_missing_passed(ws: Path,
                                                             monkeypatch: pytest.MonkeyPatch) -> None:
    """check 走错入口必须报错 —— 静默走完只会把已勾的验收清零还回 accepted 0 装成功。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a", check="一; 二; 三")
    _sub_act(sk, "check", "feat-x", "sub-a", passed="all")
    with pytest.raises(SkeinError, match="不收 --check"):
        _sub_act(sk, "check", "feat-x", "sub-a", passed="", check="一")
    with pytest.raises(SkeinError, match="缺 --passed"):
        _sub_act(sk, "check", "feat-x", "sub-a", passed="")
    assert _load(ws, "feat-x")["subtasks"][0]["acceptance_done"] == [1, 2, 3]


def test_subtask_done_rejects_passed(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """done 语义是验收全过, 收 --passed 只会让调用方以为自己在挑条目勾。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "start", "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="不收 --passed"):
        _sub_act(sk, "done", "feat-x", "sub-a", passed="1")


def test_subtask_fail_records_note(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "start", "feat-x", "sub-a")
    assert _sub_act(sk, "fail", "feat-x", "sub-a", note="编译炸了")["status"] == SubtaskStatus.FAILED
    assert _load(ws, "feat-x")["subtasks"][0]["note"] == "编译炸了"


def test_subtask_done_clears_stale_fail_note(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """重试成功后 fail 的备注必须消失, 否则看板上 done 的 subtask 挂着已失效的失败原因。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "start", "feat-x", "sub-a")
    _sub_act(sk, "fail", "feat-x", "sub-a", note="隔离目录不对")
    _sub_act(sk, "start", "feat-x", "sub-a")
    _sub_act(sk, "done", "feat-x", "sub-a")
    assert "note" not in _load(ws, "feat-x")["subtasks"][0]


# ── lifecycle: create 校验 ───────────────────────────────────────────────────
def test_create_rejects_non_slug_and_code_id(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError, match="非法 id"):
        _create(sk, "Feat_X")
    with pytest.raises(SkeinError, match="id 须可读"):
        _create(sk, "t01")


def test_create_repos_requires_worktree_enabled(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError, match="worktree.enabled=false"):
        _create(sk, "feat-x", repos="svc")


def test_create_rejects_bad_estimate(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError, match="预计工时非法"):
        _create(sk, "feat-x", estimate="一天半")


def test_create_like_clones_planning(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--like: 复制 prd/design + subtask 骨架, 状态与执行期留痕全部重置。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "cron-src", estimate="4")
    _add_sub(sk, "cron-src", "sub-a")
    _fill_prd(ws, "cron-src")
    t = _load(ws, "cron-src")
    t["subtasks"][0].update({"status": SubtaskStatus.DONE, "note": "上轮备注",
                             "acceptance_done": [1], "finished": 123})
    _write(ws, t)
    out = _create(sk, "cron-run2", like="cron-src")
    assert out["cloned_from"] == "cron-src"
    new = _load(ws, "cron-run2")
    assert new["estimate"] == 4, "src 的 estimate 跟着继承"
    s = new["subtasks"][0]
    assert s["status"] == SubtaskStatus.PENDING and s["finished"] is None
    assert "note" not in s and s["acceptance_done"] == []
    assert "## 目标" in (ws / ".skein" / "task" / "cron-run2" / "prd.md").read_text(encoding="utf-8")


# ── lifecycle: 计划字段编辑 ─────────────────────────────────────────────────
def test_repos_get_set_and_gates(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """repos: 查询 / worktree 禁用时拒设 / confirm 后拒改 / 正常设。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    assert sk.lifecycle.repos(_ns(id="feat-x", set=None))["repos"] == []
    with pytest.raises(SkeinError, match="worktree 禁用"):
        sk.lifecycle.repos(_ns(id="feat-x", set="svc"))
    _enable_wt(ws)
    assert sk.lifecycle.repos(_ns(id="feat-x", set="svc, web/"))["repos"] == ["svc", "web"]
    t = _load(ws, "feat-x")
    t["status"] = TaskStatus.ACTIVE  # confirm 后 (真建 worktree 见 test_activate_makes_worktree_per_declared_repo)
    _write(ws, t)
    with pytest.raises(SkeinError, match="只能在 confirm 前"):
        sk.lifecycle.repos(_ns(id="feat-x", set="svc"))


def test_estimate_get_set_and_gates(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """estimate: 查询给 subtask 合计与 overhead / 非法值 / 非正数 / confirm 后拒改。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a", estimate="2")
    sk.lifecycle.estimate(_ns(id="feat-x", set="5"))
    q = sk.lifecycle.estimate(_ns(id="feat-x", set=None))
    assert (q["estimate"], q["subtask_sum"], q["overhead"]) == (5, 2, 3)
    with pytest.raises(SkeinError, match="预计工时非法"):
        sk.lifecycle.estimate(_ns(id="feat-x", set="半天"))
    with pytest.raises(SkeinError, match="须为正数"):
        sk.lifecycle.estimate(_ns(id="feat-x", set="0"))
    _confirm(sk, ws, "feat-x")
    with pytest.raises(SkeinError, match="只能在 confirm 前"):
        sk.lifecycle.estimate(_ns(id="feat-x", set="9"))


def test_priority_get_and_set(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    assert sk.lifecycle.priority(_ns(id="feat-x", set=None))["priority"] == "normal"
    assert sk.lifecycle.priority(_ns(id="feat-x", set="urgent"))["priority"] == "urgent"


def test_deps_get_set_and_gates(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """deps: 查询 / 自引用 / 不存在 / 成环 / 设成功后不可再改 / confirm 后拒改。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    _create(sk, "feat-x")
    assert sk.lifecycle.deps(_ns(id="feat-x", set=None))["deps"] == []
    with pytest.raises(SkeinError, match="自引用"):
        sk.lifecycle.deps(_ns(id="feat-x", set="feat-x"))
    with pytest.raises(SkeinError, match="前置 task 不存在"):
        sk.lifecycle.deps(_ns(id="feat-x", set="ghost-task"))
    t = _load(ws, "base-api")
    t["deps"] = ["feat-x"]
    _write(ws, t)
    with pytest.raises(SkeinError, match="成环"):
        sk.lifecycle.deps(_ns(id="feat-x", set="base-api"))
    t["deps"] = []
    _write(ws, t)
    assert sk.lifecycle.deps(_ns(id="feat-x", set="base-api"))["deps"] == ["base-api"]
    with pytest.raises(SkeinError, match="既有依赖不可改"):
        sk.lifecycle.deps(_ns(id="feat-x", set="base-api"))


def test_deps_rejected_after_confirm(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    with pytest.raises(SkeinError, match="只能在 confirm 前"):
        sk.lifecycle.deps(_ns(id="feat-x", set="whatever"))


# ── lifecycle: 状态机 ───────────────────────────────────────────────────────
def test_research_and_plan_reject_wrong_status(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """research 只收待处理; plan 只收调研中。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    with pytest.raises(SkeinError, match="只能对待处理"):
        sk.lifecycle.research(_ns(id="feat-x"))
    with pytest.raises(SkeinError, match="只能对调研中"):
        sk.lifecycle.plan(_ns(id="feat-x"))


def test_confirm_summary_returns_review_text(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--summary 只出人审摘要, 不推进状态 (给 AskUserQuestion 用)。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _fill_prd(ws, "feat-x")
    sk.lifecycle.estimate(_ns(id="feat-x", set="8"))
    out = sk.lifecycle.confirm(_ns(id="feat-x", approved=False, unattended=False, summary=True))
    assert "summary" in out
    assert _load(ws, "feat-x")["status"] == TaskStatus.PENDING


def test_confirm_unattended_needs_authorization(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--unattended 未授权 → 拒; config 里开过一次后放行并留痕 confirmed_by。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _fill_prd(ws, "feat-x")
    sk.lifecycle.estimate(_ns(id="feat-x", set="8"))
    with pytest.raises(SkeinError, match="--unattended 未授权"):
        sk.lifecycle.confirm(_ns(id="feat-x", approved=False, unattended=True, summary=False))
    _cfg_sub(ws, "unattended: false", "unattended: true")
    sk.lifecycle.confirm(_ns(id="feat-x", approved=False, unattended=True, summary=False))
    assert _load(ws, "feat-x")["confirmed_by"] == "unattended"


def test_confirm_without_review_is_rejected(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """既没 --approved 也没 --unattended → 人审门直接拒。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _fill_prd(ws, "feat-x")
    sk.lifecycle.estimate(_ns(id="feat-x", set="8"))
    with pytest.raises(SkeinError, match="需用户审核 PRD"):
        sk.lifecycle.confirm(_ns(id="feat-x", approved=False, unattended=False, summary=False))


def test_activate_rejects_repos_when_worktree_disabled_later(
        ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """repos 声明后又把 worktree 关掉 → confirm 时 _activate 兜底拒绝。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x", repos="svc")
    _add_sub(sk, "feat-x", "sub-a", repo="svc")
    _fill_prd(ws, "feat-x")
    sk.lifecycle.estimate(_ns(id="feat-x", set="8"))
    _cfg_sub(ws, "enabled: true", "enabled: false")
    with pytest.raises(SkeinError, match="多子 git 隔离需启用 worktree"):
        sk.lifecycle.confirm(_ns(id="feat-x", approved=True, unattended=False, summary=False))


def test_activate_makes_worktree_per_declared_repo(ws: Path,
                                                   monkeypatch: pytest.MonkeyPatch) -> None:
    """--repos 的每个子 git 各开一个 worktree+分支, worktree 字段是汇总串。"""
    sub = ws / "svc"
    sub.mkdir()
    run_git(sub, "init", "-q")
    run_git(sub, "config", "user.email", "t@t.dev")
    run_git(sub, "config", "user.name", "t")
    (sub / "a.txt").write_text("a\n")
    run_git(sub, "add", "-A")
    run_git(sub, "commit", "-qm", "seed")
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x", repos="svc")
    _add_sub(sk, "feat-x", "sub-a", repo="svc")
    out = _confirm(sk, ws, "feat-x")
    assert out["worktrees"] == [{"repo": "svc", "wt": "svc/.worktrees/skein-feat-x",
                                 "branch": "skein/feat-x", "merged": False}]
    assert (ws / "svc" / ".worktrees" / "skein-feat-x").is_dir()


def test_check_is_idempotent(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """已在检查中的 task 再 check 一次不报错 (checker 自跑本命令的场景)。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _sub_act(sk, "done", "feat-x", "sub-a")
    sk.lifecycle.check(_ns(id="feat-x"))
    assert sk.lifecycle.check(_ns(id="feat-x"))["idempotent"] is True


def test_finishing_rejected_when_gate_full(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """gate 池被别的检查中/收尾中 task 占满 → 拒绝进收尾。"""
    _cfg_sub(ws, "gate: 3", "gate: 1")
    sk = _skein(ws, monkeypatch)
    for tid, sid in (("feat-x", "sub-x"), ("feat-y", "sub-y")):
        _active_task(sk, ws, tid, sid)
        _sub_act(sk, "done", tid, sid)
        sk.lifecycle.check(_ns(id=tid))
    with pytest.raises(SkeinError, match="gate 池已满"):
        sk.lifecycle.finishing(_ns(id="feat-y"))


def _to_finishing(sk: Skein, ws: Path, tid: str, sid: str) -> None:
    _sub_act(sk, "done", tid, sid)
    sk.lifecycle.check(_ns(id=tid))
    sk.lifecycle.finishing(_ns(id=tid))


def test_finish_merges_worktree_and_cleans_branch(ws: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """finish: worktree 内改动被提交并合回主仓, worktree 目录与分支双双清掉。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    wt = ws / ".worktrees" / "skein-feat-x"
    (wt / "feature.txt").write_text("done\n", encoding="utf-8")
    _to_finishing(sk, ws, "feat-x", "sub-a")
    out = sk.lifecycle.finish(_ns(id="feat-x"))
    assert out["status"] == TaskStatus.DONE
    assert (ws / "feature.txt").read_text(encoding="utf-8") == "done\n", "worktree 改动应已合回主仓"
    assert not wt.exists()
    branches = run_git_out(ws, "branch", "--list", "skein/feat-x")
    assert branches.strip() == "", "task 分支应已删除"


def run_git_out(cwd: Path, *args: str) -> str:
    import subprocess
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=True).stdout


def test_finish_reports_merge_conflict_and_keeps_finishing(
        ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """合并冲突 → abort 并保持 finishing 态, 提示解冲突后重跑 (幂等)。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    (ws / ".worktrees" / "skein-feat-x" / "clash.txt").write_text("from-worktree\n", encoding="utf-8")
    (ws / "clash.txt").write_text("from-main\n", encoding="utf-8")
    run_git(ws, "add", "-A")
    run_git(ws, "commit", "-qm", "main side")
    _to_finishing(sk, ws, "feat-x", "sub-a")
    with pytest.raises(SkeinError, match="冲突"):
        sk.lifecycle.finish(_ns(id="feat-x"))
    assert _load(ws, "feat-x")["status"] == TaskStatus.FINISHING


def test_finish_requires_finishing_status(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    with pytest.raises(SkeinError, match="只能 finish 收尾中"):
        sk.lifecycle.finish(_ns(id="feat-x"))


def test_finish_missing_worktree_is_rejected(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """worktree 目录被外部删掉 → 无法确认分支已合并, 拒绝 finish。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    _to_finishing(sk, ws, "feat-x", "sub-a")
    run_git(ws, "worktree", "remove", str(ws / ".worktrees" / "skein-feat-x"), "--force")
    with pytest.raises(SkeinError, match="worktree 缺失"):
        sk.lifecycle.finish(_ns(id="feat-x"))


# ── lifecycle: del / rename ─────────────────────────────────────────────────
def test_del_task_not_found(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError, match="task 不存在"):
        sk.lifecycle.del_(_ns(task_id="ghost", subtask_sid=None, dry_run=False))


def test_del_subtask_dry_run_and_real(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """删单个 subtask: dry-run 不落盘; 真删后剩余数下降; 未知 sid 报错。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b")
    with pytest.raises(SkeinError, match="subtask 不存在"):
        sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid="ghost", dry_run=False))
    dry = sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid="sub-a", dry_run=True))
    assert dry["dry_run"] is True and len(_load(ws, "feat-x")["subtasks"]) == 2
    out = sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid="sub-a", dry_run=False))
    assert out["remaining"] == 1
    assert [s["sid"] for s in _load(ws, "feat-x")["subtasks"]] == ["sub-b"]


def test_del_task_dry_run_lists_worktrees(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """在途 task 的 dry-run 要列出将被销毁的 worktree/分支。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid=None, dry_run=True))
    assert out["worktrees"][0]["branch"] == "skein/feat-x"
    assert (ws / ".skein" / "task" / "feat-x").exists()


def test_del_active_task_destroys_worktree_and_moves_to_trash(
        ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """真删在途 task: 先销 worktree/分支, 再软删进 trash (可恢复)。"""
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    out = sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid=None, dry_run=False))
    assert out["deleted"] is True
    assert not (ws / ".worktrees" / "skein-feat-x").exists()
    assert Path(out["trash_path"]).is_dir()
    assert not (ws / ".skein" / "task" / "feat-x").exists()


def test_del_same_day_twice_overwrites_trash(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """同日重复删同 id → 先清旧 trash 目录再落新的 (免 shutil.move 跨平台行为差异)。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    first = sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid=None, dry_run=False))
    (Path(first["trash_path"]) / "old-marker.txt").write_text("old\n", encoding="utf-8")
    _create(sk, "feat-x")
    second = sk.lifecycle.del_(_ns(task_id="feat-x", subtask_sid=None, dry_run=False))
    assert second["trash_path"] == first["trash_path"]
    assert not (Path(second["trash_path"]) / "old-marker.txt").exists()


def _rename(sk: Skein, tid: str, **over: Any) -> dict[str, Any]:
    a = _ns(tid=tid, sid=None, id=None, name=None)
    for k, v in over.items():
        setattr(a, k, v)
    return sk.lifecycle.rename(a)


def test_rename_requires_an_argument(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    with pytest.raises(SkeinError, match="至少一个"):
        _rename(sk, "feat-x")
    with pytest.raises(SkeinError, match="不可为空"):
        _rename(sk, "feat-x", name="  ")


def test_rename_subtask_id_syncs_depends_on(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """改 sid 时同 task 内别的 subtask 的 depends_on 引用一起改。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b", deps="sub-a")
    out = _rename(sk, "feat-x", sid="sub-a", id="sub-api", name="新名")
    assert out["sid"] == "sub-api" and out["name"] == "新名"
    subs = _load(ws, "feat-x")["subtasks"]
    assert subs[1]["depends_on"] == ["sub-api"]


def test_rename_subtask_errors(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _add_sub(sk, "feat-x", "sub-b")
    with pytest.raises(SkeinError, match="subtask 不存在"):
        _rename(sk, "feat-x", sid="ghost", name="n")
    with pytest.raises(SkeinError, match="sid 已占用"):
        _rename(sk, "feat-x", sid="sub-a", id="sub-b")


def test_rename_task_name_only(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    assert _rename(sk, "feat-x", name="新标题")["name"] == "新标题"
    assert _load(ws, "feat-x")["name"] == "新标题"


def test_rename_task_id_gates(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """改 task id: 在途拒 / 非法 slug 拒 / 代号式拒 / 已占用拒。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    with pytest.raises(SkeinError, match="仅限 confirm 前"):
        _rename(sk, "feat-x", id="feat-y")
    _create(sk, "feat-p")
    _create(sk, "feat-q")
    with pytest.raises(SkeinError, match="非法 id"):
        _rename(sk, "feat-p", id="Feat_Q")
    with pytest.raises(SkeinError, match="id 须可读"):
        _rename(sk, "feat-p", id="t01")
    with pytest.raises(SkeinError, match="id 已占用"):
        _rename(sk, "feat-p", id="feat-q")


def test_rename_task_id_syncs_refs(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """改 id: 目录改名 + branch 更新 + 别 task 的 deps 引用同步。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "base-api")
    _create(sk, "feat-x")
    sk.lifecycle.deps(_ns(id="feat-x", set="base-api"))
    out = _rename(sk, "base-api", id="core-api")
    assert out == {"old_id": "base-api", "new_id": "core-api"}
    assert (ws / ".skein" / "task" / "core-api").is_dir()
    assert not (ws / ".skein" / "task" / "base-api").exists()
    assert _load(ws, "core-api")["branch"] == "skein/core-api"
    assert _load(ws, "feat-x")["deps"] == ["core-api"]


# ── 补充测试：覆盖缺失的分支 ───────────────────────────────────────────────────
def test_empty_batch_msg_full_message(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """测试 _empty_batch_msg 的完整消息路径。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _confirm(sk, ws, "feat-x")
    # 让所有 subtask done 来触发 no_pending 消息
    _sub_act(sk, "done", "feat-x", "sub-a")
    msg = sk.scheduler._empty_batch_msg()
    assert "无待处理 subtask" in msg


def test_create_fails_on_invalid_estimate_format(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """测试 create 时估计工时格式错误的处理。"""
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError, match="预计工时非法"):
        _create(sk, "feat-x", estimate="invalid")


def test_repos_rejected_after_confirm(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """测试 confirm 后拒绝修改 repos。"""
    # 先启用 worktree
    _enable_wt(ws)
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    with pytest.raises(SkeinError, match="只能在 confirm 前"):
        sk.lifecycle.repos(_ns(id="feat-x", set="svc"))


def test_estimate_rejected_after_confirm(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """测试 confirm 后拒绝修改 estimate。"""
    sk = _skein(ws, monkeypatch)
    _active_task(sk, ws, "feat-x")
    with pytest.raises(SkeinError, match="只能在 confirm 前"):
        sk.lifecycle.estimate(_ns(id="feat-x", set="5"))


def test_plan_requires_all_research_subtasks_done(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """测试 plan 时要求所有 research subtask 都完成。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-r", phase=SubtaskPhase.RESEARCH)
    sk.lifecycle.research(_ns(id="feat-x"))
    # research subtask 还没 done
    with pytest.raises(SkeinError, match="调研 subtask 未全完成"):
        sk.lifecycle.plan(_ns(id="feat-x"))


def test_research_requires_research_subtask(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """测试 research 时要求有 research phase 的 subtask。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")  # 默认 EXEC phase
    with pytest.raises(SkeinError, match="无 research subtask"):
        sk.lifecycle.research(_ns(id="feat-x"))


def test_finish_auto_commit_when_no_worktrees(ws: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """测试 finish 时无 worktree 的情况下的 auto_commit。"""
    sk = _skein(ws, monkeypatch)
    _create(sk, "feat-x")
    _add_sub(sk, "feat-x", "sub-a")
    _fill_prd(ws, "feat-x")
    sk.lifecycle.estimate(_ns(id="feat-x", set="8"))
    sk.lifecycle.confirm(_ns(id="feat-x", approved=True, unattended=False, summary=False))
    _sub_act(sk, "done", "feat-x", "sub-a")
    sk.lifecycle.check(_ns(id="feat-x"))
    sk.lifecycle.finishing(_ns(id="feat-x"))
    out = sk.lifecycle.finish(_ns(id="feat-x"))
    assert out["status"] == TaskStatus.DONE
