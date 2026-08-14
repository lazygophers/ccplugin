"""归档护栏 — 关联链 (deps) 上有未完成 task 时, 整条链禁归档。"""
from __future__ import annotations

from typing import Any

from skeinlib.task.model import TaskStatus
from skeinlib.task.store import TaskStore

BLOCKED = TaskStore._unfinished_related  # 关联链护栏在落盘层 (skeinlib/store.py)
DONE = TaskStatus.DONE
ACTIVE = TaskStatus.ACTIVE
PENDING = TaskStatus.PENDING


def _t(tid: str, status: str, deps: list[str] | None = None) -> dict[str, Any]:
    return {"id": tid, "status": status, "deps": deps or []}


def test_isolated_done_task_archivable() -> None:
    assert BLOCKED([_t("a", DONE)]) == set()


def test_dep_successor_unfinished_blocks_predecessor() -> None:
    # b 依赖 a; b 进行中 → a 虽已完成也不得归档
    blocked = BLOCKED([_t("a", DONE), _t("b", ACTIVE, deps=["a"])])
    assert blocked == {"a", "b"}


def test_dep_predecessor_unfinished_blocks_successor() -> None:
    blocked = BLOCKED([_t("a", ACTIVE), _t("b", DONE, deps=["a"])])
    assert blocked == {"a", "b"}


def test_transitive_chain_blocks_whole_component() -> None:
    # a ← b ← c, 只有 c 未完成 → a/b 同被拦 (跨一级传导)
    blocked = BLOCKED([_t("a", DONE), _t("b", DONE, deps=["a"]),
                       _t("c", PENDING, deps=["b"])])
    assert blocked == {"a", "b", "c"}


def test_separate_components_independent() -> None:
    # a/b 全完成可归档; x/y 有未完成整体拦住 — 互不牵连
    blocked = BLOCKED([_t("a", DONE), _t("b", DONE, deps=["a"]),
                       _t("x", DONE), _t("y", ACTIVE, deps=["x"])])
    assert blocked == {"x", "y"}


def test_dangling_dep_id_ignored() -> None:
    # 依赖指向已归档/不存在 id → 不参与连通计算, 不误拦
    assert BLOCKED([_t("a", DONE, deps=["gone"])]) == set()
