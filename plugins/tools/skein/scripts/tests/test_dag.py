"""subtask DAG 调度测试 — add/claim/ready/done/fail/依赖拓扑/并发槽。

经 skein_cli fixture 跑 CLI + ws fixture 造隔离仓。每测独立 tmp_path, 禁碰真实 .skein/。

并发模型 (真实行为): task 级并发上限已取消 (design.md §3: 按 subtask 计数后是冗余的,
见 s3 concurrency-pools 重构) —— 只剩 subtask 级 `pools.work` (.skein/config.yaml):
单/全局 ready/claim 批 = pools.work - running subtask。
注: 历史上曾用 `max_parallel`/`max_active` 命名, 现已统一为 `pools: {work, gate}` 两键, 勿再引入独立键。
"""
from __future__ import annotations

import re
from pathlib import Path

from conftest import SkeinCli

TID = "alpha-beta"


def _create(skein_cli: SkeinCli, ws: Path, tid: str = TID) -> None:
    """create task (subtask add 前置)。"""
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")


def _fill_prd(ws: Path, tid: str) -> None:
    """写规范 prd.md 过 start 的 _validate_prd 门 (章节齐 + 无 TODO 占位)。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n"
        "## 边界\n- a\n\n## 验收标准\n- 通过\n\n## 索引\n- design.md\n")


def _set_max_active(ws: Path, n: int) -> None:
    """改写 .skein/config.yaml 的 work 池上限 (subtask 并发槽)。

    s2 把 `max_active` 拆成 `pools: {work, gate}` 后, 原来的 `^max_active:` 正则在新
    config.yaml 上匹配不到任何东西 —— 该 helper 会**静默变成空操作**, 上限仍是默认 2,
    表现为「明明设了 4 却只预览出 2 个」。故改写 pools.work。
    """
    cfg = ws / ".skein" / "config.yaml"
    txt = cfg.read_text()
    txt = re.sub(r"^(\s+)work:\s*\d+", lambda m: f"{m.group(1)}work: {n}", txt, flags=re.M)
    cfg.write_text(txt)


def _add(skein_cli: SkeinCli, ws: Path, tid: str, sid: str, *, deps: str = "",
         check: str = "", phase: str = "") -> None:
    args = ["subtask", "add", tid, sid, "--name", f"N{sid}", "--desc", "d", "--estimate", "1"]
    if deps:
        args += ["--deps", deps]
    if check:
        args += ["--check", check]
    if phase:
        args += ["--phase", phase]
    skein_cli(ws, *args)


def _backdate_created(ws: Path, tid: str, sid: str, hours_ago: float) -> None:
    """把某 subtask 的 created 往前拨 (模拟等待了 N 小时) —— s4 加权打分的等待翻盘用例专用。"""
    import json
    import time
    tj = ws / ".skein" / "task" / tid / "task.json"
    t = json.loads(tj.read_text())
    for s in t["subtasks"]:
        if s["sid"] == sid:
            s["created"] = int(time.time() - hours_ago * 3600)
    tj.write_text(json.dumps(t, ensure_ascii=False))


def _status_map(skein_cli: SkeinCli, ws: Path, tid: str) -> dict[str, str]:
    """解析 `subtask list` → {sid: 状态中文}。行格式: sid<TAB>状态<TAB>..."""
    out = skein_cli(ws, "subtask", "list", tid).stdout
    m: dict[str, str] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] and not parts[0].startswith("无"):
            m[parts[0]] = parts[1]
    return m


def _claim_sids(skein_cli: SkeinCli, ws: Path, tid: str) -> list[str]:
    """解析单 task claim 输出的 sid 列 (认领批首列 tid-free: sid<TAB>...)。"""
    out = skein_cli(ws, "subtask", "claim", tid).stdout
    sids: list[str] = []
    for line in out.splitlines():
        if line.startswith(("已认领", "就绪", "无")):
            continue
        parts = line.split("\t")
        if parts and parts[0] and not parts[0].startswith("无"):
            sids.append(parts[0])
    return sids


def test_subtask_add_registers_and_list_visible(skein_cli: SkeinCli, ws: Path) -> None:
    """add 登记: 全字段 (含 deps/check), list 可见且字段正确。"""
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "s1", check="c1;c2")
    _add(skein_cli, ws, TID, "s2", deps="s1", check="ca")
    out = skein_cli(ws, "subtask", "list", TID).stdout
    assert "s1" in out and "s2" in out
    assert "依赖:s1" in out                 # deps 落库
    st = _status_map(skein_cli, ws, TID)
    assert st["s1"] == "待处理" and st["s2"] == "待处理"


def test_claim_batch_all_ready_no_deps(skein_cli: SkeinCli, ws: Path) -> None:
    """无 deps subtask 首批 claim 全 ready (默认 max_active=2)。"""
    _set_max_active(ws, 2)
    _create(skein_cli, ws)
    for s in ("a", "b"):
        _add(skein_cli, ws, TID, s)
    claimed = _claim_sids(skein_cli, ws, TID)
    assert set(claimed) == {"a", "b"}
    assert _status_map(skein_cli, ws, TID) == {"a": "运行中", "b": "运行中"}


def test_ready_is_readonly_does_not_mutate(skein_cli: SkeinCli, ws: Path) -> None:
    """ready 只读预览: 不改状态 (list 后仍待处理)。"""
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "a")
    out = skein_cli(ws, "subtask", "ready", TID).stdout
    assert "就绪" in out and "a" in out
    assert _status_map(skein_cli, ws, TID) == {"a": "待处理"}  # 未被标 running


def test_ready_empty_when_all_running(skein_cli: SkeinCli, ws: Path) -> None:
    """满槽后 ready 无就绪 (claim 占满 2 槽)。"""
    _set_max_active(ws, 2)
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "a")
    _add(skein_cli, ws, TID, "b")
    skein_cli(ws, "subtask", "claim", TID)
    out = skein_cli(ws, "subtask", "ready", TID).stdout
    assert "无就绪" in out  # 2/2 满槽


def test_done_unblocks_dependent(skein_cli: SkeinCli, ws: Path) -> None:
    """done 后依赖它的 subtask 才进 claim 批。"""
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "b", deps="a")
    _add(skein_cli, ws, TID, "a")
    # 首批: 只 a 就绪 (b deps a)
    assert _claim_sids(skein_cli, ws, TID) == ["a"]
    skein_cli(ws, "subtask", "done", TID, "a")
    assert _status_map(skein_cli, ws, TID)["a"] == "已完成"
    # a done 后 b 就绪
    assert _claim_sids(skein_cli, ws, TID) == ["b"]


def test_fail_marks_failed_with_note(skein_cli: SkeinCli, ws: Path) -> None:
    """fail 标失败 + note 备注 (claim 后 fail)。"""
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "a")
    skein_cli(ws, "subtask", "claim", TID)
    out = skein_cli(ws, "subtask", "fail", TID, "a", "--note", "boom").stdout
    assert "失败" in out
    assert _status_map(skein_cli, ws, TID)["a"] == "失败"
    # note 落盘 (status 行查询确认)
    raw = (ws / ".skein" / "task" / TID / "task.json").read_text()
    assert "boom" in raw


def test_dep_chain_topology(skein_cli: SkeinCli, ws: Path) -> None:
    """依赖拓扑 A deps B, B deps C: claim 首批只 C → C done B ready → B done A ready。"""
    _set_max_active(ws, 3)
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "a", deps="b")
    _add(skein_cli, ws, TID, "b", deps="c")
    _add(skein_cli, ws, TID, "c")
    assert set(_claim_sids(skein_cli, ws, TID)) == {"c"}        # 只 C 无依赖
    skein_cli(ws, "subtask", "done", TID, "c")
    assert set(_claim_sids(skein_cli, ws, TID)) == {"b"}        # C done → B ready
    skein_cli(ws, "subtask", "done", TID, "b")
    assert set(_claim_sids(skein_cli, ws, TID)) == {"a"}        # B done → A ready


def test_concurrency_slot_caps_claim(skein_cli: SkeinCli, ws: Path) -> None:
    """并发槽: max_active=2, 3 个无 deps subtask → claim 只取 2 (第 3 等槽)。"""
    _set_max_active(ws, 2)
    _create(skein_cli, ws)
    for s in ("a", "b", "c"):
        _add(skein_cli, ws, TID, s)
    claimed = _claim_sids(skein_cli, ws, TID)
    assert len(claimed) == 2 and set(claimed) <= {"a", "b", "c"}
    st = _status_map(skein_cli, ws, TID)
    assert sum(1 for v in st.values() if v == "运行中") == 2
    assert sum(1 for v in st.values() if v == "待处理") == 1
    # 第 3 个在 done 释放槽后才就绪
    skein_cli(ws, "subtask", "done", TID, claimed[0])
    again = _claim_sids(skein_cli, ws, TID)
    assert len(again) == 1


def test_slot_releases_on_done_and_fail(skein_cli: SkeinCli, ws: Path) -> None:
    """done/fail 都释放槽 (running 计数下降, 新 subtask 可 claim)。"""
    _set_max_active(ws, 2)
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "a")
    _add(skein_cli, ws, TID, "b")
    _add(skein_cli, ws, TID, "c")
    skein_cli(ws, "subtask", "claim", TID)               # a,b running, c 等
    skein_cli(ws, "subtask", "fail", TID, "a")           # fail 释放一槽
    assert _claim_sids(skein_cli, ws, TID) == ["c"]       # c 进来


def test_done_sets_full_percent(skein_cli: SkeinCli, ws: Path) -> None:
    """done 即全过验收 → 100% (list 第 3 列)。"""
    _create(skein_cli, ws)
    _add(skein_cli, ws, TID, "a", check="c1;c2;c3")
    skein_cli(ws, "subtask", "claim", TID)
    skein_cli(ws, "subtask", "done", TID, "a")
    out = skein_cli(ws, "subtask", "list", TID).stdout
    line = next(l for l in out.splitlines() if l.startswith("a\t"))
    assert line.split("\t")[2] == "100%"           # 进度 100%


def test_global_claim_cross_task(skein_cli: SkeinCli, ws: Path) -> None:
    """全局 claim: 两 active task 的 ready subtask 竞争全局 max_active 槽。"""
    _set_max_active(ws, 2)
    for tid in ("alpha-beta", "gamma-delta"):
        skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
        _add(skein_cli, ws, tid, "x")
        _fill_prd(ws, tid)
        skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
        skein_cli(ws, "confirm", tid)                     # 待处理→进行中 (confirm 吸收 start)
    out = skein_cli(ws, "claim", "exec").stdout              # 全局 claim exec
    assert "已全局认领" in out
    # 两个 task 各 1 subtask, 竞争 2 槽 → 两个都进 running
    assert "alpha-beta/x" in out and "gamma-delta/x" in out


def _dry_run_order(skein_cli: SkeinCli, ws: Path) -> list[str]:
    """解析 `claim exec --dry-run` 的批预览顺序 → [tid/sid, ...]。"""
    out = skein_cli(ws, "claim", "exec", "--dry-run").stdout
    order: list[str] = []
    for line in out.splitlines():
        if "/" in line.split("\t")[0]:
            order.append(line.split("\t")[0])
    return order


def test_priority_beats_topo_depth(skein_cli: SkeinCli, ws: Path) -> None:
    """优先级压过拓扑深度: 低拓扑深度但 urgent 的 task 排在高拓扑深度但 normal 的前面。"""
    _set_max_active(ws, 2)
    # deep-chain: s1 无 dep, s2 依赖 s1, s3 依赖 s2 → s1 拓扑深度=2 (正常优先级)
    skein_cli(ws, "create", "deep-chain", "--name", "deep-chain", "--desc", "d")
    _add(skein_cli, ws, "deep-chain", "s1")
    _add(skein_cli, ws, "deep-chain", "s2", deps="s1")
    _add(skein_cli, ws, "deep-chain", "s3", deps="s2")
    _fill_prd(ws, "deep-chain")
    skein_cli(ws, "estimate", "deep-chain", "--set", "3")
    skein_cli(ws, "confirm", "deep-chain")
    # urgent-flat: 单 subtask, 拓扑深度=0, 但 urgent
    skein_cli(ws, "create", "urgent-flat", "--name", "urgent-flat", "--desc", "d",
              "--priority", "urgent")
    _add(skein_cli, ws, "urgent-flat", "x")
    _fill_prd(ws, "urgent-flat")
    skein_cli(ws, "estimate", "urgent-flat", "--set", "1")
    skein_cli(ws, "confirm", "urgent-flat")
    order = _dry_run_order(skein_cli, ws)
    assert order.index("urgent-flat/x") < order.index("deep-chain/s1")


def test_priority_does_not_cross_unfinished_dep(skein_cli: SkeinCli, ws: Path) -> None:
    """依赖硬优先: urgent 但 task 级依赖未完成的 task 不进候选池, 就绪的 normal task 正常被认领。"""
    _set_max_active(ws, 2)
    skein_cli(ws, "create", "blocker", "--name", "blocker", "--desc", "d")
    _add(skein_cli, ws, "blocker", "b1")
    _fill_prd(ws, "blocker")
    skein_cli(ws, "estimate", "blocker", "--set", "1")
    skein_cli(ws, "confirm", "blocker")  # 就绪但未完成 (status != TaskStatus.DONE)
    skein_cli(ws, "create", "urgent-waiting", "--name", "urgent-waiting", "--desc", "d",
              "--priority", "urgent", "--deps", "blocker")
    _add(skein_cli, ws, "urgent-waiting", "u1")
    _fill_prd(ws, "urgent-waiting")
    skein_cli(ws, "estimate", "urgent-waiting", "--set", "1")
    # s3 后 confirm 吸收 start, deps 未完成时 confirm 直接被拒 (旧流程是 confirm 成功、
    # start 时才拦)。两种流程下该 task 都进不了候选池 —— 这正是「依赖硬优先」要保的性质。
    skein_cli(ws, "confirm", "urgent-waiting", check=False)
    skein_cli(ws, "create", "normal-ready", "--name", "normal-ready", "--desc", "d")
    _add(skein_cli, ws, "normal-ready", "n1")
    _fill_prd(ws, "normal-ready")
    skein_cli(ws, "estimate", "normal-ready", "--set", "1")
    skein_cli(ws, "confirm", "normal-ready")
    order = _dry_run_order(skein_cli, ws)
    assert "normal-ready/n1" in order
    assert "urgent-waiting/u1" not in order


def test_claim_order_stable_on_repeat(skein_cli: SkeinCli, ws: Path) -> None:
    """四档排序 + 同档内重复认领(只读预览)结果一致 — 覆盖全部四档且验证稳定序。"""
    _set_max_active(ws, 4)
    for tid, prio in (("t-low", "low"), ("t-urgent", "urgent"), ("t-normal", "normal"),
                      ("t-high", "high")):  # 刻意打乱创建顺序, 排除「登记序恰好=优先级序」的巧合
        skein_cli(ws, "create", tid, "--name", tid, "--desc", "d", "--priority", prio)
        _add(skein_cli, ws, tid, "x")
        _fill_prd(ws, tid)
        skein_cli(ws, "estimate", tid, "--set", "1")
        skein_cli(ws, "confirm", tid)
    first = _dry_run_order(skein_cli, ws)
    second = _dry_run_order(skein_cli, ws)
    assert first == second == ["t-urgent/x", "t-high/x", "t-normal/x", "t-low/x"]


def test_zero_regression_all_same_priority(skein_cli: SkeinCli, ws: Path) -> None:
    """全部同档 (默认 normal) 时排序仍由拓扑深度→登记序决定, 与改动前逐位一致。"""
    _set_max_active(ws, 3)
    skein_cli(ws, "create", "alpha-beta", "--name", "alpha-beta", "--desc", "d")
    _add(skein_cli, ws, "alpha-beta", "s1")
    _add(skein_cli, ws, "alpha-beta", "s2", deps="s1")
    _fill_prd(ws, "alpha-beta")
    skein_cli(ws, "estimate", "alpha-beta", "--set", "2")
    skein_cli(ws, "confirm", "alpha-beta")
    skein_cli(ws, "create", "gamma-delta", "--name", "gamma-delta", "--desc", "d")
    _add(skein_cli, ws, "gamma-delta", "x")
    _fill_prd(ws, "gamma-delta")
    skein_cli(ws, "estimate", "gamma-delta", "--set", "1")
    skein_cli(ws, "confirm", "gamma-delta")
    order = _dry_run_order(skein_cli, ws)
    # alpha-beta 先登记 (ti=0) 且 s1 拓扑深度=1 > gamma-delta/x 的 0 → alpha-beta/s1 先
    assert order == ["alpha-beta/s1", "gamma-delta/x"]


def test_task_level_cap_removed_all_can_go_active(skein_cli: SkeinCli, ws: Path) -> None:
    """task 级并发上限已取消 (design item #6): N 个 task 可同时 confirm→进行中, 无阻拦。"""
    _set_max_active(ws, 2)  # 仅 subtask 级槽位, 与 task 级并发无关
    for tid in ("alpha-beta", "gamma-delta", "epsilon-zeta"):
        skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")
        _add(skein_cli, ws, tid, "x")
        _fill_prd(ws, tid)
        skein_cli(ws, "estimate", tid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
        res = skein_cli(ws, "confirm", tid)  # 三个全部放行, 无第 3 个被拦
        assert res.returncode == 0, res.stderr


# ---------- s4 concurrency-pools: 两池独立 + 加权打分 (design.md §3/§4) ----------

def test_two_pools_independent_work_full_check_still_claimable(skein_cli: SkeinCli, ws: Path) -> None:
    """两池独立: work 池满时, 检查中/收尾中的认领 (claim check) 不受影响。"""
    _set_max_active(ws, 1)  # work 池上限=1, 一占就满
    # task-b: 占满 work 池唯一的槽
    skein_cli(ws, "create", "task-b", "--name", "task-b", "--desc", "d")
    _add(skein_cli, ws, "task-b", "x")
    _fill_prd(ws, "task-b")
    skein_cli(ws, "estimate", "task-b", "--set", "1")
    skein_cli(ws, "confirm", "task-b")
    skein_cli(ws, "claim", "exec")  # 占满 work 池 (1/1)
    assert "work 池已满" in skein_cli(ws, "claim", "exec", "--dry-run").stdout

    both = skein_cli(ws, "claim", "--dry-run").stdout
    assert "work 池已满" in both and "无可认领的 check/finishing task" in both

    # task-a: 全部 subtask 已完成, 等着被 claim check 收进检查中 — 不经 claim exec (work 满进不去)
    skein_cli(ws, "create", "task-a", "--name", "task-a", "--desc", "d")
    _add(skein_cli, ws, "task-a", "y")
    _fill_prd(ws, "task-a")
    skein_cli(ws, "estimate", "task-a", "--set", "1")
    skein_cli(ws, "confirm", "task-a")
    skein_cli(ws, "subtask", "done", "task-a", "y")  # done 不设前置态门, 直接可标完成

    out = skein_cli(ws, "claim", "check").stdout
    assert "已认领进检查" in out and "task-a" in out


def test_exec_wins_over_research_on_tie(skein_cli: SkeinCli, ws: Path) -> None:
    """exec 同分优先: 关键路径权重/优先级/等待时长全相等时, phase=exec 排在 phase=research 前面。"""
    _set_max_active(ws, 2)
    skein_cli(ws, "create", "task-exec", "--name", "task-exec", "--desc", "d")
    _add(skein_cli, ws, "task-exec", "x")  # 默认 phase=exec
    _fill_prd(ws, "task-exec")
    skein_cli(ws, "estimate", "task-exec", "--set", "1")
    skein_cli(ws, "confirm", "task-exec")

    skein_cli(ws, "create", "task-research", "--name", "task-research", "--desc", "d")
    _add(skein_cli, ws, "task-research", "y", phase="research")
    _fill_prd(ws, "task-research")
    skein_cli(ws, "estimate", "task-research", "--set", "1")
    skein_cli(ws, "confirm", "task-research")

    order = _dry_run_order(skein_cli, ws)
    assert order.index("task-exec/x") < order.index("task-research/y")


def test_long_waiting_research_overtakes_fresh_exec(skein_cli: SkeinCli, ws: Path) -> None:
    """等久的 research 能翻盘: 等待时长差超过 exec 软优先加分后, research 反超同分的 exec。"""
    _set_max_active(ws, 2)
    skein_cli(ws, "create", "task-exec", "--name", "task-exec", "--desc", "d")
    _add(skein_cli, ws, "task-exec", "x")  # 刚登记, 等待≈0
    _fill_prd(ws, "task-exec")
    skein_cli(ws, "estimate", "task-exec", "--set", "1")
    skein_cli(ws, "confirm", "task-exec")

    skein_cli(ws, "create", "task-research", "--name", "task-research", "--desc", "d")
    _add(skein_cli, ws, "task-research", "y", phase="research")
    _backdate_created(ws, "task-research", "y", hours_ago=3)  # 等了 3h > W_EXEC 等价的 1h
    _fill_prd(ws, "task-research")
    skein_cli(ws, "estimate", "task-research", "--set", "1")
    skein_cli(ws, "confirm", "task-research")

    order = _dry_run_order(skein_cli, ws)
    assert order.index("task-research/y") < order.index("task-exec/x")


def test_empty_batch_message_names_which_pool_is_full(skein_cli: SkeinCli, ws: Path) -> None:
    """满槽提示指明池名: work 满报「work 池已满」, gate 满报「gate 池已满」(两处均不能只说「满槽」)。"""
    _set_max_active(ws, 1)
    skein_cli(ws, "create", "task-w", "--name", "task-w", "--desc", "d")
    _add(skein_cli, ws, "task-w", "x")
    _fill_prd(ws, "task-w")
    skein_cli(ws, "estimate", "task-w", "--set", "1")
    skein_cli(ws, "confirm", "task-w")
    skein_cli(ws, "claim", "exec")  # 占满 work 池 (1/1)
    out = skein_cli(ws, "claim", "exec", "--dry-run").stdout
    assert "work 池已满" in out

    # gate 池: 上限压到 0, 两个 task 都全 done 想收尾, finishing 应报「gate 池已满」
    cfg = ws / ".skein" / "config.yaml"
    txt = cfg.read_text()
    import re as _re
    txt = _re.sub(r"^(\s+)gate:\s*\d+", lambda m: f"{m.group(1)}gate: 0", txt, flags=_re.M)
    cfg.write_text(txt)
    skein_cli(ws, "subtask", "done", "task-w", "x")
    check_out = skein_cli(ws, "claim", "check").stdout
    assert "已认领进检查" in check_out
    finishing_out = skein_cli(ws, "claim", "check").stdout  # 第二轮: 检查中→收尾中, 撞 gate=0
    assert "gate 池已满" in finishing_out
