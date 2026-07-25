#!/usr/bin/env python3
"""看板视图 characterization 安全网 — 锚定 6 个 board 视图方法当前 JSON 输出, 供 Snapshot/view 重构证明字节级不变。

覆盖视图: _board_data / _dashboard / _queue / _task_detail / _archive_list / _search。

手法: 手工造固定时间戳 fixture (.skein/task/<id>/task.json 直写, 非走 CLI) + 冻结 now() → 输出全确定, 与 golden JSON 逐字段比对。
  - golden 缺失时首跑自举写盘并 skip (bootstrap); 存在则严格比对。
  - 覆盖五态 (待处理/就绪/进行中/检查中/已完成) + 就绪但依赖阻塞 + supertask/child + 幽灵骨架 (仅顶层索引) + 归档 task + spec 文件。

重构后重跑: 输出应与 golden 完全一致 (视图为纯投影, 仅内部结构变)。
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

SKEIN: Path = Path(__file__).parent / "skein.py"
GOLDEN: Path = Path(__file__).parent / "views_golden.json"
TNOW: int = 2_000_000_000  # 冻结 now() 返回值 (fixture 时间戳皆相对此)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("skein_v", SKEIN)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _task_json(**kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "deps": [], "subtasks": [], "contracts": [],
        "created": TNOW - 10000, "updated": TNOW - 5000,
    }
    base.update(kw)
    return base


def _sub(sid: str, status: str, **kw: Any) -> dict[str, Any]:
    s: dict[str, Any] = {
        "sid": sid, "name": f"子-{sid}", "desc": f"desc-{sid}", "status": status,
        "agent": "skein-executor", "skills": [], "depends_on": [], "验收": [],
        "created": TNOW - 9000,
    }
    s.update(kw)
    return s


def _write_task(tdir: Path, t: dict[str, Any], prd: str | None = None) -> None:
    d = tdir / t["id"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "task.json").write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8")
    if prd is not None:
        (d / "prd.md").write_text(prd, encoding="utf-8")


PRD_ALPHA = (
    "# alpha — PRD\n\n"
    "## 目标\n交付纯视图模块。\n- [x] 拆出 Snapshot\n- [ ] 六视图纯函数化\n- [ ] TODO: 占位跳过\n\n"
    "## 边界\n- [ ] 不动调度\n\n"
    "## 验收标准\n输出字节级不变。\n- [x] golden 通过\n- [ ] TestClient 覆盖\n"
)


def _seed(d: Path) -> None:
    # init 造 config.yaml + spec 骨架; 再直写 task fixture (绕 _sync, 精确控时间戳)
    git(d, "init", "-q")
    git(d, "config", "user.email", "t@t.dev")
    git(d, "config", "user.name", "t")
    (d / "seed.txt").write_text("s\n")
    git(d, "add", "-A")
    git(d, "commit", "-qm", "seed")
    subprocess.run([sys.executable, str(SKEIN), "init"], cwd=d, capture_output=True, text=True, check=True)

    tdir = d / ".skein" / "task"
    # 进行中 + 混合态 subtask (done/running/ready-pending/blocked-pending)
    _write_task(tdir, _task_json(
        id="alpha", name="Alpha 任务", status="进行中", desc="活跃任务",
        worktree="wt/alpha", started=TNOW - 8000,
        subtasks=[
            _sub("s1", "已完成", started=TNOW - 7000, finished=TNOW - 6000),
            _sub("s2", "运行中", started=TNOW - 3000),
            _sub("s3", "待处理", depends_on=["s1"]),
            _sub("s4", "待处理", depends_on=["s2"]),  # 依赖未 done → 阻塞
        ],
        contracts=["契约A", "契约B"],
    ), prd=PRD_ALPHA)
    # 检查中 (subtask 全 done)
    _write_task(tdir, _task_json(
        id="beta", name="Beta 任务", status="检查中", desc="待验收",
        worktree="wt/beta", started=TNOW - 7000, checked=TNOW - 1000,
        subtasks=[_sub("b1", "已完成", started=TNOW - 6500, finished=TNOW - 6000)],
    ))
    # 就绪 (依赖空 → 可 start)
    _write_task(tdir, _task_json(
        id="gamma", name="Gamma 任务", status="就绪", desc="待启动",
        subtasks=[_sub("g1", "待处理")],
    ))
    # 就绪但依赖 alpha (未 done) → 阻塞
    _write_task(tdir, _task_json(
        id="zeta", name="Zeta 任务", status="就绪", desc="被阻塞", deps=["alpha"],
        subtasks=[_sub("z1", "待处理")],
    ))
    # 待处理 (plan 未收敛) — 且为 supertask 的 child
    _write_task(tdir, _task_json(
        id="delta", name="Delta 任务", status="待处理", desc="规划中",
        parent="super1", subtasks=[_sub("d1", "待处理")],
    ))
    # 已完成
    _write_task(tdir, _task_json(
        id="epsilon", name="Epsilon 任务", status="已完成", desc="完成态",
        started=TNOW - 9000, finished=TNOW - 200,
        subtasks=[_sub("e1", "已完成", started=TNOW - 8000, finished=TNOW - 7000)],
    ))
    # supertask (含 child delta)
    _write_task(tdir, _task_json(
        id="super1", name="Super 任务", status="进行中", desc="聚合", kind="supertask",
        worktree="wt/super1", started=TNOW - 8500,
    ))

    # 顶层索引 (_render_tasks mirror 源): 含全部 per-task + 一个幽灵骨架 ghost1
    index = {"tasks": [
        {"id": "alpha", "status": "进行中", "deps": [], "worktree": "wt/alpha", "parent": None, "kind": "task"},
        {"id": "beta", "status": "检查中", "deps": [], "worktree": "wt/beta", "parent": None, "kind": "task"},
        {"id": "gamma", "status": "就绪", "deps": [], "worktree": None, "parent": None, "kind": "task"},
        {"id": "zeta", "status": "就绪", "deps": ["alpha"], "worktree": None, "parent": None, "kind": "task"},
        {"id": "delta", "status": "待处理", "deps": [], "worktree": None, "parent": "super1", "kind": "task"},
        {"id": "epsilon", "status": "已完成", "deps": [], "worktree": None, "parent": None, "kind": "task"},
        {"id": "super1", "status": "进行中", "deps": [], "worktree": "wt/super1", "parent": None, "kind": "supertask"},
        {"id": "ghost1", "status": "待处理", "deps": [], "worktree": None, "parent": None, "kind": "task"},
    ]}
    (d / ".skein" / "task.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    # 归档 task (archive/<年>/<月-日>/<id>)
    ad = tdir / "archive" / "2033" / "01-01" / "old1"
    ad.mkdir(parents=True, exist_ok=True)
    (ad / "task.json").write_text(json.dumps(_task_json(
        id="old1", name="Old 任务", status="已完成", desc="旧归档", finished=TNOW - 100000,
        subtasks=[_sub("o1", "已完成")],
    ), ensure_ascii=False, indent=2), encoding="utf-8")

    # spec 文件 (供 _search 命中)
    spec_cat = d / ".skein" / "spec" / "core" / "arch"
    spec_cat.mkdir(parents=True, exist_ok=True)
    (spec_cat / "zero-dep.md").write_text("# 零依赖\nalpha 相关架构约束。\n", encoding="utf-8")


def _capture(m: ModuleType, d: Path) -> dict[str, Any]:
    cwd0 = os.getcwd()
    os.chdir(d)
    # 清 ENV override 保配置确定
    saved = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("CLAUDE_PLUGIN_OPTION_")}
    orig_now = m.now
    m.now = lambda: TNOW  # type: ignore[assignment]
    try:
        sk = m.Skein()
        sk.proj = "TESTPROJ"  # 固定项目名 (否则=临时目录 basename, 随机)
        return {
            "board_data": sk._board_data(),
            "dashboard": sk._dashboard(),
            "queue": sk._queue(),
            "archive_list": sk._archive_list(),
            "task_detail_alpha": sk._task_detail("alpha"),
            "task_detail_old1": sk._task_detail("old1"),  # 走归档回落
            "task_detail_ghost1": sk._task_detail("ghost1"),  # 幽灵骨架 → None
            "search_alpha": sk._search("alpha"),
            "search_snapshot": sk._search("视图"),
            "search_empty": sk._search(""),
        }
    finally:
        m.now = orig_now  # type: ignore[assignment]
        os.environ.update(saved)
        os.chdir(cwd0)


def _run() -> dict[str, Any]:
    m = _load()
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _seed(d)
        return _capture(m, d)


def test_views_characterization() -> None:
    # 过 json round-trip: 与 golden (从 JSON 载) 同构 (tuple→list 归一)
    out = json.loads(json.dumps(_run(), ensure_ascii=False))
    if not GOLDEN.exists():
        GOLDEN.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        import pytest
        pytest.skip(f"golden 自举写盘: {GOLDEN.name} — 复跑即严格比对")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    # 逐视图比对, 定位差异更清晰
    assert set(out) == set(golden), f"视图集变化: {set(out) ^ set(golden)}"
    for key in sorted(out):
        assert out[key] == golden[key], f"视图 {key} 输出与 golden 不一致"


def test_views_deterministic() -> None:
    # 两次独立 seed+capture 应完全一致 (证明 fixture+冻结 now 无隐藏非确定性)
    a = _run()
    b = _run()
    assert a == b, "视图输出非确定 — fixture 或 now 冻结不完整"


if __name__ == "__main__":
    _run()
    print("ok")
