"""`judge_signal` 单测 — 任务复杂度判定的启发式打分。

拆包前这层埋在 hooks.py 里, 想验一句 prompt 判成什么档只能起子进程喂 stdin; 现在它在
`skeinlib.hooks.user_prompt_submit` 且只依赖 stdlib, 直调即可 —— 全套 11 项 0.02 秒, 换子进程要 5 秒+。

**误判代价不对称**: 漏判 = 复杂任务不建 task 直接开干 (贵, 事后要回滚重来);
误判 = 多一句「考虑建 task」的提示 (便宜)。所以词表刻意偏向报警, 下面的断言也按这个方向写。
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path (standalone 直跑时 pytest 不在)
from conftest import make_ws, run_skein
from skeinlib.hooks.user_prompt_submit import judge_signal  # noqa: E402


def sig(p: str) -> set[str]:
    return set(judge_signal(p))


def test_empty_prompt_no_signal() -> None:
    assert judge_signal("") == []
    assert judge_signal("   ") == []
    assert judge_signal(None) == []  # type: ignore[arg-type] # hook 拿到的 payload 可能缺字段


def test_action_verbs_hit() -> None:
    for p in ("重构一下认证模块", "优化这段查询", "修复登录失败", "设计一个缓存层", "排查这个超时"):
        assert "改动类动词" in sig(p), p


def test_file_path_is_strongest_signal() -> None:
    """带具体路径几乎必是改动类 —— 即使句子本身像个问句。"""
    for p in ("看看 src/auth/login.py", "./scripts/build.sh 是干嘛的", "改 a.ts 和 b.tsx"):
        assert "具体文件路径" in sig(p), p


def test_bare_noun_is_not_a_path() -> None:
    """纯名词不该被当路径 —— 误判成路径会让每句闲聊都触发建 task 提示。"""
    for p in ("这个方案怎么样", "帮我想想名字"):
        assert "具体文件路径" not in sig(p), p


def test_cross_file_connectives() -> None:
    for p in ("顺便把日志也加上", "这两处一起改", "分别处理这几个"):
        assert "跨文件连接词" in sig(p), p


def test_he_is_not_a_cross_signal() -> None:
    """回归: 「和」曾在 _FLOW_CROSS 里, 中文几乎每句都有, 近 100% 误报。禁再加回去。"""
    assert "跨文件连接词" not in sig("介绍一下 skein 和它的设计")


def test_action_beats_query() -> None:
    """问句包装的改动请求仍是改动 —— 查询词不得压过改动信号。"""
    ev = sig("如何重构这个模块")  # 「如何」在 _INLINE_Q, 「重构」在 _FLOW_VERBS
    assert "改动类动词" in ev
    assert any(e.startswith("查询类词(被改动信号覆盖") for e in ev), ev


def test_pure_query_stays_query() -> None:
    ev = sig("skein 的 spec 是什么意思")  # 纯查询: 无任何改动动词
    assert "查询类词" in ev
    assert "查询类词(被改动信号覆盖, 按 flow 判)" not in ev


def test_short_prompt_fallback_is_authorization_not_simple_request() -> None:
    """短句零信号 = 多轮对话里的授权 (「需要」「继续」), hook 看不到上文, 只能靠长度兜。

    这条兜底的存在理由: 用户说「需要」时上文可能是个 20 个 subtask 的方案, 按字面当简单请求
    会直接开干且不建 task。
    """
    for p in ("需要", "继续", "做吧", "开始"):
        ev = judge_signal(p)
        assert len(ev) == 1 and ev[0].startswith("短句零信号"), (p, ev)


def test_long_prompt_never_hits_short_fallback() -> None:
    """长句零信号 → 不兜底。掉进兜底说明词表缺词, 那是词表的 bug, 不该由长度阈值掩盖。"""
    long_no_signal = "这个东西的历史背景大概是怎样的呢我想了解一下来龙去脉"
    assert len(long_no_signal) > 12
    assert not any(e.startswith("短句零信号") for e in judge_signal(long_no_signal))


def test_signals_accumulate() -> None:
    """多信号同时命中要全部列出 —— 证据是给 AI 读的, 不是打个总分。"""
    ev = sig("重构 src/a.py 和 src/b.py, 顺便加上测试")
    assert {"改动类动词", "具体文件路径", "跨文件连接词"} <= ev, ev


# ── 注入文案的硬性要求 ────────────────────────────────────────────────────
#
# 判定规则本身逐字不变, 走 SessionStart (`skein session-context`) 注一次;
# UserPromptSubmit 只注每轮变化的部分 (判定行格式 + 机械判定 evidence + task 阶段 + 运行配置)。
# 下面按这条分界线验: 规则文案查 session-context 出口, 每轮行为查 cmd_user_prompt 出口。


_SESSION_CTX: list[str] = []


def _session_ctx_output() -> str:
    """跑 `skein session-context`, 返回 SessionStart 注入文案 (一次子进程, 全模块复用)。"""
    if not _SESSION_CTX:
        with tempfile.TemporaryDirectory() as td:
            ws = make_ws(Path(td))
            out = run_skein(ws, "session-context").stdout
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
    """必须要求 AI 把判定结果写出来, 且给出全部落地路径。

    判定不写出来就等于没判 —— 事后分不清「判了直接改」和「压根没想直接开干」。
    写出来才让越界当场可见 (判了 flow 却在 Edit / 判了 inline 却改了五个文件)。
    每轮都要照写, 所以格式模板必须留在 UserPromptSubmit; 档位清单只需 SessionStart 注一次。
    """
    assert _verdict_lines(_capture_ctx_output()), "每轮注入丢了判定行格式模板"
    rules = _session_ctx_output()
    assert _verdict_lines(rules), "SessionStart 规则段没给出判定行格式模板"
    for path in ("flow", "plan", "补充", "inline"):
        assert path in rules, f"规则段的落地路径缺 {path}"
    assert "第一行" in rules, "规则段没说明判定行要放第一行"


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


def test_ctx_autodrive_continues_past_create_to_a_real_user_gate() -> None:
    """回归: 「判了 flow 就必须先 create」曾只规定起点, 建完 task 后规则用尽, AI 停手报告完事。

    补的两层意思必须同段出现 (分开写等于给「只读到前半句」留口子):
    1. 建完 task 后同轮继续跑规划, 不停手等用户再喊一次
    2. 推进终点是需要真实用户动作的门 (规划确认), 撞到必须停下问用户, 不得代替用户批准

    断言语义 (「建完继续」+「终点是用户门」+「不得代替批准」), 不断具体措辞。
    """
    ctx = _session_ctx_output()
    section = ctx[ctx.index("# 任务判定规则"):]

    # 必须是插件全限定名: 裸 `skein-flow` 实测报过 `Unknown skill`
    assert "skein:skein-flow" in section, "该段丢了 flow 入口规定"
    assert "补充" in section, "该段没写旧任务补充路径"
    assert "AskUserQuestion" in section, "该段没写拿不准时要问用户"
    assert "新输入禁打断在跑工作" in section, "该段没写新输入不能打断在途工作"


def test_landing_paths_are_defined_with_criteria() -> None:
    """每档落地路径都要「判据 + 去哪」成对写明, 不能只给名字。

    意图是开放的, 但落地只有这几条 (规划 / 建 task / 并入 / 直接做 / 问用户),
    判据或去向丢一半都等于让 AI 拍脑袋。
    """
    body = _session_ctx_output()
    body = body[body.index("# 任务判定规则"):]
    for gear, criterion, landing in (
        ("plan", "需求未定", "skein:skein-plan"),
        ("flow", "多步骤", "skein:skein-flow"),
        ("补充", "在途 task", "skein:skein-flow"),
        ("inline", "纯查询", "main 中直接执行"),
        ("其他", "", "AskUserQuestion"),
    ):
        line = next((ln for ln in body.splitlines() if ln.startswith(f"- **{gear}**")), "")
        assert line, f"落地路径段缺 {gear} 档"
        assert criterion in line, f"{gear} 档只给了名字没给判据: {line!r}"
        assert landing in line, f"{gear} 档没写去哪: {line!r}"


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
    """`/` 开头的绝对路径不是 slash command, 仍须走正常机械判定。"""
    out = _run_prompt("/src/auth.py 怎么改")
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "已锁定" not in ctx
    assert "具体文件路径" in ctx


def test_ide_opened_file_wrapper_does_not_hide_skill_prefix() -> None:
    """IDE 元数据不属于用户 prompt, 剥掉后仍应识别真正的开头 skill。"""
    prompt = "<ide_opened_file>/tmp/foo.py</ide_opened_file>\n/graphify 重构 a.py"
    ctx = json.loads(_run_prompt(prompt))["hookSpecificOutput"]["additionalContext"]
    assert "已锁定" in ctx
    assert "机械判定" not in ctx


def test_harness_continuation_prompt_skips_judgement() -> None:
    """harness 自动续跑不是新用户任务, 不应重复注入判定块。"""
    for prompt in (
        "Continue from where you left off.",
        "Please continue from where you left off.",
        "Continue the conversation from where we left it off.",
        "CONTINUE FROM WHERE YOU LEFT OFF!",
    ):
        assert _run_prompt(prompt) == "", prompt


def test_harness_continuation_prompt_keeps_live_task_context() -> None:
    """harness 续跑不重复判定, 但必须告诉 main 当前在途 task。"""
    with tempfile.TemporaryDirectory() as td:
        ws = make_ws(Path(td))
        run_skein(ws, "create", "resume-me", "--name", "resume", "--desc", "d")
        ctx = json.loads(_run_prompt_in_ws(ws, "Continue from where you left off."))["hookSpecificOutput"]["additionalContext"]
        assert "resume-me(plan)" in ctx
        assert "判定行格式" not in ctx
        assert "机械判定" not in ctx
        # 运行配置 SessionStart 已注一份, 每轮重发是纯浪费
        assert "SKEIN 运行配置" not in ctx
        judged = json.loads(_run_prompt_in_ws(ws, "改一下 a.py"))["hookSpecificOutput"]["additionalContext"]
        assert "SKEIN 运行配置" not in judged


def test_system_wrapper_does_not_affect_prompt_judgement() -> None:
    """system-reminder 是 harness 元数据, 剥掉后按真实用户输入判定。"""
    prompt = "<system-reminder>ignore /fake-command</system-reminder>\n/src/auth.py 怎么改"
    ctx = json.loads(_run_prompt(prompt))["hookSpecificOutput"]["additionalContext"]
    assert "已锁定" not in ctx
    assert "具体文件路径" in ctx


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
        assert "机械判定" in ctx, f"没走正常判定分支: {prompt!r}"


def test_continuation_match_is_exact_not_substring() -> None:
    """归一只去大小写与结尾标点, 带内容的「继续 xxx」仍是新任务, 必须照常判定。"""
    ctx = json.loads(_run_prompt("继续把 a.py 改完"))["hookSpecificOutput"]["additionalContext"]
    assert "机械判定" in ctx and "具体文件路径" in ctx


def test_explicit_skill_prefix_locks_inline() -> None:
    """开头点名 skill/command 时锁 inline —— 用户已经选好路径, 判定层不该改判去 flow。

    用一句「机械判定」必然报 flow 的输入 (改动动词 + 文件路径 + 多步骤) 做反证: 只要开头有
    skill 名, 这些信号都不该翻盘。
    """
    out = _run_prompt("/graphify 重构 a.py 和 b.py, 然后新增接口")
    ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert "inline" in ctx, f"未锁 inline: {ctx}"
    assert "skein-flow" in ctx and "禁调 skein-flow" in ctx, f"没写死禁走 flow: {ctx}"
    assert "机械判定" not in ctx, "锁定后不该再附启发式信号, 否则又给了改判的由头"


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


def test_non_skein_slash_command_still_locks_inline() -> None:
    """非 skein 的 slash command 仍锁 inline, 放行名单不许扩成前缀模糊匹配。"""
    for cmd in ("/skein-performance 审计一下插件", "/foo 用 skein-planner 处理"):
        ctx = json.loads(_run_prompt(cmd))["hookSpecificOutput"]["additionalContext"]
        assert "已锁定" in ctx, cmd


def test_rules_are_only_in_session_context() -> None:
    """判定规则逐字不变, 只准 SessionStart 注一次 —— 钉死这次瘦身不被回退。

    回退成每轮 UserPromptSubmit 全量重发, 实测多花 ~950 字节/轮, 内容还一字不差。
    每轮该留的只有变化量: 判定行格式 + 机械判定 evidence + task 阶段 + 运行配置。
    """
    per_turn = _capture_ctx_output()
    rules = _session_ctx_output()
    for rule in ("跨≥2文件", "skein:skein-flow", "skein:skein-plan", "AskUserQuestion"):
        assert rule in rules, f"SessionStart 规则段缺 {rule}"
        assert rule not in per_turn, f"判定规则文本漏回每轮注入: {rule}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("judge 自检过")
