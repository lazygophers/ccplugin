"""dispatch hint 与 CLI 契约的可跑检查。

来源是一次真实会话的实测缺口 (session 7d8cc4e4):
- dispatch hint 没有成品 prompt → main 自撰 prompt 撑爆 / 干脆不派, 479 次 Edit 全在 main 里;
- `prd check --list 1` 传序号必然「无匹配」白跑。

原先同文件还钉着两条预防式守卫 (`&&` 串接硬阻 / main 亲做时的派发提醒)。两者已撤 ——
落盘状态本身就是真值, 串接中途失败各命令自己会报错, 预防式拦截换来的只是重试与等待。
"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SkeinCli
from skeinlib.core.scheduling import _dispatch_hints


def test_hint_carries_ready_to_use_prompt() -> None:
    """三类 hint 都带成品 prompt, 且串里含 main 唯一需要的三参数。"""
    tasks = {"order-create-api": {"id": "order-create-api", "worktrees": []}}
    hints = _dispatch_hints(claimed=[{"tid": "order-create-api", "sid": "s1", "phase": "exec", "repo": None}],
                            checked=["order-create-api"], finishing=["order-create-api"], tasks=tasks, root=Path("/repo"))
    assert len(hints) == 3
    for hint in hints:
        assert hint["prompt"], f"{hint['agent']} 无成品 prompt"
        # skein 体系内 agent 入参一律 JSON: 单行、无自然语言包裹、可直接 json.loads
        assert "\n" not in hint["prompt"]
        p = json.loads(hint["prompt"])
        assert p["tid"] == "order-create-api"
        assert p["worktree"] in ("on", "off")
    exec_hint = json.loads(next(h for h in hints if h["agent"].endswith("executor"))["prompt"])
    assert exec_hint["sid"] == "s1" and "subtask show" in exec_hint["action"]


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
