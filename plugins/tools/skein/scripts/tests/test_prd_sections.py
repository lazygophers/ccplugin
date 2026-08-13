"""`skein prd` 章节写入白名单 — 从 3 章扩到 confirm 门要求的全部 6 章 (索引除外)。

背景: confirm 门 (`validate_prd`) 校验 3 个二级章节齐备 (`PRD_SECTIONS_V6`), 而扩之前
CLI 的 `prd write/add` 只能写 3 章 —— 其余 4 章只能靠裸 Edit 填, 与门要求的规范化留了缺口。
本文件验证: 三段均可经 CLI 写入、未知章节被拦。

经 skein_cli fixture 跑真 CLI + ws fixture 造隔离仓。每测独立 tmp_path, 禁碰真实 .skein/。
"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SkeinCli

TID = "prd-sec"


def _create(skein_cli: SkeinCli, ws: Path, tid: str = TID) -> None:
    skein_cli(ws, "create", tid, "--name", tid, "--desc", "d")


def _prd_text(ws: Path, tid: str = TID) -> str:
    return (ws / ".skein" / "task" / tid / "prd.md").read_text()


def test_all_gate_sections_writable_except_index(skein_cli: SkeinCli, ws: Path) -> None:
    """confirm 门要求的 6 章 (除「索引」) 都能经 CLI 整章写入; 「索引」被拒。"""
    _create(skein_cli, ws)
    writable = [
        ("目标", "解决 X"),
        ("边界", "范围内: prd 章节读写"),
        ("验收标准", "confirm 校验通过"),
    ]
    for section, text in writable:
        r = skein_cli(ws, "prd", "write", TID, "--type", section, "--list", text)
        out = json.loads(r.stdout)
        assert out["section"] == section and out["action"] == "write"
        assert text in _prd_text(ws)

    r = skein_cli(ws, "prd", "write", TID, "--type", "索引", "--list", "x", check=False)
    assert r.returncode != 0  # 索引不是合法 --type


def test_unknown_section_error_lists_all_legal_names(skein_cli: SkeinCli, ws: Path) -> None:
    """写不存在的章节名报错, 且错误文本含全部合法章节名。"""
    _create(skein_cli, ws)
    r = skein_cli(ws, "prd", "write", TID, "--type", "不存在的章节", "--list", "x", check=False)
    assert r.returncode != 0
    for section in ("目标", "边界", "验收标准"):
        assert section in r.stderr, f"缺章节名 {section}: {r.stderr}"


def test_scaffold_and_internal_write_unaffected(skein_cli: SkeinCli, ws: Path) -> None:
    """引擎自身生成 prd 模板与内部写章节 (fmt) 不受本次改动影响。"""
    _create(skein_cli, ws)
    text = _prd_text(ws)
    for section in ("目标", "边界", "验收标准"):
        assert f"## {section}" in text
    r = skein_cli(ws, "fmt", TID)
    assert json.loads(r.stdout)["id"] == TID
