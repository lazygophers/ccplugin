"""`_judge_signal` 单测 — 任务复杂度判定的启发式打分。

拆包前这层埋在 hooks.py 里, 想验一句 prompt 判成什么档只能起子进程喂 stdin; 现在它在
`skeinlib.hooks.judge` 且只依赖 stdlib, 直调即可 —— 全套 11 项 0.02 秒, 换子进程要 5 秒+。

**误判代价不对称**: 漏判 = 复杂任务不建 task 直接开干 (贵, 事后要回滚重来);
误判 = 多一句「考虑建 task」的提示 (便宜)。所以词表刻意偏向报警, 下面的断言也按这个方向写。
"""
from __future__ import annotations

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path (standalone 直跑时 pytest 不在)
from skeinlib.hooks.judge import _judge_signal  # noqa: E402


def sig(p: str) -> set[str]:
    return set(_judge_signal(p))


def test_empty_prompt_no_signal() -> None:
    assert _judge_signal("") == []
    assert _judge_signal("   ") == []
    assert _judge_signal(None) == []  # type: ignore[arg-type]  hook 拿到的 payload 可能缺字段


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
        ev = _judge_signal(p)
        assert len(ev) == 1 and ev[0].startswith("短句零信号"), (p, ev)


def test_long_prompt_never_hits_short_fallback() -> None:
    """长句零信号 → 不兜底。掉进兜底说明词表缺词, 那是词表的 bug, 不该由长度阈值掩盖。"""
    long_no_signal = "这个东西的历史背景大概是怎样的呢我想了解一下来龙去脉"
    assert len(long_no_signal) > 12
    assert not any(e.startswith("短句零信号") for e in _judge_signal(long_no_signal))


def test_signals_accumulate() -> None:
    """多信号同时命中要全部列出 —— 证据是给 AI 读的, 不是打个总分。"""
    ev = sig("重构 src/a.py 和 src/b.py, 顺便加上测试")
    assert {"改动类动词", "具体文件路径", "跨文件连接词"} <= ev, ev


# ── 注入文案的硬性要求 (改 _CTX / _PREFIX_RULE 时这些不能丢) ──────────────────
def test_ctx_demands_an_explicit_verdict_line() -> None:
    """必须要求 AI 把判定结果写出来, 且三档齐全。

    判定不写出来就等于没判 —— 事后分不清「判了 inline」和「压根没想直接开干」。
    写出来才让越界当场可见 (判了 flow 却在 Edit / 判了 inline 却改了五个文件)。
    """
    from skeinlib.hooks.judge import _CTX, _PREFIX_RULE
    for text, where in ((_CTX, "_CTX"), (_PREFIX_RULE, "_PREFIX_RULE")):
        assert "判定:" in text, f"{where} 没给出判定行格式"
        for verdict in ("flow", "补充", "inline"):
            assert verdict in text, f"{where} 的判定档缺 {verdict}"
    assert "第一行" in _PREFIX_RULE, "_PREFIX_RULE 没说明判定行要放第一行"


def test_ctx_has_no_escaped_backticks() -> None:
    """注入文案里不得出现 `\\``  —— 那是 Python 字符串转义漏出来的字面反斜杠。

    踩过一次: 前缀规则里写 \\` 想表示反引号, 注入到 prompt 后用户看到的是带反斜杠的怪字符串。
    示例格式改用缩进代码块, 不靠反引号包裹。
    """
    from skeinlib.hooks.judge import _CTX, _PREFIX_RULE, _UNINIT_PLAIN, _UNINIT_TRELLIS
    for text, where in ((_CTX, "_CTX"), (_PREFIX_RULE, "_PREFIX_RULE"),
                        (_UNINIT_PLAIN, "_UNINIT_PLAIN"), (_UNINIT_TRELLIS, "_UNINIT_TRELLIS")):
        assert "\\`" not in text, f"{where} 有转义漏出的反斜杠+反引号"


def test_three_verdicts_are_defined_in_criteria() -> None:
    """判据段要把三档各自的判定条件都写明, 不能只给格式不给依据。"""
    from skeinlib.hooks.judge import _CTX
    head = _CTX[:_CTX.index("## 🛑")]
    for token in ("flow", "inline", "补充", "倾向序"):
        assert token in head, f"判据段缺 {token}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("judge 自检过")
