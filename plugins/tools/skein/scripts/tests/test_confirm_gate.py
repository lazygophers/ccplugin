"""`skein task confirm` 的人审门 — PRD 必须经用户过目才能进就绪。

**本文件刻意不走 conftest 的 `run_skein`**: 那个 helper 为了让 28 处调用点能跑, 会自动补上
`--approved`。用它来测这道门等于用绕过器测绕过器 —— 门哪天退化成 no-op, 那 28 个调用点一个
都发现不了。所以这里直接起子进程跑真 CLI。

## 门的设计意图 (详见 commands._require_user_review)
confirm 之前的三道门校验的都是**结构** (prd 填齐 / ≥1 subtask / 工时), AI 自己就能填满再自己
confirm。所以需要一道要真人参与的门。

两条合法来源, 强制力不同:
- **看板点击** (最稳): 用户在 task 详情点「确认规划」→ 端点转 `confirm <id> --approved`。
  AI 没有浏览器, 物理上点不了。
- **对话确认**: main 先 `--summary` 取摘要 → `AskUserQuestion` → 带 `--approved` 再跑。
  靠流程纪律 —— 答案 AI 伪造不了, 但「有没有真的问」得 main 自觉。

## 🛑 CLI 绝不读 stdin
曾有一段 TTY 交互 (打印摘要 + 等用户敲 task id), 已整段删除: CLI 是被 skill/agent 调用的,
任何交互都会把调用方挂住。`test_cli_never_blocks_on_stdin` 守这条。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import SKEIN, run_skein  # noqa: E402

PRD = """# {tid} — PRD

## 目标
- [ ] 让 confirm 真的需要人看

## 边界
- 不动 start

## 验收标准
- [ ] 无 --approved 被拒

"""

def _ready_task(ws: Path, tid: str = "feat-x") -> str:
    """造一个「结构上完全够格、只差人审」的 task。"""
    run_skein(ws, "create", tid, "--name", "任务X", "--desc", "d")
    run_skein(ws, "subtask", "add", tid, "s1", "--name", "子一", "--desc", "d", "--estimate", "2")
    (ws / ".skein/task" / tid / "prd.md").write_text(PRD.format(tid=tid))
    (ws / ".skein/task" / tid / "design.md").write_text(
        f"# {tid} — 详细设计\n\n## 测试接缝 (seam)\n- [x] 复用 tests/test_statemachine.py\n")
    run_skein(ws, "estimate", tid, "--set", "4")
    return tid

def _raw(ws: Path, *args: str, timeout: float = 20) -> subprocess.CompletedProcess[str]:
    """直跑 CLI, 不经 conftest 的 confirm 特判。**不喂 stdin** —— CLI 不该读它。"""
    return subprocess.run([sys.executable, str(SKEIN), *args], cwd=ws, env=dict(os.environ),
                          capture_output=True, text=True, timeout=timeout)

def _task(ws: Path, tid: str) -> dict[str, Any]:
    return dict(json.loads((ws / ".skein/task" / tid / "task.json").read_text()))

def test_bare_confirm_is_refused_and_names_both_channels(ws: Path) -> None:
    """无 `--approved` → 拒, 并把两条合法来源都说清楚。

    报错文案是给 AI 读的操作指引 —— 只说「被拒」不说怎么过, AI 会自己瞎试。
    """
    tid = _ready_task(ws)
    r = _raw(ws, "task", "confirm", tid)
    assert r.returncode != 0, f"无 --approved 竟放行: {r.stdout}"
    assert "需用户审核" in r.stderr, r.stderr
    assert "看板点击" in r.stderr, f"未提看板通道: {r.stderr}"
    assert "--summary" in r.stderr and "AskUserQuestion" in r.stderr and "--approved" in r.stderr, \
        f"未提对话通道: {r.stderr}"
    assert _task(ws, tid)["status"] == "pending", "被拒后状态不该变"

def test_cli_never_blocks_on_stdin(ws: Path) -> None:
    """🛑 CLI 是被 skill/agent 调用的 —— **任何** stdin 交互都会把调用方挂死。

    三条路径都关掉 stdin (DEVNULL) 并设超时: 谁要是加回一个 `input()`/`readline()`,
    这里会 TimeoutExpired 而不是静静地挂在真实调用里。
    """
    tid = _ready_task(ws)
    for args in (["task", "confirm", tid], ["task", "confirm", tid, "--summary"],
                 ["task", "confirm", tid, "--approved"]):
        r = subprocess.run([sys.executable, str(SKEIN), *args], cwd=ws,
                           stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=20)
        assert r.returncode in (0, 1), f"{args} 退出码异常 {r.returncode}: {r.stderr}"

def test_summary_prints_and_does_not_change_state(ws: Path) -> None:
    """`--summary` 只出摘要 (给 main 塞进 AskUserQuestion / 看板对话框), 不动状态。"""
    tid = _ready_task(ws)
    r = _raw(ws, "task", "confirm", tid, "--summary")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    summary = data.get("summary", "")
    assert "## 目标" in summary and "## subtask" in summary, f"摘要不完整: {summary}"
    assert _task(ws, tid)["status"] == "pending", "--summary 不该改状态"

def test_summary_shows_what_user_needs_to_judge(ws: Path) -> None:
    """摘要要够用户判断该不该放行: 目标 / 边界 / 验收 / subtask 拆解 / 工时。"""
    tid = _ready_task(ws)
    data = json.loads(_raw(ws, "task", "confirm", tid, "--summary").stdout)
    out = data.get("summary", "")
    for must in ("目标", "边界", "验收标准", "subtask", "预计工时",
                 "让 confirm 真的需要人看", "[s1]"):
        assert must in out, f"摘要缺 {must!r}:\n{out}"

def test_approved_passes_and_records_channel(ws: Path) -> None:
    """`--approved` → 放行, 记 confirmed_by + 时间戳。"""
    tid = _ready_task(ws)
    r = _raw(ws, "task", "confirm", tid, "--approved")
    assert r.returncode == 0, f"--approved 仍被拒: {r.stderr}"
    t = _task(ws, tid)
    assert t["status"] == "active"  # confirm 吸收 start: 待处理→进行中, 无就绪中间态
    assert t.get("confirmed_by") == "user", f"审核渠道记错: {t.get('confirmed_by')}"
    assert t.get("confirmed"), "未记录审核时间"

def test_structural_gates_still_run_before_review(ws: Path) -> None:
    """人审门在结构门**之后** —— 缺 subtask 时该报缺 subtask, 不该先要人审一个残缺的 PRD。"""
    run_skein(ws, "create", "bare", "--name", "空", "--desc", "d")
    r = _raw(ws, "task", "confirm", "bare")
    assert "无 subtask 登记" in r.stderr, r.stderr
    assert "需用户审核" not in r.stderr, "结构不全就不该惊动用户"

def test_summary_also_gated_by_structure(ws: Path) -> None:
    """`--summary` 同样走结构门 —— 免得把一份残缺 PRD 端到用户面前让人批。"""
    run_skein(ws, "create", "bare-two", "--name", "空", "--desc", "d")
    r = _raw(ws, "task", "confirm", "bare-two", "--summary")
    assert r.returncode != 0 and "无 subtask 登记" in r.stderr, r.stderr

# ── 看板通道: exec 白名单 (前端「确认规划」按钮走这条) ─────────────────────────
def test_board_whitelist_maps_confirm_to_fixed_argv() -> None:
    """看板点击 → 固定 argv, 不接受前端传任何 flag。

    这是人审门最硬的一条通道 (main 没浏览器点不了), 所以端点侧的 argv 必须写死:
    只认 `id`, 其余键一律忽略 —— 前端能拼 flag 的话, 这条通道就退化成跟 --approved 一样了。
    """
    from skeinlib.utils.exec_policy import exec_argv
    argv = exec_argv({"cmd": "confirm", "id": "feat-x", "extra": "--force", "flags": "-rf"})
    assert argv is not None and argv[-3:] == ["confirm", "feat-x", "--approved"], argv
    assert "--force" not in argv and "-rf" not in argv, f"前端传的 flag 泄进 argv: {argv}"

    # 看板不开 --summary 端点: 用户点按钮时 PRD 就在眼前, 不必再弹一遍摘要
    assert exec_argv({"cmd": "confirm-summary", "id": "feat-x"}) is None, \
        "confirm-summary 不该在白名单里 (看板无二次确认框)"

    assert exec_argv({"cmd": "confirm"}) is None, "缺 id 应拒"
    assert exec_argv({"cmd": "confirm", "id": "  "}) is None, "空白 id 应拒"

def test_board_confirm_does_not_shell_out(ws: Path) -> None:
    """id 里的 shell 元字符只是普通字符串 — argv 固定构造, 从不拼 shell。"""
    from skeinlib.utils.exec_policy import exec_argv
    argv = exec_argv({"cmd": "confirm", "id": "x; rm -rf /"})
    assert argv is not None and argv[-2] == "x; rm -rf /", argv
    assert not any(";" in a for a in argv[:-2]), "元字符逃到了别的 argv 位"

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
