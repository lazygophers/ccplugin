"""本轮加固的四条新逻辑各留一个可跑检查。

来源都是一次真实会话的实测缺口 (session 7d8cc4e4):
- dispatch hint 没有成品 prompt → main 自撰 prompt 撑爆 / 干脆不派, 479 次 Edit 全在 main 里;
- `prd check --list 1` 传序号必然「无匹配」白跑;
- 「禁 && 长链」只写在文档里, 实测违反 37 次;
- flow gate 判的是看板展示名而非落盘枚举, 是条死分支。
"""
from __future__ import annotations

import json
from pathlib import Path

import subprocess
import sys

from conftest import HOOKS, SkeinCli
from skeinlib.core.scheduling import _dispatch_hints
from skeinlib.hooks.pre_tool_use import chained_writes


def test_hint_carries_ready_to_use_prompt() -> None:
    """三类 hint 都带成品 prompt, 且串里含 main 唯一需要的三参数。"""
    tasks = {"order-create-api": {"id": "order-create-api", "worktrees": []}}
    hints = _dispatch_hints(claimed=[{"tid": "order-create-api", "sid": "s1", "phase": "exec", "repo": None}],
                            checked=["order-create-api"], finishing=["order-create-api"], tasks=tasks, root=Path("/repo"))
    assert len(hints) == 3
    for hint in hints:
        assert hint["prompt"], f"{hint['agent']} 无成品 prompt"
        assert "order-create-api" in hint["prompt"]
    exec_hint = next(h for h in hints if h["agent"].endswith("executor"))
    assert "s1" in exec_hint["prompt"] and "subtask show" in exec_hint["prompt"]


def test_hint_prompt_omitted_on_mismatch() -> None:
    """workdir 推不出来时不发 prompt —— 派出去也只会在错目录动手。"""
    tasks = {"order-create-api": {"id": "order-create-api", "worktrees": [{"repo": "a"}, {"repo": "b"}]}}
    hints = _dispatch_hints(claimed=[{"tid": "order-create-api", "sid": "s1", "phase": "exec", "repo": None}],
                            tasks=tasks, root=Path("/repo"))
    assert hints[0]["mismatch"] == "multi_repo_subtask_missing_repo"
    assert "prompt" not in hints[0]


def test_prd_check_accepts_index(skein_cli: SkeinCli, ws: Path) -> None:
    """`--list <纯数字>` = 章节内第 N 条; 越界报错而非静默勾错行。"""
    skein_cli(ws, "create", "order-create-api", "--name", "t", "--desc", "d")
    skein_cli(ws, "prd", "write", "order-create-api", "--type", "acceptance", "--list", "首条验收\n次条验收")
    skein_cli(ws, "prd", "check", "order-create-api", "--type", "acceptance", "--list", "2")
    body = skein_cli(ws, "prd", "read", "order-create-api", "--type", "acceptance").stdout
    assert "- [ ] 首条验收" in body and "- [x] 次条验收" in body, body
    assert skein_cli(ws, "prd", "check", "order-create-api", "--type", "acceptance", "--list", "9",
                     check=False).returncode != 0


def test_chained_writes_detects_only_state_writes() -> None:
    """只抓状态写命令的串接, 读命令串一起无所谓。"""
    assert len(chained_writes("skein task create a --name x && skein prd write a --type goal --list y")) == 2
    assert chained_writes("skein list --status open && git status --short") == []
    assert len(chained_writes("skein task create a --name x")) == 1  # 单条不算串接, 守门只拦 >1


def test_bash_guard_blocks_chained_skein_writes(ws: Path) -> None:
    """PreToolUse 对串接的状态写命令返回 2 (阻断)。"""
    payload = {"tool_name": "Bash", "cwd": str(ws), "tool_input": {
        "command": "skein task create a --name x && skein subtask add a s1 --name y"}}
    result = subprocess.run([sys.executable, str(HOOKS), "guard"], cwd=ws,
                            capture_output=True, text=True, check=False, input=json.dumps(payload))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "禁止" in result.stderr


def test_dispatch_reminder_fires_on_running_subtask(skein_cli: SkeinCli, ws: Path) -> None:
    """有 running subtask 时 main 改源码 → PostToolUse 提醒改派 executor。"""
    from skeinlib.hooks.post_tool_use import _dispatch_reminder
    skein_cli(ws, "create", "order-create-api", "--name", "t", "--desc", "d")
    skein_cli(ws, "subtask", "add", "order-create-api", "s1", "--name", "n", "--desc", "d", "--estimate", "1")
    skein_dir = str(ws / ".skein")
    tasks = [{"id": "order-create-api", "status": "active"}]
    assert _dispatch_reminder(skein_dir, tasks) == 0  # pending, 不提醒
    task_file = ws / ".skein" / "task" / "order-create-api" / "task.json"
    data = json.loads(task_file.read_text(encoding="utf-8"))
    data["subtasks"][0]["status"] = "running"
    task_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _dispatch_reminder(skein_dir, tasks)
    assert "order-create-api/s1" in buf.getvalue() and "skein-executor" in buf.getvalue()
    buf2 = io.StringIO()
    with contextlib.redirect_stdout(buf2):
        _dispatch_reminder(skein_dir, tasks)
    assert buf2.getvalue() == "", "同一 subtask 重复提醒"
