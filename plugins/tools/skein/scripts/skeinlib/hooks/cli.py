from __future__ import annotations

import importlib
import sys
from typing import Any, Callable, cast

from skeinlib.hooks import DISPATCH, _ARGV_DISPATCH


def _resolve(name: str) -> Callable[..., int]:
    module_name, _, function_name = DISPATCH[name].partition(":")
    module = importlib.import_module(f"skeinlib.hooks.{module_name}")
    return cast(Callable[..., int], getattr(module, function_name))


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.stderr.write(f"用法: skein-hooks {{{'|'.join(DISPATCH)}}}\n")
        return 2
    name = sys.argv[1]
    function = _resolve(name)
    if name in _ARGV_DISPATCH:
        return function(name.split("-", 1)[1])
    payload = load_stdin()
    if payload is None:
        return 0
    return function(payload)


def self_check() -> int:
    from skeinlib.hooks.user_prompt_submit import judge_signal

    cases: list[tuple[str, list[str]]] = [
        ("改 hooks.py 和 spec.py 的判定", ["具体文件路径", "改动类动词"]),
        ("在 src/auth.py 加 login 函数", ["具体文件路径", "改动类动词"]),
        ("参考 admin-api 搭建骨架, 用 go-zero 脚手架", ["新建类信号"]),
        ("什么是 SKEIN", ["查询类词"]),
        ("先做 a 然后做 b 接着做 c", ["多步骤标记"]),
        ("继续", ["短句零信号(可能是对前文方案的授权 — 回看上文按那个方案的复杂度判档, 禁按字面当简单请求)"]),
    ]
    failures: list[tuple[str, Any, Any, str]] = []
    if not isinstance(judge_signal("test"), list):
        failures.append(("judge_signal", "list", type(judge_signal("test")).__name__, "应返回 list"))
    for prompt, expected in cases:
        evidence = judge_signal(prompt)
        for signal in expected:
            if signal not in evidence:
                failures.append((prompt, signal, evidence, "期望证据缺失"))
        print(f"  ev={evidence} | {prompt!r}")
    print(f"FAIL count: {len(failures)}")
    return 1 if failures else 0


from skeinlib.hooks.util import load_stdin

__all__ = ["DISPATCH", "_ARGV_DISPATCH", "_resolve", "main", "self_check"]
