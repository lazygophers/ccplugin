"""prd.md 加锁 — 编辑类工具打向 prd.md 硬阻, 走既有 `task.json`/`task.md` 那份名单/判断。

背景: `BLOCKED`(skeinlib/hooks/util.py) 原只挡 task.json/task.md, 本次把 prd.md 并进同一份
名单, **不新增第二套判断** —— guard 硬阻 + permission 不主动放行两处都直接吃 BLOCKED 更新。
拦截文案须给可照抄的 `skein prd` 命令形态 (与真实 CLI --help 一致)。

验证点:
1. Edit/Write 打 prd.md → guard 硬阻 (exit 2), 文案含可照抄命令
2. `skein prd read/write` 走 Bash CLI (ENGINE 白名单) → permission 照放, 不受本次改动影响
3. 复用同一份 BLOCKED, 不另起并行名单
4. 引擎内部生成模板 + `prd write` 落盘不受影响 (真跑 CLI)
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from typing import Any, Callable

from conftest import SkeinCli

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from skeinlib.hooks.guard import cmd_guard
from skeinlib.hooks.permission import cmd_permission
from skeinlib.hooks.util import BLOCKED

TID = "prd-lock"


def _capture(func: Callable[[dict[str, Any]], int], d: dict[str, Any]) -> tuple[int, str, str]:
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = StringIO(), StringIO()
    try:
        code = func(d)
        return code, sys.stdout.getvalue(), sys.stderr.getvalue()
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def test_blocked_reuses_same_list() -> None:
    """prd.md 并进既有 BLOCKED, 不是另起一份名单 (guard/permission 都读同一个 util.BLOCKED)。"""
    assert BLOCKED == {"task.json", "task.md", "prd.md"}


def test_guard_blocks_edit_on_prd(tmp_path: Path) -> None:
    """Edit 打向 .skein/task/<tid>/prd.md → 硬阻, 文案给出可照抄的 CLI 命令。"""
    prd = tmp_path / ".skein" / "task" / TID / "prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("## 目标\n占位\n")

    d = {"tool_name": "Edit", "tool_input": {"file_path": str(prd)}, "cwd": str(tmp_path)}
    code, out, err = _capture(cmd_guard, d)

    assert code == 2, "prd.md 应与 task.json/task.md 同样被硬阻"
    assert "禁直接读写" in err
    assert "prd.md" in err
    assert "skein prd write" in err, "文案须含可照抄的写入命令"
    assert "skein prd read" in err, "文案须含可照抄的读取命令"


def test_guard_blocks_write_on_prd(tmp_path: Path) -> None:
    """Write 同理被硬阻 (与 Edit 走同一分支)。"""
    prd = tmp_path / ".skein" / "task" / TID / "prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("## 目标\n占位\n")

    d = {"tool_name": "Write", "tool_input": {"file_path": str(prd), "content": "x"},
         "cwd": str(tmp_path)}
    code, _, err = _capture(cmd_guard, d)

    assert code == 2
    assert "prd.md" in err


def test_guard_allows_read_on_prd(tmp_path: Path) -> None:
    """prd.md 只锁写不锁读 —— 加锁理由是章节结构由引擎保证, 不是保密。

    验收明写「读 prd 不受影响」: 它本来就是给人读的散文, 挡掉 Read 只会逼调用方绕道,
    而绕道的那条路 (`skein prd read`) 一次只能取一章, 通读全文反而更贵。
    """
    prd = tmp_path / ".skein" / "task" / TID / "prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("## 目标\n占位\n")

    d = {"tool_name": "Read", "tool_input": {"file_path": str(prd)}, "cwd": str(tmp_path)}
    code, _, err = _capture(cmd_guard, d)

    assert code == 0, f"Read 打 prd.md 应放行, 却被拦: {err!r}"
    assert err == "", f"放行时不该有拦截文案: {err!r}"


def test_guard_still_blocks_read_on_task_json(tmp_path: Path) -> None:
    """回归: 放行 prd 的读不得波及 task.json —— 它的读阻是既有行为, 取态另有专门命令。"""
    tj = tmp_path / ".skein" / "task" / TID / "task.json"
    tj.parent.mkdir(parents=True)
    tj.write_text("{}")

    d = {"tool_name": "Read", "tool_input": {"file_path": str(tj)}, "cwd": str(tmp_path)}
    code, _, err = _capture(cmd_guard, d)

    assert code == 2, "task.json 的 Read 硬阻是既有行为, 不该被本次改动放开"


def test_permission_does_not_auto_allow_prd(tmp_path: Path) -> None:
    """permission 不再对 prd.md 主动放行 (退回默认流程, 由 guard 硬阻兜底)。"""
    prd = tmp_path / ".skein" / "task" / TID / "prd.md"
    d = {"tool_name": "Edit", "tool_input": {"file_path": str(prd)}, "cwd": str(tmp_path)}
    code, out, _ = _capture(cmd_permission, d)

    assert code == 0, "permission 只放行不阻断, 永远返回 0"
    assert out == "", "prd.md 不该被 permission 主动 allow (BLOCKED 命中, 退回默认流程)"


def test_permission_allows_skein_prd_read_via_bash() -> None:
    """`skein prd read ...` 走 Bash + ENGINE 白名单 → 照放, 不受本次改动影响 (读态走 CLI 即放行)。"""
    d = {"tool_name": "Bash", "tool_input": {"command": f"skein prd read {TID} --type 目标"}}
    code, out, _ = _capture(cmd_permission, d)

    assert code == 0
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["decision"]["behavior"] == "allow"


def test_scaffold_and_prd_write_cli_unaffected(skein_cli: SkeinCli, ws: Path) -> None:
    """引擎内部生成模板 + `skein prd write` 落盘走内部路径, 天然绕开本次的编辑工具拦截。"""
    skein_cli(ws, "create", TID, "--name", TID, "--desc", "d")
    prd_path = ws / ".skein" / "task" / TID / "prd.md"
    assert prd_path.exists(), "create 应正常生成 prd 模板"

    r = skein_cli(ws, "prd", "write", TID, "--type", "目标", "--list", "锁 prd.md 编辑")
    assert json.loads(r.stdout)["action"] == "write"
    assert "锁 prd.md 编辑" in prd_path.read_text()
