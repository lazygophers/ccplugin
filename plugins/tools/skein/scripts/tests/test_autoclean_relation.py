"""归档护栏 — 关联链 (deps + parent/child) 上有未完成 task 时, 整条链禁归档。"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

SKEIN = Path(__file__).resolve().parent.parent / "skein.py"
_spec = importlib.util.spec_from_file_location("skein_mod", SKEIN)
assert _spec and _spec.loader
skein_mod = importlib.util.module_from_spec(_spec)
sys.modules["skein_mod"] = skein_mod
_spec.loader.exec_module(skein_mod)

DONE = skein_mod.S_DONE
BLOCKED = skein_mod.Skein._unfinished_related


def _t(tid: str, status: str, deps: list[str] | None = None,
       parent: str | None = None) -> dict[str, Any]:
    return {"id": tid, "status": status, "deps": deps or [], "parent": parent}


def test_isolated_done_task_archivable() -> None:
    assert BLOCKED([_t("a", DONE)]) == set()


def test_dep_successor_unfinished_blocks_predecessor() -> None:
    # b 依赖 a; b 进行中 → a 虽已完成也不得归档
    blocked = BLOCKED([_t("a", DONE), _t("b", "进行中", deps=["a"])])
    assert blocked == {"a", "b"}


def test_dep_predecessor_unfinished_blocks_successor() -> None:
    blocked = BLOCKED([_t("a", "进行中"), _t("b", DONE, deps=["a"])])
    assert blocked == {"a", "b"}


def test_transitive_chain_blocks_whole_component() -> None:
    # a ← b ← c, 只有 c 未完成 → a/b 同被拦 (跨一级传导)
    blocked = BLOCKED([_t("a", DONE), _t("b", DONE, deps=["a"]),
                       _t("c", "待处理", deps=["b"])])
    assert blocked == {"a", "b", "c"}


def test_parent_child_relation_blocks() -> None:
    blocked = BLOCKED([_t("sup", "进行中"), _t("kid", DONE, parent="sup")])
    assert blocked == {"sup", "kid"}


def test_separate_components_independent() -> None:
    # a/b 全完成可归档; x/y 有未完成整体拦住 — 互不牵连
    blocked = BLOCKED([_t("a", DONE), _t("b", DONE, deps=["a"]),
                       _t("x", DONE), _t("y", "进行中", deps=["x"])])
    assert blocked == {"x", "y"}


def test_dangling_dep_id_ignored() -> None:
    # 依赖指向已归档/不存在 id → 不参与连通计算, 不误拦
    assert BLOCKED([_t("a", DONE, deps=["gone"])]) == set()
