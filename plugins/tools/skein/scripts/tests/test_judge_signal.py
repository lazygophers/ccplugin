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
from conftest import make_ws
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


# ── 注入文案的硬性要求 (通过 cmd_user_prompt 输出验证) ──────────────────────


def _verdict_lines(text: str) -> list[str]:
    """格式模板行 (缩进的 `[skein] 判定: …`); 散文里提到判定行的句子不算。"""
    return [ln.strip() for ln in text.splitlines() if ln.strip().startswith("[skein] 判定:")]


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
    return json.loads(buf.getvalue())["hookSpecificOutput"]["additionalContext"]


def test_ctx_demands_an_explicit_verdict_line() -> None:
    """必须要求 AI 把判定结果写出来, 且给出落地路径三条。

    判定不写出来就等于没判 —— 事后分不清「判了直接改」和「压根没想直接开干」。
    写出来才让越界当场可见 (判了 flow 却在 Edit / 判了 inline 却改了五个文件)。
    """
    ctx = _capture_ctx_output()
    assert _verdict_lines(ctx), "注入文案没给出判定行格式模板"
    for path in ("flow", "补充", "inline"):
        assert path in ctx, f"注入文案的落地路径缺 {path}"
    assert "第一行" in ctx, "注入文案没说明判定行要放第一行"


def test_every_verdict_line_demands_a_reason() -> None:
    """每条判定行模板都要带 (原因: …) —— 曾经只有 inline 那档带理由。

    只写结论不写原因, 越界看不见: 「判定: inline 直接改」后面改了五个文件, 到底是判据用错还是
    判据没读, 事后分不出来, 用户也没法纠偏到点上。原因把判据摊开, 判错才当场可反驳。
    """
    ctx = _capture_ctx_output()
    for ln in _verdict_lines(ctx):
        assert "原因" in ln, f"这条判定行没要求写原因: {ln!r}"


def test_ctx_has_no_escaped_backticks() -> None:
    """注入文案里不得出现 `\\``  —— 那是 Python 字符串转义漏出来的字面反斜杠。

    踩过一次: 前缀规则里写 \\` 想表示反引号, 注入到 prompt 后用户看到的是带反斜杠的怪字符串。
    示例格式改用缩进代码块, 不靠反引号包裹。
    """
    ctx = _capture_ctx_output()
    assert "\\`" not in ctx, "注入文案有转义漏出的反斜杠+反引号"


def test_ctx_autodrive_continues_past_create_to_a_real_user_gate() -> None:
    """回归: 「判了 flow 就必须先 create」曾只规定起点, 建完 task 后规则用尽, AI 停手报告完事。

    补的两层意思必须同段出现 (分开写等于给「只读到前半句」留口子):
    1. 建完 task 后同轮继续跑规划, 不停手等用户再喊一次
    2. 推进终点是需要真实用户动作的门 (规划确认), 撞到必须停下问用户, 不得代替用户批准

    断言语义 (「建完继续」+「终点是用户门」+「不得代替批准」), 不断具体措辞。
    """
    ctx = _capture_ctx_output()
    section = ctx[ctx.index("# 任务判定"):]

    assert "Skill(name='skein-flow'" in section, "该段丢了 flow 入口规定"
    assert "补充" in section, "该段没写旧任务补充路径"
    assert "AskUserQuestion" in section, "该段没写拿不准时要问用户"
    assert "新输入禁打断在跑的工作" in section, "该段没写新输入不能打断在途工作"


def test_three_landing_paths_are_defined_with_criteria() -> None:
    """「落地路径」段要把三条路各自的判定条件 + 拿不准时的取向都写明, 不能只给名字不给依据。

    意图是开放的, 但落地只有这三条 (建 task / 并入 / 直接做), 判据丢了就等于让 AI 拍脑袋。
    """
    ctx = _capture_ctx_output()
    body = ctx[ctx.index("# 任务判定"):]
    for token in ("flow", "inline", "补充", "其他", "判断条件", "判定条件"):
        assert token in body, f"落地路径段缺 {token}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("judge 自检过")
