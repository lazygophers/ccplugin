"""exec_policy.py 全分支覆盖 — exec_argv 是纯函数，逐分支验证 argv 构造。

白名单命令严格 enum → 固定 argv: 每条分支一行 assert 就够，不需要 fixture。
"""
from __future__ import annotations

import sys
from typing import Optional

from skeinlib.utils.exec_policy import exec_argv
from skeinlib.utils.paths import SKEIN_ENTRY

BASE = [sys.executable, str(SKEIN_ENTRY)]


def _body(**kw: object) -> dict[str, object]:
    return dict(kw)


def test_list_no_status() -> None:
    assert exec_argv({"cmd": "list"}) == BASE + ["list", "--json"]


def test_list_with_status() -> None:
    assert exec_argv({"cmd": "list", "status": "active"}) == BASE + ["list", "--json", "--status", "active"]


def test_list_empty_status_ignored() -> None:
    assert exec_argv({"cmd": "list", "status": "  "}) == BASE + ["list", "--json"]


def test_ready() -> None:
    assert exec_argv({"cmd": "ready"}) == BASE + ["ready"]


def test_doctor() -> None:
    assert exec_argv({"cmd": "doctor"}) == BASE + ["doctor"]


def test_status_no_id_returns_none() -> None:
    assert exec_argv({"cmd": "status"}) is None
    assert exec_argv({"cmd": "status", "id": ""}) is None


def test_status_with_id() -> None:
    assert exec_argv({"cmd": "status", "id": "t1"}) == BASE + ["status", "t1", "--json"]


def test_status_with_id_and_sid() -> None:
    assert exec_argv({"cmd": "status", "id": "t1", "sid": "s1"}) == BASE + ["status", "t1", "s1", "--json"]




def test_subtask_list_no_id_returns_none() -> None:
    assert exec_argv({"cmd": "subtask-list"}) is None


def test_subtask_list_with_id() -> None:
    assert exec_argv({"cmd": "subtask-list", "id": "t1"}) == BASE + ["subtask", "list", "t1"]


def test_create_missing_fields_returns_none() -> None:
    assert exec_argv({"cmd": "create"}) is None
    assert exec_argv({"cmd": "create", "id": "t1"}) is None
    assert exec_argv({"cmd": "create", "id": "t1", "name": "n"}) is None


def test_create_full() -> None:
    r = exec_argv({"cmd": "create", "id": "t1", "name": "n", "desc": "d"})
    assert r == BASE + ["task", "create", "t1", "--name", "n", "--desc", "d"]


def test_create_with_deps() -> None:
    r = exec_argv({"cmd": "create", "id": "t1", "name": "n", "desc": "d", "deps": "t0"})
    assert r == BASE + ["task", "create", "t1", "--name", "n", "--desc", "d", "--deps", "t0"]


def test_subtask_add_missing_fields() -> None:
    assert exec_argv({"cmd": "subtask-add"}) is None
    assert exec_argv({"cmd": "subtask-add", "id": "t1"}) is None
    assert exec_argv({"cmd": "subtask-add", "id": "t1", "sid": "s1"}) is None


def test_subtask_add_full() -> None:
    r = exec_argv({"cmd": "subtask-add", "id": "t1", "sid": "s1", "name": "n", "desc": "d", "estimate": "1"})
    assert r == BASE + ["subtask", "add", "t1", "s1", "--name", "n", "--desc", "d", "--estimate", "1"]


def test_subtask_add_with_deps() -> None:
    r = exec_argv({"cmd": "subtask-add", "id": "t1", "sid": "s1", "name": "n", "desc": "d",
                   "estimate": "1", "deps": "s0"})
    assert r == BASE + ["subtask", "add", "t1", "s1", "--name", "n", "--desc", "d", "--estimate", "1",
                        "--deps", "s0"]


def test_clean_invalid_days_returns_none() -> None:
    assert exec_argv({"cmd": "clean", "days": True}) is None
    assert exec_argv({"cmd": "clean", "days": -1}) is None
    assert exec_argv({"cmd": "clean", "days": "abc"}) is None
    assert exec_argv({"cmd": "clean", "days": [1]}) is None


def test_clean_valid_int() -> None:
    assert exec_argv({"cmd": "clean", "days": 7}) == BASE + ["clean", "--days", "7"]


def test_clean_valid_str() -> None:
    assert exec_argv({"cmd": "clean", "days": "30"}) == BASE + ["clean", "--days", "30"]


def test_clean_zero() -> None:
    assert exec_argv({"cmd": "clean", "days": 0}) == BASE + ["clean", "--days", "0"]


def test_confirm_no_id_returns_none() -> None:
    assert exec_argv({"cmd": "confirm"}) is None


def test_confirm_with_id() -> None:
    assert exec_argv({"cmd": "confirm", "id": "t1"}) == BASE + ["task", "confirm", "t1", "--approved"]


def test_finish_no_id_returns_none() -> None:
    assert exec_argv({"cmd": "finish"}) is None


def test_finish_with_id() -> None:
    assert exec_argv({"cmd": "finish", "id": "t1"}) == BASE + ["task", "finish", "t1"]


def test_force_boolean_true_only() -> None:
    for cmd, argv in (
        ("confirm", ["task", "confirm", "t1", "--approved", "--force"]),
        ("finish", ["task", "finish", "t1", "--force"]),
        ("del", ["del", "t1", "--force"]),
    ):
        assert exec_argv({"cmd": cmd, "id": "t1", "force": True}) == BASE + argv
        assert "--force" not in (exec_argv({"cmd": cmd, "id": "t1", "force": "true"}) or [])


def test_priority_missing_returns_none() -> None:
    assert exec_argv({"cmd": "priority"}) is None
    assert exec_argv({"cmd": "priority", "id": "t1"}) is None


def test_priority_full() -> None:
    assert exec_argv({"cmd": "priority", "id": "t1", "set": "high"}) == BASE + ["task", "priority", "t1", "--set", "high"]


def test_del_no_id_returns_none() -> None:
    assert exec_argv({"cmd": "del"}) is None


def test_del_with_id() -> None:
    assert exec_argv({"cmd": "del", "id": "t1"}) == BASE + ["del", "t1"]


def test_prd_missing_fields_returns_none() -> None:
    assert exec_argv({"cmd": "prd"}) is None
    assert exec_argv({"cmd": "prd", "id": "t1"}) is None
    assert exec_argv({"cmd": "prd", "id": "t1", "type": "goal"}) is None


def test_prd_invalid_action_returns_none() -> None:
    assert exec_argv({"cmd": "prd", "id": "t1", "type": "goal", "action": "bogus"}) is None



def test_prd_write_needs_list() -> None:
    assert exec_argv({"cmd": "prd", "id": "t1", "type": "goal", "action": "write"}) is None






def test_unknown_cmd_returns_none() -> None:
    assert exec_argv({"cmd": "bogus"}) is None
    assert exec_argv({}) is None
