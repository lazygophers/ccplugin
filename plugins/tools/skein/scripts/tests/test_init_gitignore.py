"""skein init `.skein/.gitignore` 生成 + 幂等补缺测试。

init 首次: 写入 8 条忽略 (task.md/vision.md/lock/archive + 4 衍生 .pending-fix/.audit-log/.recall.db/trash/)。
init 再跑: 幂等补缺已存文件 (只补缺行, 不破坏用户手写条目, 不重复已有)。"""
from __future__ import annotations

from pathlib import Path

from typing import Callable

SkeinCli = Callable[..., object]

GI_EXPECTED = [
    "task.md", "vision.md", "*.lock", "spec/.archive/",
    "spec/.pending-fix", "spec/.audit-log", "spec/.recall.db", "trash/",
]


def test_init_creates_gitignore_with_all_entries(ws: Path) -> None:
    """新仓 init 生成 `.skein/.gitignore` 含全部 8 条忽略条目。"""
    gi = ws / ".skein" / ".gitignore"
    assert gi.exists()
    text = gi.read_text(encoding="utf-8")
    for e in GI_EXPECTED:
        assert e in text.splitlines(), f"gitignore 缺条目: {e}"


def test_init_idempotent_preserves_user_entries(ws: Path, skein_cli: SkeinCli) -> None:
    """再跑 init 幂等: 不破坏用户手写条目, 不重复已有, 不补齐的条目。"""
    gi = ws / ".skein" / ".gitignore"
    # 模拟用户手写: 写一个 init 模板里没有的 board/ + 缺 4 衍生
    gi.write_text(
        "# 用户手写\n"
        "task.md\n"
        "board/\n"
        "*.lock\n"
        "spec/.archive/\n",
        encoding="utf-8",
    )
    skein_cli(ws, "init")  # 再跑 init 触发幂等补缺
    text = gi.read_text(encoding="utf-8")
    lines = text.splitlines()
    # 用户手写条目保留
    assert "board/" in lines, "用户手写条目 board/ 被破坏"
    assert "# 用户手写" in lines
    # 缺的 4 衍生补上
    for e in ("spec/.pending-fix", "spec/.audit-log", "spec/.recall.db", "trash/"):
        assert e in lines, f"幂等补缺未补: {e}"
    # 已有条目不重复 (task.md 应只出现 1 次作为非注释行)
    non_comment = [ln for ln in lines if ln.strip() and not ln.startswith("#")]
    assert non_comment.count("task.md") == 1, "已存条目 task.md 被重复写入"
    assert non_comment.count("*.lock") == 1


def test_init_idempotent_noop_when_complete(ws: Path, skein_cli: SkeinCli) -> None:
    """已含全部条目时再跑 init: 不追加任何内容 (完全幂等)。"""
    gi = ws / ".skein" / ".gitignore"
    before = gi.read_text(encoding="utf-8")
    skein_cli(ws, "init")
    after = gi.read_text(encoding="utf-8")
    assert before == after, "已含全部条目时 init 仍改了文件 (应完全幂等)"
