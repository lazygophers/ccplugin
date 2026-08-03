"""`skein prd` 章节写入白名单 — 从 3 章扩到 confirm 门要求的全部 6 章 (索引除外)。

背景: confirm 门 (`validate_prd`) 校验 7 个二级章节齐备 (`PRD_SECTIONS_V6`), 而扩之前
CLI 的 `prd write/add` 只能写 3 章 —— 其余 4 章只能靠裸 Edit 填, 与门要求的规范化留了缺口。
本文件验证: 缺口补齐、索引仍被拦、User Stories 固定编号格式不被折成 checkbox。

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
        ("验证方式", "本地跑 pytest 全绿即 pass"),
        ("Testing Decisions", "只测外部行为"),
    ]
    for section, text in writable:
        r = skein_cli(ws, "prd", "write", TID, "--type", section, "--list", text)
        out = json.loads(r.stdout)
        assert out["section"] == section and out["action"] == "write"
        assert text in _prd_text(ws)

    r = skein_cli(ws, "prd", "write", TID, "--type", "索引", "--list", "x", check=False)
    assert r.returncode != 0
    assert "索引" not in r.stderr or "仅允许" in r.stderr  # 报的是「--type 仅允许」白名单, 不含索引


def test_unknown_section_error_lists_all_legal_names(skein_cli: SkeinCli, ws: Path) -> None:
    """写不存在的章节名报错, 且错误文本含全部合法章节名。"""
    _create(skein_cli, ws)
    r = skein_cli(ws, "prd", "write", TID, "--type", "不存在的章节", "--list", "x", check=False)
    assert r.returncode != 0
    for section in ("目标", "边界", "验收标准", "验证方式", "Testing Decisions"):
        assert section in r.stderr, f"缺章节名 {section}: {r.stderr}"
    assert "User Stories" in r.stderr or "stories" in r.stderr


def test_user_stories_add_keeps_fixed_numbering(skein_cli: SkeinCli, ws: Path) -> None:
    """User Stories 用 add 追加: 不折成 `- [ ]`, 编号续着已有条目数递增。"""
    _create(skein_cli, ws)
    # 模板自带第 1 条占位 "1. As a <actor> ..."
    r = skein_cli(ws, "prd", "add", TID, "--type", "User Stories",
                  "--list", "As a 用户, I want 用 CLI 填 User Stories, so that 不用裸编辑 prd")
    assert json.loads(r.stdout)["action"] == "add"
    r2 = skein_cli(ws, "prd", "add", TID, "--type", "User Stories",
                   "--list", "As a 审查者, I want 编号连续, so that 可读")
    assert json.loads(r2.stdout)["action"] == "add"

    text = _prd_text(ws)
    section = text.split("## User Stories")[1].split("## 验收标准")[0]
    assert "- [ ]" not in section  # 不被折成 checkbox
    assert "2. As a 用户" in section
    assert "3. As a 审查者" in section


def test_user_stories_write_rebuilds_from_one(skein_cli: SkeinCli, ws: Path) -> None:
    """User Stories 用 write 整章重建: 编号从 1 重排, 旧占位被清空。"""
    _create(skein_cli, ws)
    skein_cli(ws, "prd", "write", TID, "--type", "User Stories",
              "--list", "As a 用户, I want X, so that Y\\nAs a 管理员, I want Z, so that W")
    text = _prd_text(ws)
    section = text.split("## User Stories")[1].split("## 验收标准")[0]
    assert "1. As a 用户" in section
    assert "2. As a 管理员" in section
    assert "<actor>" not in section  # 旧模板占位已被整章替换清空


def test_scaffold_and_internal_write_unaffected(skein_cli: SkeinCli, ws: Path) -> None:
    """引擎自身生成 prd 模板与内部写章节 (fmt) 不受本次改动影响。"""
    _create(skein_cli, ws)
    text = _prd_text(ws)
    for section in ("目标", "边界", "User Stories", "验收标准", "验证方式", "Testing Decisions", "索引"):
        assert f"## {section}" in text
    r = skein_cli(ws, "fmt", TID)
    assert json.loads(r.stdout)["id"] == TID
