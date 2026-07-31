"""`skein confirm` 的人审门 — PRD 必须由用户本人过目才能进就绪。

**本文件刻意不走 conftest 的 `run_skein`**: 那个 helper 为了让 28 处调用点能跑, 会注入
`SKEIN_CONFIRM_ASSUME_TTY=1` 并自动喂 task id。用它来测这道门等于用绕过器测绕过器 —— 门哪天
退化成 no-op, 那 28 个调用点一个都发现不了。所以这里直接起子进程跑真 CLI。

门的设计意图 (详见 commands._require_user_review): confirm 之前的三道门校验的都是**结构**
(prd 填齐 / ≥1 subtask / 工时), AI 自己就能填满再自己 confirm。真正的门需要一个 AI 拿不到的
信号, 这里用「stdin 是不是 TTY」。这不是防对抗 (设个环境变量就绕过了), 是让**默认路径**走不通,
逼 AI 停下来把 PRD 交给人看。
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


def _raw_confirm(ws: Path, tid: str, *, assume_tty: bool = False,
                 answer: str | None = None) -> subprocess.CompletedProcess[str]:
    """直跑 CLI, 不经 conftest 的 confirm 特判。"""
    env = dict(os.environ)
    env.pop("SKEIN_CONFIRM_ASSUME_TTY", None)
    if assume_tty:
        env["SKEIN_CONFIRM_ASSUME_TTY"] = "1"
    return subprocess.run([sys.executable, str(SKEIN), "confirm", tid], cwd=ws, env=env,
                          capture_output=True, text=True, input=answer)


def _status(ws: Path, tid: str) -> str:
    import json
    return str(json.loads((ws / ".skein/task" / tid / "task.json").read_text())["status"])


def test_non_tty_is_refused(ws: Path) -> None:
    """AI 经工具跑命令时 stdin 是管道 → 必须拒, 且告诉用户该自己敲什么。"""
    tid = _ready_task(ws)
    r = _raw_confirm(ws, tid, answer="")
    assert r.returncode != 0, f"非 TTY 竟放行了: {r.stdout}"
    assert "需用户亲自审核" in r.stderr, r.stderr
    assert f"! skein confirm {tid}" in r.stderr, "未给出用户该执行的命令"
    assert _status(ws, tid) == "待处理", "被拒后状态不该变"


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
    assert t.get("confirmed_by") == "user-tty", "未记录审核渠道"
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
    assert "需用户亲自审核" not in r.stderr, "结构不全就不该惊动用户"


if __name__ == "__main__":
    import tempfile

    from conftest import make_ws
    for fn in (test_non_tty_is_refused, test_wrong_answer_is_refused,
               test_correct_answer_passes_and_records_channel,
               test_summary_shows_what_user_needs_to_judge,
               test_structural_gates_still_run_before_review):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "w"
            d.mkdir()
            fn(make_ws(d))
    print("confirm 人审门自检过")
