"""`skein confirm` 的人审门 — PRD 必须由用户本人过目才能进就绪。

**本文件刻意不走 conftest 的 `run_skein`**: 那个 helper 为了让 28 处调用点能跑, 会注入
`SKEIN_CONFIRM_ASSUME_TTY=1` 并自动喂 task id。用它来测这道门等于用绕过器测绕过器 —— 门哪天
退化成 no-op, 那 28 个调用点一个都发现不了。所以这里直接起子进程跑真 CLI。

门的设计意图 (详见 commands._require_user_review): confirm 之前的三道门校验的都是**结构**
(prd 填齐 / ≥1 subtask / 工时), AI 自己就能填满再自己 confirm。所以需要一道要人参与的门。

**两条通道, 强制力不同, 两条都测**:
- `--summary` → `AskUserQuestion` → `--approved`: 日常走这条 (用户不用离开对话)。
  参数 AI 自己能传, 脚本看不到 AskUserQuestion 的结果 —— 靠**流程纪律**, 与「有没有真的派
  agent」同级。
- 用户自己在终端敲: stdin 非 TTY 直接拒, **脚本强制**, AI 物理上过不去。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import SKEIN, run_skein  # noqa: E402

PRD = """# {tid} — PRD

## 目标
- [ ] 让 confirm 真的需要人看

## 边界
- 不动 start

## 验收标准
- [ ] 非 TTY 被拒

## 索引
- design.md
"""


def _ready_task(ws: Path, tid: str = "feat-x") -> str:
    """造一个「结构上完全够格、只差人审」的 task。"""
    run_skein(ws, "create", tid, "--name", "任务X", "--desc", "d")
    run_skein(ws, "subtask", "add", tid, "s1", "--name", "子一", "--desc", "d", "--estimate", "2")
    (ws / ".skein/task" / tid / "prd.md").write_text(PRD.format(tid=tid))
    design = ws / ".skein/task" / tid / "design.md"
    design.write_text(design.read_text().replace(
        "- [ ] TODO: 填测试接缝", "- [x] 复用 tests/test_statemachine.py"))
    run_skein(ws, "estimate", tid, "--set", "4")
    return tid


def _raw_confirm(ws: Path, tid: str, *, assume_tty: bool = False, extra: list[str] | None = None,
                 answer: str | None = None) -> subprocess.CompletedProcess[str]:
    """直跑 CLI, 不经 conftest 的 confirm 特判。"""
    env = dict(os.environ)
    env.pop("SKEIN_CONFIRM_ASSUME_TTY", None)
    if assume_tty:
        env["SKEIN_CONFIRM_ASSUME_TTY"] = "1"
    return subprocess.run([sys.executable, str(SKEIN), "confirm", tid, *(extra or [])],
                          cwd=ws, env=env, capture_output=True, text=True, input=answer)


def _status(ws: Path, tid: str) -> str:
    import json
    return str(json.loads((ws / ".skein/task" / tid / "task.json").read_text())["status"])


def test_bare_confirm_is_refused_and_names_both_channels(ws: Path) -> None:
    """裸 confirm (AI 经工具跑, stdin 是管道) → 拒, 并把两条合法通道都说清楚。

    报错文案本身是给 AI 读的操作指引 —— 只说「被拒」而不说怎么过, AI 会自己瞎试。
    """
    tid = _ready_task(ws)
    r = _raw_confirm(ws, tid, answer="")
    assert r.returncode != 0, f"非 TTY 竟放行了: {r.stdout}"
    assert "需用户审核" in r.stderr, r.stderr
    assert "--summary" in r.stderr and "AskUserQuestion" in r.stderr and "--approved" in r.stderr, \
        f"未给出对话确认那条路: {r.stderr}"
    assert f"! skein confirm {tid}" in r.stderr, "未给出终端那条路"
    assert _status(ws, tid) == "待处理", "被拒后状态不该变"


def test_summary_prints_and_does_not_change_state(ws: Path) -> None:
    """`--summary` 只出摘要给 main 塞进 AskUserQuestion, 不动状态。"""
    tid = _ready_task(ws)
    r = _raw_confirm(ws, tid, extra=["--summary"], answer="")
    assert r.returncode == 0, r.stderr
    assert "## 目标" in r.stdout and "## subtask" in r.stdout, f"摘要不完整: {r.stdout}"
    assert _status(ws, tid) == "待处理", "--summary 不该改状态"


def test_approved_passes_and_records_ask_channel(ws: Path) -> None:
    """`--approved` = 用户已在 AskUserQuestion 里批准 → 放行并记 confirmed_by=ask。"""
    import json
    tid = _ready_task(ws)
    r = _raw_confirm(ws, tid, extra=["--approved"], answer="")
    assert r.returncode == 0, f"--approved 仍被拒: {r.stderr}"
    assert _status(ws, tid) == "就绪"
    t = json.loads((ws / ".skein/task" / tid / "task.json").read_text())
    assert t.get("confirmed_by") == "ask", f"审核渠道记错: {t.get('confirmed_by')}"


def test_wrong_answer_is_refused(ws: Path) -> None:
    """输入的不是 task id → 取消, 状态不变。防手滑一路回车确认掉。"""
    tid = _ready_task(ws)
    r = _raw_confirm(ws, tid, assume_tty=True, answer="y\n")
    assert r.returncode != 0, f"输错 id 竟放行了: {r.stdout}"
    assert "已取消" in r.stderr, r.stderr
    assert _status(ws, tid) == "待处理"


def test_correct_answer_passes_and_records_channel(ws: Path) -> None:
    """输入正确 task id → 进就绪, 并留下审核渠道痕迹。"""
    import json
    tid = _ready_task(ws)
    r = _raw_confirm(ws, tid, assume_tty=True, answer=f"{tid}\n")
    assert r.returncode == 0, f"确认后仍被拒: {r.stderr}"
    assert _status(ws, tid) == "就绪"
    t = json.loads((ws / ".skein/task" / tid / "task.json").read_text())
    assert t.get("confirmed_by") == "user-tty", f"终端通道应记 user-tty: {t.get('confirmed_by')}"
    assert t.get("confirmed"), "未记录审核时间"


def test_summary_shows_what_user_needs_to_judge(ws: Path) -> None:
    """摘要要够用户判断该不该放行: 目标 / 边界 / 验收 / subtask 拆解 / 工时。"""
    tid = _ready_task(ws)
    r = _raw_confirm(ws, tid, assume_tty=True, answer=f"{tid}\n")
    out = r.stderr
    for must in ("目标", "边界", "验收标准", "subtask", "预计工时",
                 "让 confirm 真的需要人看", "[s1]"):
        assert must in out, f"摘要缺 {must!r}:\n{out}"


def test_structural_gates_still_run_before_review(ws: Path) -> None:
    """人审门在结构门**之后** —— 缺 subtask 时该报缺 subtask, 不该先要人来审一个残缺的 PRD。"""
    run_skein(ws, "create", "bare", "--name", "空", "--desc", "d")
    r = _raw_confirm(ws, "bare", answer="")
    assert "无 subtask 登记" in r.stderr, r.stderr
    assert "需用户审核" not in r.stderr, "结构不全就不该惊动用户"


if __name__ == "__main__":
    import tempfile

    from conftest import make_ws
    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "w"
            d.mkdir()
            fn(make_ws(d))
    print("confirm 人审门自检过")
