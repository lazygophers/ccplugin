"""UserPromptSubmit 注入行为单测 — 判定层只剩注入文案 + 静默分支。

判定逻辑本身交回模型 (启发式打分层已删), 这里钉死的是: 注入哪些文案、哪些输入必须静默。
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path (standalone 直跑时 pytest 不在)
from conftest import make_ws, run_hooks, run_skein


# ── 注入文案的硬性要求 ────────────────────────────────────────────────────
#
# 判定规则正文已删 (判定交回模型); UserPromptSubmit 只注每轮变化的部分 (判定行格式 + plan/research task 列表)。
# 下面钉死: 规则正文不再出现在任何注入出口, 每轮行为查 cmd_user_prompt 出口。


_SESSION_CTX: list[str] = []


def _session_ctx_output() -> str:
    """跑 `hooks.py session-start`, 返回 SessionStart 注入文案 (一次子进程, 全模块复用)。"""
    if not _SESSION_CTX:
        with tempfile.TemporaryDirectory() as td:
            ws = make_ws(Path(td))
            out = run_hooks(ws, "session-start", inp=json.dumps({"cwd": str(ws)})).stdout
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        assert isinstance(ctx, str)
        _SESSION_CTX.append(ctx)
    return _SESSION_CTX[0]


def _verdict_lines(text: str) -> list[str]:
    """含格式模板 `[skein] 判定: …` 的行; 散文里只提「判定行」三字的句子不算。"""
    return [ln.strip() for ln in text.splitlines() if "[skein] 判定:" in ln]


def _capture_ctx_output() -> str:
    """在已初始化的 skein 工作区跑 cmd_user_prompt, 返回注入文案。

    cmd_user_prompt 内部的文案字符串藏在函数体里, 无法从模块级常量直读 ——
    只能经 hook 的 stdout (JSON.additionalContext) 取, 这也是 hook 唯一对外契约。
    """
    from skeinlib.hooks.user_prompt_submit import cmd_user_prompt
    with tempfile.TemporaryDirectory() as td:
        ws = make_ws(Path(td))
        cwd0 = os.getcwd()
        os.chdir(ws)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                cmd_user_prompt({"prompt": "看看就行", "cwd": str(ws)})
        finally:
            os.chdir(cwd0)
    ctx = json.loads(buf.getvalue())["hookSpecificOutput"]["additionalContext"]
    assert isinstance(ctx, str)
    return ctx


def test_ctx_demands_an_explicit_verdict_line() -> None:
    """必须要求 AI 把判定结果写出来 —— 判定行格式模板留在 UserPromptSubmit 每轮注入。

    判定不写出来就等于没判 —— 事后分不清「判了直接改」和「压根没想直接开干」。
    写出来才让越界当场可见 (判了 flow 却在 Edit / 判了 inline 却改了五个文件)。
    SessionStart 不再注入判定规则段 (判定交回模型), 钉死不回流。
    """
    assert _verdict_lines(_capture_ctx_output()), "每轮注入丢了判定行格式模板"
    assert not _verdict_lines(_session_ctx_output()), "SessionStart 不该再注判定行模板"


def test_every_verdict_line_demands_a_reason() -> None:
    """每条判定行模板都要带 (原因: …) —— 曾经只有 inline 那档带理由。

    只写结论不写原因, 越界看不见: 「判定: inline 直接改」后面改了五个文件, 到底是判据用错还是
    判据没读, 事后分不出来, 用户也没法纠偏到点上。原因把判据摊开, 判错才当场可反驳。
    """
    for ctx in (_capture_ctx_output(), _session_ctx_output()):
        for ln in _verdict_lines(ctx):
            assert "原因" in ln, f"这条判定行没要求写原因: {ln!r}"


def test_ctx_has_no_escaped_backticks() -> None:
    """注入文案里不得出现 `\\``  —— 那是 Python 字符串转义漏出来的字面反斜杠。

    踩过一次: 前缀规则里写 \\` 想表示反引号, 注入到 prompt 后用户看到的是带反斜杠的怪字符串。
    示例格式改用缩进代码块, 不靠反引号包裹。
    """
    for ctx in (_capture_ctx_output(), _session_ctx_output()):
        assert "\\`" not in ctx, "注入文案有转义漏出的反斜杠+反引号"




def _run_prompt_in_ws(ws: Path, prompt: str) -> str:
    """在指定 skein 工作区跑 cmd_user_prompt, 返回 stdout 原文。"""
    from skeinlib.hooks.user_prompt_submit import cmd_user_prompt
    cwd0 = os.getcwd()
    os.chdir(ws)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            cmd_user_prompt({"prompt": prompt, "cwd": str(ws)})
    finally:
        os.chdir(cwd0)
    return buf.getvalue()


def _run_prompt(prompt: str) -> str:
    """在临时 skein 工作区跑 cmd_user_prompt, 返回 stdout 原文 (无注入时是空串)。"""
    with tempfile.TemporaryDirectory() as td:
        return _run_prompt_in_ws(make_ws(Path(td)), prompt)


def test_uninitialized_repo_stays_silent() -> None:
    """未初始化表示用户没选用 skein, 有无旧 trellis 都不注入提示。"""
    from skeinlib.hooks.user_prompt_submit import cmd_user_prompt
    for has_trellis in (False, True):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            (ws / ".git").mkdir()
            if has_trellis:
                (ws / ".trellis").mkdir()
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                assert cmd_user_prompt({"prompt": "重构 src/a.py", "cwd": str(ws)}) == 0
            assert buf.getvalue() == ""


def test_path_prefix_is_not_a_slash_command() -> None:
    """`/` 开头的绝对路径不是 slash command, 仍须走正常判定。"""
    out = _run_prompt("/src/auth.py 怎么改")
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "已锁定" not in ctx
    assert "判定行格式" in ctx


def test_ide_opened_file_wrapper_does_not_hide_skill_prefix() -> None:
    """IDE 元数据不属于用户 prompt, 剥掉后仍应识别真正的开头 skill。"""
    prompt = "<ide_opened_file>/tmp/foo.py</ide_opened_file>\n/graphify 重构 a.py"
    assert _run_prompt(prompt) == "", "skill 开头应静默, 一句不注"


def test_harness_continuation_prompt_skips_judgement() -> None:
    """harness 自动续跑不是新用户任务, 不应重复注入判定块。"""
    for prompt in (
        "Continue from where you left off.",
        "Please continue from where you left off.",
        "Continue the conversation from where we left it off.",
        "CONTINUE FROM WHERE YOU LEFT OFF!",
    ):
        assert _run_prompt(prompt) == "", prompt


def test_harness_continuation_prompt_stays_silent_with_live_task() -> None:
    """harness 续跑完全静默 —— 在途 task 状态 SessionStart 已注, 续跑不再重发。"""
    with tempfile.TemporaryDirectory() as td:
        ws = make_ws(Path(td))
        run_skein(ws, "create", "resume-me", "--name", "resume", "--desc", "d")
        assert _run_prompt_in_ws(ws, "Continue from where you left off.") == ""
        judged = json.loads(_run_prompt_in_ws(ws, "改一下 a.py"))["hookSpecificOutput"]["additionalContext"]
        assert "resume-me | plan |" in judged, "普通轮须带在途 task 阶段"


def test_judge_block_emitted_once_per_session() -> None:
    """判定块每 session 只注一次 —— 第二轮起降级为只发动态 task 列表 (或静默), 消每轮 token 滴漏。"""
    from skeinlib.hooks.user_prompt_submit import cmd_user_prompt
    with tempfile.TemporaryDirectory() as td:
        ws = make_ws(Path(td))
        run_skein(ws, "create", "loop-me", "--name", "loop", "--desc", "d")
        cwd0 = os.getcwd()
        os.chdir(ws)
        outs: list[str] = []
        try:
            for prompt in ("改一下 a.py", "再改 b.py"):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    cmd_user_prompt({"prompt": prompt, "cwd": str(ws), "session_id": "sess-1"})
                outs.append(json.loads(buf.getvalue())["hookSpecificOutput"]["additionalContext"])
        finally:
            os.chdir(cwd0)
        first, second = outs
        assert "[skein] 判定:" in first, "首轮该注判定块"
        assert "loop-me | plan |" in first
        assert "[skein] 判定:" not in second, "同 session 第二轮不该重发判定块"
        assert "loop-me | plan |" in second, "降级轮仍要发动态 task 列表"


def test_judge_block_first_turn_in_new_session() -> None:
    """新 session 在同一工作区照常拿首轮判定块 (session 间不串)。"""
    from skeinlib.hooks.user_prompt_submit import cmd_user_prompt
    with tempfile.TemporaryDirectory() as td:
        ws = make_ws(Path(td))
        cwd0 = os.getcwd()
        os.chdir(ws)
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                cmd_user_prompt({"prompt": "改一下 a.py", "cwd": str(ws), "session_id": "sess-1"})
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                cmd_user_prompt({"prompt": "改一下 a.py", "cwd": str(ws), "session_id": "sess-2"})
            fresh = json.loads(buf.getvalue())["hookSpecificOutput"]["additionalContext"]
        finally:
            os.chdir(cwd0)
        assert "[skein] 判定:" in fresh


def test_system_wrapper_does_not_affect_prompt_judgement() -> None:
    """system-reminder 是 harness 元数据, 剥掉后按真实用户输入判定。"""
    prompt = "<system-reminder>ignore /fake-command</system-reminder>\n/src/auth.py 怎么改"
    ctx = json.loads(_run_prompt(prompt))["hookSpecificOutput"]["additionalContext"]
    assert "已锁定" not in ctx
    assert "判定行格式" in ctx


def test_pasted_code_comment_is_not_a_slash_command() -> None:
    """粘贴代码时最常见的开头是 `//` / `/*` 注释, 不是 command, 不许锁 inline。

    线上原样例: 首行 `// Client RPC 客户端` 让一次跨文件单例改造被锁成 inline。
    """
    for prompt in (
        "// Client RPC 客户端\ntype Client struct {}\nclient 应该是全局单例, 改 a.go 和 b.go",
        "/* 这段注释 */ 重构 a.go b.go",
    ):
        ctx = json.loads(_run_prompt(prompt))["hookSpecificOutput"]["additionalContext"]
        assert "已锁定" not in ctx, f"注释开头被当成 command: {prompt!r}"
        assert "判定行格式" in ctx, f"没走正常判定分支: {prompt!r}"


def test_continuation_match_is_exact_not_substring() -> None:
    """归一只去大小写与结尾标点, 带内容的「继续 xxx」仍是新任务, 必须照常判定。"""
    ctx = json.loads(_run_prompt("继续把 a.py 改完"))["hookSpecificOutput"]["additionalContext"]
    assert "判定行格式" in ctx


def test_explicit_skill_prefix_stays_silent() -> None:
    """开头点名 skill/command 时判定层一句不注 —— 用户已选好路径, 注判定规则只会给改判由头。

    用一句必然报 flow 的输入 (改动动词 + 文件路径 + 多步骤) 做反证: 只要开头有
    skill 名, 都不该翻盘。
    """
    assert _run_prompt("/graphify 重构 a.py 和 b.py, 然后新增接口") == ""


def test_skein_flow_in_body_still_goes_flow() -> None:
    """输入里点名 skein-flow 的不锁 inline —— 这是用户显式要 flow, 交回 flow 自己判。

    两种前缀形态 (`/skein-flow` / `/skein:skein-flow`) 与写在中段, 判定层都一句不注:
    注 inline 锁就等于把用户点名的 flow 掰回 main 里直接干。
    """
    for prompt in ("/skein-flow 重构 a.py", "/skein:skein-flow 重构 a.py", "/foo 用 skein-flow 处理"):
        assert _run_prompt(prompt) == "", f"点名 skein-flow 时不该注入 inline 锁: {prompt}"


def test_skein_own_skills_are_not_downgraded_to_inline() -> None:
    """显式调用 skein 自家 skill 时判定层放行, 不锁 inline —— 用户已选好执行路径。"""
    for cmd in ("/skein:skein-plan 规划支付重构", "/skein-plan 规划支付重构",
                "/skein-redo 断点续跑", "/skein:skein-redo 续跑 task-1",
                "/skein-spec recall 支付", "/skein-grill 审我的方案", "/skein-setup"):
        assert _run_prompt(cmd) == "", cmd


def test_non_skein_slash_command_stays_silent() -> None:
    """非 skein 的 slash command 同样静默, 一律不注入。"""
    for cmd in ("/skein-performance 审计一下插件", "/foo 用 skein-planner 处理"):
        assert _run_prompt(cmd) == "", cmd


def test_verdict_rules_not_injected_anywhere() -> None:
    """判定规则段已整体删除 (判定交回模型) —— SessionStart 与每轮注入都不该再出现规则正文。

    每轮该留的只有变化量: 判定行格式模板 + plan/research task 列表。
    """
    per_turn = _capture_ctx_output()
    session = _session_ctx_output()
    for rule in ("跨≥2文件", "skein:skein-flow", "skein:skein-plan", "AskUserQuestion", "任务判定规则"):
        assert rule not in session, f"SessionStart 规则段回流: {rule}"
        assert rule not in per_turn, f"每轮注入规则正文回流: {rule}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("judge 自检过")
