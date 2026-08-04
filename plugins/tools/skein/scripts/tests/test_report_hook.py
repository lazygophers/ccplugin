"""`hooks.py report` 只在**真崩溃**时喊 bug —— 门拒绝不算 bug。

## 起因
冒烟时跑了一条少参数的 `skein task confirm <id>` (没带 `--approved`)。引擎按设计拒绝, 打印一行
「需用户审核 PRD 后才能进就绪…」并退 1。而 report hook 不看错误长什么样, 一律弹:

    ⚠️ SKEIN 脚本报错, 疑似插件 bug 请手动开 issue: …

功能正常工作却被报成 bug。危害不只是噪声: 它教调用方**撞了门就去提 issue**, 而不是照错误
提示补参数 —— 而 skein 的门 (confirm 人审门 / start 前置门 / 并发上限) 本来就是要被撞的,
撞门是常态。

## 判据
引擎的错误路径是 `raise SkeinError` → 入口 `SystemExit(str(e))`, stderr 只有一行人话,
**从不打印 traceback**。所以 `Traceback (most recent call last)` 在不在, 就是「没接住的
异常」与「主动拒绝」的分界线。

## 局限
只看 stderr 文本。若哪天引擎改成对崩溃也做 friendly 包装 (吞掉 traceback), 这条判据会失效
—— 那时得换成退出码或结构化字段, 并同步改这里的说明, 别让它继续给出虚假的安全感。
"""
from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import HOOKS  # noqa: E402

GATE_ERR = "smoke-task 需用户审核 PRD 后才能进就绪。两条路 (都要真实用户动作):"
CRASH_ERR = (
    "Traceback (most recent call last):\n"
    '  File "skein.py", line 1, in <module>\n'
    "AttributeError: 'Skein' object has no attribute 'does_not_exist'")


def _run(payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    """conftest 的 run_hooks 把 stdin 写死成空串, 这里要喂真 JSON, 故自己起进程。
    report 是纯 stdin→stdout 的转换, 不碰工作区, 所以不需要 ws fixture。"""
    return subprocess.run([sys.executable, str(HOOKS), "report"],
                          input=json.dumps(payload), capture_output=True, text=True, timeout=30)


def _report(cmd: str, err: str) -> dict[str, Any]:
    r = _run({"tool_name": "Bash", "tool_input": {"command": cmd}, "tool_error": err})
    assert r.returncode == 0, f"report hook 退非零: {r.stderr}"
    return dict(json.loads(r.stdout)) if r.stdout.strip() else {}


def test_gate_rejection_does_not_cry_bug() -> None:
    """门拒绝 (无 traceback): 递错误原文, **不**提 issue。"""
    out = _report("skein.py task confirm smoke-task", GATE_ERR)
    assert "systemMessage" not in out, (
        f"门拒绝被报成插件 bug 了: {out.get('systemMessage')!r} — "
        "撞门是 skein 的常态, 每撞一次就叫用户提 issue 是噪声。")
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "不是 bug" in ctx, f"未说明这属正常校验: {ctx}"
    assert "需用户审核 PRD" in ctx, f"错误原文没递给调用方: {ctx}"


def test_real_crash_still_cries_bug() -> None:
    """真崩溃 (带 traceback): 必须仍然引导开 issue —— 别把噪声连信号一起消掉。"""
    out = _report("skein.py status x", CRASH_ERR)
    msg = out.get("systemMessage", "")
    assert "issue" in msg, f"真崩溃却没引导报 issue: {out}"
    assert "github.com" in msg, f"issue 链接丢了: {msg}"
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "崩溃" in ctx, ctx


def test_unrelated_command_stays_silent() -> None:
    """别人的命令失败, 本 hook 一个字都不出。"""
    r = _run({"tool_name": "Bash", "tool_input": {"command": "npm run build"},
              "tool_error": "ELIFECYCLE"})
    assert r.returncode == 0
    assert not r.stdout.strip(), f"非 skein 命令失败也发声了: {r.stdout!r}"


def test_bin_wrapper_command_is_recognised() -> None:
    """`bin/skein` 短命令 (不含 .py) 也要认得出是我们的 —— 生产环境走的正是它。"""
    out = _report("skein task confirm smoke-task", GATE_ERR)
    assert out, "bin 短命令没被识别为 skein 脚本"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("report hook 自检过")
