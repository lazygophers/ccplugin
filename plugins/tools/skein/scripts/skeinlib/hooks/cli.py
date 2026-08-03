"""hook 子命令分发 —— **懒加载**是这个模块存在的全部理由。

## 为什么 DISPATCH 存的是字符串而不是函数
`{"fmt": cmd_fmt}` 这种写法要求把 11 个子命令的模块**全部**先 import 一遍, 才能拿到函数对象。
于是每跑一次 `permission` (用户每次授权都跑), 都要顺带加载 `subprocess`、`pathlib`、
整个 `skeinlib.spec` 门面 —— 全是 fmt / stop-check 才用得上的东西。

存 `"模块:函数名"` 字符串, 真正被选中的那一个才 import。热子命令 (permission / user-prompt /
flow-gate) 因此只加载自己那条链。代价是 IDE 跳转不过去, 换来的是每次对话省下的几十毫秒 ——
这层的取舍一律偏向后者。

## 两种参数协议
harness 那 9 个走 stdin JSON; `agent-start` / `agent-stop` 走 `--flag value` argv
(见 `agent.py`), 列在 `_ARGV_DISPATCH` 里, **不读 stdin** —— 免得没有输入时空等。
"""
from __future__ import annotations

import importlib
import sys
from typing import Any, Callable, cast

from skeinlib.hooks.util import load_stdin

# 子命令 → "模块名:函数名" (模块相对 skeinlib.hooks)。**禁改成直接存函数对象** —— 见模块 docstring。
DISPATCH: dict[str, str] = {
    "permission": "permission:cmd_permission",
    "guard": "guard:cmd_guard",
    "batch": "batch:cmd_batch",
    "report": "report:cmd_report",
    "fmt": "fmt:cmd_fmt",
    "spec-meta": "spec_meta:cmd_spec_meta",
    "flow-gate": "flow_gate:cmd_flow_gate",
    "stop-check": "stopcheck:cmd_stop_check",
    "user-prompt": "prompt:cmd_user_prompt",
    "agent-start": "agent:cmd_agent_hook",
    "agent-stop": "agent:cmd_agent_hook",
}

# dispatch 参数式子命令 (design.md §1): 参数走 --flag argv 而非 stdin JSON
_ARGV_DISPATCH = {"agent-start", "agent-stop"}


def _resolve(name: str) -> Callable[..., int]:
    mod_name, _, attr = DISPATCH[name].partition(":")
    mod = importlib.import_module(f"skeinlib.hooks.{mod_name}")
    return cast(Callable[..., int], getattr(mod, attr))


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.stderr.write(f"用法: skein-hooks {{{'|'.join(DISPATCH)}}}\n")
        return 2
    name = sys.argv[1]
    fn = _resolve(name)
    if name in _ARGV_DISPATCH:
        return fn(name.split("-", 1)[1])   # agent-start → "start"
    d = load_stdin()
    if d is None:
        return 0  # stdin 非法 JSON: 静默放行
    return fn(d)


def self_check() -> int:
    """`skein-hooks --self-check` — _judge_signal 的证据命中 + _CTX 拼接自检。

    ponytail: 判定逻辑是 non-trivial 分支, 留 ONE runnable check。pytest 那边有
    test_judge_signal.py (14 条) 做正式覆盖, 这条是不装 pytest 也能跑的兜底。
    """
    from skeinlib.hooks import judge
    from skeinlib.hooks.judge import _CTX, _judge_signal

    cases: list[tuple[str, list[str]]] = [
        ("改 hooks.py 和 spec.py 的判定", ["文件路径×2", "改动类动词", "跨文件连接词"]),
        ("在 src/auth.py 加 login 函数", ["文件路径×1", "改动类动词"]),
        ("参考 admin-api 搭建骨架, 用 go-zero 脚手架", ["新建类信号"]),
        ("什么是 SKEIN", ["查询类词"]),
        ("先做 a 然后做 b 接着做 c", ["多步骤标记"]),
        ("继续", []),
    ]
    fails: list[tuple[str, Any, Any, str]] = []
    shape = _judge_signal("test")
    if not isinstance(shape, list):
        fails.append(("_judge_signal", "list", type(shape).__name__, "应返回 list"))
    for p, must_have in cases:
        ev = _judge_signal(p)
        for sig in must_have:
            if sig not in ev:
                fails.append((p, sig, ev, "期望证据缺失"))
        print(f"  ev={ev} | {p!r}")
    # 证据行: 非空才拼 "本次命中", 空 _CTX 无 "本次命中"
    ctx_hit = _CTX + f"\n本次命中: {', '.join(_judge_signal('改 a.py 和 b.py'))}"
    if "本次命中" not in ctx_hit:
        fails.append(("ctx-hit", "has-line", "本次命中", "evidence 非空未拼本次命中行"))
    if "本次命中" in _CTX:
        fails.append(("ctx-empty", "no-line", "本次命中", "_CTX 默认含本次命中行 (应空时不展示)"))
    # 单一 _CTX: 三常量须已删
    for stale in ("_CTX_FLOW", "_CTX_INLINE", "_CTX_GREY"):
        if hasattr(judge, stale):
            fails.append(("_CTX", "single-ctx", stale, "应只留 _CTX"))
    # 正向化自检
    for bad in ("MUST", "禁", "违规", "黑名单"):
        if bad in _CTX:
            fails.append(("_CTX", "no-negation", bad, "正向化破规"))
    print(f"FAIL count: {len(fails)}")
    return 1 if fails else 0
